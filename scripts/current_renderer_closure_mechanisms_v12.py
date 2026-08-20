#!/usr/bin/env python3
"""Generation-neutral mechanical helpers for the current Renderer closure."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import renderer_binding
import run_daily_production_v12 as current_production


class CurrentRendererClosureMechanismError(RuntimeError):
    pass


def _already_satisfied_current_advance(root: Path, command: list[str]) -> bool:
    """Treat a verified, already-recorded Current transition as idempotent.

    Current closure phases are intentionally restartable around human/LLM pauses. The
    authoritative control plane remains run_daily_production_v12: this helper only asks its
    status/VI_STATES whether an `advance` target is already behind the validated current state.
    It never invents, rewrites, or skips a not-yet-recorded transition.
    """
    if len(command) < 3:
        return False
    script = Path(command[1]).as_posix()
    if not script.endswith("scripts/run_daily_production_v12.py") or "advance" not in command:
        return False
    try:
        date = command[command.index("--episode-date") + 1]
        target = command[command.index("--state") + 1]
    except (ValueError, IndexError):
        return False
    state_path = root / "working" / date / "production_state.json"
    request_path = root / "working" / date / "production_request.json"
    if not state_path.is_file() or not request_path.is_file():
        return False
    if target not in current_production.VI_STATES:
        return False

    module = current_production.load_module()
    status = current_production.status(module=module, workspace=root, date=date)
    validation = status.get("validation", {})
    if validation.get("status") != "pass":
        errors = validation.get("errors")
        detail = "; ".join(str(item) for item in errors) if isinstance(errors, list) else str(errors)
        raise CurrentRendererClosureMechanismError(
            f"current control-plane status is invalid before resume: {detail}"
        )
    current = status.get("current_state")
    if current not in current_production.VI_STATES:
        raise CurrentRendererClosureMechanismError(
            f"current control-plane state is unknown before resume: {current!r}"
        )
    current_index = current_production.VI_STATES.index(current)
    target_index = current_production.VI_STATES.index(target)
    if target_index < current_index:
        print(
            f"= current transition already satisfied: {target} (current={current})",
            flush=True,
        )
        return True
    return False


def run(
    root: Path,
    *args: str,
    env: dict[str, str] | None = None,
    ok_codes=(0,),
) -> int:
    command = list(args)
    print("+", " ".join(command), flush=True)
    if _already_satisfied_current_advance(root, command):
        return 0
    completed = subprocess.run(command, cwd=root, env=env, check=False)
    if completed.returncode not in ok_codes:
        raise CurrentRendererClosureMechanismError(
            f"command failed ({completed.returncode}): {' '.join(command)}"
        )
    return completed.returncode


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CurrentRendererClosureMechanismError(f"JSON root must be object: {path}")
    return value


def ensure_renderer(root: Path, renderer_root: Path) -> dict:
    try:
        return renderer_binding.verify_renderer_checkout(root, renderer_root)
    except renderer_binding.RendererBindingError as exc:
        raise CurrentRendererClosureMechanismError(str(exc)) from exc


def evidence_if_exists(root: Path, values: list[str]) -> list[str]:
    return [value for value in values if (root / value).is_file()]
