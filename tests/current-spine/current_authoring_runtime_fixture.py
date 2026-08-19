from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_TEST = ROOT / "tests/editorial-semantic-boundary/test_current_contract_e2e.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _runtime_paragraphs(index: int, narration: str) -> list[str]:
    if index == 9:
        expected = "僕からは以上、朝のNASDAQカフェでした。いってらっしゃい。おやすみなさい。"
        if narration != expected:
            raise RuntimeError("scene-09 shared synthetic closing changed; review runtime fixture explicitly")
        return [
            "僕からは以上、朝のNASDAQカフェでした。",
            "いってらっしゃい。おやすみなさい。",
        ]

    expected = f"僕はScene {index}で市場の意味を確認します。"
    if narration != expected:
        raise RuntimeError(
            f"scene-{index:02d} shared synthetic narration changed; review runtime fixture explicitly"
        )
    return [
        f"僕はScene {index}で市場を確認します。",
        "ここから市場の意味を確認します。",
    ]


def author_runtime_presentation(authoring: dict[str, Any]) -> dict[str, Any]:
    """Return one production-facing Current fixture without post-hoc qualification repair.

    The editorial-semantic fixture remains intentionally tiny. This shared runtime factory
    promotes it once into the exact 2 chunks / 2 Beats Current presentation contract used by
    parity tests and Renderer qualification. Optional authored progression fields are omitted
    when no progression has been authored; an empty array is never used as a placeholder.
    """
    value = copy.deepcopy(authoring)
    script_scenes = value.get("storyScript", {}).get("scenes", [])
    production_scenes = value.get("production", {}).get("scenes", [])
    if len(script_scenes) != 9 or len(production_scenes) != 9:
        raise RuntimeError("Current runtime fixture requires exactly 9 script/production Scenes")

    for index, (script_scene, production_scene) in enumerate(
        zip(script_scenes, production_scenes, strict=True), 1
    ):
        beats = production_scene.get("beats")
        if not isinstance(beats, list) or len(beats) != 2:
            raise RuntimeError(f"scene-{index:02d}: runtime fixture requires exactly 2 Beats")
        narration = script_scene.get("narration")
        if not isinstance(narration, str):
            raise RuntimeError(f"scene-{index:02d}: runtime narration must be a string")
        parts = _runtime_paragraphs(index, narration)
        script_scene["narration"] = "\n\n".join(parts)
        production_scene["chunks"] = [
            {"text": part, "expression": "分析"}
            for part in parts
        ]
        for beat in beats:
            if beat.get("shots") == []:
                beat.pop("shots")
            if beat.get("visualEvents") == []:
                beat.pop("visualEvents")

        projected = "\n\n".join(chunk["text"] for chunk in production_scene["chunks"])
        if projected != script_scene["narration"]:
            raise RuntimeError(f"scene-{index:02d}: runtime narration/chunk projection mismatch")

    if "以上、朝のNASDAQカフェでした" not in script_scenes[8]["narration"]:
        raise RuntimeError("scene-09 fixed closing phrase was not preserved")
    return value


def build_workspace(tmp_path: Path) -> tuple[Path, Any, dict[str, Any]]:
    semantic = _load_module("current_runtime_semantic_fixture", SEMANTIC_TEST)
    root, authoring = semantic.build_workspace(tmp_path)
    runtime_authoring = author_runtime_presentation(authoring)
    authoring_path = root / "daily-authoring" / f"{semantic.fx.DATE}.json"
    semantic.fx.write_json(authoring_path, runtime_authoring)
    return root, semantic.fx, runtime_authoring
