from __future__ import annotations

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


def assert_runtime_presentation(authoring: dict[str, Any]) -> None:
    """Assert that the single shared Current fixture is already production-facing.

    This module intentionally performs no normalization or repair. If the semantic Current
    fixture drifts from the production contract, parity and qualification must fail at the
    source instead of manufacturing a second fixture representation.
    """
    script_scenes = authoring.get("storyScript", {}).get("scenes", [])
    production_scenes = authoring.get("production", {}).get("scenes", [])
    if len(script_scenes) != 9 or len(production_scenes) != 9:
        raise RuntimeError("Current runtime fixture requires exactly 9 script/production Scenes")

    for index, (script_scene, production_scene) in enumerate(
        zip(script_scenes, production_scenes, strict=True), 1
    ):
        beats = production_scene.get("beats")
        chunks = production_scene.get("chunks")
        if not isinstance(beats, list) or len(beats) != 2:
            raise RuntimeError(f"scene-{index:02d}: Current fixture requires exactly 2 Beats")
        if not isinstance(chunks, list) or len(chunks) != 2:
            raise RuntimeError(f"scene-{index:02d}: Current fixture requires exactly 2 chunks")
        narration = script_scene.get("narration")
        if not isinstance(narration, str):
            raise RuntimeError(f"scene-{index:02d}: Current narration must be a string")
        projected = "\n\n".join(str(chunk.get("text", "")) for chunk in chunks)
        if projected != narration:
            raise RuntimeError(f"scene-{index:02d}: Current narration/chunk projection mismatch")
        for beat_index, beat in enumerate(beats, 1):
            if beat.get("shots") == []:
                raise RuntimeError(f"scene-{index:02d}-beat-{beat_index:03d}: empty shots placeholder")
            if beat.get("visualEvents") == []:
                raise RuntimeError(f"scene-{index:02d}-beat-{beat_index:03d}: empty visualEvents placeholder")

    if "以上、朝のNASDAQカフェでした" not in script_scenes[8]["narration"]:
        raise RuntimeError("scene-09 fixed closing phrase was not preserved")


def build_workspace(tmp_path: Path) -> tuple[Path, Any, dict[str, Any]]:
    semantic = _load_module("current_runtime_semantic_fixture", SEMANTIC_TEST)
    root, authoring = semantic.build_workspace(tmp_path)
    assert_runtime_presentation(authoring)
    return root, semantic.fx, authoring
