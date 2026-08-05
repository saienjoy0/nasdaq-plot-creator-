from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/build_final_production_package_hardened.py"
spec = importlib.util.spec_from_file_location("hardened_builder", SCRIPT)
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
        self.package = self.root / "episode_package_2026-08-06.md"
        self.package.write_text("package", encoding="utf-8")
        self.schema = self.root / "schema.json"
        self.schema.write_text("{}", encoding="utf-8")
        self.out = self.root / "out"
        self.calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def gate_pass(self, repo_root, package, artifacts):
        self.calls.append(("gate", len(artifacts)))
        return GateResult()

    def builder_pass(self, package, output_root, schema):
        self.calls.append(("builder", 0))
        paths = {}
        for key, name in {
            "spoken_script": "spoken.md",
            "asset_manifest": "asset.json",
            "render_spec": "render.json",
            "ir": "ir.json",
            "consistency_report": "consistency.json",
            "preflight": "preflight.json",
        }.items():
            path = output_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if key == "preflight":
                path.write_text('{"status":"pass"}', encoding="utf-8")
            else:
                path.write_text(key, encoding="utf-8")
            paths[key] = str(path)
        return {"status": "pass", "paths": paths, "hashes": {}}

    def test_01_pre_and_post_gate_wrap_builder(self):
        result = module.build_hardened(
            self.package,
            self.out,
            self.schema,
            repo_root=self.root,
            gate=self.gate_pass,
            builder=self.builder_pass,
        )
        self.assertEqual([("gate", 0), ("builder", 0), ("gate", 3)], self.calls)
        self.assertEqual("pass", result["episode_memory_hardening"]["pre_build"])
        preflight = __import__("json").loads((self.out / "preflight.json").read_text())
        self.assertEqual(
            {"pre_build": "pass", "public_artifacts": "pass"},
            preflight["episode_memory_hardening"],
        )

    def test_02_pre_gate_failure_blocks_builder(self):
        def gate(repo_root, package, artifacts):
            return GateResult(["pre failed"])

        with self.assertRaises(module.HardenedBuildError) as cm:
            module.build_hardened(
                self.package,
                self.out,
                self.schema,
                repo_root=self.root,
                gate=gate,
                builder=self.builder_pass,
            )
        self.assertIn("pre-build", str(cm.exception))
        self.assertEqual([], self.calls)

    def test_03_post_gate_failure_removes_generated_outputs(self):
        calls = 0

        def gate(repo_root, package, artifacts):
            nonlocal calls
            calls += 1
            return GateResult([] if calls == 1 else ["leak"])

        with self.assertRaises(module.HardenedBuildError):
            module.build_hardened(
                self.package,
                self.out,
                self.schema,
                repo_root=self.root,
                gate=gate,
                builder=self.builder_pass,
            )
        self.assertEqual([], list(self.out.glob("*")))

    def test_04_missing_artifact_path_fails_and_cleans(self):
        def builder(package, output_root, schema):
            path = output_root / "spoken.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("spoken", encoding="utf-8")
            return {"status": "pass", "paths": {"spoken_script": str(path)}}

        with self.assertRaises(module.HardenedBuildError) as cm:
            module.build_hardened(
                self.package,
                self.out,
                self.schema,
                repo_root=self.root,
                gate=self.gate_pass,
                builder=builder,
            )
        self.assertIn("asset_manifest", str(cm.exception))
        self.assertFalse((self.out / "spoken.md").exists())

    def test_05_output_root_outside_repo_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            with self.assertRaises(module.HardenedBuildError):
                module.build_hardened(
                    self.package,
                    Path(outside),
                    self.schema,
                    repo_root=self.root,
                    gate=self.gate_pass,
                    builder=self.builder_pass,
                )

    def test_06_base_builder_must_return_pass(self):
        def builder(package, output_root, schema):
            return {"status": "fail", "errors": ["bad"]}

        with self.assertRaises(module.HardenedBuildError):
            module.build_hardened(
                self.package,
                self.out,
                self.schema,
                repo_root=self.root,
                gate=self.gate_pass,
                builder=builder,
            )


if __name__ == "__main__":
    unittest.main()
