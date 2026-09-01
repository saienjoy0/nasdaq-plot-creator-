from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "fixup_chatgpt_daily_materialization.py"
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("daily_fixup", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def renderer_root(tmp_path: Path) -> Path:
    root = tmp_path / "renderer"
    expressions = {
        "通常": {"assetId": "foxNormal", "fallback": False},
        "分析": {"assetId": "foxAnalysis", "fallback": False},
        "ニヤリ": {"assetId": "foxSmirk", "fallback": False},
        "軽い驚き": {"assetId": "foxSlightSurprise", "fallback": False},
        "旧表情": {"assetId": "foxFallback", "fallback": True},
    }
    assets = {
        "foxNormal": {"path": "assets/fox-normal.png"},
        "foxAnalysis": {"path": "assets/fox-analysis.png"},
        "foxSmirk": {"path": "assets/fox-smirk.png"},
        "foxSlightSurprise": {"path": "assets/fox-surprise.png"},
        "foxFallback": {"path": "assets/fox-fallback.png"},
    }
    write_json(root / "config" / "fox-expression-map.json", {"expressions": expressions})
    write_json(root / "config" / "asset-manifest.json", {"assets": assets})
    return root


def authored_scene() -> dict:
    return {
        "sceneId": "scene-01",
        "initialExpression": "通常",
        "narrationChunks": [
            {"chunkId": "scene-01-chunk-001", "expression": "分析"},
        ],
        "visualEvents": [
            {
                "action": "set-expression",
                "atChunkId": "scene-01-chunk-001",
                "expression": "ニヤリ",
            }
        ],
        "visualBeats": [
            {
                "shots": [
                    {
                        "startChunkId": "scene-01-chunk-001",
                        "foxExpression": "軽い驚き",
                    }
                ]
            }
        ],
        "assetPlacements": [
            {
                "placementId": "scene-01-placement-foxAnalysis",
                "assetId": "foxAnalysis",
                "role": "fox-expression",
                "region": "wrong-region",
                "fit": "cover",
                "opacity": 0.5,
                "startChunkId": "scene-01-chunk-001",
                "endChunkId": "scene-01-chunk-001",
            }
        ],
    }


def test_renderer_map_is_authority_and_all_expression_sources_are_projected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = renderer_root(tmp_path)
    monkeypatch.setenv("NASDAQ_CAFE_RENDERER_ROOT", str(root))
    mapping = MODULE.load_renderer_expression_asset_map()
    assert mapping == {
        "通常": "foxNormal",
        "分析": "foxAnalysis",
        "ニヤリ": "foxSmirk",
        "軽い驚き": "foxSlightSurprise",
    }

    scene = authored_scene()
    added = MODULE.ensure_fox_expression_placements(scene, mapping)
    assert added == 3
    placements = {
        row["assetId"]: row
        for row in scene["assetPlacements"]
        if row.get("role") == "fox-expression"
    }
    assert set(placements) == {
        "foxNormal",
        "foxAnalysis",
        "foxSmirk",
        "foxSlightSurprise",
    }
    for placement in placements.values():
        assert placement["region"] == "fox-left"
        assert placement["fit"] == "contain"
        assert placement["opacity"] == 1
        assert placement["startChunkId"] is None
        assert placement["endChunkId"] is None


def test_unknown_authored_expression_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = renderer_root(tmp_path)
    monkeypatch.setenv("NASDAQ_CAFE_RENDERER_ROOT", str(root))
    mapping = MODULE.load_renderer_expression_asset_map()
    scene = authored_scene()
    scene["initialExpression"] = "存在しない表情"
    with pytest.raises(SystemExit, match="unsupported authored fox expression in pinned renderer"):
        MODULE.ensure_fox_expression_placements(scene, mapping)


def test_duplicate_expression_placement_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = renderer_root(tmp_path)
    monkeypatch.setenv("NASDAQ_CAFE_RENDERER_ROOT", str(root))
    mapping = MODULE.load_renderer_expression_asset_map()
    scene = authored_scene()
    duplicate = dict(scene["assetPlacements"][0])
    duplicate["placementId"] = "scene-01-placement-foxAnalysis-duplicate"
    scene["assetPlacements"].append(duplicate)
    with pytest.raises(SystemExit, match="duplicate fox-expression placements for foxAnalysis"):
        MODULE.ensure_fox_expression_placements(scene, mapping)
