#!/usr/bin/env python3
"""Lightweight producer RenderSpec -> strict Renderer 2.4 schema projection.

This module is the single compatibility source for removing producer-only fields,
flattening Visual Grammar metadata, normalizing reviewed schema aliases, and
projecting the fixed nine-scene structural roles required by Renderer. It has no
Financial/Story runtime imports.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any


class StrictRendererProjectionError(ValueError):
    pass


ROOT_ALLOWED = {
    "schemaVersion", "financialVisualContract", "episode", "editorial", "publishing",
    "sources", "review", "pronunciations", "corrections", "voiceProfileId", "scenes",
}
SCENE_ALLOWED = {
    "sceneId", "sceneNumber", "sceneRole", "formalName", "purpose", "causalScope",
    "performanceIntent", "evidenceSourceIds", "uncertainty", "timelineBasis",
    "expectedBasisType", "visualMode", "initialExpression", "headline",
    "supportingTexts", "sourceLabel", "narrationChunks", "visualBeats", "cards",
    "numbers", "nodes", "arrows", "visualEvents", "assetPlacements", "transition",
}
BEAT_ALLOWED = {
    "beatId", "startChunkId", "endChunkId", "narrationStartCue", "narrationEndCue",
    "primaryFunction", "screenState", "visualMode", "visualTemplate",
    "visualGrammarId", "transitionRole", "templateVariant", "templateConfig",
    "sequencePolicy", "finalHoldMs", "contentType", "screenQuestion",
    "primaryElement", "viewerTexts", "changeCue", "objectIds", "assetPlacementIds",
    "assetState", "returnScreenState", "evidenceSourceIds", "expressionChange",
    "fallback", "financialReturnTarget", "financialVisualTrace", "entity",
    "pictureBook", "shots",
}

# Reviewed producer vocabulary aliases only. Unknown values are intentionally left
# untouched here so the strict Renderer schema remains the final fail-closed authority.
# Template-aware legacy values are admitted for the coarse Visual Intelligence
# vocabulary check, then resolved below from the already-authored visualTemplate.
VISUAL_MODE_MAP = {
    "verification": "verification-points",
    "closing-recap": "conclusion-card",
    "causal-chain": "causal-diagram",
    "intraday-comparison": "number-comparison",
    "expectation-gap": "expected-actual-gap",
    "comparison": "timeline",
    "verification-matrix": "verification-points",
}

TEMPLATE_AWARE_VISUAL_MODE_MAP = {
    ("comparison", "event-reaction-timeline"): "timeline",
    ("comparison", "verification-matrix"): "verification-points",
    ("verification-matrix", "verification-matrix"): "verification-points",
    ("verification-matrix", "split-comparison"): "stock-comparison",
}
TEMPLATE_AWARE_VISUAL_MODES = {
    producer_mode for producer_mode, _ in TEMPLATE_AWARE_VISUAL_MODE_MAP
}


def normalize_visual_mode(value: Any, *, visual_template: Any = None) -> Any:
    """Normalize reviewed producer vocabulary without inventing template semantics."""
    if value in TEMPLATE_AWARE_VISUAL_MODES:
        return TEMPLATE_AWARE_VISUAL_MODE_MAP.get((value, visual_template), value)
    return VISUAL_MODE_MAP.get(value, value)


def _normalize_visual_mode_or_raise(
    value: Any, *, visual_template: Any, path: str
) -> Any:
    normalized = normalize_visual_mode(value, visual_template=visual_template)
    if value in TEMPLATE_AWARE_VISUAL_MODES and normalized == value:
        raise StrictRendererProjectionError(
            f"{path}: {value} visualMode requires reviewed visualTemplate"
        )
    return normalized


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixed_scene_role(index: int) -> str:
    if index == 0:
        return "opening-hook-market-direction-greeting-conclusion"
    if index == 8:
        return "closing-recap-sendoff-goodnight"
    return "editorial-body"


def strict_renderer_projection(
    render_spec: dict[str, Any],
    *,
    final_contract_path: Path,
    semantics_path: Path,
    renderer_compatibility_path: Path,
) -> dict[str, Any]:
    source = copy.deepcopy(render_spec)
    result = {key: source[key] for key in ROOT_ALLOWED if key in source}
    if source.get("schemaVersion") != "2.4.0":
        raise StrictRendererProjectionError(
            "renderer projection requires schemaVersion 2.4.0"
        )
    source_scenes = source.get("scenes", [])
    if not isinstance(source_scenes, list) or len(source_scenes) != 9:
        raise StrictRendererProjectionError("renderer projection requires exactly 9 scenes")
    scenes: list[dict[str, Any]] = []
    beat_count = 0
    for scene_index, scene in enumerate(source_scenes):
        projected_scene = {key: scene[key] for key in SCENE_ALLOWED if key in scene}
        projected_scene["sceneRole"] = _fixed_scene_role(scene_index)
        source_beats = scene.get("visualBeats", [])
        first_template = (
            source_beats[0].get("visualTemplate")
            if source_beats and isinstance(source_beats[0], dict)
            else None
        )
        projected_scene["visualMode"] = _normalize_visual_mode_or_raise(
            projected_scene.get("visualMode"),
            visual_template=first_template,
            path=f"{scene.get('sceneId')}:scene visualMode",
        )
        projected_beats: list[dict[str, Any]] = []
        for beat in source_beats:
            grammar = beat.get("visualGrammar")
            projected = {key: beat[key] for key in BEAT_ALLOWED if key in beat}
            if isinstance(grammar, dict):
                projected["visualGrammarId"] = grammar.get("grammarId")
                projected["transitionRole"] = grammar.get("transitionRole")
            elif not (
                isinstance(projected.get("visualGrammarId"), str)
                and isinstance(projected.get("transitionRole"), str)
            ):
                raise StrictRendererProjectionError(
                    f"{scene.get('sceneId')}/{beat.get('beatId')}: Visual Grammar metadata missing"
                )
            projected["visualMode"] = _normalize_visual_mode_or_raise(
                projected.get("visualMode"),
                visual_template=projected.get("visualTemplate"),
                path=f"{scene.get('sceneId')}/{beat.get('beatId')}:visualMode",
            )
            config = projected.get("templateConfig")
            if not isinstance(config, dict):
                raise StrictRendererProjectionError(
                    f"{scene.get('sceneId')}/{beat.get('beatId')}: templateConfig missing"
                )
            projected["templateVariant"] = projected.get(
                "templateVariant", config.get("variant")
            )
            projected_beats.append(projected)
            beat_count += 1
        projected_scene["visualBeats"] = projected_beats
        scenes.append(projected_scene)
    result["scenes"] = scenes
    result["visualGrammarContract"] = {
        "contractVersion": "1.0.0",
        "semanticsSha256": sha256_file(semantics_path),
        "rendererCompatibilitySha256": sha256_file(renderer_compatibility_path),
        "finalEpisodeContractSha256": sha256_file(final_contract_path),
        "beatCount": beat_count,
    }
    return result
