#!/usr/bin/env python3
"""Backward-compatible alias for the authoritative hardened Daily Production entrypoint.

Unified Story Engine v1.1 gating is integrated directly into
``run_daily_production_hardened.py``. This file remains only for callers that still use
the historical v1.1 entrypoint name; it must not install a second state-machine layer.

The authoritative gate validates Story Engine acceptance with
``require_production=True`` and ``allow_uncertified_production=True``. The External
Independent Critic remains an optional quality upgrade; those policy choices live in
the hardened entrypoint and are documented here so legacy tooling that audits the
historical alias can verify that the policy did not silently change.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StoryEngineV11Error(RuntimeError):
    pass


def _load_hardened():
    path = ROOT / "scripts/run_daily_production_hardened.py"
    spec = importlib.util.spec_from_file_location("daily_production_hardened_v11_alias", path)
    if not spec or not spec.loader:
        raise StoryEngineV11Error(f"cannot import hardened Daily Production entrypoint: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_daily_module():
    return _load_hardened().load_hardened_daily_module()


def main(argv: list[str] | None = None) -> int:
    module = load_daily_module()
    return module.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
