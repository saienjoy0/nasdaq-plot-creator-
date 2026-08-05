from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/run_real_day_acceptance_hardened.py"
spec = importlib.util.spec_from_file_location("acceptance_hardening", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.date = "2026-08-06"
        self.bundle = self.root / "bundle"
        (self.bundle / "production").mkdir(parents=True)
        self.preflight = self.bundle / "production/official_execution_preflight.json"
        self.manifest = self.bundle / "handoff_manifest.json"
        self.daily = self.root / f"daily_source_package_{self.date}.md"
        self.daily.write_text("daily", encoding="utf-8")
        self.renderer = self.root / "renderer"
        self.renderer.mkdir()
        self.technical = self.renderer / "technical.json"
        self.technical.write_text("{}", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def write_bundle(self, hardening=None):
        self.preflight.write_text(
            json.dumps({"episode_memory_hardening": hardening}), encoding="utf-8"
        )
        self.manifest.write_text(
            json.dumps(
                {
                    "files": [
                        {
                            "role": "preflight",
                            "destination_path": "production/official_execution_preflight.json",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    def validator_pass(self, **kwargs):
        return {
            "validation": {"status": "pass", "errors": [], "warnings": []},
            "mvp_status": "preview_ready_user_review_pending",
        }

    def args(self):
        return {
            "episode_date": self.date,
            "daily_source_root": self.root,
            "daily_source_path": self.daily,
            "bundle_root": self.root,
            "handoff_manifest_path": self.manifest,
            "renderer_artifact_root": self.renderer,
            "technical_report_path": self.technical,
        }

    def test_01_pass(self):
        self.write_bundle({"pre_build": "pass", "public_artifacts": "pass"})
        result = module.validate_acceptance_hardened(
            **self.args(), validator=self.validator_pass
        )
        self.assertNotIn("episode_memory_hardening", result)
        self.assertTrue(
            any(
                "episode-memory hardening evidence verified" in item
                for item in result["validation"]["warnings"]
            )
        )

    def test_02_missing_hardening_rejected(self):
        self.write_bundle(None)
        with self.assertRaises(module.HardenedAcceptanceError):
            module.validate_acceptance_hardened(
                **self.args(), validator=self.validator_pass
            )

    def test_03_partial_hardening_rejected(self):
        self.write_bundle({"pre_build": "pass", "public_artifacts": "fail"})
        with self.assertRaises(module.HardenedAcceptanceError):
            module.validate_acceptance_hardened(
                **self.args(), validator=self.validator_pass
            )

    def test_04_duplicate_preflight_role_rejected(self):
        self.write_bundle({"pre_build": "pass", "public_artifacts": "pass"})
        value = json.loads(self.manifest.read_text())
        value["files"].append(dict(value["files"][0]))
        self.manifest.write_text(json.dumps(value))
        with self.assertRaises(module.HardenedAcceptanceError):
            module.validate_acceptance_hardened(
                **self.args(), validator=self.validator_pass
            )

    def test_05_base_acceptance_must_pass(self):
        self.write_bundle({"pre_build": "pass", "public_artifacts": "pass"})

        def validator_fail(**kwargs):
            return {"validation": {"status": "fail"}}

        with self.assertRaises(module.HardenedAcceptanceError):
            module.validate_acceptance_hardened(
                **self.args(), validator=validator_fail
            )


if __name__ == "__main__":
    unittest.main()
