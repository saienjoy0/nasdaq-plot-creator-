from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

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


fixture = load_module("current_authoring_runtime_fixture_for_parity", FIXTURE_PATH)
closure = load_module(
    "current_authoring_closure_for_parity",
    ROOT / "scripts/validate_chatgpt_daily_authoring_closure.py",
)


def registry() -> dict:
    return json.loads((ROOT / "contracts/financial_recipe_registry.json").read_text(encoding="utf-8"))


def run_materializer(root: Path, date: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/materialize_chatgpt_daily_authoring.py"),
            "--date",
            date,
            "--repo-root",
            str(root),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def write_authoring(root: Path, fx, authoring: dict) -> Path:
    path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(path, authoring)
    return path


def test_current_runtime_fixture_schema_closure_and_materializer_agree(tmp_path: Path):
    root, fx, authoring = fixture.build_workspace(tmp_path)
    authoring_path = root / "daily-authoring" / f"{fx.DATE}.json"

    semantic = load_module(
        "current_authoring_semantic_for_parity",
        root / "scripts/validate_editorial_semantic_boundary.py",
    )
    acceptance = semantic.validate_boundary(root, fx.DATE, authoring_path)
    acceptance_path = root / "verification" / fx.DATE / "editorial_semantic_acceptance.json"
    semantic.atomic_write_json(acceptance_path, acceptance)
    semantic.verify_acceptance(root, fx.DATE, acceptance_path)

    assert closure.validate_authoring(authoring, registry()) == []

    completed = run_materializer(root, fx.DATE)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    render_path = root / "render-specs" / fx.DATE / "render_spec.json"
    render = json.loads(render_path.read_text(encoding="utf-8"))
    assert len(render["scenes"]) == 9
    assert sum(len(scene["visualBeats"]) for scene in render["scenes"]) == 18


def test_chunk_beat_drift_is_rejected_by_closure_and_direct_materializer(tmp_path: Path):
    root, fx, authoring = fixture.build_workspace(tmp_path)
    broken = copy.deepcopy(authoring)
    broken["production"]["scenes"][0]["chunks"].pop()
    errors = closure.validate_authoring(broken, registry())
    assert any("chunks/beats length mismatch" in error for error in errors)
    write_authoring(root, fx, broken)
    completed = run_materializer(root, fx.DATE)
    assert completed.returncode != 0
    assert "chunks/beats length mismatch" in completed.stdout + completed.stderr


def test_empty_shots_placeholder_is_rejected_by_closure_and_direct_materializer(tmp_path: Path):
    root, fx, authoring = fixture.build_workspace(tmp_path)
    broken = copy.deepcopy(authoring)
    broken["production"]["scenes"][0]["beats"][0]["shots"] = []
    errors = closure.validate_authoring(broken, registry())
    assert any("authored shots must contain 1-4" in error for error in errors)
    write_authoring(root, fx, broken)
    completed = run_materializer(root, fx.DATE)
    assert completed.returncode != 0
    assert "authored shots must contain 1-4" in completed.stdout + completed.stderr


def test_empty_visual_events_placeholder_is_rejected_by_closure_and_direct_materializer(tmp_path: Path):
    root, fx, authoring = fixture.build_workspace(tmp_path)
    broken = copy.deepcopy(authoring)
    broken["production"]["scenes"][0]["beats"][0]["visualEvents"] = []
    errors = closure.validate_authoring(broken, registry())
    assert any("visualEvents must be a non-empty array" in error for error in errors)
    write_authoring(root, fx, broken)
    completed = run_materializer(root, fx.DATE)
    assert completed.returncode != 0
    assert "visualEvents must be a non-empty array" in completed.stdout + completed.stderr


def test_schema_rejects_empty_authored_progression_arrays(tmp_path: Path):
    root, fx, authoring = fixture.build_workspace(tmp_path)
    broken = copy.deepcopy(authoring)
    broken["production"]["scenes"][0]["beats"][0]["shots"] = []
    path = write_authoring(root, fx, broken)
    semantic = load_module(
        "current_authoring_semantic_empty_shots",
        root / "scripts/validate_editorial_semantic_boundary.py",
    )
    with pytest.raises(Exception, match="shots|minItems|non-empty"):
        semantic.validate_boundary(root, fx.DATE, path)
