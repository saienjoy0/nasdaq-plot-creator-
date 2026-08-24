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
VISUAL_MODE_MAP = {
    "verification": "verification-points",
    "closing-recap": "conclusion-card",
    "causal-chain": "causal-diagram",
    "intraday-comparison": "number-comparison",
    "expectation-gap": "expected-actual-gap",
}

# Producer `comparison` is intentionally generic. Renderer 2.4 assigns the concrete
# visualMode by Visual Template, so this compatibility layer must preserve that
# distinction instead of collapsing every comparison into one Renderer mode.
COMPARISON_MODE_BY_TEMPLATE = {
    "event-reaction-timeline": "timeline",
    "verification-matrix": "verification-points",
    "split-comparison": "stock-comparison",
    "focus-matrix": "stock-comparison",
    "index-return-bars": "stock-comparison",
    "diverging-stock-bars": "stock-comparison",
    "dual-asset-split": "stock-comparison",
    "metric-comparison-board": "number-comparison",
    "market-pulse-grid": "number-comparison",
}


def normalize_visual_mode(value: Any, visual_template: Any = None) -> Any:
    if value == "comparison" and isinstance(visual_template, str):
        return COMPARISON_MODE_BY_TEMPLATE.get(visual_template, value)
    return VISUAL_MODE_MAP.get(value, value)


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
        projected_beats: list[dict[str, Any]] = []
        for beat in scene.get("visualBeats", []):
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
            projected["visualMode"] = normalize_visual_mode(
                projected.get("visualMode"), projected.get("visualTemplate")
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
        source_scene_mode = projected_scene.get("visualMode")
        if source_scene_mode == "comparison" and projected_beats:
            projected_scene["visualMode"] = projected_beats[0].get("visualMode")
        else:
            projected_scene["visualMode"] = normalize_visual_mode(source_scene_mode)
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
