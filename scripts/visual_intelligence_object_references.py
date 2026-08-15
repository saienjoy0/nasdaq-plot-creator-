#!/usr/bin/env python3
"""Fail-closed object-reference reconciliation for Visual Intelligence Renderer input.

This layer runs immediately after producer -> Renderer projection. It never chooses
visual content. It only keeps already-authored object references consistent when a
projection deterministically replaces one Beat object with another Renderer-native
object.

Rules:
- unchanged object inventories are a no-op;
- an unambiguous 1 -> 1 replacement may be rebound inside that Beat only;
- approved specialized complex rewrites are validated, not guessed;
- every other N -> M rewrite fails closed;
- references outside the owning Beat make a replacement ambiguous and fail;
- Visual Events, Shot targets, and object-bearing templateConfig fields are checked.
"""
from __future__ import annotations

import copy
from typing import Any


class ObjectReferenceReconciliationError(ValueError):
    pass


SHOT_SCALAR_REFERENCE_FIELDS = (
    "primaryTargetId",
    "referenceTargetId",
    "outcomeTargetId",
    "cameraTargetId",
)
SHOT_LIST_REFERENCE_FIELDS = ("secondaryTargetIds",)

TEMPLATE_CONFIG_SCALAR_REFERENCE_FIELDS = ("outcomeNodeId",)
TEMPLATE_CONFIG_LIST_REFERENCE_FIELDS = (
    "nodeOrder",
    "displayOrder",
    "metricIds",
    "causalStepIds",
    "highlightObjectIds",
)

# eventOrderIds are event identities, not visual-object identities. seriesObjectIds
# are renderer objects and therefore participate in reconciliation.
REACTION_TIMELINE_LIST_REFERENCE_FIELDS = ("seriesObjectIds",)


def _string_list(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ObjectReferenceReconciliationError(
            f"E_VISUAL_OBJECT_REFERENCE_INVALID:{label}"
        )
    return value


def _chunk_positions(scene: dict[str, Any], *, scene_index: int) -> dict[str, int]:
    chunks = scene.get("narrationChunks")
    if not isinstance(chunks, list):
        raise ObjectReferenceReconciliationError(
            f"E_VISUAL_OBJECT_REFERENCE_INVALID:scene={scene_index}:narrationChunks"
        )
    positions: dict[str, int] = {}
    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict) or not isinstance(chunk.get("chunkId"), str):
            raise ObjectReferenceReconciliationError(
                f"E_VISUAL_OBJECT_REFERENCE_INVALID:scene={scene_index}:chunk={index + 1}"
            )
        chunk_id = chunk["chunkId"]
        if chunk_id in positions:
            raise ObjectReferenceReconciliationError(
                f"E_VISUAL_OBJECT_REFERENCE_INVALID:duplicate-chunk:{chunk_id}"
            )
        positions[chunk_id] = index
    return positions


def _beat_chunk_range(
    beat: dict[str, Any], *, positions: dict[str, int], scene_index: int, beat_index: int
) -> tuple[int, int]:
    start_id = beat.get("startChunkId")
    end_id = beat.get("endChunkId")
    if start_id not in positions or end_id not in positions:
        raise ObjectReferenceReconciliationError(
            "E_VISUAL_OBJECT_REFERENCE_INVALID:"
            f"scene={scene_index}:beat={beat_index}:chunk-range"
        )
    start = positions[start_id]
    end = positions[end_id]
    if start > end:
        raise ObjectReferenceReconciliationError(
            "E_VISUAL_OBJECT_REFERENCE_INVALID:"
            f"scene={scene_index}:beat={beat_index}:chunk-order"
        )
    return start, end


def _event_is_local(
    event: dict[str, Any], *, positions: dict[str, int], start: int, end: int
) -> bool:
    chunk_id = event.get("atChunkId")
    if not isinstance(chunk_id, str) or chunk_id not in positions:
        raise ObjectReferenceReconciliationError(
            f"E_VISUAL_OBJECT_REFERENCE_INVALID:event-chunk:{chunk_id}"
        )
    return start <= positions[chunk_id] <= end


def _replace_scalar_reference(container: dict[str, Any], key: str, old_id: str, new_id: str) -> None:
    if container.get(key) == old_id:
        container[key] = new_id


def _replace_list_reference(container: dict[str, Any], key: str, old_id: str, new_id: str) -> None:
    value = container.get(key)
    if value is None:
        return
    refs = _string_list(value, label=key)
    container[key] = [new_id if item == old_id else item for item in refs]


