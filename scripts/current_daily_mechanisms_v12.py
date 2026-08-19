#!/usr/bin/env python3
"""Generation-neutral mechanical helpers for the current v1.2 control plane.

This module deliberately exposes only filesystem/JSON/error primitives from the
original daily implementation. It does not expose legacy state ordering, request
writers, transition policy, Final policy, or legacy/hardened wrapper policy.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import run_daily_production as base

DailyProductionError = base.DailyProductionError
ERROR_CODES = base.ERROR_CODES
canonical_json = base.canonical_json
sha256_file = base.sha256_file
safe_path = base.safe_path
load_json = base.load_json
write_atomic = base.write_atomic
work_dir = base.work_dir
request_path = base.request_path
state_path = base.state_path
validate_date_in_name = base.validate_date_in_name
validate_approval_record = base.validate_approval_record


def load_module():
    """Return a module-like mechanical surface without legacy policy entrypoints."""
    return sys.modules[__name__]


def load_external_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
