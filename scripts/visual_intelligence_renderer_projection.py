#!/usr/bin/env python3
"""Project approved producer RenderSpec into strict 18-Beat Renderer input for Visual Intelligence.

The Visual Intelligence boundary consumes the deterministic Renderer intermediate
already produced by `materialize_renderer_sources.py`, applies the already-compiled
Financial Recipe Plan, reuses the established Renderer 2.4 object canonicalizers,
then removes producer-only schema extensions. It MUST NOT change Story meaning,
narration, viewer text, Scene/Beat order, or Beat count.
Authoring Beat IDs remain the stable AI-facing identity even when the deterministic
Renderer intermediate temporarily uses canonical `vb-*` IDs.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import remotion_240_projection
import renderer_strict_projection
import viewer_surface_projection


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

SEMANTIC_BEAT_FIELDS = (
    "screenQuestion",
    "primaryElement",
    "viewerTexts",
    "narrationStartCue",
    "narrationEndCue",
)


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualIntelligenceRendererProjectionError(
            f"E_VISUAL_RENDERER_INPUT_INVALID:{label}:{exc}"
        ) from exc
    if not isinstance(value, dict):
        raise VisualIntelligenceRendererProjectionError(
            f"E_VISUAL_RENDERER_INPUT_INVALID:{label}:root must be object"
        )
    return value


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _assert_semantic_alignment(
    producer: dict[str, Any],
    candidate: dict[str, Any],
    *,
    stage: str,
) -> None:
    producer_scenes = producer.get("scenes")
    candidate_scenes = candidate.get("scenes")
    if not isinstance(producer_scenes, list) or not isinstance(candidate_scenes, list):
        raise VisualIntelligenceRendererProjectionError(
            f"E_VISUAL_RENDERER_PROJECTION_INVALID:{stage}:scenes"
        )
    if len(producer_scenes) != len(candidate_scenes):
        raise VisualIntelligenceRendererProjectionError(
            f"E_VISUAL_RENDERER_PROJECTION_SCENE_COUNT_CHANGED:{stage}"
        )
    for scene_index, (producer_scene, candidate_scene) in enumerate(
        zip(producer_scenes, candidate_scenes, strict=True)
    ):
        if producer_scene.get("narrationChunks") != candidate_scene.get("narrationChunks"):
            raise VisualIntelligenceRendererProjectionError(
                f"E_VISUAL_RENDERER_PROJECTION_NARRATION_CHANGED:{stage}:scene={scene_index + 1}"
            )
        producer_beats = producer_scene.get("visualBeats", [])
        candidate_beats = candidate_scene.get("visualBeats", [])
        if len(producer_beats) != len(candidate_beats):
            raise VisualIntelligenceRendererProjectionError(
                f"E_VISUAL_RENDERER_PROJECTION_BEAT_COUNT_CHANGED:{stage}:scene={scene_index + 1}"
            )
        for beat_index, (producer_beat, candidate_beat) in enumerate(
            zip(producer_beats, candidate_beats, strict=True)
        ):
            for field in SEMANTIC_BEAT_FIELDS:
                if producer_beat.get(field) != candidate_beat.get(field):
                    raise VisualIntelligenceRendererProjectionError(
                        "E_VISUAL_RENDERER_PROJECTION_SEMANTIC_FIELD_CHANGED:"
                        f"{stage}:scene={scene_index + 1}:beat={beat_index + 1}:field={field}"
                    )


def _restore_authoring_beat_ids(
    producer: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    restored = copy.deepcopy(candidate)
    producer_scenes = producer.get("scenes", [])
    candidate_scenes = restored.get("scenes", [])
    if len(producer_scenes) != len(candidate_scenes):
        raise VisualIntelligenceRendererProjectionError(
            "E_VISUAL_RENDERER_PROJECTION_SCENE_COUNT_CHANGED:beat-id-restore"
        )
    seen: set[str] = set()
    for scene_index, (producer_scene, candidate_scene) in enumerate(
        zip(producer_scenes, candidate_scenes, strict=True)
    ):
        producer_beats = producer_scene.get("visualBeats", [])
        candidate_beats = candidate_scene.get("visualBeats", [])
        if len(producer_beats) != len(candidate_beats):
            raise VisualIntelligenceRendererProjectionError(
                f"E_VISUAL_RENDERER_PROJECTION_BEAT_COUNT_CHANGED:beat-id-restore:scene={scene_index + 1}"
            )
        for beat_index, (producer_beat, candidate_beat) in enumerate(
            zip(producer_beats, candidate_beats, strict=True)
        ):
            source_id = producer_beat.get("beatId")
            if not isinstance(source_id, str) or not source_id:
                raise VisualIntelligenceRendererProjectionError(
                    f"E_VISUAL_RENDERER_INPUT_INVALID:missing producer beatId:scene={scene_index + 1}:beat={beat_index + 1}"
                )
            if source_id in seen:
                raise VisualIntelligenceRendererProjectionError(
                    f"E_VISUAL_RENDERER_INPUT_INVALID:duplicate producer beatId:{source_id}"
                )
            seen.add(source_id)
            candidate_beat["beatId"] = source_id
    return restored


def _renderer_intermediate(
    producer: dict[str, Any], *, repo_root: Path, date: str
) -> dict[str, Any]:
    path = repo_root / "working" / date / "render_spec_intermediate.json"
    if not path.is_file():
        return copy.deepcopy(producer)
    intermediate = _load_json_object(path, "renderer intermediate")
    if intermediate.get("schemaVersion") != "2.4.0":
        raise VisualIntelligenceRendererProjectionError(
            "E_VISUAL_RENDERER_INPUT_INVALID: intermediate must be render_spec 2.4.0"
        )
    _assert_semantic_alignment(producer, intermediate, stage="intermediate")
    return intermediate


def _apply_financial_recipe_plan(
    candidate: dict[str, Any], *, repo_root: Path, date: str
) -> dict[str, Any]:
    financial_contract_path = (
        repo_root / "working" / date / "financial_final_episode_contract.json"
    )
    recipe_plan_path = repo_root / "working" / date / "financial_recipe_plan.json"
    if not financial_contract_path.is_file() and not recipe_plan_path.is_file():
        return candidate
    if not financial_contract_path.is_file() or not recipe_plan_path.is_file():
        raise VisualIntelligenceRendererProjectionError(
            "E_VISUAL_FINANCIAL_PROJECTION_INCOMPLETE: financial contract/recipe plan pair required"
        )

    financial_contract = _load_json_object(
        financial_contract_path, "financial Final Episode Contract"
    )
    recipe_plan = _load_json_object(recipe_plan_path, "Financial Recipe Plan")
    if recipe_plan.get("episodeDate") != date:
        raise VisualIntelligenceRendererProjectionError(
            "E_VISUAL_FINANCIAL_PROJECTION_STALE: recipe plan episodeDate mismatch"
        )
    expected_contract_sha = recipe_plan.get("finalEpisodeContract", {}).get("sha256")
    actual_contract_sha = _sha256_file(financial_contract_path)
    if expected_contract_sha != actual_contract_sha:
        raise VisualIntelligenceRendererProjectionError(
            "E_VISUAL_FINANCIAL_PROJECTION_STALE: Final Episode Contract SHA mismatch"
        )

    try:
        import financial_visual_cross_artifact as financial_cross
    except ImportError as exc:
        raise VisualIntelligenceRendererProjectionError(
            f"E_VISUAL_FINANCIAL_PROJECTION_DEPENDENCY:{exc}"
        ) from exc

    projected = copy.deepcopy(candidate)
    try:
        financial_cross.apply_selected_plans(
            financial_contract,
            recipe_plan,
            _sha256_file(recipe_plan_path),
            projected,
            "2.4.0",
        )
    except (KeyError, financial_cross.CrossArtifactError) as exc:
        raise VisualIntelligenceRendererProjectionError(
            f"E_VISUAL_FINANCIAL_PROJECTION_INVALID:{exc}"
        ) from exc
    return projected


def _materialize_vnext_object_inventory(candidate: dict[str, Any]) -> dict[str, Any]:
    """Reuse established Renderer 2.4 object projections without changing Beat semantics.

    Visual Intelligence must see the same Renderer-native object inventory that final
    rendering sees. In particular, legacy producer Expected/Actual/Gap data is one
    three-line card, while `expected-actual-gap-flow` legally requires three role
    cards. The established Remotion 2.4 projection already performs this exact
    lossless split and rewrites its show events. Reuse it here instead of duplicating
    template semantics.
    """
    projected = copy.deepcopy(candidate)
    used_event_ids = {
        event["eventId"]
        for scene in projected.get("scenes", [])
        for event in scene.get("visualEvents", [])
        if isinstance(event, dict) and isinstance(event.get("eventId"), str)
    }
    for scene in projected.get("scenes", []):
        if not isinstance(scene, dict):
            continue
        for beat in scene.get("visualBeats", []):
            if not isinstance(beat, dict):
                continue
            if (
                beat.get("visualMode") == "expected-actual-gap"
                and beat.get("visualTemplate") == "expected-actual-gap-flow"
            ):
                try:
                    remotion_240_projection._materialize_expected_actual_gap(
                        scene, beat, used_event_ids
                    )
                except remotion_240_projection.ProjectionError as exc:
                    raise VisualIntelligenceRendererProjectionError(
                        f"E_VISUAL_OBJECT_INVENTORY_INVALID:{exc}"
                    ) from exc
    return projected


def _synchronize_replaced_object_events(
    producer: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    """Keep deterministic Visual Events bound to the objects a projected Beat displays.

    Financial/object projection may replace one producer object with one Renderer-native
    object (for example, a source-receipt card with its typed metric receipt). In that
    unambiguous 1->1 case, every scene event that targeted the removed producer object
    is rebound to the replacement object. More complex cardinality changes are never
    guessed here: an established specialized canonicalizer must already have authored
    all required event targets, otherwise this boundary fails closed.
    """
    projected = copy.deepcopy(candidate)
    producer_scenes = producer.get("scenes", [])
    projected_scenes = projected.get("scenes", [])
    if len(producer_scenes) != len(projected_scenes):
        raise VisualIntelligenceRendererProjectionError(
            "E_VISUAL_EVENT_BINDING_SCENE_COUNT_CHANGED"
        )

    for scene_index, (producer_scene, projected_scene) in enumerate(
        zip(producer_scenes, projected_scenes, strict=True), start=1
    ):
        producer_beats = producer_scene.get("visualBeats", [])
        projected_beats = projected_scene.get("visualBeats", [])
        if len(producer_beats) != len(projected_beats):
            raise VisualIntelligenceRendererProjectionError(
                f"E_VISUAL_EVENT_BINDING_BEAT_COUNT_CHANGED:scene={scene_index}"
            )
        events = projected_scene.get("visualEvents", [])
        if not isinstance(events, list):
            raise VisualIntelligenceRendererProjectionError(
                f"E_VISUAL_EVENT_BINDING_INVALID:scene={scene_index}:visualEvents"
            )

        all_projected_object_ids = [
            object_id
            for beat in projected_beats
            if isinstance(beat, dict)
            for object_id in beat.get("objectIds", [])
            if isinstance(object_id, str)
        ]

        for beat_index, (producer_beat, projected_beat) in enumerate(
            zip(producer_beats, projected_beats, strict=True), start=1
        ):
            old_ids = producer_beat.get("objectIds", [])
            new_ids = projected_beat.get("objectIds", [])
            if old_ids == new_ids:
                continue
            if not (
                isinstance(old_ids, list)
                and isinstance(new_ids, list)
                and all(isinstance(value, str) for value in old_ids)
                and all(isinstance(value, str) for value in new_ids)
            ):
                raise VisualIntelligenceRendererProjectionError(
                    f"E_VISUAL_EVENT_BINDING_INVALID:scene={scene_index}:beat={beat_index}:objectIds"
                )

            producer_events = producer_scene.get("visualEvents", [])
            source_targeted = {
                event.get("targetId")
                for event in producer_events
                if isinstance(event, dict) and event.get("targetId") in old_ids
            }

            if len(old_ids) == 1 and len(new_ids) == 1:
                old_id, new_id = old_ids[0], new_ids[0]
                if old_id != new_id:
                    # Rebinding is ambiguous if the old object still belongs to another
                    # projected Beat. Do not steal shared display ownership.
                    other_uses = sum(
                        1
                        for other_index, other_beat in enumerate(projected_beats)
                        if other_index != beat_index - 1
                        and old_id in other_beat.get("objectIds", [])
                    )
                    if other_uses:
                        raise VisualIntelligenceRendererProjectionError(
                            f"E_VISUAL_EVENT_BINDING_AMBIGUOUS:{old_id}"
                        )
                    for event in events:
                        if isinstance(event, dict) and event.get("targetId") == old_id:
                            event["targetId"] = new_id

            # If the producer actually displayed the replaced object, the projected Beat
            # must have a display-event reference for every replacement object. This is
            # what validates specialized 1->N canonicalizers such as Expected/Actual/Gap.
            if source_targeted:
                projected_targets = {
                    event.get("targetId")
                    for event in events
                    if isinstance(event, dict) and event.get("targetId") in new_ids
                }
                missing = [value for value in new_ids if value not in projected_targets]
                if missing:
                    raise VisualIntelligenceRendererProjectionError(
                        "E_VISUAL_EVENT_BINDING_MISSING:"
                        f"scene={scene_index}:beat={beat_index}:targets={','.join(missing)}"
                    )

            removed_ids = [value for value in old_ids if value not in new_ids]
            for old_id in removed_ids:
                if old_id in all_projected_object_ids:
                    continue
                if any(
                    isinstance(event, dict) and event.get("targetId") == old_id
                    for event in events
                ):
                    raise VisualIntelligenceRendererProjectionError(
                        f"E_VISUAL_EVENT_BINDING_STALE:{old_id}"
                    )
    return projected


def _normalize_selectable_viewer_inventory(candidate: dict[str, Any]) -> dict[str, Any]:
    """Normalize every object that Visual Intelligence may later make viewer-visible.

    The first viewer-surface projection runs before Financial/Visual Intelligence object
    inventory exists. A source receipt or other typed object can therefore be hidden at
    authoring time and become visible only after AI-B selects its Candidate. Normalize
    that selectable inventory before Candidate Builder so Critic and production see the
    exact same display-safe text. Speech and Beat-authored viewer semantics are untouched.
    """
    projected = copy.deepcopy(candidate)
    conversions: list[viewer_surface_projection.Conversion] = []

    def normalize(container: dict[str, Any], key: str, path: str) -> None:
        value = container.get(key)
        if not isinstance(value, str):
            return
        normalized = viewer_surface_projection.normalize_viewer_text(
            value,
            path=path,
            conversions=conversions,
        )
        viewer_surface_projection.assert_viewer_text_safe(normalized, path)
        container[key] = normalized

    for scene_index, scene in enumerate(projected.get("scenes", [])):
        if not isinstance(scene, dict):
            continue
        base = f"$.scenes[{scene_index}]"
        for card_index, card in enumerate(scene.get("cards", [])):
            if not isinstance(card, dict):
                continue
            card_base = f"{base}.cards[{card_index}]"
            normalize(card, "title", f"{card_base}.title")
            for line_index, line in enumerate(card.get("lines", [])):
                if not isinstance(line, dict):
                    continue
                line_base = f"{card_base}.lines[{line_index}]"
                normalize(line, "label", f"{line_base}.label")
                normalize(line, "value", f"{line_base}.value")
        for number_index, number in enumerate(scene.get("numbers", [])):
            if not isinstance(number, dict):
                continue
            number_base = f"{base}.numbers[{number_index}]"
            for key in ("label", "value", "unit", "comparison"):
                normalize(number, key, f"{number_base}.{key}")
        for node_index, node in enumerate(scene.get("nodes", [])):
            if isinstance(node, dict):
                normalize(node, "label", f"{base}.nodes[{node_index}].label")
        for arrow_index, arrow in enumerate(scene.get("arrows", [])):
            if isinstance(arrow, dict):
                normalize(arrow, "label", f"{base}.arrows[{arrow_index}].label")
    return projected


def project_visual_intelligence_renderer_input(
    render_spec: dict[str, Any], *, repo_root: Path, date: str
) -> dict[str, Any]:
    """Return strict 18-Beat Renderer input without mutating approved producer data."""
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
    candidate = _renderer_intermediate(render_spec, repo_root=repo_root, date=date)
    candidate = _apply_financial_recipe_plan(candidate, repo_root=repo_root, date=date)
    _assert_semantic_alignment(render_spec, candidate, stage="financialized-intermediate")
    candidate = _restore_authoring_beat_ids(render_spec, candidate)
    candidate = _materialize_vnext_object_inventory(candidate)
    candidate = _synchronize_replaced_object_events(render_spec, candidate)
    candidate = _normalize_selectable_viewer_inventory(candidate)
    _assert_semantic_alignment(render_spec, candidate, stage="renderer-object-inventory")
    _validate_mode_vocabulary(candidate)

    try:
        strict = renderer_strict_projection.strict_renderer_projection(
            candidate,
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
    _assert_semantic_alignment(render_spec, strict, stage="strict")

    producer_beat_ids = [
        beat.get("beatId")
        for scene in render_spec.get("scenes", [])
        for beat in scene.get("visualBeats", [])
    ]
    strict_beat_ids = [
        beat.get("beatId")
        for scene in strict.get("scenes", [])
        for beat in scene.get("visualBeats", [])
    ]
    if strict_beat_ids != producer_beat_ids:
        raise VisualIntelligenceRendererProjectionError(
            "E_VISUAL_RENDERER_PROJECTION_BEAT_ID_DRIFT"
        )
    return strict
