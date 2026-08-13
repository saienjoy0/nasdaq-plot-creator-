#!/usr/bin/env python3
"""Materialize approved card content into Remotion template data objects."""

from __future__ import annotations

import re
from typing import Any

import remotion_240_projection


class TemplateDataError(ValueError):
    pass


NUMERIC_TEMPLATE_IDS = {"diverging-stock-bars", "index-return-bars"}
SHARED_UNIT_TEMPLATE_IDS = {"diverging-stock-bars", "index-return-bars"}
CAUSAL_TEMPLATE_IDS = {"causal-lane", "macro-pressure"}
NUMBER_RE = re.compile(r"[+-]?\d+(?:\.\d+)?")


def _parse_numeric_text(text: str) -> tuple[str, str, float, int, str]:
    matches = list(NUMBER_RE.finditer(text))
    if not matches:
        raise TemplateDataError(f"approved numeric display has no number: {text!r}")
    match = matches[-1]
    token = match.group(0)
    numeric = float(token)
    precision = len(token.split(".", 1)[1]) if "." in token else 0
    if "%" in text[match.end() :]:
        unit = "%"
    elif "億ドル" in text[match.end() :]:
        unit = "億ドル"
    elif "ドル" in text[match.end() :]:
        unit = "ドル"
    else:
        unit = ""
    value = f"{token}{unit}"
    label = (text[: match.start()] + text[match.end() :]).replace(unit, "").strip()
    label = label.rstrip("：:：/／-–— ") or text
    return label, value, numeric, precision, unit


def _normalize_referenced_numbers(
    scene: dict[str, Any], beat: dict[str, Any]
) -> list[dict[str, Any]]:
    number_map = {
        item.get("numberId"): item
        for item in scene.get("numbers", [])
        if isinstance(item, dict)
    }
    referenced = [number_map.get(item) for item in beat.get("objectIds", [])]
    numbers = [item for item in referenced if isinstance(item, dict)]
    if len(numbers) < 2:
        raise TemplateDataError(
            f"{scene.get('sceneId')}/{beat.get('beatId')}: numeric template has fewer than two numbers"
        )
    for number in numbers:
        text = number.get("value")
        if not isinstance(text, str) or not text.strip():
            raise TemplateDataError(
                f"{scene.get('sceneId')}/{beat.get('beatId')}: numeric display text missing"
            )
        label, value, numeric, precision, unit = _parse_numeric_text(text)
        number["label"] = label
        number["value"] = value
        number["numericValue"] = numeric
        number["precision"] = precision
        number["unit"] = unit
    return numbers


def _single_approved_card_id(scene: dict[str, Any], beat: dict[str, Any]) -> str:
    cards = [
        item
        for item in scene.get("cards", [])
        if isinstance(item, dict)
        and isinstance(item.get("cardId"), str)
        and 2 <= len(item.get("lines", [])) <= 6
    ]
    if len(cards) != 1:
        raise TemplateDataError(
            f"{scene.get('sceneId')}/{beat.get('beatId')}: numeric template has no unique approved source card"
        )
    return cards[0]["cardId"]


def _use_mixed_metric_template(
    beat: dict[str, Any], numbers: list[dict[str, Any]]
) -> None:
    if len(numbers) != 2:
        raise TemplateDataError(
            f"{beat.get('beatId')}: mixed metric two-lane template requires exactly two numbers"
        )
    lane_labels = [item.get("label") for item in numbers]
    if not all(isinstance(item, str) and item.strip() for item in lane_labels):
        raise TemplateDataError(
            f"{beat.get('beatId')}: mixed metric two-lane template requires two numeric labels"
        )

    beat["visualTemplate"] = "tailwind-headwind"
    beat["contentType"] = "tailwind-headwind"
    beat["visualGrammarId"] = "evidence"
    beat["templateVariant"] = "two-lane"
    config = beat.get("templateConfig")
    if not isinstance(config, dict):
        raise TemplateDataError(
            f"{beat.get('beatId')}: numeric templateConfig missing"
        )
    config["variant"] = "two-lane"
    config["laneLabels"] = [item.strip() for item in lane_labels]


def _materialize_numeric_template(scene: dict[str, Any], beat: dict[str, Any]) -> None:
    original_template = beat.get("visualTemplate")
    number_ids = {
        item.get("numberId")
        for item in scene.get("numbers", [])
        if isinstance(item, dict)
    }
    referenced_number_count = len(
        [item for item in beat.get("objectIds", []) if item in number_ids]
    )
    if referenced_number_count < 2:
        card_ids = {
            item.get("cardId")
            for item in scene.get("cards", [])
            if isinstance(item, dict)
        }
        referenced_card_count = len(
            [item for item in beat.get("objectIds", []) if item in card_ids]
        )
        if referenced_card_count == 0:
            beat["objectIds"] = [_single_approved_card_id(scene, beat)]
        remotion_240_projection._materialize_numbers_from_card_lines(scene, beat)
    numbers = _normalize_referenced_numbers(scene, beat)
    units = {item.get("unit", "") for item in numbers}
    if original_template in SHARED_UNIT_TEMPLATE_IDS and len(units) != 1:
        _use_mixed_metric_template(beat, numbers)
    beat["visualMode"] = "number-comparison"


