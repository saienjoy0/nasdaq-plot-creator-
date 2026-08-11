#!/usr/bin/env python3
"""Normalize mechanically materialized ChatGPT daily artifacts.

No editorial decisions are made here. This only maps the same approved review scores
into the two existing schemas and binds reaction sidecars to the generated Beat IDs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = ap.parse_args()
    root = args.repo_root.resolve()
    date = args.date
    authoring = load(root / "daily-authoring" / f"{date}.json")
    review = authoring["review"]

    creative_path = root / "working" / date / "story-engine" / "templates" / "creative_review.template.json"
    creative = load(creative_path)
    creative["scores"] = review["storyScores"]
    creative["total_score"] = sum(review["storyScores"].values())
    dump(creative_path, creative)

    render_path = root / "render-specs" / date / "render_spec.json"
    render = load(render_path)
    render["review"]["scores"] = review["rendererScores"]
    render["review"]["totalScore"] = sum(review["rendererScores"].values())
    dump(render_path, render)

    reaction_path = root / "working" / date / "reaction_timeline_bindings.json"
    reaction = load(reaction_path)
    expected_ids = []
    for scene_index, scene in enumerate(authoring["scenes"], 1):
        for beat_index, beat in enumerate(scene["beats"], 1):
            if "reactionBinding" in beat:
                expected_ids.append(f"scene-{scene_index:02d}-beat-{beat_index:03d}")
    rows = reaction.get("bindings", [])
    if len(rows) != len(expected_ids):
        raise SystemExit(f"reaction binding count mismatch: rows={len(rows)} expected={len(expected_ids)}")
    for row, beat_id in zip(rows, expected_ids, strict=True):
        row["visualBeatId"] = beat_id
    dump(reaction_path, reaction)

    print(f"FIXED daily materialization {date}: review schemas + {len(rows)} reaction bindings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
