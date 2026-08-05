from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import financial_recipe_compiler as compiler  # noqa: E402
import financial_visual_cross_artifact as cross  # noqa: E402

FIX = ROOT / "tests" / "final-episode-contract" / "fixtures"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_render_spec(date: str = "2026-07-31") -> dict:
    scenes = []
    for number in range(1, 10):
        sid = f"scene-{number:02d}"
        chunk_id = f"{sid}-chunk-001"
        beat_ids = [f"vb-{number:02d}-01"]
        if number == 4:
            beat_ids.append("vb-04-02")
        beats = []
        for beat_id in beat_ids:
            beats.append({
                "beatId": beat_id,
                "startChunkId": chunk_id,
                "endChunkId": chunk_id,
                "narrationStartCue": f"Speech {number}.",
                "narrationEndCue": f"Speech {number}.",
                "primaryFunction": "Explain",
                "screenState": "Data",
                "visualMode": "text-focus",
                "visualTemplate": "text-focus",
                "templateConfig": {},
                "sequencePolicy": "static",
                "finalHoldMs": 500,
                "contentType": "text",
                "screenQuestion": f"Question {number}",
                "primaryElement": f"Primary {number}",
                "viewerTexts": [f"Viewer {number}"],
                "changeCue": f"Caption {number}",
                "objectIds": [],
                "assetPlacementIds": [],
                "assetState": "not-required",
                "returnScreenState": None,
                "evidenceSourceIds": ["source-001"],
                "expressionChange": None,
                "fallback": None,
                "entity": None,
                "pictureBook": None,
            })
        scenes.append({
            "sceneId": sid,
            "sceneNumber": number,
            "headline": f"Headline {number}",
            "supportingTexts": [f"Support {number}"],
            "narrationChunks": [{
                "chunkId": chunk_id,
                "speechText": f"Speech {number}.",
                "captionText": f"Caption {number}",
                "expression": "通常",
                "pauseAfterMs": 200,
            }],
            "visualBeats": beats,
            "assetPlacements": [],
        })
    return {
        "schemaVersion": "2.2.0",
        "episode": {"id": date, "targetDate": date},
        "publishing": {},
        "review": {"verdict": "approved", "approvedForCodex": True},
        "scenes": scenes,
    }


class FinancialVisualCrossArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.production = self.repo / "production-root"
        for name in (
            "final_episode_contract.schema.json",
            "financial_visual_candidate_plan.schema.json",
            "financial_recipe_registry.json",
            "financial_recipe_plan.schema.json",
            "financial_visual_diversity_report.schema.json",
            "financial_visual_consistency_report.schema.json",
        ):
            (self.repo / "contracts").mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "contracts" / name, self.repo / "contracts" / name)

        fixture_dir = self.repo / "tests" / "final-episode-contract" / "fixtures"
        fixture_dir.mkdir(parents=True)
        shutil.copy2(FIX / "episode_package_2026-07-31.md", fixture_dir)
        contract = json.loads((FIX / "final_episode_contract.valid.json").read_text(encoding="utf-8"))
        self.date = contract["episodeDate"]
        self.final_contract_path = self.repo / "production" / self.date / "final_episode_contract.json"
        write_json(self.final_contract_path, contract)
        self.recipe_plan_path = self.repo / "production" / self.date / "financial_recipe_plan.json"
        self.compile_recipe()
        self.create_base_production()

    def tearDown(self):
        self.temp.cleanup()

    def compile_recipe(self) -> dict:
        value = compiler.compile_recipe_plan(
            self.final_contract_path,
            self.repo,
            self.repo / "contracts/financial_recipe_registry.json",
            self.repo / "contracts/financial_recipe_plan.schema.json",
            self.repo / "contracts/final_episode_contract.schema.json",
            self.repo / "contracts/financial_visual_candidate_plan.schema.json",
        )
        write_json(self.recipe_plan_path, value)
        return value

    def create_base_production(self) -> None:
        date = self.date
        render_path = self.production / "render-specs" / date / "render_spec.json"
        spoken_path = self.production / "episodes" / date / f"spoken_script_{date}.md"
        asset_path = self.production / "episodes" / date / "asset_manifest.json"
        consistency_path = self.production / "verification" / date / "production_consistency_report.json"
        preflight_path = self.production / "verification" / date / "official_execution_preflight.json"
        write_json(render_path, make_render_spec(date))
        spoken_path.parent.mkdir(parents=True, exist_ok=True)
        spoken_path.write_text("\n".join(f"Speech {i}." for i in range(1, 10)) + "\n", encoding="utf-8")
        write_json(asset_path, {
            "contract_version": "1.0.0",
            "episode_date": date,
            "selected_path": "not-required",
            "assets": [],
        })
        write_json(consistency_path, {
            "contract_version": "1.0.0",
            "episode_date": date,
            "status": "pass",
            "errors": [],
            "unresolved_states": 0,
        })
        write_json(preflight_path, {
            "contract_version": "1.0.0",
            "episode_date": date,
            "status": "pass",
            "artifacts": {
                "render_spec": sha(render_path),
                "spoken_script": sha(spoken_path),
                "asset_manifest": sha(asset_path),
                "consistency_report": sha(consistency_path),
            },
            "unresolved_states": 0,
            "preview_authorized": True,
            "final_authorized": False,
            "warnings": [],
        })

    def integrate(self, diversity: Path | None = None) -> dict:
        return cross.integrate(
            final_contract_path=self.final_contract_path,
            recipe_plan_path=self.recipe_plan_path,
            repo_root=self.repo,
            production_root=self.production,
            renderer_schema_version="2.3.0",
            final_schema_path=self.repo / "contracts/final_episode_contract.schema.json",
            candidate_schema_path=self.repo / "contracts/financial_visual_candidate_plan.schema.json",
            registry_path=self.repo / "contracts/financial_recipe_registry.json",
            recipe_plan_schema_path=self.repo / "contracts/financial_recipe_plan.schema.json",
            diversity_schema_path=self.repo / "contracts/financial_visual_diversity_report.schema.json",
            consistency_schema_path=self.repo / "contracts/financial_visual_consistency_report.schema.json",
            diversity_report_path=diversity,
        )

    def load_render(self) -> dict:
        return json.loads((self.production / "render-specs" / self.date / "render_spec.json").read_text())

    def target_beat(self, render: dict | None = None) -> dict:
        render = render or self.load_render()
        scene = next(scene for scene in render["scenes"] if scene["sceneId"] == "scene-04")
        return next(beat for beat in scene["visualBeats"] if beat["beatId"] == "vb-04-02")

    def rewrite_financial_annex(self, contract: dict) -> None:
        package = self.repo / contract["episodePackage"]["path"]
        text = package.read_text(encoding="utf-8")
        start = text.index("<!--BEGIN_FINANCIAL_VISUAL_ANNEX-->")
        end = text.index("<!--END_FINANCIAL_VISUAL_ANNEX-->") + len("<!--END_FINANCIAL_VISUAL_ANNEX-->")
        block = (
            "<!--BEGIN_FINANCIAL_VISUAL_ANNEX-->\n```json\n"
            + json.dumps(contract["financialVisuals"], ensure_ascii=False, indent=2)
            + "\n```\n<!--END_FINANCIAL_VISUAL_ANNEX-->"
        )
        package.write_text(text[:start] + block + text[end:], encoding="utf-8")
        contract["episodePackage"]["sha256"] = sha(package)
        write_json(self.final_contract_path, contract)

    def make_fallback(self) -> Path:
        contract = json.loads(self.final_contract_path.read_text())
        contract["financialVisuals"]["intents"][0]["metrics"][2]["numericValue"] = 1.2
        self.rewrite_financial_annex(contract)
        self.compile_recipe()
        report = {
            "contractVersion": "1.0.0",
            "episodeDate": self.date,
            "recipePlanSha256": sha(self.recipe_plan_path),
            "status": "pass",
            "reviewedAfterFallback": True,
            "checks": {
                "screenStateTypesAtLeast3": True,
                "nonAnalysisBeatsAtLeast2": True,
                "frontBackMajorChange": True,
                "noFourConsecutiveSameState": True,
                "heroCardCondition": True,
                "returnTargetsConfirmed": True,
            },
            "reviewNote": "Fallback後も画面多様性を確認済み。",
        }
        path = self.repo / "production" / self.date / "financial_visual_diversity_report.json"
        write_json(path, report)
        return path

    def test_01_preferred_integration_passes(self):
        result = self.integrate()
        self.assertEqual("pass", result["status"])
        self.assertEqual(1, result["selectionCount"])
        self.assertEqual(0, result["fallbackCount"])

    def test_02_selected_template_and_trace_are_frozen(self):
        self.integrate()
        beat = self.target_beat()
        self.assertEqual("earnings-surprise", beat["visualTemplate"])
        self.assertEqual("zero-baseline", beat["templateVariant"])
        self.assertEqual("preferred", beat["financialVisualTrace"]["selectedPath"])
        self.assertEqual(sha(self.recipe_plan_path), beat["financialVisualTrace"]["recipePlanSha256"])

    def test_03_public_cues_come_from_final_episode_contract(self):
        self.integrate()
        beat = self.target_beat()
        self.assertEqual("Expectedを説明し始める", beat["narrationStartCue"])
        self.assertEqual("Gapの意味を言い切る", beat["narrationEndCue"])
        self.assertEqual("それでも市場が見た差は何か", beat["screenQuestion"])

    def test_04_objects_sources_and_comparison_match_selected_plan(self):
        self.integrate()
        beat = self.target_beat()
        self.assertEqual(["aws-expected", "aws-actual", "aws-gap"], beat["objectIds"])
        self.assertEqual(["source-001"], beat["evidenceSourceIds"])
        self.assertEqual("AWS revenue, same quarter and currency", beat["templateConfig"]["comparisonBasis"])

    def test_05_stale_recipe_plan_is_rejected(self):
        plan = json.loads(self.recipe_plan_path.read_text())
        plan["selections"][0]["reasonCodes"] = ["PREFERRED_PLAN_INVALID"]
        write_json(self.recipe_plan_path, plan)
        with self.assertRaisesRegex(cross.CrossArtifactError, "stale"):
            self.integrate()

    def test_06_missing_target_render_beat_is_rejected(self):
        render = self.load_render()
        scene = next(scene for scene in render["scenes"] if scene["sceneId"] == "scene-04")
        scene["visualBeats"] = [beat for beat in scene["visualBeats"] if beat["beatId"] != "vb-04-02"]
        write_json(self.production / "render-specs" / self.date / "render_spec.json", render)
        with self.assertRaisesRegex(cross.CrossArtifactError, "missing"):
            self.integrate()

    def test_07_render_episode_date_mismatch_is_rejected(self):
        render = self.load_render()
        render["episode"]["targetDate"] = "2026-08-01"
        write_json(self.production / "render-specs" / self.date / "render_spec.json", render)
        with self.assertRaisesRegex(cross.CrossArtifactError, "render spec episode date"):
            self.integrate()

    def test_08_missing_spoken_text_is_rejected(self):
        path = self.production / "episodes" / self.date / f"spoken_script_{self.date}.md"
        path.write_text(path.read_text().replace("Speech 4.", ""), encoding="utf-8")
        with self.assertRaisesRegex(cross.CrossArtifactError, "spoken script"):
            self.integrate()

    def test_09_asset_manifest_date_mismatch_is_rejected(self):
        path = self.production / "episodes" / self.date / "asset_manifest.json"
        value = json.loads(path.read_text())
        value["episode_date"] = "2026-08-01"
        write_json(path, value)
        with self.assertRaisesRegex(cross.CrossArtifactError, "asset manifest episode date"):
            self.integrate()

    def test_10_non_selected_metadata_is_removed(self):
        render = self.load_render()
        beat = self.target_beat(render)
        beat["preferredPlanId"] = "leak"
        beat["fallbackPlanId"] = "leak"
        write_json(self.production / "render-specs" / self.date / "render_spec.json", render)
        self.integrate()
        beat = self.target_beat()
        self.assertNotIn("preferredPlanId", beat)
        self.assertNotIn("fallbackPlanId", beat)

    def test_11_fallback_requires_diversity_report(self):
        self.make_fallback()
        with self.assertRaisesRegex(cross.CrossArtifactError, "requires a post-fallback diversity"):
            self.integrate()

    def test_12_fallback_with_approved_diversity_passes(self):
        diversity = self.make_fallback()
        result = self.integrate(diversity)
        self.assertEqual(1, result["fallbackCount"])
        self.assertEqual("pass", result["fallbackDiversity"])
        beat = self.target_beat()
        self.assertEqual("expected-actual-bullet", beat["visualTemplate"])
        self.assertEqual("fallback", beat["financialVisualTrace"]["selectedPath"])

    def test_13_diversity_recipe_sha_mismatch_is_rejected(self):
        diversity = self.make_fallback()
        report = json.loads(diversity.read_text())
        report["recipePlanSha256"] = "0" * 64
        write_json(diversity, report)
        with self.assertRaisesRegex(cross.CrossArtifactError, "recipePlanSha256"):
            self.integrate(diversity)

    def test_14_preflight_is_rebound_and_final_stays_blocked(self):
        result = self.integrate()
        preflight = json.loads((self.production / "verification" / self.date / "official_execution_preflight.json").read_text())
        self.assertEqual("pass", preflight["financial_visuals"]["status"])
        self.assertEqual(result["hashes"]["render_spec"], preflight["artifacts"]["render_spec"])
        self.assertTrue(preflight["preview_authorized"])
        self.assertFalse(preflight["final_authorized"])

    def test_15_rerun_is_byte_identical(self):
        first = self.integrate()
        second = self.integrate()
        self.assertEqual(first["hashes"], second["hashes"])

    def test_16_diversity_report_is_forbidden_without_fallback(self):
        report = self.repo / "fake-diversity.json"
        report.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(cross.CrossArtifactError, "must be omitted"):
            self.integrate(report)


if __name__ == "__main__":
    unittest.main()
