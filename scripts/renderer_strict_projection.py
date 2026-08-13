#!/usr/bin/env python3
"""Lightweight producer RenderSpec -> strict Renderer 2.4 schema projection.

This module is the single compatibility source for removing producer-only fields,
flattening Visual Grammar metadata, and normalizing reviewed schema aliases. It has
no Financial/Story runtime imports so pre-Visual-Intelligence use cannot accidentally
depend on unrelated production packages.
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
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    scenes: list[dict[str, Any]] = []
    beat_count = 0
    for scene in source.get("scenes", []):
        projected_scene = {key: scene[key] for key in SCENE_ALLOWED if key in scene}
        projected_scene["visualMode"] = VISUAL_MODE_MAP.get(
            projected_scene.get("visualMode"), projected_scene.get("visualMode")
        )
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
            projected["visualMode"] = VISUAL_MODE_MAP.get(
                projected.get("visualMode"), projected.get("visualMode")
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
