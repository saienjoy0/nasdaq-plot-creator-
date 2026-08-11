#!/usr/bin/env python3
"""Synchronize the 2026-08-10 evidence-first Visual Beat into Story bindings.

Acceptance-only helper. It changes no narration or causal meaning. The purpose is to
make Pre-TTS validation, Story auxiliary bindings, Renderer 2.4 canonicalization, and
the public episode package see the same explicitly authored Scene 8 verified series.

The Story projection intentionally keeps spoken narration and visible caption text as
separate fields. The final package validator requires every visible render string to
remain auditable in the package, so this helper also records the already-derived
caption strings in a machine-only annex. It never rewrites the spoken narration.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

DATE = "2026-08-10"
CAPTION_BEGIN = "<!--BEGIN_DISPLAY_CAPTION_PROJECTION-->"
CAPTION_END = "<!--END_DISPLAY_CAPTION_PROJECTION-->"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def canonical_visual_beat_id(value: str) -> str:
    if re.fullmatch(r"vb-0[1-9]-[0-9]{2}", value):
        return value
    match = re.fullmatch(r"scene-(0[1-9])-beat-([0-9]{3})", value)
    if match:
        return f"vb-{match.group(1)}-{int(match.group(2)):02d}"
    raise SystemExit(f"unsupported Scene 8 Visual Beat ID alias: {value}")


def sync_caption_projection(render: dict[str, Any], package_path: Path) -> int:
    captions: dict[str, str] = {}
    for scene in render.get("scenes", []):
        if not isinstance(scene, dict):
            continue
        scene_id = scene.get("sceneId")
        for chunk in scene.get("narrationChunks", []):
            if not isinstance(chunk, dict):
                continue
            chunk_id = chunk.get("chunkId")
            caption = chunk.get("captionText")
            if (
                isinstance(scene_id, str)
                and isinstance(chunk_id, str)
                and isinstance(caption, str)
                and caption.strip()
            ):
                captions[f"{scene_id}/{chunk_id}"] = caption
    if not captions:
        raise SystemExit("display caption projection is empty")

    text = package_path.read_text(encoding="utf-8")
    if CAPTION_BEGIN in text or CAPTION_END in text:
        if text.count(CAPTION_BEGIN) != 1 or text.count(CAPTION_END) != 1:
            raise SystemExit("display caption projection markers are malformed")
        start = text.index(CAPTION_BEGIN)
        end = text.index(CAPTION_END, start) + len(CAPTION_END)
        text = (text[:start] + text[end:]).rstrip()
    annex = (
        CAPTION_BEGIN
        + "\n```json\n"
        + json.dumps(
            {
                "contractVersion": "1.0.0",
                "episodeDate": DATE,
                "derivation": "captionText is the deterministic display projection of approved speechText; spoken narration is unchanged",
                "captions": captions,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n```\n"
        + CAPTION_END
    )
    package_path.write_text(text + "\n\n" + annex + "\n", encoding="utf-8")
    return len(captions)


def apply(root: Path) -> dict[str, Any]:
    render_path = root / f"render-specs/{DATE}/render_spec.json"
    bindings_path = root / f"working/{DATE}/story-engine/story_production_bindings.json"
    package_path = root / f"episodes/{DATE}/episode_package_public_{DATE}.md"
    render = load(render_path)
    bindings = load(bindings_path)
    scene8 = next(
        scene for scene in render.get("scenes", []) if scene.get("sceneNumber") == 8
    )
    beat = scene8["visualBeats"][0]
    beat_id = beat.get("beatId")
    if not isinstance(beat_id, str) or not beat_id:
        raise SystemExit("Scene 8 beatId missing")
    visual_beat_id = canonical_visual_beat_id(
        str(beat.get("visualBeatId") or beat_id)
    )
    config = beat.get("templateConfig")
    if not isinstance(config, dict):
        raise SystemExit("Scene 8 templateConfig missing")
    reaction = config.get("reactionTimeline")
    if not isinstance(reaction, dict):
        raise SystemExit("Scene 8 reactionTimeline config missing")
    object_ids = beat.get("objectIds")
    if not isinstance(object_ids, list) or len(object_ids) < 3:
        raise SystemExit("Scene 8 verified series objectIds missing")
    event_order = reaction.get("eventOrderIds")
    series_ids = reaction.get("seriesObjectIds")
    if event_order != object_ids or series_ids != object_ids:
        raise SystemExit("Scene 8 reaction order must match authored objectIds")
    if reaction.get("precision") != "verified-intraday-series":
        raise SystemExit("Scene 8 reaction precision is not verified-intraday-series")

    overrides = bindings.setdefault("beat_overrides", {})
    override = overrides.setdefault(beat_id, {})
    override.update(
        {
            "screenQuestion": beat["screenQuestion"],
            "primaryElement": beat["primaryElement"],
            "viewerTexts": beat["viewerTexts"],
            "changeCue": beat["changeCue"],
            "contentType": "event-reaction-timeline",
            "visualTemplate": "event-reaction-timeline",
            "visualMode": "timeline",
            "screenState": "Chart",
            "templateVariant": "verified-series",
            "visualGrammarId": "reaction",
            "transitionRole": "major-shift",
            "reactionTimelineBinding": {
                "visualBeatId": visual_beat_id,
                "visualTemplate": "event-reaction-timeline",
                "templateVariant": "verified-series",
                "precision": "verified-intraday-series",
                "eventOrderIds": list(object_ids),
                "seriesObjectIds": list(object_ids),
                "evidenceBasis": (
                    "Longbridge verified 1-minute Kline minute-close around the "
                    "2026-08-07 08:30 ET BLS release: QQQ 719.16 -> 720.23 -> 720.531. "
                    "Timing alignment evidence only; not causal proof."
                ),
            },
        }
    )
    write(bindings_path, bindings)
    caption_count = sync_caption_projection(render, package_path)
    return {
        "status": "pass",
        "episodeDate": DATE,
        "beatId": beat_id,
        "visualBeatId": visual_beat_id,
        "visualTemplate": "event-reaction-timeline",
        "templateVariant": "verified-series",
        "precision": "verified-intraday-series",
        "seriesObjectIds": list(object_ids),
        "visualGrammarId": "reaction",
        "captionProjectionCount": caption_count,
        "narrationChanged": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = apply(args.repo_root.resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
