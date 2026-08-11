#!/usr/bin/env python3
"""Run the 2026-08-10 Interest A/B through the validator-aligned revised fixture."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

BASE_DRIVER = Path(__file__).with_name("run_2026_08_10_interest_regression.py")


def load_base():
    spec = importlib.util.spec_from_file_location("interest_regression_base", BASE_DRIVER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    base = load_base()

    def patch_revised_templates(root: Path):
        output = root / f"verification/{base.DATE}/interest_revised_fixture_materialization.json"
        base.run(
            sys.executable,
            "tests/story-engine/fixtures/2026-08-10-interest/materialize_revised_interest_fixture_v2.py",
            "--repo-root",
            str(root),
            "--output",
            str(output),
            cwd=root,
        )
        return base.load(output)

    base._patch_revised_templates = patch_revised_templates
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