def _materialize_causal_template(scene: dict[str, Any], beat: dict[str, Any]) -> None:
    card_map = {
        item.get("cardId"): item
        for item in scene.get("cards", [])
        if isinstance(item, dict)
    }
    referenced = [
        card_map[item]
        for item in beat.get("objectIds", [])
        if item in card_map
    ]
    if len(referenced) != 1:
        raise TemplateDataError(
            f"{scene.get('sceneId')}/{beat.get('beatId')}: causal template requires one approved source card"
        )
    lines = [
        line.get("value")
        for line in referenced[0].get("lines", [])
        if isinstance(line, dict) and isinstance(line.get("value"), str)
    ]
    if not 2 <= len(lines) <= 4:
        raise TemplateDataError(
            f"{scene.get('sceneId')}/{beat.get('beatId')}: causal source must contain 2-4 ordered lines"
        )
    existing_node_ids = {
        item.get("nodeId")
        for item in scene.get("nodes", [])
        if isinstance(item, dict)
    }
    existing_arrow_ids = {
        item.get("arrowId")
        for item in scene.get("arrows", [])
        if isinstance(item, dict)
    }
    node_ids: list[str] = []
    nodes = scene.setdefault("nodes", [])
    arrows = scene.setdefault("arrows", [])
    arrow_ids: list[str] = []
    for index, label in enumerate(lines, start=1):
        node_id = f"{beat['beatId']}.node-{index:02d}"
        node_ids.append(node_id)
        if node_id not in existing_node_ids:
            nodes.append({"nodeId": node_id, "label": label})
            existing_node_ids.add(node_id)
        if index > 1:
            arrow_id = f"{beat['beatId']}.arrow-{index-1:02d}"
            arrow_ids.append(arrow_id)
            if arrow_id not in existing_arrow_ids:
                arrows.append(
                    {
                        "arrowId": arrow_id,
                        "fromNodeId": node_ids[index - 2],
                        "toNodeId": node_id,
                        "label": "",
                    }
                )
                existing_arrow_ids.add(arrow_id)
    ordered_objects: list[str] = [node_ids[0]]
    for index in range(1, len(node_ids)):
        ordered_objects.append(node_ids[index])
        ordered_objects.append(arrow_ids[index - 1])
    beat["objectIds"] = ordered_objects
    beat["visualMode"] = "causal-diagram"
    config = beat.get("templateConfig")
    if not isinstance(config, dict):
        raise TemplateDataError(
            f"{scene.get('sceneId')}/{beat.get('beatId')}: templateConfig missing"
        )
    config["nodeOrder"] = node_ids
    config["outcomeNodeId"] = node_ids[-1]


