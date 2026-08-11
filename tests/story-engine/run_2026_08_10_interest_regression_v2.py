#!/usr/bin/env python3
"""Run the 2026-08-10 Interest A/B through the exact H4 pre-Story path."""
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

    def materialize_h4_baseline(root: Path, acceptance_source: Path) -> None:
        verification = root / f"verification/{base.DATE}"
        verification.mkdir(parents=True, exist_ok=True)
        base.run(
            sys.executable,
            "tests/real-day-2026-08-10/materialize_fixture.py",
            "--repo-root",
            str(root),
            "--acceptance-source",
            str(acceptance_source),
            "--output",
            str(verification / "interest_h4_fixture_materialization.json"),
            cwd=root,
        )
        # Mirror the historical H4 workflow before Story Engine materialization.
        base.run(
            sys.executable,
            "tests/real-day-2026-08-10/restore_immutable_intake.py",
            "--repo-root",
            str(root),
            "--acceptance-source",
            str(acceptance_source),
            "--output",
            str(verification / "interest_h4_immutable_intake_restore.json"),
            cwd=root,
        )
        base.run(
            sys.executable,
            "tests/real-day-2026-08-10/sync_story_plan_authoring.py",
            "--repo-root",
            str(root),
            "--output",
            str(verification / "interest_h4_story_plan_authoring_sync.json"),
            cwd=root,
        )
        base.run(
            sys.executable,
            "tests/real-day-2026-08-10/sync_scene3_renderer_authoring.py",
            "--repo-root",
            str(root),
            "--output",
            str(verification / "interest_h4_scene3_renderer_authoring_sync.json"),
            cwd=root,
        )
        base.run(
            sys.executable,
            "tests/real-day-2026-08-10/sync_public_timing_authoring.py",
            "--repo-root",
            str(root),
            "--output",
            str(verification / "interest_h4_public_timing_authoring_sync.json"),
            cwd=root,
        )
        base.run(
            sys.executable,
            "scripts/story-engine/materialize_story_engine.py",
            "--repo-root",
            str(root),
            "--date",
            base.DATE,
            "--external-critic",
            "off",
            cwd=root,
        )

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

    base._materialize_h4_baseline = materialize_h4_baseline
    base._patch_revised_templates = patch_revised_templates
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
