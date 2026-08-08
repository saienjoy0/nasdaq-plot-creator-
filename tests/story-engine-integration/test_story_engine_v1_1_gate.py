from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_relative(src_root: Path, dst_root: Path, relative: str) -> Path:
    source = src_root / relative
    target = dst_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


class CriticReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_module(
            "critic_receipt_v11_test",
            ROOT / "scripts/story-engine/validate_critic_execution_receipt.py",
        )
        cls.request = ROOT / "working/2026-08-06/story-engine/templates/critic_request.json"
        cls.receipt = ROOT / "working/2026-08-06/story-engine/templates/critic_execution_receipt.json"
        cls.request_schema = ROOT / "skills/nasdaq-cafe-story-engine/contracts/critic_request.schema.json"
        cls.receipt_schema = ROOT / "skills/nasdaq-cafe-story-engine/contracts/critic_execution_receipt.schema.json"

    def validate(self, request: Path, receipt: Path, root: Path):
        return self.validator.validate(
            request,
            receipt,
            repo_root=root,
            request_schema=self.request_schema,
            receipt_schema=self.receipt_schema,
        )

    def test_committed_critic_receipt_passes(self):
        result = self.validate(self.request, self.receipt, ROOT)
        self.assertEqual("pass", result["status"], result)
        warning_codes = {item["code"] for item in result["warnings"]}
        self.assertIn("W_NOT_CRYPTOGRAPHIC", warning_codes)

    def test_same_author_and_critic_id_is_rejected(self):
        receipt_doc = json.loads(self.receipt.read_text(encoding="utf-8"))
        receipt_doc["critic_invocation_id"] = receipt_doc["author_invocation_id"]
        with tempfile.TemporaryDirectory() as temp:
            receipt_path = Path(temp) / "receipt.json"
            receipt_path.write_text(json.dumps(receipt_doc, ensure_ascii=False), encoding="utf-8")
            result = self.validate(self.request, receipt_path, ROOT)
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("E_CRITIC_ID", codes)
        self.assertIn("E_NOT_INDEPENDENT", codes)

    def test_frozen_input_blob_drift_is_rejected(self):
        request_doc = copy.deepcopy(json.loads(self.request.read_text(encoding="utf-8")))
        request_doc["inputs"][0]["git_blob_sha"] = "0" * 40
        with tempfile.TemporaryDirectory() as temp:
            request_path = Path(temp) / "request.json"
            request_path.write_text(json.dumps(request_doc, ensure_ascii=False), encoding="utf-8")
            # The receipt intentionally points to the committed request, so a
            # substituted request cannot satisfy either the receipt or input bind.
            result = self.validate(request_path, self.receipt, ROOT)
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("E_REQUEST_PATH", codes)
        self.assertIn("E_BLOB_SHA", codes)


