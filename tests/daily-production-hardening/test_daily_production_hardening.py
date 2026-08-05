from __future__ import annotations

import importlib.util
import sys
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


if __name__ == "__main__":
    unittest.main()
