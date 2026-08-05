from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/build_renderer_handoff_hardened.py"
spec = importlib.util.spec_from_file_location("renderer_handoff_hardening", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.date = "2026-08-06"
        preflight_dir = self.root / f"verification/{self.date}"
        preflight_dir.mkdir(parents=True)
        self.preflight = preflight_dir / "official_execution_preflight.json"
        self.bundle_root = self.root / "bundles"

    def tearDown(self):
        self.tmp.cleanup()

    def write_preflight(self, hardening=None):
        self.preflight.write_text(
            json.dumps({"status": "pass", "episode_memory_hardening": hardening}),
            encoding="utf-8",
        )

    def builder(self, **kwargs):
        target = self.bundle_root / "x"
        (target / "production").mkdir(parents=True, exist_ok=True)
        (target / "production/official_execution_preflight.json").write_bytes(
            self.preflight.read_bytes()
        )
        return {"status": "created", "bundle_path": str(target)}

    def args(self):
        return {
            "source_root": self.root,
            "bundle_root": self.bundle_root,
            "date": self.date,
            "mode": "preview",
            "plot_commit": "a" * 40,
            "renderer_commit": "b" * 40,
            "renderer_contract_version": "2.2.0",
        }

    def test_01_pass(self):
        self.write_preflight({"pre_build": "pass", "public_artifacts": "pass"})
        result = module.build_handoff_hardened(**self.args(), builder=self.builder)
        self.assertEqual("pass", result["episode_memory_hardening"])

    def test_02_missing_hardening_rejected(self):
        self.write_preflight(None)
        with self.assertRaises(module.HardenedHandoffError):
            module.build_handoff_hardened(**self.args(), builder=self.builder)

    def test_03_partial_hardening_rejected(self):
        self.write_preflight({"pre_build": "pass", "public_artifacts": "fail"})
        with self.assertRaises(module.HardenedHandoffError):
            module.build_handoff_hardened(**self.args(), builder=self.builder)

    def test_04_bundled_loss_deletes_created_bundle(self):
        self.write_preflight({"pre_build": "pass", "public_artifacts": "pass"})

        def bad_builder(**kwargs):
            target = self.bundle_root / "bad"
            (target / "production").mkdir(parents=True)
            (target / "production/official_execution_preflight.json").write_text(
                "{}", encoding="utf-8"
            )
            return {"status": "created", "bundle_path": str(target)}

        with self.assertRaises(module.HardenedHandoffError):
            module.build_handoff_hardened(**self.args(), builder=bad_builder)
        self.assertFalse((self.bundle_root / "bad").exists())

    def test_05_noop_loss_is_not_deleted(self):
        self.write_preflight({"pre_build": "pass", "public_artifacts": "pass"})

        def bad_builder(**kwargs):
            target = self.bundle_root / "existing"
            (target / "production").mkdir(parents=True)
            (target / "production/official_execution_preflight.json").write_text(
                "{}", encoding="utf-8"
            )
            return {"status": "noop", "bundle_path": str(target)}

        with self.assertRaises(module.HardenedHandoffError):
            module.build_handoff_hardened(**self.args(), builder=bad_builder)
        self.assertTrue((self.bundle_root / "existing").exists())


if __name__ == "__main__":
    unittest.main()
