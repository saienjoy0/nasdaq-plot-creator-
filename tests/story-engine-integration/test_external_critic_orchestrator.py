from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    CRYPTO_AVAILABLE = True
except ModuleNotFoundError:
    serialization = None
    Ed25519PrivateKey = None
    CRYPTO_AVAILABLE = False

ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(CRYPTO_AVAILABLE, "external Critic crypto tests run in Story Engine v1.1 Gate CI")
class ExternalCriticOrchestratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_module(
            "external_critic_runner_test",
            ROOT / "scripts/story-engine/run_external_critic_orchestrator.py",
        )
        cls.preflight = load_module(
            "external_critic_preflight_test",
            ROOT / "scripts/story-engine/preflight_external_critic_orchestrator.py",
        )
        cls.request = ROOT / "working/2026-08-06/story-engine/templates/critic_request.json"
        cls.request_schema = ROOT / "skills/nasdaq-cafe-story-engine/contracts/critic_request.schema.json"

    def test_prepare_bundle_reconstructs_all_allowed_inputs_and_03_04(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = Path(temp) / "bundle"
            request, manifest = self.runner.prepare_bundle(
                repo_root=ROOT,
                request_path=self.request,
                request_schema=self.request_schema,
                bundle_dir=bundle,
            )
            self.assertEqual("2026-08-06", request["episode_date"])
            roles = {row["role"] for row in manifest["inputs"]}
            self.assertEqual(
                {
                    "story_plan_template",
                    "story_script_template",
                    "draft_episode_package",
                    "visual_bindings",
                    "fox_bible",
                    "editorial_bible",
                    "packed_rules_manifest",
                },
                roles,
            )
            rules = {row["logical_path"] for row in manifest["logical_rules"]}
            self.assertEqual(
                {
                    "source-of-truth/03_episode_production_spec.md",
                    "source-of-truth/04_entertainment_inquisitor.md",
                },
                rules,
            )
            self.assertTrue((bundle / "logical_rules/03_episode_production_spec.md").is_file())
            self.assertTrue((bundle / "logical_rules/04_entertainment_inquisitor.md").is_file())

    def test_adapter_image_must_be_digest_pinned(self):
        self.assertIsNotNone(self.runner.PINNED_IMAGE_RE.fullmatch("example/critic@sha256:" + "a" * 64))
        self.assertIsNone(self.runner.PINNED_IMAGE_RE.fullmatch("example/critic:latest"))

    def test_review_gate_rejects_unresolved_critical(self):
        request = json.loads(self.request.read_text(encoding="utf-8"))
        review = {
            "episode_date": request["episode_date"],
            "reviewer": "independent_critic",
            "round": request["required_review"]["round"],
            "verdict": "pass",
            "total_score": request["required_review"]["minimum_total_score"],
            "immediate_failures": [],
            "findings": [{"severity": "critical", "status": "open"}],
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "review.json"
            path.write_text(json.dumps(review), encoding="utf-8")
            with self.assertRaises(self.runner.OrchestratorError):
                self.runner.validate_review(path, request)

    def test_preflight_signing_identity_matches_active_trust_key(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repo = base / "repo"
            repo.mkdir()
            private_path = base / "private-key.pem"
            key = Ed25519PrivateKey.generate()
            private_path.write_bytes(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
            public_pem = key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")
            trust = base / "trust.json"
            trust.write_text(
                json.dumps(
                    {
                        "contract_version": "1.0.0",
                        "keys": [
                            {
                                "key_id": "critic-key-01",
                                "orchestrator_id": "external-critic-01",
                                "algorithm": "ed25519",
                                "public_key_pem": public_pem,
                                "status": "active",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            self.preflight.validate_trust_identity(
                runner=self.runner,
                repo_root=repo,
                private_key_path=private_path,
                private_key_password_env=None,
                key_id="critic-key-01",
                orchestrator_id="external-critic-01",
                trust_registry=trust,
                trust_schema=ROOT / "skills/nasdaq-cafe-story-engine/contracts/trusted_critic_orchestrators.schema.json",
            )

    def test_preflight_rejects_private_key_inside_repo(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            private_path = repo / "private.pem"
            key = Ed25519PrivateKey.generate()
            private_path.write_bytes(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
            trust = Path(temp) / "trust.json"
            trust.write_text('{"contract_version":"1.0.0","keys":[]}', encoding="utf-8")
            with self.assertRaises(self.preflight.PreflightError):
                self.preflight.validate_trust_identity(
                    runner=self.runner,
                    repo_root=repo,
                    private_key_path=private_path,
                    private_key_password_env=None,
                    key_id="missing",
                    orchestrator_id="external-critic-01",
                    trust_registry=trust,
                    trust_schema=ROOT / "skills/nasdaq-cafe-story-engine/contracts/trusted_critic_orchestrators.schema.json",
                )


if __name__ == "__main__":
    unittest.main()
