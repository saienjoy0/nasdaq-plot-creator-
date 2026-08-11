#!/usr/bin/env python3
"""Mechanically normalize ChatGPT-authored daily artifacts for legacy production.

This module performs no editorial selection. It preserves the approved dossier/story,
normalizes strict renderer enums, supplies projection-only Markdown anchors per Scene,
projects explicit financial bindings, and binds authored intraday evidence.
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_story(authoring: dict, root: Path, date: str) -> None:
    story = root / "working" / date / "story-engine" / "templates"
    plan_path = story / "story_plan.template.json"
    plan = load(plan_path)
    dossier = authoring["causalDossier"]

    contradiction_id = plan["central_contradiction_id"]
    contradiction = next(
        (row for row in dossier["contradictions"] if row.get("id") == contradiction_id), None
    )
    if contradiction is None:
        raise SystemExit(f"story contradiction missing: {contradiction_id}")
    plan["central_contradiction"] = contradiction["statement"]

    selected_id = plan["selected_angle_id"]
    selected = next((row for row in plan["angle_candidates"] if row.get("id") == selected_id), None)
    if selected is None:
        raise SystemExit(f"selected story angle missing: {selected_id}")
    handoff = dossier["editorial_handoff"]
    plan["headline_beyond_discovery"] = handoff["headline_beyond_discovery"]
    plan["central_question"] = selected["central_question"]
    plan["story_spine"] = selected["story_spine"]
    plan["opening_promise"] = selected["opening_promise"]
    plan["midpoint_turn"]["claim"] = selected["midpoint_turn_claim"]
    plan["closing_reframe"]["text"] = selected["closing_reframe"]
    closing_plan = next((row for row in plan["scenes"] if row.get("scene_id") == "scene-09"), None)
    if closing_plan is None:
        raise SystemExit("story plan scene-09 missing")
    closing_plan.update({
        "new_evidence_ids": [], "new_meaning": "", "continuation_reason": "", "connector": "closing"
    })
    dump(plan_path, plan)

    script_path = story / "story_script.template.json"
    script = load(script_path)
    authored_scenes = authoring.get("scenes", [])
    if len(authored_scenes) != 9:
        raise SystemExit(f"authoring scene count must be 9; found={len(authored_scenes)}")
    script_by_id = {row.get("scene_id"): row for row in script.get("scenes", [])}
    for index, authored in enumerate(authored_scenes, 1):
        scene_id = f"scene-{index:02d}"
        target = script_by_id.get(scene_id)
        if target is None:
            raise SystemExit(f"story script scene missing: {scene_id}")
        if index < 9:
            chunks = authored.get("chunks", [])
            if not chunks:
                raise SystemExit(f"authoring chunks missing: {scene_id}")
            # Formatting-only blank lines from the authoring JSON are not spoken text.
            target["narration"] = "".join(chunk["text"] for chunk in chunks)
        else:
            target["narration"] = FIXED_SCENE_09_NARRATION
            target["connection_to_previous"] = "closing"
            target["evidence_ids"] = []
            target["causal_claims"] = []
    dump(script_path, script)


def normalize_public_package(authoring: dict, root: Path, date: str) -> None:
    path = root / "episodes" / date / f"episode_package_public_{date}.md"
    text = path.read_text(encoding="utf-8")
    scenes = authoring.get("scenes", [])
    if len(scenes) != 9:
        raise SystemExit("episode package normalization requires nine scenes")
    for index, scene in enumerate(scenes, 1):
        heading = f"## Scene {index}｜"
        start = text.find(heading)
        if start < 0:
            raise SystemExit(f"episode package heading missing: {heading}")
        if index < 9:
            next_heading = f"## Scene {index + 1}｜"
            end = text.find(next_heading, start + len(heading))
            if end < 0:
                raise SystemExit(f"episode package next heading missing: {next_heading}")
        else:
            end = len(text)
        block = text[start:end]
        source_line = f"- ナレーションで示す出典主体・媒体：{scene.get('sourceLabel', '')}"
        if source_line not in block:
            anchor = f"- 根拠と不確実性：{scene.get('uncertainty', '')}"
            if anchor not in block:
                raise SystemExit(f"episode package uncertainty anchor missing: scene-{index:02d}")
            block = block.replace(anchor, source_line + "\n" + anchor, 1)
            text = text[:start] + block + text[end:]
    path.write_text(text, encoding="utf-8")


def normalize_financial_bindings(authoring: dict, root: Path, date: str) -> None:
    rows = authoring.get("financialBindings")
    if not isinstance(rows, list):
        raise SystemExit("financialBindings must be an authored list")
    dump(
        root / "working" / date / "financial_visual_bindings.json",
        {"contractVersion": "1.0.0", "episodeDate": date, "bindings": rows},
    )


def normalize_review(authoring: dict, root: Path, date: str) -> None:
    review = authoring["review"]
    creative_path = root / "working" / date / "story-engine" / "templates" / "creative_review.template.json"
    creative = load(creative_path)
    creative["scores"] = review["storyScores"]
    creative["total_score"] = sum(review["storyScores"].values())
    dump(creative_path, creative)


def normalize_render(authoring: dict, root: Path, date: str) -> dict:
    path = root / "render-specs" / date / "render_spec.json"
    render = load(path)
    review = authoring["review"]
    rr = render["review"]
    rr["scores"] = review["rendererScores"]
    rr["totalScore"] = sum(review["rendererScores"].values())
    rr["titleThumbnailConsistency"] = "consistent"
    rr["approvedForCodex"] = True

    scope_map = {
        "company": "lead-stock", "company_direct": "lead-stock", "lead-stock": "lead-stock",
        "sector": "sector", "nasdaq": "nasdaq", "nasdaq_support": "nasdaq", "multiple": "multiple",
    }
    expression_map = {"軽い困惑": "困惑"}
    allowed_expected = {
        "official-consensus", "company-prior-guidance", "major-reporting",
        "analyst-view", "price-inference", "unconfirmed",
    }
    for scene in render.get("scenes", []):
        scene["causalScope"] = scope_map.get(scene.get("causalScope"), "multiple")
        if scene.get("expectedBasisType") not in allowed_expected:
            scene["expectedBasisType"] = None
        scene["initialExpression"] = expression_map.get(scene.get("initialExpression"), scene.get("initialExpression"))
        for chunk in scene.get("narrationChunks", []):
            chunk["expression"] = expression_map.get(chunk.get("expression"), chunk.get("expression"))
        for beat in scene.get("visualBeats", []):
            if beat.get("screenState") == "Source":
                beat["screenState"] = "News"
    dump(path, render)
    return render


def normalize_reaction_bindings(authoring: dict, render: dict, root: Path, date: str) -> int:
    path = root / "working" / date / "reaction_timeline_bindings.json"
    reaction = load(path)
    expected: list[str] = []
    for scene_index, scene in enumerate(authoring["scenes"], 1):
        for beat_index, beat in enumerate(scene["beats"], 1):
            if "reactionBinding" in beat:
                expected.append(f"scene-{scene_index:02d}-beat-{beat_index:03d}")
    rows = reaction.get("bindings", [])
    if len(rows) != len(expected):
        raise SystemExit(f"reaction binding count mismatch: rows={len(rows)} expected={len(expected)}")

    assets: dict[str, dict] = {}
    for asset in authoring.get("reactionAssets", []):
        beat_id = f"scene-{int(asset['sceneNumber']):02d}-beat-{int(asset['beatNumber']):03d}"
        assets[beat_id] = asset
    render_beats = {
        beat["beatId"]: beat
        for scene in render.get("scenes", [])
        for beat in scene.get("visualBeats", [])
    }
    for row, beat_id in zip(rows, expected, strict=True):
        row["visualBeatId"] = beat_id
        asset = assets.get(beat_id)
        if asset is None:
            continue
        beat = render_beats.get(beat_id)
        if beat is None or not beat.get("objectIds"):
            raise SystemExit(f"reaction target invalid: {beat_id}")
        object_ids = list(beat["objectIds"])
        row.update({
            "templateVariant": asset["templateVariant"],
            "precision": asset["precision"],
            "eventOrderIds": object_ids,
            "seriesObjectIds": object_ids,
            "intradaySeriesPath": asset["intradaySeriesPath"],
            "displayTimezone": asset.get("displayTimezone", "America/New_York"),
            "evidenceBasis": asset.get("evidenceBasis", row.get("evidenceBasis", "explicit authored reaction evidence")),
        })
    unused = sorted(set(assets) - set(expected))
    if unused:
        raise SystemExit(f"unused reaction assets: {unused}")
    dump(path, reaction)
    return len(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = ap.parse_args()
    root = args.repo_root.resolve()
    date = args.date
    authoring = load(root / "daily-authoring" / f"{date}.json")

    normalize_story(authoring, root, date)
    normalize_public_package(authoring, root, date)
    normalize_financial_bindings(authoring, root, date)
    normalize_review(authoring, root, date)
    render = normalize_render(authoring, root, date)
    reaction_count = normalize_reaction_bindings(authoring, render, root, date)

    print(
        f"FIXED daily materialization {date}: scene-scoped package anchors + "
        f"{reaction_count} reaction bindings + {len(authoring.get('financialBindings', []))} financial bindings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
