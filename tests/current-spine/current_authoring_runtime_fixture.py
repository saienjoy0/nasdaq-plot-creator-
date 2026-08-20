from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_TEST = ROOT / "tests/editorial-semantic-boundary/test_current_contract_e2e.py"
VISUAL_GRAMMAR_COMPATIBILITY = ROOT / "contracts/visual_grammar_renderer_compatibility.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _bind_existing_current_visual_grammar(authoring: dict[str, Any]) -> None:
    """Use the existing Plot↔Renderer compatibility contract as the sole grammar source.

    The semantic fixture deliberately does not own Renderer grammar literals. Runtime-facing
    Current tests resolve the authored template through the same frozen compatibility contract
    that production uses. This mirrors Renderer makeCurrentVisualGrammarFixture(), which also
    selects the first allowed grammar for the current visual template.
    """
    compatibility = json.loads(VISUAL_GRAMMAR_COMPATIBILITY.read_text(encoding="utf-8"))
    templates = compatibility.get("templates")
    if not isinstance(templates, list):
        raise RuntimeError("Current visual grammar compatibility templates must be an array")

    allowed_by_template: dict[str, list[str]] = {}
    for item in templates:
        if not isinstance(item, dict):
            continue
        template_id = item.get("visualTemplateId")
        grammar_ids = item.get("allowedGrammarIds")
        if (
            isinstance(template_id, str)
            and isinstance(grammar_ids, list)
            and grammar_ids
            and all(isinstance(grammar_id, str) and grammar_id for grammar_id in grammar_ids)
        ):
            allowed_by_template[template_id] = grammar_ids

    production = authoring.get("production")
    if not isinstance(production, dict):
        raise RuntimeError("Current runtime fixture requires production object")
    scenes = production.get("scenes")
    if not isinstance(scenes, list):
        raise RuntimeError("Current runtime fixture requires production.scenes array")

    for scene_index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise RuntimeError(f"scene-{scene_index:02d}: Current production Scene must be an object")
        beats = scene.get("beats")
        if not isinstance(beats, list):
            raise RuntimeError(f"scene-{scene_index:02d}: Current fixture requires Beats array")
        for beat_index, beat in enumerate(beats, 1):
            if not isinstance(beat, dict):
                raise RuntimeError(
                    f"scene-{scene_index:02d}-beat-{beat_index:03d}: Current Beat must be an object"
                )
            template_id = beat.get("visualTemplate")
            allowed = allowed_by_template.get(str(template_id))
            if not allowed:
                raise RuntimeError(
                    f"scene-{scene_index:02d}-beat-{beat_index:03d}: "
                    f"visualTemplate {template_id!r} is absent from Current compatibility contract"
                )
            beat["grammarId"] = allowed[0]


def assert_runtime_presentation(authoring: dict[str, Any]) -> None:
    """Assert that the single shared Current fixture is already production-facing.

    Runtime grammar comes from the existing frozen Plot↔Renderer compatibility contract;
    everything else is consumed exactly as authored. If the semantic Current fixture drifts
    from the production contract, parity and qualification fail at this shared source instead
    of manufacturing another fixture representation.
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
    _bind_existing_current_visual_grammar(authoring)
    semantic.fx.write_json(root / "daily-authoring" / f"{semantic.fx.DATE}.json", authoring)
    assert_runtime_presentation(authoring)
    return root, semantic.fx, authoring
