#!/usr/bin/env python3
"""Finalize mixed Scene 2/3 Renderer authoring for the frozen H4 fixture.

TEST ONLY. Scene 2 uses a matrix comparison on Beat 2, which Renderer 2.4 requires
to bind to 2-6 numeric objects. Scene 3 intentionally uses Expected/Actual/Gap on
Beat 1 and a numeric comparison on Beat 2; once Beat 2 is bound to stable number
objects, its legacy source card must not survive because an expected-actual-gap scene
must contain exactly the three projected role cards.
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
SCENE2_NUMBER_IDS = ["scene-02-number-compare-001", "scene-02-number-compare-002"]
SCENE3_CARD_ID = "scene-03-card-002"
SCENE3_NUMBER_IDS = ["scene-03-number-compare-001", "scene-03-number-compare-002"]


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


def _sync_scene2(render: dict[str, Any]) -> dict[str, Any]:
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
    if beat2 is None or beat2.get("visualTemplate") != "focus-matrix":
        raise Scene3AuthoringError("Scene 2 Beat 2 focus-matrix authoring drift")

    cards = {
        item.get("cardId"): item
        for item in scene.get("cards", [])
        if isinstance(item, dict) and isinstance(item.get("cardId"), str)
    }
    card = cards.get(SCENE2_CARD_ID)
    if not isinstance(card, dict):
        raise Scene3AuthoringError("Scene 2 comparison source card missing")
    lines = card.get("lines")
    if not isinstance(lines, list) or len(lines) < 2:
        raise Scene3AuthoringError("Scene 2 comparison source card requires two lines")

    numbers = scene.setdefault("numbers", [])
    if not isinstance(numbers, list):
        raise Scene3AuthoringError("Scene 2 numbers must be an array")
    id_set = set(SCENE2_NUMBER_IDS)
    numbers[:] = [
        item
        for item in numbers
        if not (isinstance(item, dict) and item.get("numberId") in id_set)
    ]
    numbers.extend(
        [
            {
                "numberId": SCENE2_NUMBER_IDS[0],
                "label": "5月・6月 改定",
                "value": "-10.3",
                "unit": "万人",
                "numericValue": -10.3,
                "comparison": None,
                "tone": "neutral",
            },
            {
                "numberId": SCENE2_NUMBER_IDS[1],
                "label": "NASDAQ",
                "value": "+1.30",
                "unit": "%",
                "numericValue": 1.30,
                "comparison": None,
                "tone": "neutral",
            },
        ]
    )
    beat2["objectIds"] = SCENE2_NUMBER_IDS

    events = scene.get("visualEvents")
    if not isinstance(events, list):
        raise Scene3AuthoringError("Scene 2 visualEvents missing")
    source_index = next(
        (
            index
            for index, event in enumerate(events)
            if isinstance(event, dict)
            and event.get("action") == "show"
            and event.get("targetId") == SCENE2_CARD_ID
        ),
        None,
    )
    if source_index is None:
        raise Scene3AuthoringError("Scene 2 comparison show event missing")
    source_event = events[source_index]
    first_event = deepcopy(source_event)
    first_event["targetId"] = SCENE2_NUMBER_IDS[0]
    second_event = deepcopy(source_event)
    second_event["eventId"] = "event-020"
    second_event["targetId"] = SCENE2_NUMBER_IDS[1]
    second_event["offsetMs"] = max(int(source_event.get("offsetMs", 0)), 0) + 120
    events[source_index : source_index + 1] = [first_event, second_event]

    return {
        "beat_2_number_ids": SCENE2_NUMBER_IDS,
        "show_event_ids": [first_event.get("eventId"), second_event.get("eventId")],
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


def sync(*, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    path = root / f"render-specs/{DATE}/render_spec.json"
    render = load_json(path)
    if render.get("episode", {}).get("targetDate") != DATE:
        raise Scene3AuthoringError("render targetDate drift")

    scenes = render.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 9:
        raise Scene3AuthoringError("render must contain exactly nine scenes")

    scene2_result = _sync_scene2(render)
    scene3_result = _sync_scene3(render)
    digest = write_json(path, render)
    return {
        "status": "pass",
        "episode_date": DATE,
        "render_authoring_sha256": digest,
        "scene_2": scene2_result,
        "scene_3": scene3_result,
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