def _beat_reference_values(beat: dict[str, Any]) -> list[str]:
    values: list[str] = []
    shots = beat.get("shots")
    if shots is not None:
        if not isinstance(shots, list):
            raise ObjectReferenceReconciliationError("E_VISUAL_OBJECT_REFERENCE_INVALID:shots")
        for shot in shots:
            if not isinstance(shot, dict):
                raise ObjectReferenceReconciliationError("E_VISUAL_OBJECT_REFERENCE_INVALID:shot")
            for key in SHOT_SCALAR_REFERENCE_FIELDS:
                value = shot.get(key)
                if isinstance(value, str):
                    values.append(value)
            for key in SHOT_LIST_REFERENCE_FIELDS:
                value = shot.get(key)
                if value is not None:
                    values.extend(_string_list(value, label=f"shot.{key}"))

    config = beat.get("templateConfig")
    if isinstance(config, dict):
        for key in TEMPLATE_CONFIG_SCALAR_REFERENCE_FIELDS:
            value = config.get(key)
            if isinstance(value, str):
                values.append(value)
        for key in TEMPLATE_CONFIG_LIST_REFERENCE_FIELDS:
            value = config.get(key)
            if value is not None:
                values.extend(_string_list(value, label=f"templateConfig.{key}"))
        reaction = config.get("reactionTimeline")
        if reaction is not None:
            if not isinstance(reaction, dict):
                raise ObjectReferenceReconciliationError(
                    "E_VISUAL_OBJECT_REFERENCE_INVALID:templateConfig.reactionTimeline"
                )
            for key in REACTION_TIMELINE_LIST_REFERENCE_FIELDS:
                value = reaction.get(key)
                if value is not None:
                    values.extend(
                        _string_list(value, label=f"templateConfig.reactionTimeline.{key}")
                    )
    return values


def _rebind_beat_references(beat: dict[str, Any], old_id: str, new_id: str) -> None:
    shots = beat.get("shots")
    if shots is not None:
        if not isinstance(shots, list):
            raise ObjectReferenceReconciliationError("E_VISUAL_OBJECT_REFERENCE_INVALID:shots")
        for shot in shots:
            if not isinstance(shot, dict):
                raise ObjectReferenceReconciliationError("E_VISUAL_OBJECT_REFERENCE_INVALID:shot")
            for key in SHOT_SCALAR_REFERENCE_FIELDS:
                _replace_scalar_reference(shot, key, old_id, new_id)
            for key in SHOT_LIST_REFERENCE_FIELDS:
                _replace_list_reference(shot, key, old_id, new_id)

    config = beat.get("templateConfig")
    if isinstance(config, dict):
        for key in TEMPLATE_CONFIG_SCALAR_REFERENCE_FIELDS:
            _replace_scalar_reference(config, key, old_id, new_id)
        for key in TEMPLATE_CONFIG_LIST_REFERENCE_FIELDS:
            _replace_list_reference(config, key, old_id, new_id)
        reaction = config.get("reactionTimeline")
        if reaction is not None:
            if not isinstance(reaction, dict):
                raise ObjectReferenceReconciliationError(
                    "E_VISUAL_OBJECT_REFERENCE_INVALID:templateConfig.reactionTimeline"
                )
            for key in REACTION_TIMELINE_LIST_REFERENCE_FIELDS:
                _replace_list_reference(reaction, key, old_id, new_id)


def _is_approved_complex_rewrite(
    producer_beat: dict[str, Any], projected_beat: dict[str, Any], old_ids: list[str], new_ids: list[str]
) -> bool:
    expected_actual_gap = (
        len(old_ids) == 1
        and len(new_ids) == 3
        and projected_beat.get("visualTemplate") == "expected-actual-gap-flow"
        and projected_beat.get("visualMode") == "expected-actual-gap"
    )
    config = projected_beat.get("templateConfig")
    node_order = config.get("nodeOrder") if isinstance(config, dict) else None
    causal_card_to_graph = (
        len(old_ids) == 1
        and len(new_ids) in {3, 5, 7}
        and projected_beat.get("visualTemplate") in {"causal-lane", "macro-pressure"}
        and projected_beat.get("visualMode") == "causal-diagram"
        and isinstance(node_order, list)
        and all(isinstance(item, str) for item in node_order)
        and 2 <= len(node_order) <= 4
        and len(new_ids) == (2 * len(node_order)) - 1
        and all(item in new_ids for item in node_order)
        and config.get("outcomeNodeId") == node_order[-1]
    )
    return expected_actual_gap or causal_card_to_graph


