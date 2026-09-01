#!/usr/bin/env python3
"""Fail-closed resume checks for the forward-only Current production state."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import run_daily_production_v12 as production


class CurrentProductionResumeError(RuntimeError):
    pass


def production_status(root: Path, date: str) -> dict[str, Any]:
    try:
        return production.status(
            module=production.load_module(),
            workspace=root.resolve(),
            date=date,
        )
    except Exception as exc:
        raise CurrentProductionResumeError(f"current production status invalid: {exc}") from exc


def validated_current_state(root: Path, date: str) -> str:
    result = production_status(root, date)
    validation = result.get("validation")
    if not isinstance(validation, dict) or validation.get("status") != "pass":
        errors = validation.get("errors") if isinstance(validation, dict) else None
        detail = "; ".join(str(item) for item in errors) if isinstance(errors, list) else "unknown validation failure"
        raise CurrentProductionResumeError(f"current production state is stale: {detail}")
    state = result.get("current_state")
    if state not in production.VI_STATES:
        raise CurrentProductionResumeError(f"unknown current production state: {state!r}")
    return str(state)


def has_reached(root: Path, date: str, target: str) -> bool:
    return state_has_reached(validated_current_state(root, date), target)


def state_has_reached(current: str, target: str) -> bool:
    if target not in production.VI_STATES:
        raise CurrentProductionResumeError(f"unknown target production state: {target!r}")
    if current not in production.VI_STATES:
        raise CurrentProductionResumeError(f"unknown current production state: {current!r}")
    return production.VI_STATES.index(current) >= production.VI_STATES.index(target)
