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
    return daily_module


def load_hardened_daily_module():
    daily = _load_module("daily_production_base", ROOT / "scripts/run_daily_production.py")
    final = _load_module(
        "final_production_hardened",
        ROOT / "scripts/build_final_production_package_hardened.py",
    )
    handoff = _load_module(
        "renderer_handoff_hardened",
        ROOT / "scripts/build_renderer_handoff_hardened.py",
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
