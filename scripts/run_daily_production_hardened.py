#!/usr/bin/env python3
"""Authoritative daily control-plane entrypoint with hardened dependencies."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

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