def _validate_complex_rewrite(
    *,
    producer_scene: dict[str, Any],
    projected_scene: dict[str, Any],
    producer_beat: dict[str, Any],
    projected_beat: dict[str, Any],
    old_ids: list[str],
    new_ids: list[str],
    positions: dict[str, int],
    start: int,
    end: int,
    scene_index: int,
    beat_index: int,
) -> None:
    if not _is_approved_complex_rewrite(producer_beat, projected_beat, old_ids, new_ids):
        raise ObjectReferenceReconciliationError(
            "E_VISUAL_OBJECT_REWRITE_AMBIGUOUS:"
            f"scene={scene_index}:beat={beat_index}:old={len(old_ids)}:new={len(new_ids)}"
        )

    projected_beats = projected_scene.get("visualBeats", [])
    for old_id in old_ids:
        if any(
            isinstance(other, dict)
            and other is not projected_beat
            and old_id in other.get("objectIds", [])
            for other in projected_beats
        ):
            raise ObjectReferenceReconciliationError(
                f"E_VISUAL_OBJECT_REWRITE_SHARED:{old_id}:scene={scene_index}"
            )
        for source_event in producer_scene.get("visualEvents", []):
            if not isinstance(source_event, dict) or source_event.get("targetId") != old_id:
                continue
            if not _event_is_local(source_event, positions=positions, start=start, end=end):
                raise ObjectReferenceReconciliationError(
                    "E_VISUAL_OBJECT_REFERENCE_OUTSIDE_BEAT:"
                    f"{old_id}:scene={scene_index}:beat={beat_index}"
                )

    local_targets: set[str] = set()
    events = projected_scene.get("visualEvents", [])
    if not isinstance(events, list):
        raise ObjectReferenceReconciliationError(
            f"E_VISUAL_OBJECT_REFERENCE_INVALID:scene={scene_index}:visualEvents"
        )
    for event in events:
        if not isinstance(event, dict):
            raise ObjectReferenceReconciliationError(
                f"E_VISUAL_OBJECT_REFERENCE_INVALID:scene={scene_index}:event"
            )
        if _event_is_local(event, positions=positions, start=start, end=end):
            target = event.get("targetId")
            if isinstance(target, str):
                local_targets.add(target)

    missing = [object_id for object_id in new_ids if object_id not in local_targets]
    if missing:
        raise ObjectReferenceReconciliationError(
            "E_VISUAL_OBJECT_REFERENCE_MISSING:"
            f"scene={scene_index}:beat={beat_index}:targets={','.join(missing)}"
        )
    for old_id in old_ids:
        if old_id in local_targets or old_id in _beat_reference_values(projected_beat):
            raise ObjectReferenceReconciliationError(
                f"E_VISUAL_OBJECT_REFERENCE_STALE:{old_id}"
            )


