#!/usr/bin/env python3
"""Resolve Remotion sequencePolicy from transformed objects and approved events."""

from __future__ import annotations

from typing import Any


class SequencePolicyError(ValueError):
    pass


def resolve_sequence_policies(render_spec: dict[str, Any]) -> None:
    scenes = render_spec.get("scenes")
    if not isinstance(scenes, list):
        raise SequencePolicyError("render spec scenes must be an array")
    for scene in scenes:
        chunks = scene.get("narrationChunks", [])
        chunk_order = {
            chunk.get("chunkId"): index
            for index, chunk in enumerate(chunks)
            if isinstance(chunk, dict)
        }
        events = scene.get("visualEvents", [])
        for beat in scene.get("visualBeats", []):
            object_ids = list(beat.get("objectIds", []))
            if not object_ids:
                beat["sequencePolicy"] = "static"
                continue
            start_index = chunk_order.get(beat.get("startChunkId"))
            end_index = chunk_order.get(beat.get("endChunkId"))
            if start_index is None or end_index is None:
                raise SequencePolicyError(
                    f"{scene.get('sceneId')}/{beat.get('beatId')}: chunk range invalid"
                )
            selected = set(object_ids)
            show_targets: set[str] = set()
            for event in events:
                if not isinstance(event, dict) or event.get("action") != "show":
                    continue
                target = event.get("targetId")
                if target not in selected:
                    continue
                event_index = chunk_order.get(event.get("atChunkId"))
                if event_index is None:
                    continue
                if start_index <= event_index <= end_index:
                    show_targets.add(target)
            if show_targets == selected:
                beat["sequencePolicy"] = "explicit"
            elif not show_targets:
                beat["sequencePolicy"] = "object-order-fallback"
            else:
                raise SequencePolicyError(
                    f"{scene.get('sceneId')}/{beat.get('beatId')}: "
                    f"partial show sequence targets={sorted(show_targets)} "
                    f"objects={object_ids}"
                )
