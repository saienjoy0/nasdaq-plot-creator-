#!/usr/bin/env python3
"""Lightweight producer RenderSpec -> strict Renderer schema projection.

This module is the single compatibility source for removing producer-only fields,
flattening Visual Grammar metadata, normalizing reviewed schema aliases, and
projecting the fixed nine-scene structural roles required by Renderer. For Current-v2
it reads only already-accepted Daily Authoring/Causal Dossier authority to fill the
Renderer metadata shape; it never makes editorial choices.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import current_compatibility_adapter_v12 as current_compat


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
    "primaryFunction", "screenState", "visualMode", "visualTemplate", "semanticScope",
    "visualGrammarId", "transitionRole", "templateVariant", "templateConfig",
    "sequencePolicy", "finalHoldMs", "contentType", "screenQuestion",
    "primaryElement", "viewerTexts", "changeCue", "objectIds", "assetPlacementIds",
    "assetState", "returnScreenState", "evidenceSourceIds", "expressionChange",
    "fallback", "financialReturnTarget", "financialVisualTrace", "entity",
    "pictureBook", "shots",
}
SUPPORTED_RENDER_SPEC_VERSIONS = frozenset({"2.4.0", "2.5.0"})

# Canonical Renderer mapping, mirrored from the exact pinned Renderer
# `src/spec/visual-component-registry.ts`. The Visual Template is the more specific
# contract; producer modes are compatibility vocabulary and must not override the
# template's Renderer mode when the producer mode is already reviewed/known.
VISUAL_MODE_BY_TEMPLATE = {
    "opening-contradiction": "conclusion-card",
    "market-pulse-grid": "number-comparison",
    "earnings-surprise": "expected-actual-gap",
    "dual-asset-split": "stock-comparison",
    "macro-pressure": "causal-diagram",
    "source-receipt": "text-focus",
    "hero-number": "text-focus",
    "closing-recap": "conclusion-card",
    "final-assembly": "conclusion-card",
    "conclusion-card": "conclusion-card",
    "expected-actual-bullet": "expected-actual-gap",
    "expected-actual-gap-flow": "expected-actual-gap",
    "metric-comparison-board": "number-comparison",
    "index-return-bars": "stock-comparison",
    "diverging-stock-bars": "stock-comparison",
    "split-comparison": "stock-comparison",
    "focus-matrix": "stock-comparison",
    "causal-lane": "causal-diagram",
    "tailwind-headwind": "causal-diagram",
    "evidence-boundary": "verification-points",
    "verification-checklist": "verification-points",
    "verification-matrix": "verification-points",
    "analogy-steps": "causal-diagram",
    "entity-card-full": "text-focus",
    "news-media": "news-media",
    "event-reaction-timeline": "timeline",
    "text-focus": "text-focus",
}

# Reviewed producer vocabulary aliases. Unknown values are intentionally left
# untouched so the strict Renderer schema remains the final fail-closed authority.
# Template IDs are also accepted scene-level aliases because historical producer
# payloads occasionally used a template name in visualMode.
VISUAL_MODE_MAP = {
    **VISUAL_MODE_BY_TEMPLATE,
    "verification": "verification-points",
    "causal-chain": "causal-diagram",
    "intraday-comparison": "number-comparison",
    "expectation-gap": "expected-actual-gap",
    # Early vocabulary admission only. Beat projection resolves generic comparison
    # from the exact Visual Template below.
    "comparison": "stock-comparison",
}

RENDERER_CANONICAL_MODES = frozenset(VISUAL_MODE_BY_TEMPLATE.values())
TEMPLATE_CANONICALIZABLE_PRODUCER_MODES = frozenset(
    {*RENDERER_CANONICAL_MODES, "comparison", "verification-matrix"}
)


def normalize_visual_mode(value: Any, visual_template: Any = None) -> Any:
    if (
        isinstance(visual_template, str)
        and visual_template in VISUAL_MODE_BY_TEMPLATE
        and value in TEMPLATE_CANONICALIZABLE_PRODUCER_MODES
    ):
        return VISUAL_MODE_BY_TEMPLATE[visual_template]
    return VISUAL_MODE_MAP.get(value, value)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StrictRendererProjectionError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise StrictRendererProjectionError(f"{label} must be an object")
    return value


def _current_v2_root_projection(
    source: dict[str, Any], *, final_contract_path: Path
) -> dict[str, Any]:
    """Fill Renderer root metadata from the same accepted Current-v2 authority.

    `final_contract_path` is always `working/<date>/final_episode_contract.json` on
    the production path, so it gives us the exact workspace/date without another
    runtime input. If this is not a Current-v2 day, return the source unchanged.
    """
    final_contract = final_contract_path.resolve()
    try:
        date = final_contract.parent.name
        repo_root = final_contract.parents[2]
    except IndexError:
        return source
    authoring_path = repo_root / "daily-authoring" / f"{date}.json"
    if not authoring_path.is_file():
        return source
    authoring = _load_json_object(authoring_path, "Current Daily Authoring")
    if authoring.get("contractVersion") != "2.0.0":
        return source
    if authoring.get("episodeDate") != date:
        raise StrictRendererProjectionError("Current Daily Authoring episodeDate mismatch")
    dossier_ref = authoring.get("causalDossier")
    if not isinstance(dossier_ref, dict) or not isinstance(dossier_ref.get("path"), str):
        raise StrictRendererProjectionError("Current Daily Authoring causalDossier binding missing")
    dossier_path = (repo_root / dossier_ref["path"]).resolve()
    dossier = _load_json_object(dossier_path, "Current Causal Dossier")
    projected = copy.deepcopy(source)
    try:
        projected["editorial"] = current_compat.project_renderer_editorial(
            dossier=dossier,
            production=authoring["production"],
            story_plan=authoring["storyPlan"],
        )
        projected["publishing"] = current_compat.project_renderer_publishing(
            authoring["publishing"]
        )
        projected["review"] = current_compat.project_creative_review(
            authoring["creativeReview"]
        )
    except (KeyError, current_compat.CurrentCompatibilityError) as exc:
        raise StrictRendererProjectionError(
            f"Current-v2 Renderer root compatibility failed: {exc}"
        ) from exc
    return projected


def _fixed_scene_role(index: int) -> str:
    if index == 0:
        return "opening-hook-market-direction-greeting-conclusion"
    if index == 8:
        return "closing-recap-sendoff-goodnight"
    return "editorial-body"


def _normalize_scene_contract_fields(projected_scene: dict[str, Any]) -> None:
    scope = projected_scene.get("causalScope")
    if scope not in current_compat.CAUSAL_SCOPE_MAP:
        raise StrictRendererProjectionError(f"unsupported producer causalScope: {scope!r}")
    projected_scene["causalScope"] = current_compat.CAUSAL_SCOPE_MAP[scope]
    try:
        projected_scene["expectedBasisType"] = current_compat.project_expected_basis(
            projected_scene.get("expectedBasisType")
        )
    except current_compat.CurrentCompatibilityError as exc:
        raise StrictRendererProjectionError(str(exc)) from exc


def _normalize_beat_contract_fields(projected: dict[str, Any]) -> None:
    state = projected.get("screenState")
    if state not in current_compat.SCREEN_STATE_MAP:
        raise StrictRendererProjectionError(f"unsupported producer screenState: {state!r}")
    projected["screenState"] = current_compat.SCREEN_STATE_MAP[state]
    return_state = projected.get("returnScreenState")
    if return_state is not None:
        if return_state not in current_compat.SCREEN_STATE_MAP:
            raise StrictRendererProjectionError(
                f"unsupported producer returnScreenState: {return_state!r}"
            )
        projected["returnScreenState"] = current_compat.SCREEN_STATE_MAP[return_state]


def strict_renderer_projection(
    render_spec: dict[str, Any],
    *,
    final_contract_path: Path,
    semantics_path: Path,
    renderer_compatibility_path: Path,
) -> dict[str, Any]:
    source = _current_v2_root_projection(
        copy.deepcopy(render_spec), final_contract_path=final_contract_path
    )
    result = {key: source[key] for key in ROOT_ALLOWED if key in source}
    if source.get("schemaVersion") not in SUPPORTED_RENDER_SPEC_VERSIONS:
        raise StrictRendererProjectionError(
            "renderer projection requires schemaVersion 2.4.0 or 2.5.0"
        )
    source_scenes = source.get("scenes", [])
    if not isinstance(source_scenes, list) or len(source_scenes) != 9:
        raise StrictRendererProjectionError("renderer projection requires exactly 9 scenes")
    scenes: list[dict[str, Any]] = []
    beat_count = 0
    for scene_index, scene in enumerate(source_scenes):
        projected_scene = {key: scene[key] for key in SCENE_ALLOWED if key in scene}
        projected_scene["sceneRole"] = _fixed_scene_role(scene_index)
        _normalize_scene_contract_fields(projected_scene)
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
            _normalize_beat_contract_fields(projected)
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
        elif projected_beats and source_scene_mode in TEMPLATE_CANONICALIZABLE_PRODUCER_MODES:
            # Scene mode is a summary surface. Use the first already-authored Beat's
            # Renderer-canonical mode instead of guessing a template at Scene level.
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