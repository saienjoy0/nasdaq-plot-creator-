#!/usr/bin/env python3
"""Lightweight producer RenderSpec -> strict Renderer 2.4 schema projection.

This module is the single compatibility source for removing producer-only fields,
flattening Visual Grammar metadata, normalizing reviewed schema aliases, and
projecting the fixed nine-scene structural roles required by Renderer. It has no
Financial/Story runtime imports and may not invent editorial meaning.
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

EXPECTED_BASIS_MAP = {
    "official_consensus": "official-consensus",
    "company_prior_guidance": "company-prior-guidance",
    "major_reporting": "major-reporting",
    "analyst_view": "analyst-view",
    "price_inference": "price-inference",
    "unconfirmed": "unconfirmed",
    "not_applicable": None,
    "not-applicable": None,
}
CAUSAL_SCOPE_MAP = {
    "company": "lead-stock",
    "company_direct": "lead-stock",
    "lead-stock": "lead-stock",
    "sector": "sector",
    "sector_support": "sector",
    "nasdaq": "nasdaq",
    "nasdaq_support": "nasdaq",
    "nasdaq_wide": "nasdaq",
    "multiple": "multiple",
}
SCREEN_STATE_MAP = {"Source": "News"}
PRODUCER_REVIEW_SCORE_MAP = {
    "opening": "openingHook",
    "progression": "storyProgression",
    "discovery": "discovery",
    "clarity": "clarity",
    "fox_voice": "foxCharacter",
    "late_payoff": "reasonToFinish",
}
RENDERER_REVIEW_SCORE_KEYS = set(PRODUCER_REVIEW_SCORE_MAP.values())


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


def _normalize_expected_basis_type(value: Any) -> Any:
    if value is None:
        return None
    return EXPECTED_BASIS_MAP.get(value, value)


def _project_editorial_shell(value: Any) -> Any:
    """Complete only Renderer-required mechanical shell fields.

    Existing strict fields always win. Empty arrays/nulls represent the absence of an
    authored compatibility value; they do not assert new market meaning. The program's
    fixed final lens supplies the minimum target index when the older Current producer
    predates the Renderer-required targetIndices field.
    """
    if not isinstance(value, dict):
        return value
    result = copy.deepcopy(value)
    result.setdefault("leadTheme", None)
    result.setdefault("targetIndices", ["Nasdaq Composite"])
    result.setdefault("directMaterial", [])
    result.setdefault("nasdaqDrivers", [])
    result.setdefault("amplifiers", [])
    result.setdefault("offsettingFactors", [])
    result.setdefault("expectedSourceIds", [])
    result.setdefault("timelineBasis", None)
    result.setdefault("verificationPoints", [])
    if "expectedBasisType" in result:
        result["expectedBasisType"] = _normalize_expected_basis_type(
            result.get("expectedBasisType")
        )
    return result


def _first_non_empty(values: Any) -> str | None:
    if not isinstance(values, list):
        return None
    for value in values:
        if isinstance(value, str) and value.strip():
            return value
    return None


def _project_publishing_shell(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    result = copy.deepcopy(value)
    if "recommendedTitle" not in result:
        chosen = _first_non_empty(result.get("titleCandidates"))
        if chosen is not None:
            result["recommendedTitle"] = chosen
    if "recommendedThumbnailText" not in result:
        chosen = _first_non_empty(result.get("thumbnailTextCandidates"))
        if chosen is not None:
            result["recommendedThumbnailText"] = chosen
    return result


def _project_review_shell(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    result = copy.deepcopy(value)
    scores = result.get("scores")
    if isinstance(scores, dict) and set(scores) != RENDERER_REVIEW_SCORE_KEYS:
        if set(PRODUCER_REVIEW_SCORE_MAP).issubset(scores):
            result["scores"] = {
                renderer_key: scores[producer_key]
                for producer_key, renderer_key in PRODUCER_REVIEW_SCORE_MAP.items()
            }
    if result.get("largestDropoffRisk") == "":
        result["largestDropoffRisk"] = "none-identified"
    if (
        "titleThumbnailConsistency" not in result
        and result.get("verdict") == "approved"
        and result.get("approvedForCodex") is True
    ):
        result["titleThumbnailConsistency"] = "consistent"
    return result


def _normalize_causal_scope(value: Any) -> Any:
    return CAUSAL_SCOPE_MAP.get(value, value)


def _normalize_screen_state(value: Any) -> Any:
    return SCREEN_STATE_MAP.get(value, value)


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
    if "editorial" in source:
        source["editorial"] = _project_editorial_shell(source["editorial"])
    if "publishing" in source:
        source["publishing"] = _project_publishing_shell(source["publishing"])
    if "review" in source:
        source["review"] = _project_review_shell(source["review"])

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
        if "causalScope" in projected_scene:
            projected_scene["causalScope"] = _normalize_causal_scope(
                projected_scene.get("causalScope")
            )
        if "expectedBasisType" in projected_scene:
            projected_scene["expectedBasisType"] = _normalize_expected_basis_type(
                projected_scene.get("expectedBasisType")
            )
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
            if "screenState" in projected:
                projected["screenState"] = _normalize_screen_state(
                    projected.get("screenState")
                )
            if "returnScreenState" in projected:
                projected["returnScreenState"] = _normalize_screen_state(
                    projected.get("returnScreenState")
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