def reconcile_projected_object_references(
    producer: dict[str, Any], projected: dict[str, Any]
) -> dict[str, Any]:
    """Return a reference-consistent projected RenderSpec or fail closed.

    The input dictionaries are never mutated.
    """
    result = copy.deepcopy(projected)
    producer_scenes = producer.get("scenes")
    projected_scenes = result.get("scenes")
    if not isinstance(producer_scenes, list) or not isinstance(projected_scenes, list):
        raise ObjectReferenceReconciliationError("E_VISUAL_OBJECT_REFERENCE_INVALID:scenes")
    if len(producer_scenes) != len(projected_scenes):
        raise ObjectReferenceReconciliationError("E_VISUAL_OBJECT_REFERENCE_SCENE_COUNT_CHANGED")

    for scene_index, (producer_scene, projected_scene) in enumerate(
        zip(producer_scenes, projected_scenes, strict=True), start=1
    ):
        if not isinstance(producer_scene, dict) or not isinstance(projected_scene, dict):
            raise ObjectReferenceReconciliationError(
                f"E_VISUAL_OBJECT_REFERENCE_INVALID:scene={scene_index}"
            )
        producer_beats = producer_scene.get("visualBeats")
        projected_beats = projected_scene.get("visualBeats")
        if not isinstance(producer_beats, list) or not isinstance(projected_beats, list):
            raise ObjectReferenceReconciliationError(
                f"E_VISUAL_OBJECT_REFERENCE_INVALID:scene={scene_index}:visualBeats"
            )
        if len(producer_beats) != len(projected_beats):
            raise ObjectReferenceReconciliationError(
                f"E_VISUAL_OBJECT_REFERENCE_BEAT_COUNT_CHANGED:scene={scene_index}"
            )
        positions = _chunk_positions(producer_scene, scene_index=scene_index)
        producer_events = producer_scene.get("visualEvents", [])
        projected_events = projected_scene.get("visualEvents", [])
        if not isinstance(producer_events, list) or not isinstance(projected_events, list):
            raise ObjectReferenceReconciliationError(
                f"E_VISUAL_OBJECT_REFERENCE_INVALID:scene={scene_index}:visualEvents"
            )
        projected_event_by_id = {
            event.get("eventId"): event
            for event in projected_events
            if isinstance(event, dict) and isinstance(event.get("eventId"), str)
        }

        for beat_index, (producer_beat, projected_beat) in enumerate(
            zip(producer_beats, projected_beats, strict=True), start=1
        ):
            if not isinstance(producer_beat, dict) or not isinstance(projected_beat, dict):
                raise ObjectReferenceReconciliationError(
                    f"E_VISUAL_OBJECT_REFERENCE_INVALID:scene={scene_index}:beat={beat_index}"
                )
            old_ids = _string_list(
                producer_beat.get("objectIds", []),
                label=f"scene={scene_index}:beat={beat_index}:producer.objectIds",
            )
            new_ids = _string_list(
                projected_beat.get("objectIds", []),
                label=f"scene={scene_index}:beat={beat_index}:projected.objectIds",
            )
            if old_ids == new_ids:
                continue

            start, end = _beat_chunk_range(
                producer_beat,
                positions=positions,
                scene_index=scene_index,
                beat_index=beat_index,
            )

            if not (len(old_ids) == 1 and len(new_ids) == 1):
                _validate_complex_rewrite(
                    producer_scene=producer_scene,
                    projected_scene=projected_scene,
                    producer_beat=producer_beat,
                    projected_beat=projected_beat,
                    old_ids=old_ids,
                    new_ids=new_ids,
                    positions=positions,
                    start=start,
                    end=end,
                    scene_index=scene_index,
                    beat_index=beat_index,
                )
                continue

            old_id, new_id = old_ids[0], new_ids[0]
            if old_id == new_id:
                continue

            for other_index, other_beat in enumerate(projected_beats, start=1):
                if other_index == beat_index or not isinstance(other_beat, dict):
                    continue
                other_ids = other_beat.get("objectIds", [])
                if isinstance(other_ids, list) and old_id in other_ids:
                    raise ObjectReferenceReconciliationError(
                        f"E_VISUAL_OBJECT_REWRITE_SHARED:{old_id}:scene={scene_index}"
                    )

            for source_event in producer_events:
                if not isinstance(source_event, dict) or source_event.get("targetId") != old_id:
                    continue
                if not _event_is_local(source_event, positions=positions, start=start, end=end):
                    raise ObjectReferenceReconciliationError(
                        "E_VISUAL_OBJECT_REFERENCE_OUTSIDE_BEAT:"
                        f"{old_id}:scene={scene_index}:beat={beat_index}"
                    )
                event_id = source_event.get("eventId")
                if not isinstance(event_id, str) or event_id not in projected_event_by_id:
                    raise ObjectReferenceReconciliationError(
                        f"E_VISUAL_OBJECT_REFERENCE_EVENT_MISSING:{event_id}"
                    )
                target_event = projected_event_by_id[event_id]
                current_target = target_event.get("targetId")
                if current_target not in (old_id, new_id):
                    raise ObjectReferenceReconciliationError(
                        "E_VISUAL_OBJECT_REFERENCE_EVENT_DRIFT:"
                        f"{event_id}:{current_target}"
                    )
                target_event["targetId"] = new_id

            for event in projected_events:
                if not isinstance(event, dict) or event.get("targetId") != old_id:
                    continue
                if not _event_is_local(event, positions=positions, start=start, end=end):
                    raise ObjectReferenceReconciliationError(
                        "E_VISUAL_OBJECT_REFERENCE_OUTSIDE_BEAT:"
                        f"{old_id}:scene={scene_index}:beat={beat_index}"
                    )
                event["targetId"] = new_id

            _rebind_beat_references(projected_beat, old_id, new_id)

            if any(
                isinstance(event, dict) and event.get("targetId") == old_id
                for event in projected_events
            ) or old_id in _beat_reference_values(projected_beat):
                raise ObjectReferenceReconciliationError(
                    f"E_VISUAL_OBJECT_REFERENCE_STALE:{old_id}"
                )

    return result
