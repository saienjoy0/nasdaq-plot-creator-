from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/run_daily_production_hardened.py"
spec = importlib.util.spec_from_file_location("daily_hardening", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def final_build(*args, **kwargs):
    return {"final": True}


def handoff_build(*args, **kwargs):
    return {"handoff": True}


def acceptance_validate(*args, **kwargs):
    return {"validation": {"status": "pass"}}


def acceptance_write(*args, **kwargs):
    return {"json": "x", "markdown": "y"}


class StaleInputError(ValueError):
    def __init__(self):
        super().__init__("stale preflight evidence")
        self.code = "E_STALE_INPUT"


class Tests(unittest.TestCase):
    def test_01_patch_replaces_all_base_dependencies(self):
        daily = SimpleNamespace(
            final_builder=object(), handoff_builder=object(), acceptance_runner=object()
        )
        patched = module.patch_daily_module(
            daily,
            final_module=SimpleNamespace(build_hardened=final_build),
            handoff_module=SimpleNamespace(build_handoff_hardened=handoff_build),
            acceptance_module=SimpleNamespace(
                validate_acceptance_hardened=acceptance_validate
            ),
            acceptance_writer=SimpleNamespace(write_report=acceptance_write),
        )
        self.assertIs(final_build, patched.final_builder.build)
        self.assertIs(handoff_build, patched.handoff_builder.build_handoff)
        self.assertIs(acceptance_validate, patched.acceptance_runner.validate_acceptance)
        self.assertIs(acceptance_write, patched.acceptance_runner.write_report)

    def test_02_missing_final_dependency_rejected(self):
        with self.assertRaises(module.DailyHardeningError):
            module.patch_daily_module(
                SimpleNamespace(),
                final_module=SimpleNamespace(),
                handoff_module=SimpleNamespace(build_handoff_hardened=handoff_build),
                acceptance_module=SimpleNamespace(
                    validate_acceptance_hardened=acceptance_validate
                ),
                acceptance_writer=SimpleNamespace(write_report=acceptance_write),
            )

    def test_03_missing_handoff_dependency_rejected(self):
        with self.assertRaises(module.DailyHardeningError):
            module.patch_daily_module(
                SimpleNamespace(),
                final_module=SimpleNamespace(build_hardened=final_build),
                handoff_module=SimpleNamespace(),
                acceptance_module=SimpleNamespace(
                    validate_acceptance_hardened=acceptance_validate
                ),
                acceptance_writer=SimpleNamespace(write_report=acceptance_write),
            )

    def test_04_missing_acceptance_dependency_rejected(self):
        with self.assertRaises(module.DailyHardeningError):
            module.patch_daily_module(
                SimpleNamespace(),
                final_module=SimpleNamespace(build_hardened=final_build),
                handoff_module=SimpleNamespace(build_handoff_hardened=handoff_build),
                acceptance_module=SimpleNamespace(),
                acceptance_writer=SimpleNamespace(write_report=acceptance_write),
            )

    def test_05_missing_report_writer_rejected(self):
        with self.assertRaises(module.DailyHardeningError):
            module.patch_daily_module(
                SimpleNamespace(),
                final_module=SimpleNamespace(build_hardened=final_build),
                handoff_module=SimpleNamespace(build_handoff_hardened=handoff_build),
                acceptance_module=SimpleNamespace(
                    validate_acceptance_hardened=acceptance_validate
                ),
                acceptance_writer=SimpleNamespace(),
            )

    def test_06_retries_once_after_guarded_preflight_rebind(self):
        date = "2026-08-06"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state_path = root / "working" / date / "production_state.json"
            preflight_path = (
                root / "verification" / date / "official_execution_preflight.json"
            )
            state_path.parent.mkdir(parents=True)
            preflight_path.parent.mkdir(parents=True)

            preflight_path.write_text(
                json.dumps(
                    {
                        "episode_memory_hardening": {
                            "pre_build": "pass",
                            "public_artifacts": "pass",
                        }
                    }
                ),
                encoding="utf-8",
            )
            original_sha = hashlib.sha256(preflight_path.read_bytes()).hexdigest()
            state_path.write_text(
                json.dumps(
                    {
                        "current_state": "production_package_valid",
                        "transitions": [
                            {
                                "state": "production_package_valid",
                                "evidence": [
                                    {
                                        "path": f"verification/{date}/official_execution_preflight.json",
                                        "sha256": original_sha,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            calls = {"count": 0}

            def base_build_handoff(**kwargs):
                calls["count"] += 1
                if calls["count"] == 1:
                    value = json.loads(preflight_path.read_text(encoding="utf-8"))
                    value["episode_memory_hardening"]["handoff_recheck"] = "pass"
                    preflight_path.write_text(json.dumps(value), encoding="utf-8")
                    raise StaleInputError()
                return {"status": "noop"}

            def load_json(path, label):
                return json.loads(Path(path).read_text(encoding="utf-8"))

            def write_atomic(path, value):
                Path(path).write_text(json.dumps(value), encoding="utf-8")

            daily = SimpleNamespace(
                ERROR_CODES={"stale": "E_STALE_INPUT"},
                build_handoff=base_build_handoff,
                state_path=lambda workspace, episode_date: Path(workspace)
                / "working"
                / episode_date
                / "production_state.json",
                load_json=load_json,
                write_atomic=write_atomic,
                sha256_file=lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            )
            patched = module.patch_daily_module(
                daily,
                final_module=SimpleNamespace(build_hardened=final_build),
                handoff_module=SimpleNamespace(build_handoff_hardened=handoff_build),
                acceptance_module=SimpleNamespace(
                    validate_acceptance_hardened=acceptance_validate
                ),
                acceptance_writer=SimpleNamespace(write_report=acceptance_write),
            )
            result = patched.build_handoff(
                workspace=root,
                date=date,
                bundle_root=root / "bundles",
                plot_commit="a" * 40,
            )
            self.assertEqual({"status": "noop"}, result)
            self.assertEqual(2, calls["count"])
            state = json.loads(state_path.read_text(encoding="utf-8"))
            current_sha = hashlib.sha256(preflight_path.read_bytes()).hexdigest()
            self.assertEqual(
                current_sha,
                state["transitions"][0]["evidence"][0]["sha256"],
            )
            self.assertEqual(
                "handoff_recheck_persisted",
                state["evidence_rebindings"][0]["reason"],
            )


if __name__ == "__main__":
    unittest.main()
