#!/usr/bin/env python3
"""Authoritative daily control-plane entrypoint with hardened dependencies.

Story Engine passes remain internal to editorial production. The public Daily
Production state machine advances directly from ``causal_dossier_valid`` to
``episode_package_final`` only when one hash-bound Story Engine v1.1 acceptance,
the final episode package, projection report, and Pre-TTS Visual Gate report pass.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEGACY_STORY_STATES = {"story_plan_valid", "script_draft_ready", "creative_review_passed"}


class DailyHardeningError(RuntimeError):
    pass


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise DailyHardeningError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _install_story_v11_gate(daily_module: Any) -> None:
    """Keep Story Engine passes internal and guard the single public final gate."""
    raw_states = getattr(daily_module, "STATES", None)
    original = getattr(daily_module, "add_transition", None)
    if raw_states is None or not callable(original):
        return

    daily_module.STATES = [
        state for state in list(raw_states) if state not in LEGACY_STORY_STATES
    ]
    try:
        causal_index = daily_module.STATES.index("causal_dossier_valid")
        final_index = daily_module.STATES.index("episode_package_final")
    except ValueError as exc:
        raise DailyHardeningError(
            "base daily state machine lacks causal_dossier_valid/episode_package_final"
        ) from exc
    if final_index != causal_index + 1:
        raise DailyHardeningError(
            "Story Engine internal passes must not appear as public Daily Production states"
        )

    acceptance_validator = _load_module(
        "story_engine_acceptance_v1_1_hardened_gate",
        ROOT / "scripts/story-engine/validate_story_engine_acceptance_v1_1.py",
    )

    def guarded_add_transition(
        *,
        workspace: Path,
        date: str,
        new_state: str,
        evidence_paths: list[Path],
        allow_multi_step: bool = False,
    ):
        if new_state in LEGACY_STORY_STATES:
            raise daily_module.DailyProductionError(
                daily_module.ERROR_CODES["stale"],
                f"{new_state} is an internal Story Engine pass and is not a Daily Production state",
            )

        if new_state == "episode_package_final":
            root = Path(workspace).resolve()
            resolved = [
                daily_module.safe_path(root, path, "episode final evidence")
                for path in evidence_paths
            ]
            acceptance_paths = [
                path for path in resolved if path.name == "story_engine_acceptance.json"
            ]
            package_paths = [
                path
                for path in resolved
                if path.name.startswith("episode_package_") and path.suffix == ".md"
            ]
            projection_paths = [
                path for path in resolved if path.name == "story_projection_report.json"
            ]
            visual_gate_paths = [
                path for path in resolved if path.name == "pre_tts_visual_gate.json"
            ]

            if len(acceptance_paths) != 1:
                raise daily_module.DailyProductionError(
                    daily_module.ERROR_CODES["stale"],
                    "episode_package_final requires exactly one Story Engine v1.1 acceptance",
                )
            if len(package_paths) != 1:
                raise daily_module.DailyProductionError(
                    daily_module.ERROR_CODES["episode"],
                    "episode_package_final requires exactly one final episode package",
                )
            if len(projection_paths) != 1:
                raise daily_module.DailyProductionError(
                    daily_module.ERROR_CODES["package"],
                    "episode_package_final requires exactly one story_projection_report.json",
                )
            if len(visual_gate_paths) != 1:
                raise daily_module.DailyProductionError(
                    daily_module.ERROR_CODES["render"],
                    "episode_package_final requires exactly one pre_tts_visual_gate.json",
                )

            result = acceptance_validator.validate_acceptance(
                acceptance_paths[0],
                repo_root=root,
                require_production=True,
                allow_uncertified_production=True,
            )
            if result["status"] != "pass":
                messages = "; ".join(
                    item.get("message", "Story Engine acceptance failed")
                    for item in result.get("errors", [])
                )
                raise daily_module.DailyProductionError(
                    daily_module.ERROR_CODES["inquisition"],
                    f"Story Engine v1.1 production gate failed: {messages}",
                )

            projection = daily_module.load_json(
                projection_paths[0], "Story Engine projection report"
            )
            if projection.get("episode_date") != date or projection.get("status") != "pass":
                raise daily_module.DailyProductionError(
                    daily_module.ERROR_CODES["package"],
                    "Story Engine projection report must be PASS for the same episode date",
                )

            visual_gate = daily_module.load_json(
                visual_gate_paths[0], "Pre-TTS Visual Gate report"
            )
            if (
                visual_gate.get("episodeDate") != date
                or visual_gate.get("status") != "PASS"
                or visual_gate.get("violations") != []
            ):
                raise daily_module.DailyProductionError(
                    daily_module.ERROR_CODES["render"],
                    "Pre-TTS Visual Gate must be PASS with zero violations for the same episode date",
                )

        return original(
            workspace=workspace,
            date=date,
            new_state=new_state,
            evidence_paths=evidence_paths,
            allow_multi_step=allow_multi_step,
        )

    daily_module.add_transition = guarded_add_transition


def _rebind_handoff_preflight_evidence(
    daily_module: Any, *, workspace: Path, date: str
) -> bool:
    """Backward-compatible recovery for older handoff implementations."""
    workspace = Path(workspace).resolve()
    state_path = daily_module.state_path(workspace, date)
    if not state_path.is_file():
        return False
    state = daily_module.load_json(state_path, "production state")
    if state.get("current_state") != "production_package_valid":
        return False
    preflight_path = workspace / f"verification/{date}/official_execution_preflight.json"
    if not preflight_path.is_file():
        return False
    relative = preflight_path.relative_to(workspace).as_posix()
    matches: list[dict[str, Any]] = []
    for transition in state.get("transitions", []):
        for evidence in transition.get("evidence", []):
            if evidence.get("path") == relative:
                matches.append(evidence)
    if len(matches) != 1:
        return False
    evidence = matches[0]
    actual_sha = daily_module.sha256_file(preflight_path)
    declared_sha = evidence.get("sha256")
    if declared_sha == actual_sha:
        return False
    preflight = daily_module.load_json(preflight_path, "handoff-updated preflight")
    hardening = preflight.get("episode_memory_hardening")
    required = {
        "pre_build": "pass",
        "public_artifacts": "pass",
        "handoff_recheck": "pass",
    }
    if not isinstance(hardening, dict) or any(
        hardening.get(key) != expected for key, expected in required.items()
    ):
        return False
    evidence["sha256"] = actual_sha
    state.setdefault("evidence_rebindings", []).append(
        {
            "path": relative,
            "previous_sha256": declared_sha,
            "sha256": actual_sha,
            "reason": "handoff_recheck_persisted",
        }
    )
    daily_module.write_atomic(state_path, state)
    return True


def _install_handoff_retry(daily_module: Any) -> None:
    original = getattr(daily_module, "build_handoff", None)
    if not callable(original):
        return

    def build_handoff_with_rebind(*args, **kwargs):
        try:
            return original(*args, **kwargs)
        except Exception as exc:
            stale_code = getattr(daily_module, "ERROR_CODES", {}).get("stale")
            if getattr(exc, "code", None) != stale_code:
                raise
            workspace = kwargs.get("workspace")
            date = kwargs.get("date")
            if workspace is None or date is None:
                raise
            if not _rebind_handoff_preflight_evidence(
                daily_module, workspace=Path(workspace), date=str(date)
            ):
                raise
            return original(*args, **kwargs)

    daily_module.build_handoff = build_handoff_with_rebind


def patch_daily_module(
    daily_module: Any,
    *,
    final_module: Any,
    handoff_module: Any,
    acceptance_module: Any,
    acceptance_writer: Any,
) -> Any:
    required = {
        "final": getattr(final_module, "build_hardened", None),
        "handoff": getattr(handoff_module, "build_handoff_hardened", None),
        "acceptance": getattr(acceptance_module, "validate_acceptance_hardened", None),
        "writer": getattr(acceptance_writer, "write_report", None),
    }
    missing = [name for name, value in required.items() if not callable(value)]
    if missing:
        raise DailyHardeningError(
            f"hardened daily dependencies are incomplete: {', '.join(missing)}"
        )

    daily_module.final_builder = SimpleNamespace(build=required["final"])
    daily_module.handoff_builder = SimpleNamespace(build_handoff=required["handoff"])
    daily_module.acceptance_runner = SimpleNamespace(
        validate_acceptance=required["acceptance"],
        write_report=required["writer"],
    )
    _install_story_v11_gate(daily_module)
    _install_handoff_retry(daily_module)
    return daily_module


def load_hardened_daily_module():
    daily = _load_module("daily_production_base", ROOT / "scripts/run_daily_production.py")
    final = _load_module(
        "final_production_hardened",
        ROOT / "scripts/build_final_production_package_hardened.py",
    )
    handoff = _load_module(
        "renderer_handoff_240",
        ROOT / "scripts/build_renderer_handoff_240.py",
    )
    acceptance = _load_module(
        "real_day_acceptance_hardened",
        ROOT / "scripts/run_real_day_acceptance_hardened.py",
    )
    acceptance_writer = _load_module(
        "real_day_acceptance_writer", ROOT / "scripts/run_real_day_acceptance.py"
    )
    return patch_daily_module(
        daily,
        final_module=final,
        handoff_module=handoff,
        acceptance_module=acceptance,
        acceptance_writer=acceptance_writer,
    )


def main(argv: list[str] | None = None) -> int:
    module = load_hardened_daily_module()
    return module.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
