#!/usr/bin/env python3
"""Authoritative Daily Production entry point for Unified Story Engine v1.1.

Keeps Story Engine internal passes out of the public Daily Production state machine.
The only public transition is causal_dossier_valid -> episode_package_final, guarded by
one hash-bound Story Engine acceptance artifact plus the final episode package and
projection report.

External Independent Critic certification is an optional quality upgrade for daily
operation. The daily gate still requires the complete editorial review, causality guards,
scene guards and artifact lineage. When no orchestrator-signed external Critic receipt
exists, production may proceed only through the validator's explicit uncertified-policy
path, which reports that certification is absent instead of pretending it occurred.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEGACY_STORY_STATES = {"story_plan_valid", "script_draft_ready", "creative_review_passed"}


class StoryEngineV11Error(RuntimeError):
    pass


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise StoryEngineV11Error(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _install_v11_gate(daily: Any) -> Any:
    daily.STATES = [state for state in daily.STATES if state not in LEGACY_STORY_STATES]
    original = daily.add_transition
    acceptance_validator = load_module(
        "story_engine_acceptance_v1_1_daily_gate",
        ROOT / "scripts/story-engine/validate_story_engine_acceptance_v1_1.py",
    )

    def add_transition(*, workspace: Path, date: str, new_state: str, evidence_paths: list[Path], allow_multi_step: bool = False):
        if new_state in LEGACY_STORY_STATES:
            raise daily.DailyProductionError(
                daily.ERROR_CODES["stale"],
                f"{new_state} is an internal Story Engine pass and is not a Daily Production state in v1.1",
            )
        if new_state == "episode_package_final":
            root = Path(workspace).resolve()
            resolved = [daily.safe_path(root, path, "episode final evidence") for path in evidence_paths]
            acceptance_paths = [path for path in resolved if path.name == "story_engine_acceptance.json"]
            package_paths = [path for path in resolved if path.name.startswith("episode_package_") and path.suffix == ".md"]
            projection_paths = [path for path in resolved if path.name == "story_projection_report.json"]
            if len(acceptance_paths) != 1:
                raise daily.DailyProductionError(
                    daily.ERROR_CODES["stale"],
                    "episode_package_final requires exactly one Story Engine v1.1 acceptance",
                )
            if len(package_paths) != 1:
                raise daily.DailyProductionError(
                    daily.ERROR_CODES["episode"],
                    "episode_package_final requires exactly one final episode package",
                )
            if len(projection_paths) != 1:
                raise daily.DailyProductionError(
                    daily.ERROR_CODES["package"],
                    "episode_package_final requires exactly one story_projection_report.json",
                )
            result = acceptance_validator.validate_acceptance(
                acceptance_paths[0],
                repo_root=root,
                require_production=True,
                allow_uncertified_production=True,
            )
            if result["status"] != "pass":
                messages = "; ".join(item.get("message", "Story Engine acceptance failed") for item in result.get("errors", []))
                raise daily.DailyProductionError(
                    daily.ERROR_CODES["inquisition"],
                    f"Story Engine v1.1 production gate failed: {messages}",
                )
            projection = daily.load_json(projection_paths[0], "Story Engine projection report")
            if projection.get("episode_date") != date or projection.get("status") != "pass":
                raise daily.DailyProductionError(
                    daily.ERROR_CODES["package"],
                    "Story Engine projection report must be PASS for the same episode date",
                )
        return original(
            workspace=workspace,
            date=date,
            new_state=new_state,
            evidence_paths=evidence_paths,
            allow_multi_step=allow_multi_step,
        )

    daily.add_transition = add_transition
    return daily


def load_daily_module():
    hardened = load_module(
        "daily_production_hardened_legacy_story_states",
        ROOT / "scripts/run_daily_production_hardened.py",
    )
    return _install_v11_gate(hardened.load_hardened_daily_module())


def main(argv: list[str] | None = None) -> int:
    module = load_daily_module()
    return module.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
