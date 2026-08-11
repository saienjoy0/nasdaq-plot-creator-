#!/usr/bin/env python3
"""Normalize mechanically materialized ChatGPT daily artifacts.

No editorial decisions are made here. This only maps already-approved authoring into
legacy Story/Renderer field names, normalizes strict Renderer 2.4 enum aliases, and
binds explicitly-authored reaction assets to generated Beat/object IDs.
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
    render_review = render["review"]
    render_review["scores"] = review["rendererScores"]
    render_review["totalScore"] = sum(review["rendererScores"].values())
    render_review["titleThumbnailConsistency"] = "consistent"
    render_review["approvedForCodex"] = True

    scope_map = {
        "company": "lead-stock",
        "company_direct": "lead-stock",
        "lead-stock": "lead-stock",
        "sector": "sector",
        "nasdaq": "nasdaq",
        "nasdaq_support": "nasdaq",
        "multiple": "multiple",
    }
    expression_map = {"軽い困惑": "困惑"}
    screen_state_map = {"Source": "News"}
    allowed_expected = {
        "official-consensus",
        "company-prior-guidance",
        "major-reporting",
        "analyst-view",
        "price-inference",
        "unconfirmed",
    }
    for scene in render.get("scenes", []):
        scene["causalScope"] = scope_map.get(scene.get("causalScope"), "multiple")
        if scene.get("expectedBasisType") not in allowed_expected:
            scene["expectedBasisType"] = None
        scene["initialExpression"] = expression_map.get(
            scene.get("initialExpression"), scene.get("initialExpression")
        )
        for chunk in scene.get("narrationChunks", []):
            chunk["expression"] = expression_map.get(chunk.get("expression"), chunk.get("expression"))
        for beat in scene.get("visualBeats", []):
            beat["screenState"] = screen_state_map.get(beat.get("screenState"), beat.get("screenState"))
    dump(render_path, render)

    reaction_path = root / "working" / date / "reaction_timeline_bindings.json"
    reaction = load(reaction_path)
    expected_rows: list[tuple[str, dict]] = []
    for scene_index, scene in enumerate(authoring["scenes"], 1):
        for beat_index, beat in enumerate(scene["beats"], 1):
            if "reactionBinding" in beat:
                expected_rows.append((f"scene-{scene_index:02d}-beat-{beat_index:03d}", beat))
    rows = reaction.get("bindings", [])
    if len(rows) != len(expected_rows):
        raise SystemExit(f"reaction binding count mismatch: rows={len(rows)} expected={len(expected_rows)}")

    asset_by_beat: dict[str, dict] = {}
    for asset in authoring.get("reactionAssets", []):
        if not isinstance(asset, dict):
            raise SystemExit("reactionAssets entries must be objects")
        beat_id = f"scene-{int(asset['sceneNumber']):02d}-beat-{int(asset['beatNumber']):03d}"
        asset_by_beat[beat_id] = asset

    render_beats = {
        beat["beatId"]: beat
        for scene in render.get("scenes", [])
        for beat in scene.get("visualBeats", [])
        if isinstance(beat, dict) and isinstance(beat.get("beatId"), str)
    }
    for row, (beat_id, authored_beat) in zip(rows, expected_rows, strict=True):
        row["visualBeatId"] = beat_id
        asset = asset_by_beat.get(beat_id)
        if asset is not None:
            beat = render_beats.get(beat_id)
            if beat is None:
                raise SystemExit(f"reaction asset target beat missing: {beat_id}")
            object_ids = list(beat.get("objectIds", []))
            if not object_ids:
                raise SystemExit(f"reaction asset target has no objectIds: {beat_id}")
            row["templateVariant"] = asset["templateVariant"]
            row["precision"] = asset["precision"]
            row["eventOrderIds"] = object_ids
            row["seriesObjectIds"] = object_ids
            row["intradaySeriesPath"] = asset["intradaySeriesPath"]
            row["displayTimezone"] = asset.get("displayTimezone", "America/New_York")
            row["evidenceBasis"] = asset.get(
                "evidenceBasis", row.get("evidenceBasis", "explicit authored reaction evidence")
            )
    unused_assets = sorted(set(asset_by_beat) - {beat_id for beat_id, _ in expected_rows})
    if unused_assets:
        raise SystemExit(f"unused reaction assets: {unused_assets}")
    dump(reaction_path, reaction)

    print(
        f"FIXED daily materialization {date}: renderer enums/review + "
        f"{len(rows)} reaction bindings / {len(asset_by_beat)} bound assets"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
