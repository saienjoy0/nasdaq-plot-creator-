#!/usr/bin/env python3
"""Deterministically project authored causal cards into Renderer graph objects."""
from __future__ import annotations

import copy
from typing import Any

import remotion_240_projection
import remotion_template_data


class VisualIntelligenceCausalInventoryError(ValueError):
    pass


def _used_event_ids(render: dict[str, Any]) -> set[str]:
    seen: set[str] = set()
    for scene_index, scene in enumerate(render.get("scenes", []), start=1):
        if not isinstance(scene, dict):
            continue
        for event_index, event in enumerate(scene.get("visualEvents", []), start=1):
            if not isinstance(event, dict):
                raise VisualIntelligenceCausalInventoryError(
                    f"E_VISUAL_CAUSAL_INVENTORY_INVALID:scene={scene_index}:event={event_index}"
                )
            event_id = event.get("eventId")
            if not isinstance(event_id, str) or not event_id:
                raise VisualIntelligenceCausalInventoryError(
                    f"E_VISUAL_CAUSAL_INVENTORY_INVALID:scene={scene_index}:eventId"
                )
            if event_id in seen:
                raise VisualIntelligenceCausalInventoryError(
                    f"E_VISUAL_CAUSAL_INVENTORY_DUPLICATE_EVENT:{event_id}"
                )
            seen.add(event_id)
    return seen


def materialize_causal_inventory(render: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(render)
    used_event_ids = _used_event_ids(result)

    for scene_index, scene in enumerate(result.get("scenes", []), start=1):
        if not isinstance(scene, dict):
            raise VisualIntelligenceCausalInventoryError(
                f"E_VISUAL_CAUSAL_INVENTORY_INVALID:scene={scene_index}"
            )
        node_ids = {
            item.get("nodeId")
            for item in scene.get("nodes", [])
            if isinstance(item, dict) and isinstance(item.get("nodeId"), str)
        }
        card_ids = {
            item.get("cardId")
            for item in scene.get("cards", [])
            if isinstance(item, dict) and isinstance(item.get("cardId"), str)
        }
        beats = scene.get("visualBeats", [])
        if not isinstance(beats, list):
            raise VisualIntelligenceCausalInventoryError(
                f"E_VISUAL_CAUSAL_INVENTORY_INVALID:scene={scene_index}:visualBeats"
            )

        for beat_index, beat in enumerate(beats, start=1):
            if not isinstance(beat, dict):
                raise VisualIntelligenceCausalInventoryError(
                    f"E_VISUAL_CAUSAL_INVENTORY_INVALID:scene={scene_index}:beat={beat_index}"
                )
            if beat.get("visualTemplate") not in remotion_template_data.CAUSAL_TEMPLATE_IDS:
                continue

            old_ids = beat.get("objectIds", [])
            if not isinstance(old_ids, list) or not all(isinstance(item, str) for item in old_ids):
                raise VisualIntelligenceCausalInventoryError(
                    f"E_VISUAL_CAUSAL_INVENTORY_INVALID:scene={scene_index}:beat={beat_index}:objectIds"
                )
            if len([item for item in old_ids if item in node_ids]) >= 2:
                continue

            referenced_cards = [item for item in old_ids if item in card_ids]
            if len(referenced_cards) != 1:
                raise VisualIntelligenceCausalInventoryError(
                    "E_VISUAL_CAUSAL_INVENTORY_SOURCE_CARD:"
                    f"scene={scene_index}:beat={beat_index}:count={len(referenced_cards)}"
                )
            source_card_id = referenced_cards[0]
            other_owners = [
                other.get("beatId", f"beat-{other_index}")
                for other_index, other in enumerate(beats, start=1)
                if other is not beat
                and isinstance(other, dict)
                and source_card_id in other.get("objectIds", [])
            ]
            if other_owners:
                raise VisualIntelligenceCausalInventoryError(
                    "E_VISUAL_CAUSAL_INVENTORY_SHARED_SOURCE:"
                    f"{source_card_id}:{','.join(map(str, other_owners))}"
                )

            try:
                remotion_template_data._materialize_causal_template(scene, beat)
            except remotion_template_data.TemplateDataError as exc:
                raise VisualIntelligenceCausalInventoryError(
                    f"E_VISUAL_CAUSAL_INVENTORY_INVALID:{exc}"
                ) from exc

            generated_ids = beat.get("objectIds", [])
            if not isinstance(generated_ids, list) or len(generated_ids) not in {3, 5, 7}:
                raise VisualIntelligenceCausalInventoryError(
                    "E_VISUAL_CAUSAL_INVENTORY_GENERATED_SHAPE:"
                    f"scene={scene_index}:beat={beat_index}"
                )
            remotion_240_projection._rewrite_expected_gap_events(
                scene,
                primary_old_card_id=source_card_id,
                removed_card_ids={source_card_id},
                generated_ids=generated_ids,
                used_event_ids=used_event_ids,
            )

    return result
