#!/usr/bin/env python3
"""Synchronize 2026-08-10 evidence-first visual authoring into Story bindings.

Acceptance-only helper. It changes no narration or causal meaning. It keeps the
approved Story, Pre-TTS validation, Renderer 2.4 finalization, and public package on
the same explicitly authored visual contract.

Four narrow corrections are made:
- Scene 5 Beat 1 is qualitative supporting-factor analysis, so it is authored as
  nonnumeric ``tailwind-headwind / causal`` rather than fake numeric evidence.
- Scene 6 Beat 1 shows the actual Microchip Q1 FY27 IR as ``news-media / evidence``
  while that Beat narrates the company results and guidance.
- Scene 6 Beat 2 keeps the existing SOXX/MCHP/NVIDIA market-pulse comparison and is
  explicitly ``reaction`` grammar, preserving the Scene 6 reaction role.
- Scene 8 carries the verified QQQ minute series with an explicit reaction binding.

The helper also records already-derived display captions in a machine-only annex;
spoken narration is never rewritten.
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
    raise SystemExit(f"unsupported Visual Beat ID alias: {value}")


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


def patch_scene5_support_forces(render: dict[str, Any], overrides: dict[str, Any]) -> str:
    scene5 = next(
        scene for scene in render.get("scenes", []) if scene.get("sceneNumber") == 5
    )
    beat = scene5["visualBeats"][0]
    beat_id = beat.get("beatId")
    if not isinstance(beat_id, str) or not beat_id:
        raise SystemExit("Scene 5 Beat 1 beatId missing")
    object_ids = beat.get("objectIds")
    if not isinstance(object_ids, list) or len(object_ids) != 1:
        raise SystemExit("Scene 5 Beat 1 must keep its single approved support-factor card")
    selected_numbers = {
        item.get("numberId")
        for item in scene5.get("numbers", [])
        if isinstance(item, dict)
    }.intersection(object_ids)
    if selected_numbers:
        raise SystemExit("Scene 5 support-force Beat unexpectedly selects numeric objects")

    beat["visualTemplate"] = "tailwind-headwind"
    beat["templateVariant"] = "two-lane"
    beat["contentType"] = "supporting-forces"
    beat["visualMode"] = "conclusion-card"
    beat["screenState"] = "Data"
    config = beat.get("templateConfig")
    if not isinstance(config, dict):
        raise SystemExit("Scene 5 Beat 1 templateConfig missing")
    config.clear()
    config.update(
        {
            "variant": "two-lane",
            "comparisonBasis": "NASDAQへの主因候補と同日に存在した増幅要因",
            "dataBasis": "Reuters 2026-08-07 market reporting",
            "laneLabels": ["追い風", "留保"],
            "nodeOrder": [],
            "outcomeNodeId": None,
        }
    )
    grammar = beat.get("visualGrammar")
    if not isinstance(grammar, dict):
        raise SystemExit("Scene 5 Beat 1 visualGrammar missing")
    grammar["grammarId"] = "causal"
    beat["visualGrammarId"] = "causal"

    override = overrides.setdefault(beat_id, {})
    override.update(
        {
            "screenQuestion": beat["screenQuestion"],
            "primaryElement": beat["primaryElement"],
            "viewerTexts": beat["viewerTexts"],
            "changeCue": beat["changeCue"],
            "contentType": "supporting-forces",
            "visualTemplate": "tailwind-headwind",
            "visualMode": "conclusion-card",
            "screenState": "Data",
            "templateVariant": "two-lane",
            "visualGrammarId": "causal",
            "transitionRole": grammar["transitionRole"],
        }
    )
    override.pop("reactionTimelineBinding", None)
    return beat_id


def patch_scene6_microchip_media(render: dict[str, Any], overrides: dict[str, Any]) -> str:
    scene6 = next(
        scene for scene in render.get("scenes", []) if scene.get("sceneNumber") == 6
    )
    beat = scene6["visualBeats"][0]
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
        item for item in scene6.get("evidenceSourceIds", []) if isinstance(item, str)
    ]
    if "source-004" not in scene_source_ids:
        scene_source_ids.append("source-004")
    scene6["evidenceSourceIds"] = scene_source_ids

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
                "variant": "default",
                "comparisonBasis": None,
                "dataBasis": "Microchip Technology official Q1 FY27 investor-relations release",
                "laneLabels": [],
                "nodeOrder": [],
                "outcomeNodeId": None,
            },
        }
    )
    grammar = beat.get("visualGrammar")
    if not isinstance(grammar, dict):
        raise SystemExit("Scene 6 Beat 1 visualGrammar missing")
    grammar["grammarId"] = "evidence"
    beat["visualGrammarId"] = "evidence"
    scene6["visualEvents"] = [
        event
        for event in scene6.get("visualEvents", [])
        if not (
            isinstance(event, dict)
            and event.get("targetId") == "scene-06-card-001"
        )
    ]

    override = overrides.setdefault(beat_id, {})
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
    return beat_id


def patch_scene6_market_reaction(render: dict[str, Any], overrides: dict[str, Any]) -> str:
    scene6 = next(
        scene for scene in render.get("scenes", []) if scene.get("sceneNumber") == 6
    )
    if len(scene6.get("visualBeats", [])) < 2:
        raise SystemExit("Scene 6 requires the existing market reaction Beat 2")
    beat = scene6["visualBeats"][1]
    beat_id = beat.get("beatId")
    if not isinstance(beat_id, str) or not beat_id:
        raise SystemExit("Scene 6 Beat 2 beatId missing")
    if beat.get("visualTemplate") != "market-pulse-grid":
        raise SystemExit(
            f"Scene 6 Beat 2 must stay market-pulse-grid, got {beat.get('visualTemplate')!r}"
        )
    object_ids = beat.get("objectIds")
    if not isinstance(object_ids, list) or len(object_ids) < 3:
        raise SystemExit("Scene 6 Beat 2 market reaction objects missing")
    grammar = beat.get("visualGrammar")
    if not isinstance(grammar, dict):
        raise SystemExit("Scene 6 Beat 2 visualGrammar missing")
    grammar["grammarId"] = "reaction"
    beat["visualGrammarId"] = "reaction"

    override = overrides.setdefault(beat_id, {})
    override.update(
        {
            "visualGrammarId": "reaction",
            "transitionRole": grammar["transitionRole"],
        }
    )
    return beat_id


def patch_scene8_verified_series(render: dict[str, Any], overrides: dict[str, Any]) -> tuple[str, str, list[str]]:
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
    if reaction.get("eventOrderIds") != object_ids or reaction.get("seriesObjectIds") != object_ids:
        raise SystemExit("Scene 8 reaction order must match authored objectIds")
    if reaction.get("precision") != "verified-intraday-series":
        raise SystemExit("Scene 8 reaction precision is not verified-intraday-series")

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
    return beat_id, visual_beat_id, list(object_ids)


def apply(root: Path) -> dict[str, Any]:
    render_path = root / f"render-specs/{DATE}/render_spec.json"
    bindings_path = root / f"working/{DATE}/story-engine/story_production_bindings.json"
    package_path = root / f"episodes/{DATE}/episode_package_public_{DATE}.md"
    render = load(render_path)
    bindings = load(bindings_path)
    overrides = bindings.setdefault("beat_overrides", {})

    scene5_beat_id = patch_scene5_support_forces(render, overrides)
    scene6_beat_id = patch_scene6_microchip_media(render, overrides)
    scene6_reaction_beat_id = patch_scene6_market_reaction(render, overrides)
    beat_id, visual_beat_id, object_ids = patch_scene8_verified_series(render, overrides)

    write(render_path, render)
    write(bindings_path, bindings)
    caption_count = sync_caption_projection(render, package_path)
    return {
        "status": "pass",
        "episodeDate": DATE,
        "scene5BeatId": scene5_beat_id,
        "scene5VisualTemplate": "tailwind-headwind",
        "scene5VisualGrammarId": "causal",
        "scene6BeatId": scene6_beat_id,
        "scene6VisualTemplate": "news-media",
        "scene6VisualGrammarId": "evidence",
        "scene6ReactionBeatId": scene6_reaction_beat_id,
        "scene6ReactionVisualTemplate": "market-pulse-grid",
        "scene6ReactionVisualGrammarId": "reaction",
        "beatId": beat_id,
        "visualBeatId": visual_beat_id,
        "visualTemplate": "event-reaction-timeline",
        "templateVariant": "verified-series",
        "precision": "verified-intraday-series",
        "seriesObjectIds": object_ids,
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
