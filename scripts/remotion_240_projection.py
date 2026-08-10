#!/usr/bin/env python3
"""Deterministic projection of approved producer data into Remotion 2.4 objects."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

ALLOWED_EXPECTED_BASIS = {
    "official-consensus",
    "company-prior-guidance",
    "major-reporting",
    "analyst-view",
    "price-inference",
    "unconfirmed",
}
TRANSIENT_SCREEN_STATES = {"EntityFocus", "MainWithEntity", "PictureBook", "News"}
NUMBER_MODES = {"number-comparison", "stock-comparison"}
REACTION_VARIANT_PRECISION = {
    "verified-series": "verified-intraday-series",
    "reported-sequence": "reported-sequence",
    "official-time-plus-close": "official-time-plus-close",
    "close-only": "close-only",
}


class ProjectionError(ValueError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectionError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectionError(f"{label} must be an object")
    return value


def _card_by_id(scene: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["cardId"]: item
        for item in scene.get("cards", [])
        if isinstance(item, dict) and isinstance(item.get("cardId"), str)
    }


def _number_ids(scene: dict[str, Any]) -> set[str]:
    return {
        item["numberId"]
        for item in scene.get("numbers", [])
        if isinstance(item, dict) and isinstance(item.get("numberId"), str)
    }


def _next_event_id(used_event_ids: set[str]) -> str:
    for number in range(1, 1000):
        candidate = f"event-{number:03d}"
        if candidate not in used_event_ids:
            used_event_ids.add(candidate)
            return candidate
    raise ProjectionError("no Visual Event IDs remain")


def _materialize_numbers_from_card_lines(
    scene: dict[str, Any], beat: dict[str, Any]
) -> None:
    existing_numbers = _number_ids(scene)
    if len([item for item in beat.get("objectIds", []) if item in existing_numbers]) >= 2:
        return
    cards = _card_by_id(scene)
    referenced_cards = [cards[item] for item in beat.get("objectIds", []) if item in cards]
    if not referenced_cards:
        raise ProjectionError(
            f"{scene.get('sceneId')}/{beat.get('beatId')}: "
            "number comparison has no approved card data"
        )
    generated: list[str] = []
    numbers = scene.setdefault("numbers", [])
    for card_index, card in enumerate(referenced_cards, start=1):
        for line_index, line in enumerate(card.get("lines", []), start=1):
            if not isinstance(line, dict) or not isinstance(line.get("value"), str):
                continue
            number_id = (
                f"{beat['beatId']}.card-{card_index:02d}.line-{line_index:02d}"
            )
            if number_id not in existing_numbers:
                numbers.append(
                    {
                        "numberId": number_id,
                        "label": str(
                            line.get("label") or card.get("title") or line_index
                        ),
                        "value": line["value"],
                        "unit": "",
                        "comparison": None,
                        "tone": line.get("tone", "neutral"),
                    }
                )
                existing_numbers.add(number_id)
            generated.append(number_id)
    if len(generated) < 2:
        raise ProjectionError(
            f"{scene.get('sceneId')}/{beat.get('beatId')}: "
            "fewer than two approved numeric display lines"
        )
    beat["objectIds"] = generated


def _rewrite_expected_gap_events(
    scene: dict[str, Any],
    *,
    primary_old_card_id: str,
    removed_card_ids: set[str],
    generated_ids: list[str],
    used_event_ids: set[str],
) -> None:
    rewritten: list[dict[str, Any]] = []
    for event in scene.get("visualEvents", []):
        target = event.get("targetId")
        if target == primary_old_card_id:
            for index, target_id in enumerate(generated_ids):
                item = copy.deepcopy(event)
                if index > 0:
                    item["eventId"] = _next_event_id(used_event_ids)
                item["targetId"] = target_id
                rewritten.append(item)
        elif target in removed_card_ids:
            continue
        else:
            rewritten.append(event)
    scene["visualEvents"] = rewritten


def _materialize_expected_actual_gap(
    scene: dict[str, Any], beat: dict[str, Any], used_event_ids: set[str]
) -> None:
    cards = _card_by_id(scene)
    referenced_ids = [item for item in beat.get("objectIds", []) if item in cards]
    referenced = [cards[item] for item in referenced_ids]
    if not referenced or len(referenced[0].get("lines", [])) < 3:
        raise ProjectionError(
            f"{scene.get('sceneId')}/{beat.get('beatId')}: "
            "Expected/Actual/Gap source card is incomplete"
        )
    source_lines = referenced[0]["lines"][:3]
    roles = ("expected", "actual", "gap")
    generated_cards: list[dict[str, Any]] = []
    generated_ids: list[str] = []
    for role, line in zip(roles, source_lines, strict=True):
        card_id = f"{scene['sceneId']}-card-{role}"
        generated_ids.append(card_id)
        generated_cards.append(
            {
                "cardId": card_id,
                "role": role,
                "title": role.capitalize(),
                "lines": [
                    {
                        "label": str(line.get("label") or role),
                        "value": str(line["value"]),
                        "tone": line.get("tone", "neutral"),
                    }
                ],
            }
        )

    # Only the cards explicitly consumed by this Expected/Actual/Gap Beat are
    # projection inputs. Other cards may belong to later Beats in the same Scene and
    # must remain addressable. Replacing the entire Scene card collection caused
    # valid follow-up Beat objectIds and show events to become dangling references.
    removed_card_ids = set(referenced_ids)
    primary_old_card_id = referenced_ids[0]
    projected_cards: list[dict[str, Any]] = []
    inserted = False
    for item in scene.get("cards", []):
        card_id = item.get("cardId") if isinstance(item, dict) else None
        if card_id in removed_card_ids:
            if not inserted:
                projected_cards.extend(generated_cards)
                inserted = True
            continue
        projected_cards.append(item)
    if not inserted:
        projected_cards.extend(generated_cards)
    scene["cards"] = projected_cards
    beat["objectIds"] = generated_ids
    _rewrite_expected_gap_events(
        scene,
        primary_old_card_id=primary_old_card_id,
        removed_card_ids=removed_card_ids,
        generated_ids=generated_ids,
        used_event_ids=used_event_ids,
    )


def _reaction_bindings(path: Path, episode_date: str) -> dict[str, dict[str, Any]]:
    document = load_json(path, "reaction timeline bindings")
    if document.get("contractVersion") != "1.0.0":
        raise ProjectionError("reaction timeline bindings contractVersion must be 1.0.0")
    if document.get("episodeDate") != episode_date:
        raise ProjectionError("reaction timeline bindings episodeDate mismatch")
    rows = document.get("bindings")
    if not isinstance(rows, list):
        raise ProjectionError("reaction timeline bindings.bindings must be an array")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ProjectionError("reaction timeline binding must be an object")
        beat_id = row.get("visualBeatId")
        if not isinstance(beat_id, str) or not beat_id:
            raise ProjectionError("reaction timeline binding visualBeatId is required")
        if beat_id in result:
            raise ProjectionError(f"duplicate reaction timeline binding: {beat_id}")
        variant = row.get("templateVariant")
        precision = row.get("precision")
        if REACTION_VARIANT_PRECISION.get(variant) != precision:
            raise ProjectionError(
                f"{beat_id}: reaction timeline variant/precision mismatch"
            )
        event_order = row.get("eventOrderIds")
        series = row.get("seriesObjectIds")
        if not isinstance(event_order, list) or not event_order:
            raise ProjectionError(f"{beat_id}: eventOrderIds must be non-empty")
        if not isinstance(series, list):
            raise ProjectionError(f"{beat_id}: seriesObjectIds must be an array")
        if precision != "verified-intraday-series" and series:
            raise ProjectionError(
                f"{beat_id}: non-series precision must not declare seriesObjectIds"
            )
        result[beat_id] = row
    return result


def _apply_reaction_binding(
    beat: dict[str, Any], binding: dict[str, Any]
) -> None:
    if beat.get("visualTemplate") != binding.get("visualTemplate"):
        raise ProjectionError(
            f"{beat.get('beatId')}: reaction timeline template mismatch"
        )
    event_order = list(binding["eventOrderIds"])
    if beat.get("objectIds") != event_order:
        raise ProjectionError(
            f"{beat.get('beatId')}: reaction timeline object order differs from approved binding"
        )
    variant = binding["templateVariant"]
    beat["templateVariant"] = variant
    config = beat.get("templateConfig")
    if not isinstance(config, dict):
        raise ProjectionError(f"{beat.get('beatId')}: templateConfig missing")
    config["variant"] = variant
    config["reactionTimeline"] = {
        "precision": binding["precision"],
        "eventOrderIds": event_order,
        "seriesObjectIds": list(binding["seriesObjectIds"]),
    }


def _canonical_visual_data(
    scene: dict[str, Any],
    used_event_ids: set[str],
    reaction_bindings: dict[str, dict[str, Any]],
    used_reaction_bindings: set[str],
) -> None:
    beats = scene.get("visualBeats", [])
    for beat_index, beat in enumerate(beats):
        mode = beat.get("visualMode")
        if mode in NUMBER_MODES:
            _materialize_numbers_from_card_lines(scene, beat)
        elif mode == "expected-actual-gap":
            if beat_index == 0:
                _materialize_expected_actual_gap(scene, beat, used_event_ids)
            else:
                beat["visualMode"] = "text-focus"
                beat["objectIds"] = []
        if beat.get("visualTemplate") == "event-reaction-timeline":
            beat_id = beat.get("beatId")
            binding = reaction_bindings.get(beat_id)
            if binding is None:
                raise ProjectionError(
                    f"{scene.get('sceneId')}/{beat_id}: reaction timeline binding missing"
                )
            _apply_reaction_binding(beat, binding)
            used_reaction_bindings.add(beat_id)
    if beats:
        scene["visualMode"] = beats[0]["visualMode"]


def canonicalize_render_spec(
    render_spec: dict[str, Any],
    *,
    episode_date: str,
    reaction_bindings_path: Path,
) -> None:
    scenes = render_spec.get("scenes", [])
    if not isinstance(scenes, list) or len(scenes) != 9:
        raise ProjectionError("renderer projection requires exactly nine scenes")
    reaction_bindings = _reaction_bindings(reaction_bindings_path, episode_date)
    used_reaction_bindings: set[str] = set()
    used_event_ids = {
        event["eventId"]
        for scene in scenes
        for event in scene.get("visualEvents", [])
        if isinstance(event, dict) and isinstance(event.get("eventId"), str)
    }
    for index, scene in enumerate(scenes):
        expected_role = (
            "opening-hook-market-direction-greeting-conclusion"
            if index == 0
            else "closing-recap-sendoff-goodnight"
            if index == 8
            else "editorial-body"
        )
        scene["sceneRole"] = expected_role
        if scene.get("expectedBasisType") not in ALLOWED_EXPECTED_BASIS:
            scene["expectedBasisType"] = None
        if index == 8:
            scene["transition"] = {"type": "none", "durationMs": 0}
        _canonical_visual_data(
            scene,
            used_event_ids,
            reaction_bindings,
            used_reaction_bindings,
        )
        beats = scene.get("visualBeats", [])
        for beat_index, beat in enumerate(beats):
            next_beat = beats[beat_index + 1] if beat_index + 1 < len(beats) else None
            if next_beat is None:
                beat["returnScreenState"] = None
                continue
            if (
                beat.get("returnScreenState") is not None
                or beat.get("screenState") in TRANSIENT_SCREEN_STATES
            ):
                beat["returnScreenState"] = next_beat.get("screenState")
    if used_reaction_bindings != set(reaction_bindings):
        raise ProjectionError(
            "unused reaction timeline bindings: "
            f"{sorted(set(reaction_bindings) - used_reaction_bindings)}"
        )