def _earlier_display_texts(render_spec: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for scene in render_spec.get("scenes", [])[:8]:
        headline = scene.get("headline")
        if isinstance(headline, str) and headline:
            values.add(headline)
        values.update(
            item for item in scene.get("supportingTexts", [])
            if isinstance(item, str) and item
        )
        for beat in scene.get("visualBeats", []):
            values.update(
                item for item in beat.get("viewerTexts", [])
                if isinstance(item, str) and item
            )
        for card in scene.get("cards", []):
            for line in card.get("lines", []):
                value = line.get("value")
                if isinstance(value, str) and value:
                    values.add(value)
    return values


def _collapse_two_beat_terminal_scene(scene: dict[str, Any]) -> None:
    """Project the authored two-Beat closing into the Renderer's one assembly Beat.

    Daily authoring intentionally keeps two narration/visual Beats per Scene (18 total).
    Renderer 2.4 intentionally accepts one terminal assembly Beat. This projection keeps
    both narration chunks and only collapses their visual shell; it makes no editorial
    choice and introduces no new display text.
    """
    beats = scene.get("visualBeats", [])
    if len(beats) != 2:
        return
    first, last = beats
    cards = [item for item in scene.get("cards", []) if isinstance(item, dict)]
    first_object_ids = set(first.get("objectIds", []))
    first_cards = [
        card for card in cards
        if isinstance(card.get("cardId"), str) and card["cardId"] in first_object_ids
    ]
    if len(first_cards) != 1:
        raise TemplateDataError(
            "Scene 9 two-Beat projection requires one approved card on the first Beat"
        )
    keep_card = first_cards[0]
    keep_card_id = keep_card["cardId"]
    removed_card_ids = {
        card.get("cardId")
        for card in cards
        if isinstance(card.get("cardId"), str) and card.get("cardId") != keep_card_id
    }

    first["endChunkId"] = last.get("endChunkId", first.get("endChunkId"))
    first["narrationEndCue"] = last.get(
        "narrationEndCue", first.get("narrationEndCue")
    )
    first["finalHoldMs"] = last.get("finalHoldMs", first.get("finalHoldMs", 500))
    first["returnScreenState"] = None
    first["objectIds"] = [keep_card_id]
    first["evidenceSourceIds"] = list(
        dict.fromkeys(
            [
                *first.get("evidenceSourceIds", []),
                *last.get("evidenceSourceIds", []),
            ]
        )
    )

    scene["visualBeats"] = [first]
    scene["cards"] = [keep_card]
    scene["visualEvents"] = [
        event
        for event in scene.get("visualEvents", [])
        if not (
            isinstance(event, dict)
            and event.get("targetId") in removed_card_ids
        )
    ]


def _normalize_terminal_scene(
    render_spec: dict[str, Any], terminal_binding: dict[str, Any]
) -> None:
    scenes = render_spec.get("scenes", [])
    if len(scenes) != 9:
        raise TemplateDataError("terminal normalization requires exactly nine scenes")
    if terminal_binding.get("contractVersion") != "1.0.0":
        raise TemplateDataError("terminal assembly binding contractVersion must be 1.0.0")
    scene = scenes[-1]
    if terminal_binding.get("finalSceneId") != scene.get("sceneId"):
        raise TemplateDataError("terminal assembly binding finalSceneId mismatch")
    lines = terminal_binding.get("lines")
    if (
        not isinstance(lines, list)
        or len(lines) != 3
        or not all(isinstance(item, str) and item for item in lines)
    ):
        raise TemplateDataError("terminal assembly binding requires exactly three lines")
    earlier = _earlier_display_texts(render_spec)
    missing = [item for item in lines if item not in earlier]
    if missing:
        raise TemplateDataError(
            f"terminal assembly binding contains text not introduced earlier: {missing}"
        )

    _collapse_two_beat_terminal_scene(scene)
    beats = scene.get("visualBeats", [])
    if len(beats) != 1:
        raise TemplateDataError("Scene 9 requires exactly one final assembly Beat")
    beat = beats[0]
    cards = [item for item in scene.get("cards", []) if isinstance(item, dict)]
    if len(cards) != 1 or cards[0].get("cardId") not in beat.get("objectIds", []):
        raise TemplateDataError("Scene 9 final assembly requires one approved recap card")
    cards[0]["lines"] = [
        {"label": str(index), "tone": "neutral", "value": value}
        for index, value in enumerate(lines, start=1)
    ]
    beat["viewerTexts"] = list(lines)
    beat["changeCue"] = lines[0]
    beat["visualTemplate"] = "final-assembly"
    beat["contentType"] = "final-assembly"
    beat["visualGrammarId"] = "assembly"
    beat["transitionRole"] = "closing"
    beat["templateVariant"] = "default"
    config = beat.get("templateConfig")
    if not isinstance(config, dict):
        raise TemplateDataError("Scene 9 final assembly templateConfig missing")
    config["variant"] = "default"


def _sync_visual_grammar_beat_count(render_spec: dict[str, Any]) -> None:
    """Synchronize the derived Renderer beat count after terminal projection."""
    contract = render_spec.get("visualGrammarContract")
    if not isinstance(contract, dict):
        raise TemplateDataError("visualGrammarContract must be an object")
    contract["beatCount"] = sum(
        len(scene.get("visualBeats", []))
        for scene in render_spec.get("scenes", [])
        if isinstance(scene, dict)
    )


def _normalize_impossible_major_shifts(render_spec: dict[str, Any]) -> None:
    previous: dict[str, Any] | None = None
    for scene in render_spec.get("scenes", []):
        for beat in scene.get("visualBeats", []):
            if (
                previous is not None
                and beat.get("transitionRole") == "major-shift"
                and beat.get("visualTemplate") == previous.get("visualTemplate")
                and beat.get("templateConfig", {}).get("variant")
                == previous.get("templateConfig", {}).get("variant")
            ):
                beat["transitionRole"] = "continuation"
            previous = beat


def materialize_template_data(
    render_spec: dict[str, Any], *, terminal_binding: dict[str, Any]
) -> None:
    scenes = render_spec.get("scenes")
    if not isinstance(scenes, list):
        raise TemplateDataError("render spec scenes must be an array")
    for scene in scenes:
        for beat in scene.get("visualBeats", []):
            template = beat.get("visualTemplate")
            if template in NUMERIC_TEMPLATE_IDS:
                _materialize_numeric_template(scene, beat)
            elif template in CAUSAL_TEMPLATE_IDS:
                _materialize_causal_template(scene, beat)
        beats = scene.get("visualBeats", [])
        if beats:
            scene["visualMode"] = beats[0]["visualMode"]
    _normalize_terminal_scene(render_spec, terminal_binding)
    _sync_visual_grammar_beat_count(render_spec)
    _normalize_impossible_major_shifts(render_spec)
