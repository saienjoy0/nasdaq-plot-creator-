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


class GateResult:
    def __init__(self, errors=None):
        self.errors = errors or []
        self.warnings = []


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.date = "2026-08-06"
        preflight_dir = self.root / f"verification/{self.date}"
        preflight_dir.mkdir(parents=True)
        self.preflight = preflight_dir / "official_execution_preflight.json"
        self.bundle_root = self.root / "bundles"
        episode_dir = self.root / f"episodes/{self.date}"
        episode_dir.mkdir(parents=True)
        (episode_dir / f"episode_package_{self.date}.md").write_text("package", encoding="utf-8")
        (episode_dir / f"spoken_script_{self.date}.md").write_text("spoken", encoding="utf-8")
        (episode_dir / "asset_manifest.json").write_text("{}", encoding="utf-8")
        render_dir = self.root / f"render-specs/{self.date}"
        render_dir.mkdir(parents=True)
        (render_dir / "render_spec.json").write_text("{}", encoding="utf-8")
        self.gate_calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def gate_pass(self, source_root, package, artifacts):
        self.gate_calls.append((package, list(artifacts)))
        return GateResult()

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

    def build(self, **kwargs):
        return module.build_handoff_hardened(
            **self.args(), gate=self.gate_pass, builder=self.builder, **kwargs
        )

    def test_01_pass_bundles_recheck_and_restores_source(self):
        self.write_preflight(module.BASE_HARDENING)
        original = self.preflight.read_bytes()
        result = self.build()
        self.assertEqual("pass", result["episode_memory_hardening"])
        self.assertEqual(1, len(self.gate_calls))
        self.assertEqual(original, self.preflight.read_bytes())
        bundled = json.loads(
            (
                self.bundle_root
                / "x/production/official_execution_preflight.json"
            ).read_text()
        )
        self.assertEqual(
            module.HANDOFF_HARDENING,
            bundled["episode_memory_hardening"],
        )

    def test_02_missing_hardening_rejected(self):
        self.write_preflight(None)
        with self.assertRaises(module.HardenedHandoffError):
            self.build()

    def test_03_partial_hardening_rejected(self):
        self.write_preflight({"pre_build": "pass", "public_artifacts": "fail"})
        with self.assertRaises(module.HardenedHandoffError):
            self.build()

    def test_04_bundled_loss_deletes_created_bundle_and_restores_source(self):
        self.write_preflight(module.BASE_HARDENING)
        original = self.preflight.read_bytes()

        def bad_builder(**kwargs):
            target = self.bundle_root / "bad"
            (target / "production").mkdir(parents=True)
            (target / "production/official_execution_preflight.json").write_text(
                "{}", encoding="utf-8"
            )
            return {"status": "created", "bundle_path": str(target)}

        with self.assertRaises(module.HardenedHandoffError):
            module.build_handoff_hardened(
                **self.args(), gate=self.gate_pass, builder=bad_builder
            )
        self.assertFalse((self.bundle_root / "bad").exists())
        self.assertEqual(original, self.preflight.read_bytes())

    def test_05_noop_loss_is_not_deleted_and_source_is_restored(self):
        self.write_preflight(module.BASE_HARDENING)
        original = self.preflight.read_bytes()

        def bad_builder(**kwargs):
            target = self.bundle_root / "existing"
            (target / "production").mkdir(parents=True)
            (target / "production/official_execution_preflight.json").write_text(
                "{}", encoding="utf-8"
            )
            return {"status": "noop", "bundle_path": str(target)}

        with self.assertRaises(module.HardenedHandoffError):
            module.build_handoff_hardened(
                **self.args(), gate=self.gate_pass, builder=bad_builder
            )
        self.assertTrue((self.bundle_root / "existing").exists())
        self.assertEqual(original, self.preflight.read_bytes())

    def test_06_handoff_recheck_failure_blocks_builder(self):
        self.write_preflight(module.BASE_HARDENING)
        original = self.preflight.read_bytes()
        builder_called = False

        def gate_fail(source_root, package, artifacts):
            return GateResult(["late leak"])

        def builder(**kwargs):
            nonlocal builder_called
            builder_called = True
            return {}

        with self.assertRaises(module.HardenedHandoffError) as cm:
            module.build_handoff_hardened(
                **self.args(), gate=gate_fail, builder=builder
            )
        self.assertIn("handoff-time", str(cm.exception))
        self.assertFalse(builder_called)
        self.assertEqual(original, self.preflight.read_bytes())

    def test_07_builder_exception_restores_source(self):
        self.write_preflight(module.BASE_HARDENING)
        original = self.preflight.read_bytes()

        def exploding_builder(**kwargs):
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            module.build_handoff_hardened(
                **self.args(), gate=self.gate_pass, builder=exploding_builder
            )
        self.assertEqual(original, self.preflight.read_bytes())


if __name__ == "__main__":
    unittest.main()
