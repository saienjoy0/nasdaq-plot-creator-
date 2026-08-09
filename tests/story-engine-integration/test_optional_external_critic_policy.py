from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeReceiptValidator:
    @staticmethod
    def validate(*args, **kwargs):
        return {"status": "pass", "errors": [], "warnings": []}


class OptionalExternalCriticPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_module(
            "story_acceptance_optional_critic_test",
            ROOT / "scripts/story-engine/validate_story_engine_acceptance_v1_1.py",
        )

    def run_validation(
        self,
        *,
        attestation_strength: str,
        allow_uncertified: bool,
        require_production: bool = True,
    ):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            acceptance_path = root / "story_engine_acceptance.json"
            acceptance_path.write_text("{}\n", encoding="utf-8")

            acceptance = {
                "contract_version": "1.1.0",
                "episode_date": "2026-08-06",
                "status": "pass",
                "production_eligible": attestation_strength == "orchestrator_signed",
                "artifacts": {
                    "causal_dossier": {"path": "dossier.json", "sha256": "x"},
                    "story_plan": {"path": "plan.json", "sha256": "x"},
                    "story_script": {"path": "script.json", "sha256": "x"},
                    "creative_review": {"path": "review.json", "sha256": "x"},
                    "critic_request": {"path": "request.json", "sha256": "x"},
                    "critic_execution_receipt": {"path": "receipt.json", "sha256": "x"},
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
                    "author_invocation_id": "author-run",
                    "critic_invocation_id": "critic-run",
                    "isolation_mode": "separate_invocation",
                },
            }
            request = {
                "episode_date": "2026-08-06",
                "inputs": [],
            }
            receipt = {
                "episode_date": "2026-08-06",
                "author_invocation_id": "author-run",
                "critic_invocation_id": "critic-run",
                "review": {"path": "review-source.json"},
                "provenance": {"attestation_strength": attestation_strength},
            }
            review = {"verdict": "pass", "total_score": 27}
            objects = {
                acceptance_path.resolve(): acceptance,
                (root / "request.json").resolve(): request,
                (root / "receipt.json").resolve(): receipt,
                (root / "review.json").resolve(): review,
                (root / "review-source.json").resolve(): review,
            }

            def fake_load(path: Path):
                resolved = Path(path).resolve()
                if resolved not in objects:
                    raise AssertionError(f"unexpected load: {resolved}")
                return objects[resolved]

            def fake_safe(repo_root: Path, ref: dict, label: str, errors: list):
                return (Path(repo_root) / ref["path"]).resolve()

            with (
                patch.object(self.validator, "load", side_effect=fake_load),
                patch.object(self.validator, "safe", side_effect=fake_safe),
                patch.object(self.validator, "load_module", return_value=FakeReceiptValidator),
            ):
                return self.validator.validate_acceptance(
                    acceptance_path,
                    repo_root=root,
                    require_production=require_production,
                    allow_uncertified_production=allow_uncertified,
                )

    def test_strict_mode_still_blocks_repository_provenance(self):
        result = self.run_validation(
            attestation_strength="repository_provenance",
            allow_uncertified=False,
        )
        self.assertEqual("fail", result["status"], result)
        self.assertFalse(result["critic_certified"])
        self.assertEqual("not_certified", result["external_critic_status"])
        self.assertEqual("external_critic_required", result["production_policy"])
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("E_PRODUCTION_ELIGIBILITY", codes)
        self.assertIn("E_CRITIC_PROCESS_NOT_PROVEN", codes)

    def test_optional_mode_allows_production_without_claiming_certification(self):
        result = self.run_validation(
            attestation_strength="repository_provenance",
            allow_uncertified=True,
        )
        self.assertEqual("pass", result["status"], result)
        self.assertTrue(result["production_allowed_by_policy"])
        self.assertFalse(result["production_eligible"])
        self.assertFalse(result["critic_certified"])
        self.assertEqual("not_certified", result["external_critic_status"])
        self.assertEqual("external_critic_optional", result["production_policy"])
        self.assertIn(
            "W_EXTERNAL_CRITIC_NOT_CERTIFIED",
            {item["code"] for item in result["warnings"]},
        )

    def test_signed_external_critic_remains_certified_in_strict_mode(self):
        result = self.run_validation(
            attestation_strength="orchestrator_signed",
            allow_uncertified=False,
        )
        self.assertEqual("pass", result["status"], result)
        self.assertTrue(result["production_allowed_by_policy"])
        self.assertTrue(result["production_eligible"])
        self.assertTrue(result["critic_certified"])
        self.assertEqual("certified", result["external_critic_status"])
        self.assertEqual("external_critic_required", result["production_policy"])

    def test_artifact_only_mode_preserves_legacy_warning_and_reports_certification(self):
        result = self.run_validation(
            attestation_strength="repository_provenance",
            allow_uncertified=False,
            require_production=False,
        )
        self.assertEqual("pass", result["status"], result)
        warning_codes = {item["code"] for item in result["warnings"]}
        self.assertIn("W_PRODUCTION_BLOCKED", warning_codes)
        self.assertIn("W_EXTERNAL_CRITIC_NOT_CERTIFIED", warning_codes)
        self.assertEqual("artifact_validation_only", result["production_policy"])

    def test_daily_wrapper_explicitly_selects_optional_external_critic_policy(self):
        source = (ROOT / "scripts/run_daily_production_story_engine_v1_1.py").read_text(encoding="utf-8")
        self.assertIn("require_production=True", source)
        self.assertIn("allow_uncertified_production=True", source)
        self.assertIn("optional quality upgrade", source)


if __name__ == "__main__":
    unittest.main()
