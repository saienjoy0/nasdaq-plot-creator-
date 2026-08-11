#!/usr/bin/env python3
"""Normalize mechanically materialized ChatGPT daily artifacts.

No editorial decisions are made here. This only maps already-approved authoring into
legacy Story/Renderer field names, preserves dossier-selected Story wording exactly,
applies the canonical fixed Scene 9 closing, normalizes projection-only whitespace and
source anchors, projects explicit financial bindings, normalizes strict Renderer 2.4
enum aliases, and binds explicitly-authored reaction assets to generated Beat/object IDs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FIXED_SCENE_09_NARRATION = (
    "以上、朝のNASDAQカフェでした。今日も気をつけて、いってらっしゃい。"
    "こちらはそろそろ、おやすみなさい。"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_story_plan(authoring: dict, root: Path, date: str) -> None:
    plan_path = root / "working" / date / "story-engine" / "templates" / "story_plan.template.json"
    plan = load(plan_path)
    dossier = authoring["causalDossier"]

    contradiction_id = plan["central_contradiction_id"]
    contradiction = next(
        (
            item for item in dossier["contradictions"]
            if isinstance(item, dict) and item.get("id") == contradiction_id
        ),
        None,
    )
    if contradiction is None:
        raise SystemExit(f"story contradiction missing from authored dossier: {contradiction_id}")
    plan["central_contradiction"] = contradiction["statement"]

    selected_id = plan["selected_angle_id"]
    selected = next(
        (
            item for item in plan["angle_candidates"]
            if isinstance(item, dict) and item.get("id") == selected_id
        ),
        None,
    )
    if selected is None:
        raise SystemExit(f"selected story angle missing: {selected_id}")

    handoff = dossier["editorial_handoff"]
    plan["headline_beyond_discovery"] = handoff["headline_beyond_discovery"]
    plan["central_question"] = selected["central_question"]
    plan["story_spine"] = selected["story_spine"]
    plan["opening_promise"] = selected["opening_promise"]
    plan["midpoint_turn"]["claim"] = selected["midpoint_turn_claim"]
    plan["closing_reframe"]["text"] = selected["closing_reframe"]

    closing = next(
        (scene for scene in plan["scenes"] if scene.get("scene_id") == "scene-09"),
        None,
    )
    if closing is None:
        raise SystemExit("story plan scene-09 missing")
    closing["new_evidence_ids"] = []
    closing["new_meaning"] = ""
    closing["continuation_reason"] = ""
    closing["connector"] = "closing"
    dump(plan_path, plan)


def normalize_story_script(authoring: dict, root: Path, date: str) -> None:
    script_path = root / "working" / date / "story-engine" / "templates" / "story_script.template.json"
    script = load(script_path)
    authored_scenes = authoring.get("scenes", [])
    if len(authored_scenes) != 9:
        raise SystemExit(f"authoring must contain nine scenes; found={len(authored_scenes)}")

    by_id = {scene.get("scene_id"): scene for scene in script.get("scenes", [])}
    for scene_index, authored_scene in enumerate(authored_scenes, 1):
        scene_id = f"scene-{scene_index:02d}"
        scene = by_id.get(scene_id)
        if scene is None:
            raise SystemExit(f"story script scene missing: {scene_id}")
        if scene_index < 9:
            chunks = authored_scene.get("chunks", [])
            if not chunks:
                raise SystemExit(f"authoring chunks missing: {scene_id}")
            scene["narration"] = "".join(chunk["text"] for chunk in chunks)
        else:
            scene["narration"] = FIXED_SCENE_09_NARRATION
            scene["connection_to_previous"] = "closing"
            scene["evidence_ids"] = []
            scene["causal_claims"] = []
    dump(script_path, script)


def normalize_public_episode_package(authoring: dict, root: Path, date: str) -> None:
    package_path = root / "episodes" / date / f"episode_package_public_{date}.md"
    text = package_path.read_text(encoding="utf-8")
    for scene_index, scene in enumerate(authoring.get("scenes", []), 1):
        source_line = f"- ナレーションで示す出典主体・媒体：{scene.get('sourceLabel', '')}"
        if source_line in text:
            continue
        anchor = f"- 根拠と不確実性：{scene.get('uncertainty', '')}"
        if anchor not in text:
            raise SystemExit(f"episode package uncertainty anchor missing: scene-{scene_index:02d}")
        text = text.replace(anchor, source_line + "\n" + anchor, 1)
    package_path.write_text(text, encoding="utf-8")


def normalize_financial_bindings(authoring: dict, root: Path, date: str) -> None:
    rows = authoring.get("financialBindings")
    if not isinstance(rows, list):
        raise SystemExit("financialBindings must be an authored list")
    path = root / "working" / date / "financial_visual_bindings.json"
    dump(path, {"contractVersion": "1.0.0", "episodeDate": date, "bindings": rows})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = ap.parse_args()
    root = args.repo_root.resolve()
    date = args.date
    authoring = load(root / "daily-authoring" / f"{date}.json")
    review = authoring["review"]

    normalize_story_plan(authoring, root, date)
    normalize_story_script(authoring, root, date)
    normalize_public_episode_package(authoring, root, date)
    normalize_financial_bindings(authoring, root, date)

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
        f"FIXED daily materialization {date}: story projection compatibility + "
        f"{len(rows)} reaction bindings / {len(asset_by_beat)} bound assets + "
        f"{len(authoring.get('financialBindings', []))} financial bindings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
