from __future__ import annotations

import copy
import importlib.util
import json
import os
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
renderer_sources = load_module(
    "current_renderer_sources_for_parity",
    ROOT / "scripts/materialize_renderer_sources.py",
)


def registry() -> dict:
    return json.loads((ROOT / "contracts/financial_recipe_registry.json").read_text(encoding="utf-8"))


def run_materializer(
    root: Path,
    date: str,
    *,
    renderer_root: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    if renderer_root is None:
        renderer_root = install_renderer_expression_contract(root)
    env = os.environ.copy()
    env["NASDAQ_CAFE_RENDERER_ROOT"] = str(renderer_root)
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
        env=env,
        text=True,
        capture_output=True,
    )


def write_authoring(root: Path, fx, authoring: dict) -> Path:
    path = root / "daily-authoring" / f"{fx.DATE}.json"
    fx.write_json(path, authoring)
    return path


def semantic_validator(root: Path, name: str):
    return load_module(name, root / "scripts/validate_editorial_semantic_boundary.py")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def install_renderer_expression_contract(root: Path) -> Path:
    renderer = root / "renderer"
    write_json(renderer / "config" / "fox-expression-map.json", {
        "expressions": {
            "通常": {"assetId": "foxNormal", "fallback": False},
            "分析": {"assetId": "foxAnalysis", "fallback": False},
            "軽い驚き": {"assetId": "foxSlightSurprise", "fallback": False},
        }
    })
    write_json(renderer / "config" / "asset-manifest.json", {
        "assets": {
            "foxNormal": {"path": "assets/fox-normal.png"},
            "foxAnalysis": {"path": "assets/fox-analysis.png"},
            "foxSlightSurprise": {"path": "assets/fox-surprise.png"},
        }
    })
    return renderer


def test_current_runtime_fixture_schema_closure_materializer_and_source_projection_agree(tmp_path: Path):
    root, fx, authoring = fixture.build_workspace(tmp_path)
    authoring_path = root / "daily-authoring" / f"{fx.DATE}.json"

    semantic = semantic_validator(root, "current_authoring_semantic_for_parity")
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
    normalized, _ = renderer_sources.normalize_render_base(render)
    assert [source["sourceId"] for source in normalized["sources"]] == ["source-001"]


def test_current_materializer_projects_all_authored_fox_expression_assets(tmp_path: Path):
    root, fx, authoring = fixture.build_workspace(tmp_path)
    scene = authoring["production"]["scenes"][0]
    scene["initialExpression"] = "軽い驚き"
    for chunk in scene["chunks"]:
        chunk["expression"] = "分析"
    write_authoring(root, fx, authoring)
    renderer = install_renderer_expression_contract(root)

    completed = run_materializer(root, fx.DATE, renderer_root=renderer)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    render = json.loads(
        (root / "render-specs" / fx.DATE / "render_spec.json").read_text(encoding="utf-8")
    )
    placements = [
        row
        for row in render["scenes"][0]["assetPlacements"]
        if row.get("role") == "fox-expression"
    ]
    assert {row["assetId"] for row in placements} == {"foxAnalysis", "foxSlightSurprise"}
    for placement in placements:
        assert placement["region"] == "fox-left"
        assert placement["fit"] == "contain"
        assert placement["opacity"] == 1
        assert placement["startChunkId"] is None
        assert placement["endChunkId"] is None


def test_empty_source_registry_fails_schema_closure_and_renderer_projection(tmp_path: Path):
    root, fx, authoring = fixture.build_workspace(tmp_path)
    broken = copy.deepcopy(authoring)
    broken["production"]["sources"] = []
    errors = closure.validate_authoring(broken, registry())
    assert any("at least one renderable source-NNN" in error for error in errors)

    path = write_authoring(root, fx, broken)
    semantic = semantic_validator(root, "current_authoring_semantic_empty_sources")
    with pytest.raises(Exception, match="sources|minItems|non-empty"):
        semantic.validate_boundary(root, fx.DATE, path)

    render = json.loads((root / "render-specs" / fx.DATE / "render_spec.json").read_text(encoding="utf-8")) if (root / "render-specs" / fx.DATE / "render_spec.json").is_file() else None
    if render is None:
        write_authoring(root, fx, authoring)
        completed = run_materializer(root, fx.DATE)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        render = json.loads((root / "render-specs" / fx.DATE / "render_spec.json").read_text(encoding="utf-8"))
    render["sources"] = []
    with pytest.raises(renderer_sources.RendererSourceError, match="renderer source registry would be empty"):
        renderer_sources.normalize_render_base(render)


def test_historical_only_sources_fail_closure_before_renderer_projection(tmp_path: Path):
    _, _, authoring = fixture.build_workspace(tmp_path)
    broken = copy.deepcopy(authoring)
    broken["production"]["sources"] = [{
        "sourceId": "memory-001",
        "sourceType": "historical-memory",
        "title": "historical context",
    }]
    errors = closure.validate_authoring(broken, registry())
    assert any("at least one renderable source-NNN" in error for error in errors)


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
    semantic = semantic_validator(root, "current_authoring_semantic_empty_shots")
    with pytest.raises(Exception, match="shots|minItems|non-empty"):
        semantic.validate_boundary(root, fx.DATE, path)
