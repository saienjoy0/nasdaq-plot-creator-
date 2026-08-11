#!/usr/bin/env python3
"""Complete deterministic `show` sequences for every multi-object Visual Beat.

This is a renderer-compatibility repair only. It never changes object content, order,
visual template, narration, or editorial meaning. The ChatGPT authoring materializer
already emits one `show` event for each Beat; this script adds only the missing objects
in authored object order so `sequencePolicy=explicit` is complete rather than partial.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EVENT_RE = re.compile(r"^event-(\d{3})$")


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return value


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = ap.parse_args()
    root = args.repo_root.resolve()
    path = root / "render-specs" / args.date / "render_spec.json"
    render = load(path)

    serial = 0
    for scene in render.get("scenes", []):
        for event in scene.get("visualEvents", []):
            match = EVENT_RE.fullmatch(str(event.get("eventId", "")))
            if match:
                serial = max(serial, int(match.group(1)))

    added = 0
    for scene in render.get("scenes", []):
        events = scene.setdefault("visualEvents", [])
        chunks = scene.get("narrationChunks", [])
        chunk_order = {
            chunk.get("chunkId"): index
            for index, chunk in enumerate(chunks)
            if isinstance(chunk, dict)
        }
        for beat in scene.get("visualBeats", []):
            object_ids = list(beat.get("objectIds", []))
            if len(object_ids) <= 1:
                continue
            start_id = beat.get("startChunkId")
            end_id = beat.get("endChunkId")
            start_index = chunk_order.get(start_id)
            end_index = chunk_order.get(end_id)
            if start_index is None or end_index is None:
                raise SystemExit(f"invalid Beat chunk range: {scene.get('sceneId')}/{beat.get('beatId')}")
            selected = set(object_ids)
            shown: set[str] = set()
            for event in events:
                if event.get("action") != "show" or event.get("targetId") not in selected:
                    continue
                event_index = chunk_order.get(event.get("atChunkId"))
                if event_index is not None and start_index <= event_index <= end_index:
                    shown.add(event["targetId"])
            missing = [object_id for object_id in object_ids if object_id not in shown]
            for ordinal, object_id in enumerate(missing, start=1):
                serial += 1
                if serial > 999:
                    raise SystemExit("visual event serial exceeds renderer contract")
                events.append({
                    "eventId": f"event-{serial:03d}",
                    "atChunkId": start_id,
                    "timing": "chunk-start",
                    "action": "show",
                    "targetId": object_id,
                    "offsetMs": min(9000, ordinal * 180),
                    "expression": None,
                    "motionPreset": "rise-soft",
                    "durationMs": 420,
                    "easingPreset": "smooth-out",
                })
                added += 1

    path.write_text(json.dumps(render, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"COMPLETED visual show sequences {args.date}: added={added}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
