#!/usr/bin/env python3
"""Finalize mixed Scene 2/3/7 Renderer authoring for the frozen H4 fixture.

TEST ONLY. Scene 2 Beat 2 compares a payroll revision (people) with NASDAQ return
(percent), so it must stay a card-based evidence boundary rather than a shared-axis
numeric matrix. Scene 3 intentionally uses Expected/Actual/Gap on Beat 1 and a numeric
comparison on Beat 2; once Beat 2 is bound to stable number objects, its legacy source
card must not survive because an expected-actual-gap scene must contain exactly the
three projected role cards. Scene 7 Beat 2 is a one-card synthesis of a broad tailwind
and stock-specific dispersion, so it uses the evidence grammar on a two-lane surface
without inventing numeric matrix inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

DATE = "2026-08-10"
SCENE2_CARD_ID = "scene-02-card-002"
SCENE3_CARD_ID = "scene-03-card-002"
SCENE3_NUMBER_IDS = ["scene-03-number-compare-001", "scene-03-number-compare-002"]
SCENE7_CARD_ID = "scene-07-card-002"


class Scene3AuthoringError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Scene3AuthoringError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise Scene3AuthoringError(f"JSON root must be object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temp = path.with_name(f".{path.name}.h4-mixed-renderer.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sync_scene2(render: dict[str, Any], bindings: dict[str, Any]) -> dict[str, Any]:
    scene = render["scenes"][1]
    if scene.get("sceneId") != "scene-02":
        raise Scene3AuthoringError("Scene 2 identity drift")

    beats = scene.get("visualBeats")
    if not isinstance(beats, list):
        raise Scene3AuthoringError("Scene 2 visualBeats missing")
    beat2 = next(
        (
            item
            for item in beats
            if isinstance(item, dict)
            and item.get("beatId") in {"vb-02-02", "scene-02-beat-002"}
        ),
        None,
    )
    if beat2 is None:
        raise Scene3AuthoringError("Scene 2 Beat 2 missing")

    cards = {
        item.get("cardId"): item
        for item in scene.get("cards", [])
        if isinstance(item, dict) and isinstance(item.get("cardId"), str)
    }
    card = cards.get(SCENE2_CARD_ID)
    if not isinstance(card, dict):
        raise Scene3AuthoringError("Scene 2 comparison source card missing")
    values = [
        line.get("value")
        for line in card.get("lines", [])
        if isinstance(line, dict) and isinstance(line.get("value"), str)
    ]
    if len(values) < 2 or not any("万人" in value for value in values) or not any("%" in value for value in values):
        raise Scene3AuthoringError(
            "Scene 2 Beat 2 no longer represents the mixed-unit payroll/NASDAQ comparison"
        )

    beat2["objectIds"] = [SCENE2_CARD_ID]
    for field, value in {
        "contentType": "text-focus",
        "visualMode": "text-focus",
        "visualTemplate": "evidence-boundary",
        "templateVariant": "confirmed-vs-unconfirmed",
    }.items():
        beat2[field] = value
    config = beat2.get("templateConfig")
    if not isinstance(config, dict):
        raise Scene3AuthoringError("Scene 2 Beat 2 templateConfig missing")
    config["variant"] = "confirmed-vs-unconfirmed"
    grammar = beat2.get("visualGrammar")
    if not isinstance(grammar, dict):
        raise Scene3AuthoringError("Scene 2 Beat 2 visualGrammar missing")
    grammar["grammarId"] = "evidence"
    grammar["transitionRole"] = "continuation"

    overrides = bindings.get("beat_overrides")
    if not isinstance(overrides, dict):
        raise Scene3AuthoringError("story production beat_overrides must be an object")
    override = overrides.setdefault("scene-02-beat-002", {})
    override.update(
        {
            "contentType": "text-focus",
            "visualMode": "text-focus",
            "visualTemplate": "evidence-boundary",
            "templateVariant": "confirmed-vs-unconfirmed",
            "visualGrammarId": "evidence",
            "transitionRole": "continuation",
        }
    )

    stale_number_ids = {"scene-02-number-compare-001", "scene-02-number-compare-002"}
    numbers = scene.get("numbers")
    if not isinstance(numbers, list):
        raise Scene3AuthoringError("Scene 2 numbers must be an array")
    numbers[:] = [
        item
        for item in numbers
        if not (isinstance(item, dict) and item.get("numberId") in stale_number_ids)
    ]
    events = scene.get("visualEvents")
    if not isinstance(events, list):
        raise Scene3AuthoringError("Scene 2 visualEvents missing")
    events[:] = [
        event
        for event in events
        if not (
            isinstance(event, dict)
            and event.get("targetId") in stale_number_ids
        )
    ]
    if not any(
        isinstance(event, dict)
        and event.get("action") == "show"
        and event.get("targetId") == SCENE2_CARD_ID
        for event in events
    ):
        events.append(
            {
                "eventId": "event-004",
                "action": "show",
                "atChunkId": beat2["startChunkId"],
                "durationMs": 560,
                "easingPreset": "smooth-out",
                "expression": None,
                "motionPreset": "rise-soft",
                "offsetMs": 0,
                "targetId": SCENE2_CARD_ID,
                "timing": "chunk-start",
            }
        )

    return {
        "beat_2_object_ids": beat2["objectIds"],
        "visual_template": beat2["visualTemplate"],
        "template_variant": beat2["templateVariant"],
        "visible_values": values,
    }


def _sync_scene3(render: dict[str, Any]) -> dict[str, Any]:
    scene = render["scenes"][2]
    if scene.get("sceneId") != "scene-03":
        raise Scene3AuthoringError("Scene 3 identity drift")

    beats = scene.get("visualBeats")
    if not isinstance(beats, list) or len(beats) < 2:
        raise Scene3AuthoringError("Scene 3 Visual Beats missing")
    beat1 = next(
        (item for item in beats if isinstance(item, dict) and item.get("beatId") in {"vb-03-01", "scene-03-beat-001"}),
        None,
    )
    beat2 = next(
        (item for item in beats if isinstance(item, dict) and item.get("beatId") in {"vb-03-02", "scene-03-beat-002"}),
        None,
    )
    if beat1 is None or beat2 is None:
        raise Scene3AuthoringError("Scene 3 Beat identity drift")
    if beat1.get("visualMode") != "expected-actual-gap":
        raise Scene3AuthoringError("Scene 3 Beat 1 must remain expected-actual-gap")
    if beat2.get("visualMode") != "number-comparison" or beat2.get("objectIds") != SCENE3_NUMBER_IDS:
        raise Scene3AuthoringError("Scene 3 Beat 2 stable number binding drift")

    numbers = {
        item.get("numberId")
        for item in scene.get("numbers", [])
        if isinstance(item, dict)
    }
    missing_numbers = [number_id for number_id in SCENE3_NUMBER_IDS if number_id not in numbers]
    if missing_numbers:
        raise Scene3AuthoringError(f"Scene 3 stable numbers missing: {missing_numbers}")

    cards = scene.get("cards")
    if not isinstance(cards, list):
        raise Scene3AuthoringError("Scene 3 cards missing")
    if not any(isinstance(item, dict) and item.get("cardId") == SCENE3_CARD_ID for item in cards):
        raise Scene3AuthoringError(f"Scene 3 legacy comparison card missing: {SCENE3_CARD_ID}")
    scene["cards"] = [
        item
        for item in cards
        if not (isinstance(item, dict) and item.get("cardId") == SCENE3_CARD_ID)
    ]

    events = scene.get("visualEvents")
    if not isinstance(events, list):
        raise Scene3AuthoringError("Scene 3 visualEvents missing")
    source_index = next(
        (
            index
            for index, event in enumerate(events)
            if isinstance(event, dict)
            and event.get("action") == "show"
            and event.get("targetId") == SCENE3_CARD_ID
        ),
        None,
    )
    if source_index is None:
        raise Scene3AuthoringError("Scene 3 legacy comparison show event missing")

    source_event = events[source_index]
    first_event = deepcopy(source_event)
    first_event["targetId"] = SCENE3_NUMBER_IDS[0]
    second_event = deepcopy(source_event)
    second_event["eventId"] = "event-019"
    second_event["targetId"] = SCENE3_NUMBER_IDS[1]
    second_event["offsetMs"] = max(int(source_event.get("offsetMs", 0)), 0) + 120
    events[source_index : source_index + 1] = [first_event, second_event]

    if any(
        isinstance(event, dict) and event.get("targetId") == SCENE3_CARD_ID
        for event in events
    ):
        raise Scene3AuthoringError("Scene 3 legacy card event survived sync")

    return {
        "removed_card_id": SCENE3_CARD_ID,
        "beat_2_number_ids": SCENE3_NUMBER_IDS,
        "show_event_ids": [first_event.get("eventId"), second_event.get("eventId")],
    }


def _sync_scene7(render: dict[str, Any], bindings: dict[str, Any]) -> dict[str, Any]:
    scene = render["scenes"][6]
    if scene.get("sceneId") != "scene-07":
        raise Scene3AuthoringError("Scene 7 identity drift")

    beats = scene.get("visualBeats")
    if not isinstance(beats, list):
        raise Scene3AuthoringError("Scene 7 visualBeats missing")
    beat2 = next(
        (
            item
            for item in beats
            if isinstance(item, dict)
            and item.get("beatId") in {"vb-07-02", "scene-07-beat-002"}
        ),
        None,
    )
    if beat2 is None:
        raise Scene3AuthoringError("Scene 7 Beat 2 missing")
    if beat2.get("objectIds") != [SCENE7_CARD_ID]:
        raise Scene3AuthoringError("Scene 7 Beat 2 card binding drift")

    cards = {
        item.get("cardId"): item
        for item in scene.get("cards", [])
        if isinstance(item, dict) and isinstance(item.get("cardId"), str)
    }
    card = cards.get(SCENE7_CARD_ID)
    if not isinstance(card, dict):
        raise Scene3AuthoringError("Scene 7 synthesis card missing")
    values = [
        line.get("value")
        for line in card.get("lines", [])
        if isinstance(line, dict) and isinstance(line.get("value"), str)
    ]
    expected_values = ["広い金利追い風", "個別材料で差", "Microsoft +0.03%"]
    if values[:3] != expected_values:
        raise Scene3AuthoringError(f"Scene 7 synthesis card text drift: {values[:3]}")

    beat2["contentType"] = "text-focus"
    beat2["visualMode"] = "text-focus"
    beat2["visualTemplate"] = "tailwind-headwind"
    beat2["templateVariant"] = "two-lane"
    config = beat2.get("templateConfig")
    if not isinstance(config, dict):
        raise Scene3AuthoringError("Scene 7 Beat 2 templateConfig missing")
    config["variant"] = "two-lane"
    grammar = beat2.get("visualGrammar")
    if not isinstance(grammar, dict):
        raise Scene3AuthoringError("Scene 7 Beat 2 visualGrammar missing")
    grammar["grammarId"] = "evidence"
    grammar["transitionRole"] = "continuation"

    overrides = bindings.get("beat_overrides")
    if not isinstance(overrides, dict):
        raise Scene3AuthoringError("story production beat_overrides must be an object")
    override = overrides.setdefault("scene-07-beat-002", {})
    override.update(
        {
            "contentType": "text-focus",
            "visualMode": "text-focus",
            "visualTemplate": "tailwind-headwind",
            "templateVariant": "two-lane",
            "visualGrammarId": "evidence",
            "transitionRole": "continuation",
        }
    )

    return {
        "beat_2_object_ids": beat2["objectIds"],
        "visual_template": beat2["visualTemplate"],
        "visual_grammar_id": grammar["grammarId"],
        "visible_values": values[:3],
    }


def sync(*, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    render_path = root / f"render-specs/{DATE}/render_spec.json"
    bindings_path = root / f"working/{DATE}/story-engine/story_production_bindings.json"
    render = load_json(render_path)
    bindings = load_json(bindings_path)
    if render.get("episode", {}).get("targetDate") != DATE:
        raise Scene3AuthoringError("render targetDate drift")
    if bindings.get("episode_date") != DATE:
        raise Scene3AuthoringError("Story production bindings date drift")

    scenes = render.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 9:
        raise Scene3AuthoringError("render must contain exactly nine scenes")

    scene2_result = _sync_scene2(render, bindings)
    scene3_result = _sync_scene3(render)
    scene7_result = _sync_scene7(render, bindings)
    render_digest = write_json(render_path, render)
    bindings_digest = write_json(bindings_path, bindings)
    return {
        "status": "pass",
        "episode_date": DATE,
        "render_authoring_sha256": render_digest,
        "story_production_bindings_sha256": bindings_digest,
        "scene_2": scene2_result,
        "scene_3": scene3_result,
        "scene_7": scene7_result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = sync(repo_root=args.repo_root.resolve())
    except Scene3AuthoringError as exc:
        print(json.dumps({"status": "fail", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2

    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output
        if not output.is_absolute():
            output = args.repo_root.resolve() / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
