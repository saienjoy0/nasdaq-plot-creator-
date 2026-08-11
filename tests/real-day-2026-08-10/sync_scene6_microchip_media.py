#!/usr/bin/env python3
"""Keep Scene 6 Beat 1 aligned with the approved Microchip IR visual.

Acceptance-only. The approved narration for this Beat states Microchip Q1 FY27
results and guidance, so the visual is the actual company IR document rather than the
legacy BLS/rate/close reaction timeline. No narration, facts, or causality are changed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DATE = "2026-08-10"


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


def apply(root: Path) -> dict[str, Any]:
    render_path = root / f"render-specs/{DATE}/render_spec.json"
    bindings_path = root / f"working/{DATE}/story-engine/story_production_bindings.json"
    render = load(render_path)
    bindings = load(bindings_path)

    scene = next(
        item for item in render.get("scenes", []) if item.get("sceneNumber") == 6
    )
    beat = scene["visualBeats"][0]
    beat_id = beat.get("beatId")
    if not isinstance(beat_id, str) or not beat_id:
        raise SystemExit("Scene 6 Beat 1 beatId missing")

    source_ids = [
        item for item in beat.get("evidenceSourceIds", []) if isinstance(item, str)
    ]
    if "source-004" not in source_ids:
        source_ids.append("source-004")
    beat["evidenceSourceIds"] = source_ids
    scene_source_ids = [
        item for item in scene.get("evidenceSourceIds", []) if isinstance(item, str)
    ]
    if "source-004" not in scene_source_ids:
        scene_source_ids.append("source-004")
    scene["evidenceSourceIds"] = scene_source_ids

    beat.update(
        {
            "contentType": "news-media",
            "visualTemplate": "news-media",
            "visualMode": "news-media",
            "screenState": "News",
            "templateVariant": "default",
            "objectIds": [],
            "sequencePolicy": "explicit",
            "screenQuestion": "Microchipは何を発表した？",
            "primaryElement": "Microchip Q1 FY27 公式IR",
            "changeCue": "Microchip Q1 FY27公式IR",
            "viewerTexts": [
                "Microchip Q1 FY27 公式IR",
                "売上 14.85億ドル / 非GAAP EPS 0.76ドル",
                "次四半期売上 15.89億〜16.18億ドル",
            ],
            "templateConfig": {
                "comparisonBasis": None,
                "dataBasis": "Microchip Technology official Q1 FY27 investor-relations release",
                "laneLabels": [],
                "nodeOrder": [],
                "outcomeNodeId": None,
                "variant": "default",
            },
        }
    )
    grammar = beat.get("visualGrammar")
    if not isinstance(grammar, dict):
        raise SystemExit("Scene 6 Beat 1 visualGrammar missing")
    grammar["grammarId"] = "evidence"
    beat["visualGrammarId"] = "evidence"

    scene["visualEvents"] = [
        event
        for event in scene.get("visualEvents", [])
        if not (
            isinstance(event, dict)
            and event.get("targetId") == "scene-06-card-001"
        )
    ]

    override = bindings.setdefault("beat_overrides", {}).setdefault(beat_id, {})
    override.update(
        {
            "screenQuestion": beat["screenQuestion"],
            "primaryElement": beat["primaryElement"],
            "viewerTexts": beat["viewerTexts"],
            "changeCue": beat["changeCue"],
            "contentType": "news-media",
            "visualTemplate": "news-media",
            "visualMode": "news-media",
            "screenState": "News",
            "templateVariant": "default",
            "visualGrammarId": "evidence",
            "transitionRole": grammar["transitionRole"],
        }
    )
    override.pop("reactionTimelineBinding", None)

    write(render_path, render)
    write(bindings_path, bindings)
    return {
        "status": "pass",
        "episodeDate": DATE,
        "beatId": beat_id,
        "visualTemplate": "news-media",
        "visualGrammarId": "evidence",
        "sourceIds": source_ids,
        "objectIds": [],
        "legacyReactionRemoved": True,
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
