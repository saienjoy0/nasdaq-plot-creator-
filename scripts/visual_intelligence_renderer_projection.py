#!/usr/bin/env python3
"""Project producer RenderSpec 2.4 into strict Renderer input for Visual Intelligence.

This is a machine compatibility boundary only. It MUST NOT change Story meaning,
narration, evidence, viewer text, Beat order, or Beat count. Producer-only fields are
removed by the lightweight strict Renderer projection. Unknown visual modes fail
closed rather than being guessed.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import renderer_strict_projection


class VisualIntelligenceRendererProjectionError(ValueError):
    pass


RENDERER_VISUAL_MODES = {
    "conclusion-card",
    "number-comparison",
    "expected-actual-gap",
    "timeline",
    "chart",
    "causal-diagram",
    "stock-comparison",
    "news-media",
    "verification-points",
    "text-focus",
}


def _require_known_mode(value: Any, *, path: str) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise VisualIntelligenceRendererProjectionError(
            f"E_VISUAL_MODE_INVALID:{path}: visualMode must be a string"
        )
    normalized = renderer_strict_projection.VISUAL_MODE_MAP.get(value, value)
    if normalized not in RENDERER_VISUAL_MODES:
        raise VisualIntelligenceRendererProjectionError(
            f"E_VISUAL_MODE_UNMAPPED:{path}:{value}"
        )


def _validate_mode_vocabulary(render_spec: dict[str, Any]) -> None:
    scenes = render_spec.get("scenes")
    if not isinstance(scenes, list):
        raise VisualIntelligenceRendererProjectionError(
            "E_VISUAL_RENDERER_INPUT_INVALID: scenes must be an array"
        )
    for scene_index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise VisualIntelligenceRendererProjectionError(
                f"E_VISUAL_RENDERER_INPUT_INVALID: scenes[{scene_index}] must be an object"
            )
        _require_known_mode(
            scene.get("visualMode"), path=f"$.scenes[{scene_index}].visualMode"
        )
        beats = scene.get("visualBeats")
        if not isinstance(beats, list):
            raise VisualIntelligenceRendererProjectionError(
                f"E_VISUAL_RENDERER_INPUT_INVALID: scenes[{scene_index}].visualBeats must be an array"
            )
        for beat_index, beat in enumerate(beats):
            if not isinstance(beat, dict):
                raise VisualIntelligenceRendererProjectionError(
                    "E_VISUAL_RENDERER_INPUT_INVALID: "
                    f"scenes[{scene_index}].visualBeats[{beat_index}] must be an object"
                )
            _require_known_mode(
                beat.get("visualMode"),
                path=f"$.scenes[{scene_index}].visualBeats[{beat_index}].visualMode",
            )


def project_visual_intelligence_renderer_input(
    render_spec: dict[str, Any], *, repo_root: Path, date: str
) -> dict[str, Any]:
    """Return strict Renderer input without mutating the approved producer RenderSpec."""
    repo_root = repo_root.resolve()
    if render_spec.get("schemaVersion") != "2.4.0":
        raise VisualIntelligenceRendererProjectionError(
            "E_VISUAL_RENDERER_INPUT_INVALID: Visual Intelligence requires render_spec 2.4.0"
        )
    if render_spec.get("episode", {}).get("targetDate") != date:
        raise VisualIntelligenceRendererProjectionError(
            "E_VISUAL_RENDERER_INPUT_INVALID: episodeDate mismatch"
        )

    source_before = copy.deepcopy(render_spec)
    _validate_mode_vocabulary(render_spec)
    try:
        strict = renderer_strict_projection.strict_renderer_projection(
            render_spec,
            final_contract_path=(
                repo_root / "working" / date / "final_episode_contract.json"
            ),
            semantics_path=(repo_root / "contracts" / "visual_grammar_semantics.json"),
            renderer_compatibility_path=(
                repo_root / "contracts" / "visual_grammar_renderer_compatibility.json"
            ),
        )
    except (OSError, renderer_strict_projection.StrictRendererProjectionError) as exc:
        raise VisualIntelligenceRendererProjectionError(str(exc)) from exc

    if render_spec != source_before:
        raise VisualIntelligenceRendererProjectionError(
            "E_VISUAL_RENDERER_PROJECTION_MUTATED_SOURCE"
        )

    source_beat_ids = [
        beat.get("beatId")
        for scene in render_spec.get("scenes", [])
        for beat in scene.get("visualBeats", [])
        if isinstance(beat, dict)
    ]
    projected_beat_ids = [
        beat.get("beatId")
        for scene in strict.get("scenes", [])
        for beat in scene.get("visualBeats", [])
        if isinstance(beat, dict)
    ]
    if projected_beat_ids != source_beat_ids:
        raise VisualIntelligenceRendererProjectionError(
            "E_VISUAL_RENDERER_PROJECTION_BEAT_ORDER_CHANGED"
        )

    source_scenes = render_spec.get("scenes", [])
    projected_scenes = strict.get("scenes", [])
    if len(source_scenes) != len(projected_scenes):
        raise VisualIntelligenceRendererProjectionError(
            "E_VISUAL_RENDERER_PROJECTION_SCENE_COUNT_CHANGED"
        )
    for scene_index, (source_scene, projected_scene) in enumerate(
        zip(source_scenes, projected_scenes, strict=True)
    ):
        if source_scene.get("narrationChunks") != projected_scene.get("narrationChunks"):
            raise VisualIntelligenceRendererProjectionError(
                f"E_VISUAL_RENDERER_PROJECTION_NARRATION_CHANGED:scene={scene_index + 1}"
            )
        source_beats = source_scene.get("visualBeats", [])
        projected_beats = projected_scene.get("visualBeats", [])
        if len(source_beats) != len(projected_beats):
            raise VisualIntelligenceRendererProjectionError(
                f"E_VISUAL_RENDERER_PROJECTION_BEAT_COUNT_CHANGED:scene={scene_index + 1}"
            )
        for beat_index, (source_beat, projected_beat) in enumerate(
            zip(source_beats, projected_beats, strict=True)
        ):
            for field in (
                "screenQuestion",
                "primaryElement",
                "viewerTexts",
                "evidenceSourceIds",
                "narrationStartCue",
                "narrationEndCue",
            ):
                if source_beat.get(field) != projected_beat.get(field):
                    raise VisualIntelligenceRendererProjectionError(
                        "E_VISUAL_RENDERER_PROJECTION_SEMANTIC_FIELD_CHANGED:"
                        f"scene={scene_index + 1}:beat={beat_index + 1}:field={field}"
                    )
    return strict