class ProductionEligibilityTests(unittest.TestCase):
    def test_repository_provenance_validates_artifacts_but_blocks_production(self):
        acceptance_validator = load_module(
            "story_acceptance_v11_test",
            ROOT / "scripts/story-engine/validate_story_engine_acceptance_v1_1.py",
        )
        request_source = ROOT / "working/2026-08-06/story-engine/templates/critic_request.json"
        receipt_source = ROOT / "working/2026-08-06/story-engine/templates/critic_execution_receipt.json"
        request_doc = json.loads(request_source.read_text(encoding="utf-8"))
        receipt_doc = json.loads(receipt_source.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # Copy the sealed request/receipt and every file the request is allowed to expose.
            copy_relative(ROOT, root, "working/2026-08-06/story-engine/templates/critic_request.json")
            copy_relative(ROOT, root, "working/2026-08-06/story-engine/templates/critic_execution_receipt.json")
            for item in request_doc["inputs"]:
                copy_relative(ROOT, root, item["path"])
            copy_relative(ROOT, root, receipt_doc["review"]["path"])
            copy_relative(ROOT, root, "scripts/story-engine/validate_critic_execution_receipt.py")
            copy_relative(ROOT, root, "skills/nasdaq-cafe-story-engine/contracts/critic_request.schema.json")
            copy_relative(ROOT, root, "skills/nasdaq-cafe-story-engine/contracts/critic_execution_receipt.schema.json")

            dossier = root / "research/2026-08-06/causal_research_dossier_2026-08-06.json"
            dossier.parent.mkdir(parents=True, exist_ok=True)
            dossier.write_text("{}\n", encoding="utf-8")
            plan = root / "working/2026-08-06/story-engine/templates/story_plan.template.json"
            script = root / "working/2026-08-06/story-engine/templates/story_script.template.json"
            review = root / "working/2026-08-06/story-engine/templates/creative_review.template.json"
            request = root / "working/2026-08-06/story-engine/templates/critic_request.json"
            receipt = root / "working/2026-08-06/story-engine/templates/critic_execution_receipt.json"

            def ref(path: Path) -> dict[str, str]:
                return {"path": path.relative_to(root).as_posix(), "sha256": sha256(path)}

            acceptance = {
                "contract_version": "1.1.0",
                "episode_date": "2026-08-06",
                "status": "pass",
                "production_eligible": False,
                "artifacts": {
                    "causal_dossier": ref(dossier),
                    "story_plan": ref(plan),
                    "story_script": ref(script),
                    "creative_review": ref(review),
                    "critic_request": ref(request),
                    "critic_execution_receipt": ref(receipt),
                },
                "validation": {
                    "story_plan": "pass",
                    "story_script": "pass",
                    "independent_critic": "pass",
                    "independent_critic_receipt": "pass",
                    "causality_guard": "pass",
                    "scene_order_guard": "pass",
                    "scene_09_guard": "pass",
                },
                "critic": {
                    "round": 2,
                    "score": 27,
                    "verdict": "pass",
                    "author_invocation_id": receipt_doc["author_invocation_id"],
                    "critic_invocation_id": receipt_doc["critic_invocation_id"],
                    "isolation_mode": "separate_invocation",
                },
            }
            acceptance_path = root / "working/2026-08-06/story-engine/story_engine_acceptance.json"
            acceptance_path.write_text(json.dumps(acceptance, ensure_ascii=False), encoding="utf-8")

            artifact_result = acceptance_validator.validate_acceptance(
                acceptance_path,
                repo_root=root,
                require_production=False,
            )
            self.assertEqual("pass", artifact_result["status"], artifact_result)
            self.assertFalse(artifact_result["production_eligible"])
            self.assertIn("W_PRODUCTION_BLOCKED", {x["code"] for x in artifact_result["warnings"]})

            production_result = acceptance_validator.validate_acceptance(
                acceptance_path,
                repo_root=root,
                require_production=True,
            )
            self.assertEqual("fail", production_result["status"])
            codes = {item["code"] for item in production_result["errors"]}
            self.assertIn("E_PRODUCTION_ELIGIBILITY", codes)
            self.assertIn("E_CRITIC_PROCESS_NOT_PROVEN", codes)


class UnifiedDailyGateTests(unittest.TestCase):
    def test_v11_public_state_machine_has_single_story_gate(self):
        wrapper = load_module(
            "daily_story_engine_v11_test",
            ROOT / "scripts/run_daily_production_story_engine_v1_1.py",
        )
        daily = wrapper.load_daily_module()
        for legacy in ("story_plan_valid", "script_draft_ready", "creative_review_passed"):
            self.assertNotIn(legacy, daily.STATES)
        causal = daily.STATES.index("causal_dossier_valid")
        final = daily.STATES.index("episode_package_final")
        self.assertEqual(causal + 1, final)

    def test_v11_rejects_legacy_internal_state_transition(self):
        wrapper = load_module(
            "daily_story_engine_v11_reject_test",
            ROOT / "scripts/run_daily_production_story_engine_v1_1.py",
        )
        daily = wrapper.load_daily_module()
        date = "2026-08-06"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / f"daily_source_package_{date}.md"
            source.write_text("source", encoding="utf-8")
            daily.init_request(
                workspace=root,
                date=date,
                daily_source=source,
                requested_scope="preview",
                renderer_commit="a" * 40,
                renderer_contract_version="2.4.0",
            )
            evidence = root / "evidence.json"
            evidence.write_text("{}", encoding="utf-8")
            daily.add_transition(
                workspace=root,
                date=date,
                new_state="research_inputs_bound",
                evidence_paths=[evidence],
            )
            daily.add_transition(
                workspace=root,
                date=date,
                new_state="causal_dossier_valid",
                evidence_paths=[evidence],
            )
            with self.assertRaises(daily.DailyProductionError):
                daily.add_transition(
                    workspace=root,
                    date=date,
                    new_state="story_plan_valid",
                    evidence_paths=[evidence],
                )


if __name__ == "__main__":
    unittest.main()
