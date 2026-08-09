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


class FakeBundleResult:
    ok = True
    errors: list[str] = []


class FakeBundleValidator:
    @staticmethod
    def validate_bundle(*args, **kwargs):
        return FakeBundleResult()


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
        external: bool,
        attestation_strength: str | None = None,
        allow_uncertified: bool,
        require_production: bool = True,
    ):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            acceptance_path = root / "story_engine_acceptance.json"
            acceptance_path.write_text("{}\n", encoding="utf-8")

            review = {
                "episode_date": "2026-08-06",
                "reviewer": "editorial_critic",
                "verdict": "pass",
                "total_score": 28,
            }
            acceptance = {
                "contract_version": "1.1.0",
                "episode_date": "2026-08-06",
                "status": "pass",
                "production_eligible": external and attestation_strength == "orchestrator_signed",
                "artifacts": {
                    "causal_dossier": {"path": "dossier.json", "sha256": "x"},
                    "story_plan": {"path": "plan.json", "sha256": "x"},
                    "story_script": {"path": "script.json", "sha256": "x"},
                    "creative_review": {"path": "review.json", "sha256": "x"},
                },
                "validation": {
                    "story_plan": "pass",
                    "story_script": "pass",
                    "editorial_review": "pass",
                    "understanding_progression": "pass",
                    "causality_guard": "pass",
                    "scene_order_guard": "pass",
                    "scene_09_guard": "pass",
                },
                "critic": {
                    "round": 2,
                    "score": 28,
                    "verdict": "pass",
                    "reviewer": "editorial_critic",
                    "critic_certified": False,
                    "external_critic_status": "not_run",
                },
            }

            request = {"episode_date": "2026-08-06", "inputs": []}
            receipt = None
            review_source = review

            if external:
                assert attestation_strength is not None
                acceptance["artifacts"]["critic_request"] = {"path": "request.json", "sha256": "x"}
                acceptance["artifacts"]["critic_execution_receipt"] = {"path": "receipt.json", "sha256": "x"}
                acceptance["validation"]["independent_critic_receipt"] = "pass"
                acceptance["critic"].update({
                    "author_invocation_id": "author-run",
                    "critic_invocation_id": "critic-run",
                    "isolation_mode": "separate_invocation",
                    "attestation_strength": attestation_strength,
                    "external_critic_status": "certified" if attestation_strength == "orchestrator_signed" else "not_certified",
                    "critic_certified": attestation_strength == "orchestrator_signed",
                })
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

            objects = {
                acceptance_path.resolve(): acceptance,
                (root / "review.json").resolve(): review,
            }
            if external:
                objects[(root / "request.json").resolve()] = request
                objects[(root / "receipt.json").resolve()] = receipt
                objects[(root / "review-source.json").resolve()] = review_source

            def fake_load(path: Path):
                resolved = Path(path).resolve()
                if resolved not in objects:
                    raise AssertionError(f"unexpected load: {resolved}")
                return objects[resolved]

            def fake_safe(repo_root: Path, ref: dict, label: str, errors: list):
                return (Path(repo_root) / ref["path"]).resolve()

            def fake_load_module(name: str, path: Path):
                if "bundle_validator" in name:
                    return FakeBundleValidator
                if "receipt_validator" in name:
                    return FakeReceiptValidator
                raise AssertionError(f"unexpected module load: {name} {path}")

            with (
                patch.object(self.validator, "load", side_effect=fake_load),
                patch.object(self.validator, "safe", side_effect=fake_safe),
                patch.object(self.validator, "load_module", side_effect=fake_load_module),
            ):
                return self.validator.validate_acceptance(
                    acceptance_path,
                    repo_root=root,
                    require_production=require_production,
                    allow_uncertified_production=allow_uncertified,
                )

    def test_no_external_receipt_optional_mode_allows_production_without_certification(self):
        result = self.run_validation(
            external=False,
            allow_uncertified=True,
        )
        self.assertEqual("pass", result["status"], result)
        self.assertTrue(result["production_allowed_by_policy"])
        self.assertFalse(result["production_eligible"])
        self.assertFalse(result["critic_certified"])
        self.assertEqual("not_run", result["external_critic_status"])
        self.assertEqual("external_critic_optional", result["production_policy"])
        self.assertIn(
            "W_EXTERNAL_CRITIC_NOT_CERTIFIED",
            {item["code"] for item in result["warnings"]},
        )

    def test_no_external_receipt_strict_mode_blocks(self):
        result = self.run_validation(
            external=False,
            allow_uncertified=False,
        )
        self.assertEqual("fail", result["status"], result)
        self.assertFalse(result["critic_certified"])
        self.assertEqual("not_run", result["external_critic_status"])
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("E_PRODUCTION_ELIGIBILITY", codes)
        self.assertIn("E_CRITIC_PROCESS_NOT_PROVEN", codes)

    def test_repository_provenance_optional_mode_is_not_certified(self):
        result = self.run_validation(
            external=True,
            attestation_strength="repository_provenance",
            allow_uncertified=True,
        )
        self.assertEqual("pass", result["status"], result)
        self.assertFalse(result["critic_certified"])
        self.assertEqual("not_certified", result["external_critic_status"])

    def test_signed_external_critic_remains_certified_in_strict_mode(self):
        result = self.run_validation(
            external=True,
            attestation_strength="orchestrator_signed",
            allow_uncertified=False,
        )
        self.assertEqual("pass", result["status"], result)
        self.assertTrue(result["production_allowed_by_policy"])
        self.assertTrue(result["production_eligible"])
        self.assertTrue(result["critic_certified"])
        self.assertEqual("certified", result["external_critic_status"])

    def test_artifact_only_mode_without_external_receipt_passes_with_warning(self):
        result = self.run_validation(
            external=False,
            allow_uncertified=False,
            require_production=False,
        )
        self.assertEqual("pass", result["status"], result)
        self.assertEqual("artifact_validation_only", result["production_policy"])
        self.assertIn(
            "W_EXTERNAL_CRITIC_NOT_CERTIFIED",
            {item["code"] for item in result["warnings"]},
        )

    def test_daily_wrapper_explicitly_selects_optional_external_critic_policy(self):
        source = (ROOT / "scripts/run_daily_production_story_engine_v1_1.py").read_text(encoding="utf-8")
        self.assertIn("require_production=True", source)
        self.assertIn("allow_uncertified_production=True", source)
        self.assertIn("optional quality upgrade", source)


if __name__ == "__main__":
    unittest.main()
