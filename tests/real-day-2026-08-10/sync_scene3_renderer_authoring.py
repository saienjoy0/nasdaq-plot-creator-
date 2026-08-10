#!/usr/bin/env python3
"""Finalize mixed Scene 3 authoring for the frozen H4 fixture.

TEST ONLY. Scene 3 intentionally uses Expected/Actual/Gap on Beat 1 and a numeric
comparison on Beat 2. Once Beat 2 is bound to stable number objects, its legacy source
card must not survive into Renderer 2.4 because a scene whose first Beat is
expected-actual-gap must contain exactly the three projected role cards.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

DATE = "2026-08-10"
CARD_ID = "scene-03-card-002"
NUMBER_IDS = ["scene-03-number-compare-001", "scene-03-number-compare-002"]


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
    temp = path.with_name(f".{path.name}.h4-scene3.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sync(*, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    path = root / f"render-specs/{DATE}/render_spec.json"
    render = load_json(path)
    if render.get("episode", {}).get("targetDate") != DATE:
        raise Scene3AuthoringError("render targetDate drift")

    scenes = render.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 9:
        raise Scene3AuthoringError("render must contain exactly nine scenes")
    scene = scenes[2]
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
    if beat2.get("visualMode") != "number-comparison" or beat2.get("objectIds") != NUMBER_IDS:
        raise Scene3AuthoringError("Scene 3 Beat 2 stable number binding drift")

    numbers = {
        item.get("numberId")
        for item in scene.get("numbers", [])
        if isinstance(item, dict)
    }
    missing_numbers = [number_id for number_id in NUMBER_IDS if number_id not in numbers]
    if missing_numbers:
        raise Scene3AuthoringError(f"Scene 3 stable numbers missing: {missing_numbers}")

    cards = scene.get("cards")
    if not isinstance(cards, list):
        raise Scene3AuthoringError("Scene 3 cards missing")
    if not any(isinstance(item, dict) and item.get("cardId") == CARD_ID for item in cards):
        raise Scene3AuthoringError(f"Scene 3 legacy comparison card missing: {CARD_ID}")
    scene["cards"] = [
        item
        for item in cards
        if not (isinstance(item, dict) and item.get("cardId") == CARD_ID)
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
            and event.get("targetId") == CARD_ID
        ),
        None,
    )
    if source_index is None:
        raise Scene3AuthoringError("Scene 3 legacy comparison show event missing")

    source_event = events[source_index]
    first_event = deepcopy(source_event)
    first_event["targetId"] = NUMBER_IDS[0]
    second_event = deepcopy(source_event)
    second_event["eventId"] = "event-019"
    second_event["targetId"] = NUMBER_IDS[1]
    second_event["offsetMs"] = max(int(source_event.get("offsetMs", 0)), 0) + 120
    events[source_index : source_index + 1] = [first_event, second_event]

    if any(
        isinstance(event, dict) and event.get("targetId") == CARD_ID
        for event in events
    ):
        raise Scene3AuthoringError("Scene 3 legacy card event survived sync")

    digest = write_json(path, render)
    return {
        "status": "pass",
        "episode_date": DATE,
        "render_authoring_sha256": digest,
        "removed_card_id": CARD_ID,
        "beat_2_number_ids": NUMBER_IDS,
        "show_event_ids": [first_event.get("eventId"), second_event.get("eventId")],
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
