from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import final_episode_contract as module  # noqa: E402

FIX = ROOT / "tests" / "final-episode-contract" / "fixtures"
FINAL_SCHEMA = ROOT / "contracts" / "final_episode_contract.schema.json"
CANDIDATE_SCHEMA = ROOT / "contracts" / "financial_visual_candidate_plan.schema.json"
VG_REGISTRY = ROOT / "contracts" / "visual_grammar_semantics.json"
VG_REGISTRY_SCHEMA = ROOT / "contracts" / "visual_grammar_semantics.schema.json"


def load_contract() -> dict:
    return json.loads((FIX / "final_episode_contract.valid.json").read_text(encoding="utf-8"))


class FinalEpisodeContractTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        (self.repo / "contracts").mkdir(parents=True)
        (self.repo / "tests" / "final-episode-contract" / "fixtures").mkdir(parents=True)
        for source in (FINAL_SCHEMA, CANDIDATE_SCHEMA, VG_REGISTRY, VG_REGISTRY_SCHEMA):
            shutil.copy2(source, self.repo / "contracts" / source.name)
        for name in (
            "episode_package_2026-07-31.md",
            "visual_grammar_sidecar.valid.json",
        ):
            shutil.copy2(FIX / name, self.repo / "tests" / "final-episode-contract" / "fixtures" / name)

    def tearDown(self):
        self.tempdir.cleanup()

    def write_contract(self, contract: dict) -> Path:
        path = self.repo / "final_episode_contract.json"
        path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def validate(self, contract: dict):
        return module.validate_contract(
            self.write_contract(contract),
            self.repo,
            self.repo / "contracts" / FINAL_SCHEMA.name,
            self.repo / "contracts" / CANDIDATE_SCHEMA.name,
            self.repo / "contracts" / VG_REGISTRY.name,
            self.repo / "contracts" / VG_REGISTRY_SCHEMA.name,
        )

    def sync_file_sha(self, contract: dict, key: str) -> None:
        path = self.repo / contract[key]["path"]
        contract[key]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()

    def replace_financial_annex(self, contract: dict) -> None:
        package = self.repo / contract["episodePackage"]["path"]
        text = package.read_text(encoding="utf-8")
        start = text.index(module.FINANCIAL_ANNEX_BEGIN)
        end = text.index(module.FINANCIAL_ANNEX_END) + len(module.FINANCIAL_ANNEX_END)
        block = (
            module.FINANCIAL_ANNEX_BEGIN
            + "\n```json\n"
            + json.dumps(contract["financialVisuals"], ensure_ascii=False, indent=2)
            + "\n```\n"
            + module.FINANCIAL_ANNEX_END
        )
        package.write_text(text[:start] + block + text[end:], encoding="utf-8")
        self.sync_file_sha(contract, "episodePackage")

    def replace_visual_grammar_annex_from_sidecar(self, contract: dict) -> None:
        package = self.repo / contract["episodePackage"]["path"]
        sidecar = json.loads((self.repo / contract["visualGrammarSidecar"]["path"]).read_text(encoding="utf-8"))
        text = package.read_text(encoding="utf-8")
        start = text.index(module.VISUAL_GRAMMAR_ANNEX_BEGIN)
        end = text.index(module.VISUAL_GRAMMAR_ANNEX_END) + len(module.VISUAL_GRAMMAR_ANNEX_END)
        block = (
            module.VISUAL_GRAMMAR_ANNEX_BEGIN
            + "\n```json\n"
            + json.dumps(sidecar, ensure_ascii=False, indent=2)
            + "\n```\n"
            + module.VISUAL_GRAMMAR_ANNEX_END
        )
        package.write_text(text[:start] + block + text[end:], encoding="utf-8")
        self.sync_file_sha(contract, "episodePackage")

    def test_valid_final_episode_contract_passes(self):
        result = self.validate(load_contract())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["contractVersion"], "1.1.0")
        self.assertEqual(result["visualGrammarContractVersion"], "1.0.0")
        self.assertEqual(result["sceneCount"], 9)
        self.assertGreaterEqual(result["semanticGrammarCount"], 6)
        self.assertGreaterEqual(result["majorShiftCount"], 4)

    def test_episode_package_sha_mismatch_is_rejected(self):
        contract = load_contract()
        contract["episodePackage"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(module.ContractError, "episodePackage SHA mismatch"):
            self.validate(contract)

    def test_visual_grammar_sidecar_sha_mismatch_is_rejected(self):
        contract = load_contract()
        contract["visualGrammarSidecar"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(module.ContractError, "visualGrammarSidecar SHA mismatch"):
            self.validate(contract)

    def test_financial_annex_mismatch_is_rejected(self):
        contract = load_contract()
        contract["financialVisuals"]["intents"][0]["editorialNote"] = "changed only in sidecar"
        with self.assertRaisesRegex(module.ContractError, "does not byte-semantically mirror"):
            self.validate(contract)

    def test_visual_grammar_annex_sidecar_mismatch_is_rejected(self):
        contract = load_contract()
        sidecar_path = self.repo / contract["visualGrammarSidecar"]["path"]
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        sidecar["scenes"][0]["visualBeats"][0]["visualGrammar"]["grammarId"] = "evidence"
        sidecar_path.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.sync_file_sha(contract, "visualGrammarSidecar")
        with self.assertRaisesRegex(module.ContractError, "Visual Grammar annex does not"):
            self.validate(contract)

    def test_final_contract_sidecar_mismatch_is_rejected(self):
        contract = load_contract()
        contract["scenes"][0]["visualBeats"][0]["visualGrammar"]["grammarId"] = "evidence"
        with self.assertRaisesRegex(module.ContractError, "sidecar does not byte-semantically mirror"):
            self.validate(contract)

    def test_missing_grammar_on_any_beat_is_rejected_by_schema(self):
        contract = load_contract()
        contract["scenes"][0]["visualBeats"][0].pop("visualGrammar")
        with self.assertRaisesRegex(module.ContractError, "visualGrammar"):
            self.validate(contract)

    def test_return_requires_target(self):
        contract = load_contract()
        beat = contract["scenes"][3]["visualBeats"][1]
        beat["visualGrammar"]["returnTargetBeatId"] = None
        with self.assertRaisesRegex(module.ContractError, "not of type 'string'"):
            self.validate(contract)

    def test_non_return_rejects_target(self):
        contract = load_contract()
        beat = contract["scenes"][0]["visualBeats"][0]
        beat["visualGrammar"]["returnTargetBeatId"] = "vb-01-01"
        with self.assertRaisesRegex(module.ContractError, "not of type 'null'"):
            self.validate(contract)

    def test_unknown_return_target_is_rejected_by_semantic_validator(self):
        contract = load_contract()
        beat = contract["scenes"][3]["visualBeats"][1]
        beat["visualGrammar"]["returnTargetBeatId"] = "vb-09-99"
        sidecar_path = self.repo / contract["visualGrammarSidecar"]["path"]
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        sidecar["scenes"][3]["visualBeats"][1]["visualGrammar"]["returnTargetBeatId"] = "vb-09-99"
        sidecar_path.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.sync_file_sha(contract, "visualGrammarSidecar")
        self.replace_visual_grammar_annex_from_sidecar(contract)
        with self.assertRaisesRegex(module.ContractError, "VG_RETURN_TARGET_UNKNOWN"):
            self.validate(contract)

    def test_missing_target_beat_is_rejected(self):
        contract = load_contract()
        contract["financialVisuals"]["intents"][0]["target"]["visualBeatId"] = "vb-04-99"
        self.replace_financial_annex(contract)
        with self.assertRaisesRegex(module.ContractError, "target Visual Beat does not exist"):
            self.validate(contract)

    def test_unapproved_intent_is_rejected_by_schema(self):
        contract = load_contract()
        contract["financialVisuals"]["intents"][0]["status"] = "proposed"
        self.replace_financial_annex(contract)
        with self.assertRaisesRegex(module.ContractError, "approved"):
            self.validate(contract)

    def test_preferred_plan_path_mismatch_is_rejected(self):
        contract = load_contract()
        contract["financialVisuals"]["candidatePlans"][0]["path"] = "fallback"
        self.replace_financial_annex(contract)
        with self.assertRaisesRegex(module.ContractError, "path must be preferred"):
            self.validate(contract)

    def test_missing_fallback_plan_is_rejected(self):
        contract = load_contract()
        contract["financialVisuals"]["candidatePlans"].pop()
        self.replace_financial_annex(contract)
        with self.assertRaisesRegex(module.ContractError, "fallback plan not found"):
            self.validate(contract)

    def test_plan_unknown_source_is_rejected(self):
        contract = load_contract()
        contract["financialVisuals"]["candidatePlans"][0]["sourceIds"] = ["source-999"]
        self.replace_financial_annex(contract)
        with self.assertRaisesRegex(module.ContractError, "undeclared intent sources"):
            self.validate(contract)

    def test_display_order_must_exactly_cover_objects(self):
        contract = load_contract()
        contract["financialVisuals"]["candidatePlans"][0]["displayOrder"] = ["aws-expected", "aws-actual"]
        self.replace_financial_annex(contract)
        with self.assertRaisesRegex(module.ContractError, "displayOrder must exactly cover"):
            self.validate(contract)

    def test_manual_selection_before_compiler_is_rejected(self):
        contract = load_contract()
        state = contract["financialVisuals"]["intents"][0]["selectionState"]
        state["compilerSelection"] = "preferred"
        state["selectedPlanId"] = "fvp-aws-gap-preferred"
        self.replace_financial_annex(contract)
        with self.assertRaises(module.ContractError):
            self.validate(contract)

    def test_missing_visual_beat_marker_is_rejected(self):
        contract = load_contract()
        package = self.repo / contract["episodePackage"]["path"]
        text = package.read_text(encoding="utf-8").replace(
            "<!--VISUAL_BEAT:scene-04:vb-04-02-->", ""
        )
        package.write_text(text, encoding="utf-8")
        self.sync_file_sha(contract, "episodePackage")
        with self.assertRaisesRegex(module.ContractError, "marker must appear exactly once"):
            self.validate(contract)

    def test_duplicate_visual_beat_marker_is_rejected(self):
        contract = load_contract()
        package = self.repo / contract["episodePackage"]["path"]
        marker = "<!--VISUAL_BEAT:scene-04:vb-04-02-->"
        text = package.read_text(encoding="utf-8").replace(marker, marker + "\n" + marker, 1)
        package.write_text(text, encoding="utf-8")
        self.sync_file_sha(contract, "episodePackage")
        with self.assertRaisesRegex(module.ContractError, "duplicate Visual Beat marker"):
            self.validate(contract)

    def test_fallback_human_text_must_be_complete(self):
        contract = load_contract()
        beat = contract["scenes"][3]["visualBeats"][1]
        beat["fallbackHeadline"] = ""
        with self.assertRaises(module.ContractError):
            self.validate(contract)

    def test_candidate_plan_rejects_arbitrary_renderer_fields(self):
        contract = load_contract()
        contract["financialVisuals"]["candidatePlans"][0]["component"] = "ArbitraryReact"
        self.replace_financial_annex(contract)
        with self.assertRaises(module.ContractError):
            self.validate(contract)


if __name__ == "__main__":
    unittest.main()
