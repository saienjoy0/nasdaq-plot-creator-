from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = Path(__file__).with_name("current_authoring_runtime_fixture.py")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


fixture = load_module("current_authoring_runtime_fixture_for_semantic_scope", FIXTURE_PATH)
closure = load_module(
    "current_authoring_closure_for_semantic_scope",
    ROOT / "scripts/validate_chatgpt_daily_authoring_closure.py",
)


def registry() -> dict:
    return json.loads((ROOT / "contracts/financial_recipe_registry.json").read_text(encoding="utf-8"))


def _first_beat(authoring: dict) -> dict:
    return authoring["production"]["scenes"][0]["beats"][0]


def test_current_authoring_requires_explicit_visual_semantic_scope(tmp_path: Path):
    _, _, authoring = fixture.build_workspace(tmp_path)
    broken = copy.deepcopy(authoring)
    _first_beat(broken).pop("semanticScope", None)

    errors = closure.validate_authoring(broken, registry())

    assert any(
        "scene-01-beat-001: semanticScope is required" in error
        for error in errors
    )


def test_current_authoring_rejects_unknown_visual_semantic_scope(tmp_path: Path):
    _, _, authoring = fixture.build_workspace(tmp_path)
    broken = copy.deepcopy(authoring)
    _first_beat(broken)["semanticScope"] = "global-tech"

    errors = closure.validate_authoring(broken, registry())

    assert any(
        "scene-01-beat-001: semanticScope must be one of" in error
        for error in errors
    )
