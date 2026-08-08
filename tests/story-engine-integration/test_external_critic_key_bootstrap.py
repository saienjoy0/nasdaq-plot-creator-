from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/story-engine/bootstrap_external_critic_key.py"


class ExternalCriticKeyBootstrapTests(unittest.TestCase):
    def test_refuses_private_key_inside_repository(self):
        target = ROOT / ".never-create-critic-private-key.pem"
        target.unlink(missing_ok=True)
        env = os.environ.copy()
        env["TEST_CRITIC_KEY_PASSWORD"] = "test-password-123456789"
        result = subprocess.run(
            [
                sys.executable, str(SCRIPT),
                "--repo-root", str(ROOT),
                "--private-key-out", str(target),
                "--password-env", "TEST_CRITIC_KEY_PASSWORD",
                "--key-id", "test-key",
                "--orchestrator-id", "test-orchestrator",
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(2, result.returncode)
        self.assertFalse(target.exists())

    def test_generates_encrypted_key_outside_repository_and_public_registry_row(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "critic-ed25519.pem"
            env = os.environ.copy()
            password = "test-password-123456789"
            env["TEST_CRITIC_KEY_PASSWORD"] = password
            result = subprocess.run(
                [
                    sys.executable, str(SCRIPT),
                    "--repo-root", str(ROOT),
                    "--private-key-out", str(target),
                    "--password-env", "TEST_CRITIC_KEY_PASSWORD",
                    "--key-id", "test-key",
                    "--orchestrator-id", "test-orchestrator",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(target.is_file())
            self.assertEqual(0, stat.S_IMODE(target.stat().st_mode) & 0o077)
            private_key = serialization.load_pem_private_key(
                target.read_bytes(),
                password=password.encode("utf-8"),
            )
            public_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")
            row = payload["trust_registry_row"]
            self.assertEqual("test-key", row["key_id"])
            self.assertEqual("test-orchestrator", row["orchestrator_id"])
            self.assertEqual("active", row["status"])
            self.assertEqual(public_pem, row["public_key_pem"])


if __name__ == "__main__":
    unittest.main()
