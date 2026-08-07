#!/usr/bin/env python3
"""Authoritative daily control-plane entrypoint with hardened dependencies."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STORY_STATES = ["story_plan_valid", "script_draft_ready", "creative_review_passed"]


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


def _install_story_states(daily_module: Any) -> None:
    raw_states = getattr(daily_module, "STATES", None)
    if raw_states is None:
        return
    states = list(raw_states)
    if all(state in states for state in STORY_STATES):
        return
    try:
        insert_at = states.index("causal_dossier_valid") + 1
    except ValueError as exc:
        raise DailyHardeningError("base daily state machine lacks causal_dossier_valid") from exc
    states[insert_at:insert_at] = STORY_STATES
    daily_module.STATES = states


def _validate_acceptance(daily_module: Any, *, workspace: Path, date: str, evidence_paths: list[Path], artifact_key: str) -> None:
    workspace = Path(workspace).resolve()
    resolved = [daily_module.safe_path(workspace, path, f"{artifact_key} evidence") for path in evidence_paths]
    acceptance_paths = [path for path in resolved if path.name == "story_engine_acceptance.json"]
    if len(acceptance_paths) != 1:
        raise daily_module.DailyProductionError(
            daily_module.ERROR_CODES["stale"],
            f"{artifact_key} transition requires exactly one story_engine_acceptance.json",
        )
    acceptance = daily_module.load_json(acceptance_paths[0], "Story Engine acceptance")
    if acceptance.get("episode_date") != date or acceptance.get("status") != "pass":
        raise daily_module.DailyProductionError(
            daily_module.ERROR_CODES["stale"],
            "Story Engine acceptance must be PASS for the same episode date",
        )
    artifacts = acceptance.get("artifacts", {})
    item = artifacts.get(artifact_key)
    if not isinstance(item, dict):
        raise daily_module.DailyProductionError(
            daily_module.ERROR_CODES["stale"],
            f"Story Engine acceptance omits artifact {artifact_key}",
        )
    artifact_path = daily_module.safe_path(workspace, item.get("path", ""), f"Story Engine {artifact_key}")
    if daily_module.sha256_file(artifact_path) != item.get("sha256"):
        raise daily_module.DailyProductionError(
            daily_module.ERROR_CODES["stale"],
            f"Story Engine acceptance SHA mismatch for {artifact_key}",
        )
    if artifact_path not in resolved:
        raise daily_module.DailyProductionError(
            daily_module.ERROR_CODES["stale"],
            f"{artifact_key} transition evidence must include {item.get('path')}",
        )
    critic = acceptance.get("critic", {})
    if artifact_key == "creative_review":
        if critic.get("verdict") != "pass" or int(critic.get("score", 0)) < 25:
            raise daily_module.DailyProductionError(
                daily_module.ERROR_CODES["stale"],
                "creative_review_passed requires final critic PASS with score >=25",
            )


def _install_story_transition_guard(daily_module: Any) -> None:
    original = getattr(daily_module, "add_transition", None)
    if not callable(original):
        return

    def guarded_add_transition(*, workspace: Path, date: str, new_state: str, evidence_paths: list[Path], allow_multi_step: bool = False):
        artifact_by_state = {
            "story_plan_valid": "story_plan",
            "script_draft_ready": "story_script",
            "creative_review_passed": "creative_review",
        }
        artifact_key = artifact_by_state.get(new_state)
        if artifact_key:
            _validate_acceptance(
                daily_module,
                workspace=Path(workspace),
                date=str(date),
                evidence_paths=list(evidence_paths),
                artifact_key=artifact_key,
            )
        elif new_state == "episode_package_final":
            resolved = [daily_module.safe_path(Path(workspace), path, "episode final evidence") for path in evidence_paths]
            if not any(path.name == "story_engine_acceptance.json" for path in resolved):
                raise daily_module.DailyProductionError(
                    daily_module.ERROR_CODES["stale"],
                    "episode_package_final requires Story Engine acceptance evidence",
                )
            if not any(path.name.startswith("episode_package_") and path.suffix == ".md" for path in resolved):
                raise daily_module.DailyProductionError(
                    daily_module.ERROR_CODES["episode"],
                    "episode_package_final requires the final episode package",
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
        "pre_build": "pass", "public_artifacts": "pass", "handoff_recheck": "pass",
    }
    if not isinstance(hardening, dict) or any(
        hardening.get(key) != expected for key, expected in required.items()
    ):
        return False
    evidence["sha256"] = actual_sha
    state.setdefault("evidence_rebindings", []).append({
        "path": relative,
        "previous_sha256": declared_sha,
        "sha256": actual_sha,
        "reason": "handoff_recheck_persisted",
    })
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
    _install_story_states(daily_module)
    _install_story_transition_guard(daily_module)
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
