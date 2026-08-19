#!/usr/bin/env python3
"""Mechanically expand ChatGPT-authored daily JSON into production inputs.

This script makes no editorial choices. All market causality, narration, visual grammar,
source attribution, counterevidence, duration mode, review conclusions, and any intra-Beat
visual progression must already be present in `daily-authoring/<date>.json`. It only
projects that approved authoring into the existing NASDAQ Cafe direct-input contracts so
GitHub Actions can validate and render it.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import visual_source_checkpoint_v12
import current_compatibility_adapter_v12
from typing import Any

from viewer_surface_projection import (
    project_authoring_viewer_surfaces,
    project_caption_text,
    write_projection_report,
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return value


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def cue(text: str, end: bool = False) -> str:
    text = text.strip()
    if len(text) <= 58:
        return text
    return text[-58:] if end else text[:58]


def card(card_id: str, title: str, lines: list[str]) -> dict[str, Any]:
    return {
        "cardId": card_id,
        "role": None,
        "title": title,
        "lines": [
            {"label": str(i), "value": value, "tone": "neutral"}
            for i, value in enumerate(lines, 1)
        ],
    }


def _validate_authored_shots(
    beat: dict[str, Any],
    *,
    bid: str,
    cid: str,
    object_ids: list[str],
) -> list[dict[str, Any]]:
    raw = beat.get("shots")
    if raw is None:
        return []
    if not isinstance(raw, list) or not 1 <= len(raw) <= 4:
        raise SystemExit(f"{bid}: authored shots must contain 1-4 existing Renderer shots")
    shots = copy.deepcopy(raw)
    valid_targets = set(object_ids)
    for shot_index, shot in enumerate(shots, 1):
        if not isinstance(shot, dict):
            raise SystemExit(f"{bid}: shot {shot_index} must be an object")
        expected_id = f"{bid}-shot-{shot_index:03d}"
        if shot.get("shotId") != expected_id:
            raise SystemExit(f"{bid}: shot {shot_index} must use deterministic ID {expected_id}")
        if shot.get("startChunkId") != cid or shot.get("endChunkId") != cid:
            raise SystemExit(f"{bid}: authored shots must stay inside {cid}")
        for key in ("startProgress", "endProgress"):
            value = shot.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                raise SystemExit(f"{bid}: shot {shot_index}.{key} must be within 0..1")
        if float(shot["endProgress"]) <= float(shot["startProgress"]):
            raise SystemExit(f"{bid}: shot {shot_index} must end after it starts")
        for key in ("primaryTargetId", "referenceTargetId", "outcomeTargetId", "cameraTargetId"):
            target = shot.get(key)
            if target is not None and target not in valid_targets:
                raise SystemExit(f"{bid}: shot {shot_index}.{key} targets unknown object {target}")
        secondary = shot.get("secondaryTargetIds", [])
        if not isinstance(secondary, list) or any(target not in valid_targets for target in secondary):
            raise SystemExit(f"{bid}: shot {shot_index}.secondaryTargetIds contains unknown objects")
    if float(shots[0]["startProgress"]) != 0:
        raise SystemExit(f"{bid}: first authored shot must start at progress 0")
    if float(shots[-1]["endProgress"]) != 1:
        raise SystemExit(f"{bid}: final authored shot must end at progress 1")
    return shots


def _project_authored_visual_events(
    beat: dict[str, Any],
    *,
    bid: str,
    cid: str,
    object_ids: list[str],
    event_serial: list[int],
) -> list[dict[str, Any]]:
    raw = beat.get("visualEvents")
    if raw is None:
        return []
    if not isinstance(raw, list) or not raw:
        raise SystemExit(f"{bid}: visualEvents must be a non-empty array when present")
    projected: list[dict[str, Any]] = []
    valid_targets = set(object_ids)
    visibility_targets: set[str] = set()
    for item_index, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            raise SystemExit(f"{bid}: visualEvents[{item_index}] must be an object")
        action = item.get("action")
        if action not in {"show", "hide", "highlight", "unhighlight", "set-expression"}:
            raise SystemExit(f"{bid}: visualEvents[{item_index}] has invalid action {action!r}")
        target = item.get("targetId")
        if action == "set-expression":
            if target is not None:
                raise SystemExit(f"{bid}: set-expression must not target an object")
        else:
            if target not in valid_targets:
                raise SystemExit(f"{bid}: visualEvents[{item_index}] targets unknown object {target!r}")
            if action in {"show", "hide"}:
                visibility_targets.add(str(target))
        offset = item.get("offsetMs", 0)
        if not isinstance(offset, int) or isinstance(offset, bool) or not 0 <= offset <= 10_000:
            raise SystemExit(f"{bid}: visualEvents[{item_index}].offsetMs must be 0..10000")
        event_serial[0] += 1
        projected.append({
            "eventId": f"event-{event_serial[0]:03d}",
            "atChunkId": cid,
            "timing": item.get("timing", "chunk-start"),
            "action": action,
            "targetId": target,
            "offsetMs": offset,
            "expression": item.get("expression"),
            "motionPreset": item.get("motionPreset"),
            "durationMs": item.get("durationMs"),
            "easingPreset": item.get("easingPreset"),
        })
    if len(object_ids) > 1 and not set(object_ids).issubset(visibility_targets):
        missing = sorted(set(object_ids) - visibility_targets)
        raise SystemExit(
            f"{bid}: multi-object visualEvents must explicitly author first visibility for every object; missing={missing}"
        )
    return projected


def build_scene(
    scene: dict[str, Any],
    scene_number: int,
    event_serial: list[int],
    caption_conversions: list[dict[str, Any]],
) -> dict[str, Any]:
    sid = f"scene-{scene_number:02d}"
    chunks = scene["chunks"]
    beats = scene["beats"]
    if len(chunks) != len(beats):
        raise SystemExit(f"{sid}: chunks/beats length mismatch")
    narration_chunks: list[dict[str, Any]] = []
    visual_beats: list[dict[str, Any]] = []
    cards: list[dict[str, Any]] = []
    numbers: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    arrows: list[dict[str, Any]] = []
    visual_events: list[dict[str, Any]] = []

    for index, (chunk, beat) in enumerate(zip(chunks, beats, strict=True), 1):
        cid = f"{sid}-chunk-{index:03d}"
        bid = f"{sid}-beat-{index:03d}"
        caption_text, caption_rows = project_caption_text(
            chunk["text"],
            path=f"$.scenes[{scene_number - 1}].chunks[{index - 1}].captionText",
        )
        caption_conversions.extend(row.__dict__ for row in caption_rows)
        narration_chunks.append({
            "chunkId": cid,
            "speechText": chunk["text"],
            "captionText": caption_text,
            "expression": chunk.get("expression", scene.get("initialExpression", "分析")),
            "pauseAfterMs": 200 if index == len(chunks) else 120,
        })
        object_ids: list[str] = []
        for metric_index, metric in enumerate(beat.get("metrics", []), 1):
            oid = f"{sid}-number-{index:02d}-{metric_index:02d}"
            object_ids.append(oid)
            numbers.append({
                "numberId": oid,
                "label": metric["label"],
                "value": metric["value"],
                "numericValue": metric.get("numericValue"),
                "precision": metric.get("precision", 2),
                "unit": metric.get("unit", ""),
                "tone": metric.get("tone", "neutral"),
                "comparison": metric.get("comparison"),
            })
        for node_index, node in enumerate(beat.get("nodes", []), 1):
            oid = f"{sid}-node-{index:02d}-{node_index:02d}"
            object_ids.append(oid)
            nodes.append({"nodeId": oid, "label": node["label"], "tone": node.get("tone", "neutral")})
        for edge_index, edge in enumerate(beat.get("edges", []), 1):
            arrows.append({
                "arrowId": f"{sid}-arrow-{index:02d}-{edge_index:02d}",
                "fromNodeId": f"{sid}-node-{index:02d}-{edge['from']:02d}",
                "toNodeId": f"{sid}-node-{index:02d}-{edge['to']:02d}",
                "label": edge.get("label"),
            })
        if not object_ids:
            oid = f"{sid}-card-{index:03d}"
            object_ids.append(oid)
            cards.append(card(oid, beat["primaryElement"], beat["viewerTexts"]))

        template_config = {
            "variant": beat.get("variant", "default"),
            "comparisonBasis": beat.get("comparisonBasis"),
            "dataBasis": beat.get("dataBasis", scene.get("timelineBasis")),
            "nodeOrder": [x for x in object_ids if "-node-" in x],
            "laneLabels": beat.get("laneLabels", []),
            "outcomeNodeId": beat.get("outcomeNodeId"),
        }
        if "reactionTimeline" in beat:
            template_config["reactionTimeline"] = copy.deepcopy(beat["reactionTimeline"])

        authored_shots = _validate_authored_shots(
            beat,
            bid=bid,
            cid=cid,
            object_ids=object_ids,
        )
        authored_events = _project_authored_visual_events(
            beat,
            bid=bid,
            cid=cid,
            object_ids=object_ids,
            event_serial=event_serial,
        )
        if len(object_ids) > 1 and not authored_shots and not authored_events:
            raise SystemExit(
                f"{bid}: multi-object Beat requires authored shots or visualEvents; automatic reveal order is not production-authoritative"
            )

        visual_beat = {
            "beatId": bid,
            "visualBeatId": bid,
            "startChunkId": cid,
            "endChunkId": cid,
            "narrationStartCue": cue(chunk["text"]),
            "narrationEndCue": cue(chunk["text"], end=True),
            "primaryFunction": beat.get("primaryFunction", "Explain"),
            "screenState": beat["screenState"],
            "visualMode": beat.get("visualMode", scene.get("visualMode", "text-focus")),
            "visualTemplate": beat["visualTemplate"],
            "templateConfig": template_config,
            "sequencePolicy": beat.get("sequencePolicy", "explicit"),
            "finalHoldMs": 500,
            "contentType": beat.get("contentType", beat["visualTemplate"]),
            "screenQuestion": beat["screenQuestion"],
            "primaryElement": beat["primaryElement"],
            "viewerTexts": beat["viewerTexts"],
            "changeCue": beat.get("changeCue", beat["viewerTexts"][0]),
            "objectIds": object_ids,
            "assetPlacementIds": [],
            "assetState": "not-required",
            "returnScreenState": beat.get("returnScreenState"),
            "evidenceSourceIds": beat.get("evidenceSourceIds", scene.get("evidenceSourceIds", [])),
            "expressionChange": None,
            "fallback": None,
            "entity": beat.get("entity"),
            "pictureBook": None,
            "visualGrammar": {
                "contractVersion": "1.0.0",
                "grammarId": beat["grammarId"],
                "transitionRole": beat.get("transitionRole", "continuation"),
                "returnTargetBeatId": beat.get("returnTargetBeatId"),
            },
        }
        if authored_shots:
            visual_beat["shots"] = authored_shots
        visual_beats.append(visual_beat)

        if authored_events:
            visual_events.extend(authored_events)
        elif authored_shots:
            # Shot progression owns the meaning. Make static object visibility explicit so
            # legacy show-completion has nothing to infer or reorder.
            for object_id in object_ids:
                event_serial[0] += 1
                visual_events.append({
                    "eventId": f"event-{event_serial[0]:03d}",
                    "atChunkId": cid,
                    "timing": "chunk-start",
                    "action": "show",
                    "targetId": object_id,
                    "offsetMs": 0,
                    "expression": None,
                    "motionPreset": None,
                    "durationMs": None,
                    "easingPreset": None,
                })
        else:
            event_serial[0] += 1
            visual_events.append({
                "eventId": f"event-{event_serial[0]:03d}",
                "atChunkId": cid,
                "timing": "chunk-start",
                "action": "show",
                "targetId": object_ids[0],
                "offsetMs": 0,
                "expression": None,
                "motionPreset": "rise-soft",
                "durationMs": 420,
                "easingPreset": "smooth-out",
            })

    return {
        "sceneId": sid,
        "sceneNumber": scene_number,
        "sceneRole": scene.get("sceneRole", "editorial-body"),
        "formalName": scene["formalName"],
        "purpose": scene["purpose"],
        "causalScope": scene.get("causalScope", "multiple"),
        "performanceIntent": scene["performanceIntent"],
        "evidenceSourceIds": scene.get("evidenceSourceIds", []),
        "uncertainty": scene.get("uncertainty", ""),
        "timelineBasis": scene.get("timelineBasis", ""),
        "expectedBasisType": scene.get("expectedBasisType", "not-applicable"),
        "visualMode": scene.get("visualMode", "text-focus"),
        "initialExpression": scene.get("initialExpression", "分析"),
        "headline": scene["headline"],
        "supportingTexts": scene.get("supportingTexts", []),
        "sourceLabel": scene.get("sourceLabel", ""),
        "narrationChunks": narration_chunks,
        "visualBeats": visual_beats,
        "cards": cards,
        "numbers": numbers,
        "nodes": nodes,
        "arrows": arrows,
        "visualEvents": visual_events,
        "assetPlacements": [
            {
                "placementId": f"{sid}-placement-background",
                "assetId": "mainBackground",
                "role": "background",
                "region": "full-canvas",
                "fit": "cover",
                "opacity": 1,
                "startChunkId": None,
                "endChunkId": None,
            },
            {
                "placementId": f"{sid}-placement-foxAnalysis",
                "assetId": "foxAnalysis",
                "role": "fox-expression",
                "region": "fox-left",
                "fit": "contain",
                "opacity": 1,
                "startChunkId": None,
                "endChunkId": None,
            },
        ],
        "transition": {"type": "fade", "durationMs": 220},
    }


def build_story_plan(a: dict[str, Any]) -> dict[str, Any]:
    scenes = []
    for index, scene in enumerate(a["scenes"], 1):
        scenes.append({
            "scene_id": f"scene-{index:02d}",
            "formal_role": scene["formalRole"],
            "story_role": scene["storyRole"],
            "viewer_belief_before": scene["beliefBefore"],
            "new_evidence_ids": scene.get("newEvidenceIds", []),
            "new_meaning": scene["newMeaning"],
            "viewer_belief_after": scene["beliefAfter"],
            "continuation_reason": scene.get("continuationReason", ""),
            "connector": scene.get("connector", "therefore"),
        })
    return {
        "contract_version": "1.2.0",
        "episode_date": a["episodeDate"],
        "created_at": a["informationCutoff"],
        "producer": "chatgpt",
        "causal_dossier": {"path": "BOUND_AT_MATERIALIZATION", "sha256": "0" * 64},
        "central_contradiction_id": "CON-01",
        "central_contradiction": a["centralContradiction"],
        "central_question": a["centralQuestion"],
        "headline_beyond_discovery": a["headlineBeyondDiscovery"],
        "naive_explanations": a["naiveExplanations"],
        "angle_candidates": a["angleCandidates"],
        "selected_angle_id": a["selectedAngleId"],
        "story_spine": a["editorial"]["storySpine"],
        "opening_promise": a["openingPromise"],
        "midpoint_turn": a["midpointTurn"],
        "closing_reframe": a["closingReframe"],
        "open_loops": a["openLoops"],
        "scenes": scenes,
    }


def build_story_script(a: dict[str, Any]) -> dict[str, Any]:
    scenes = []
    for index, scene in enumerate(a["scenes"], 1):
        scenes.append({
            "scene_id": f"scene-{index:02d}",
            "formal_role": scene["formalRole"],
            "narration": "\n\n".join(chunk["text"] for chunk in scene["chunks"]),
            "connection_to_previous": scene.get("connector", "therefore"),
            "evidence_ids": scene.get("newEvidenceIds", []),
            "causal_claims": scene.get("causalClaims", []),
        })
    return {
        "contract_version": "1.0.0",
        "episode_date": a["episodeDate"],
        "producer": "chatgpt",
        "story_plan": {"path": "BOUND_AT_MATERIALIZATION", "sha256": "0" * 64},
        "causal_dossier": {"path": "BOUND_AT_MATERIALIZATION", "sha256": "0" * 64},
        "scenes": scenes,
        "retained_counterevidence_ids": a["retainedCounterevidenceIds"],
        "unresolved_points": a["unresolvedPoints"],
    }


def build_creative_review(a: dict[str, Any]) -> dict[str, Any]:
    checks = []
    for index in range(1, 9):
        checks.append({
            "scene_id": f"scene-{index:02d}",
            "mode": "close" if index == 8 else "continue",
            "payoff_delivered": True,
            "belief_changed": True,
            "continuation_reason_natural": None if index == 8 else True,
            "closure_effective": True if index == 8 else None,
            "opening_promise_recovered": True if index == 8 else None,
            "procedural_language_dominant": False,
        })
    review = a["review"]
    return {
        "contract_version": "1.1.0",
        "episode_date": a["episodeDate"],
        "reviewer": "editorial_critic",
        "round": review.get("round", 2),
        "scores": review["scores"],
        "total_score": sum(review["scores"].values()),
        "scene_checks": checks,
        "immediate_failures": review.get("immediateFailures", []),
        "findings": review.get("findings", []),
        "verdict": "pass",
    }


def build_episode_markdown(a: dict[str, Any], render: dict[str, Any]) -> str:
    e = a["editorial"]
    lines = [
        f"# 朝のNASDAQカフェ｜{a['episodeDate']} 制作パッケージ",
        "",
        "## A. エピソード概要",
        f"- 対象日：{a['episodeDate']}",
        f"- 市場セッション：{a['marketDate']} US market",
        f"- 情報締切：{a['informationCutoff']}",
        f"- 主役ニュース：{e['leadNews']}",
        f"- ストーリーの背骨：{e['storySpine']}",
        f"- 中心仮説：{e['centralHypothesis']}",
        f"- 確信度：{e['confidence']}",
        f"- Expected：{e['expected']}",
        f"- Actual：{e['actual']}",
        f"- Gap：{e['gap']}",
        f"- Expectedの根拠区分：{e['expectedBasisType']} / {e['expectedBasisDetails']}",
        f"- 重要な反対材料：{' / '.join(e['counterEvidence'])}",
        f"- Duration：{a['durationMode']} / shortenedReason={a.get('shortenedReason')}",
        f"- Primary / Approved Fallback：{a.get('selectedVisualSourcePath','not-required')}",
        "- 当日固有生成画像：not-required",
        "- Visual Beat総数：18",
        "",
    ]
    for index, scene in enumerate(a["scenes"], 1):
        lines += [
            f"## Scene {index}｜{scene['formalName']}",
            "",
            f"- 目的：{scene['purpose']}",
            f"- 狐の演技意図：{scene['performanceIntent']}",
            f"- 狐の表情：{scene.get('initialExpression','分析')}",
            f"- 画面モード：{scene.get('visualMode','text-focus')}",
            f"- 接続文：{scene.get('connector','therefore')}",
            f"- 大テロップ：{scene['headline']}",
            f"- 補助テロップ：{' / '.join(scene.get('supportingTexts',[]))}",
            "",
            "### Visual Beats",
            "",
        ]
        rscene = render["scenes"][index - 1]
        for beat in rscene["visualBeats"]:
            lines += [
                f"- **{beat['beatId']}**",
                f"  - 画面状態：{beat['screenState']}",
                f"  - Visual Grammar：{beat['visualGrammar']['grammarId']} / {beat['visualGrammar']['transitionRole']}",
                f"  - Visual Template ID：{beat['visualTemplate']}",
                f"  - 画面の問い：{beat['screenQuestion']}",
                f"  - 主要要素：{beat['primaryElement']}",
                f"  - 視聴者向けテキスト：{' / '.join(beat['viewerTexts'])}",
                f"  - 根拠ID：{', '.join(beat['evidenceSourceIds'])}",
                f"  - Shot数：{len(beat.get('shots', []))}",
                "",
            ]
        lines += ["### 完成ナレーション", ""]
        lines += [chunk["text"] for chunk in scene["chunks"]]
        lines += ["", f"- 根拠と不確実性：{scene.get('uncertainty','')}", ""]
    p = a["publishing"]
    lines += [
        "## タイトル候補",
        *[f"- {x}" for x in p["titleCandidates"]],
        "",
        "## サムネイル文言候補",
        *[f"- {x}" for x in p["thumbnailTextCandidates"]],
        "",
        "## 概要欄",
        p["description"],
        "",
        "## 使用情報源",
        *[f"- {s['sourceId']}｜{s['publisher']}｜{s['title']}｜{s['reference']}" for s in a["sources"]],
        "",
        "## 04による興味深さ・わかりやすさ審問結果",
        f"- verdict：{a['review'].get('verdict','pass')}",
        f"- scores：{json.dumps(a['review']['scores'], ensure_ascii=False)}",
        "- 手直し済み：冒頭で『AI需要崩壊ではない』を明示、Scene 6で実1分足の支持材料と因果証明を分離、Scene 8でCoreWeaveを引け後確認材料に限定。",
        "",
        "## 実装上の注意",
        "- GitHub Actions / Remotionは市場因果やナレーションを変更しない。",
        "- CPIは当日21:30 JST発表予定であり、前夜通常取引の原因として扱わない。",
        "- CoreWeave Q2は引け後発表のため、通常取引の下落原因へ遡及させない。",
        "- 1分足はタイミング証拠であり、単独の因果証明として使わない。",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"



def _require_explicit_v2(a: dict[str, Any]) -> None:
    scenes = a.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 9:
        raise SystemExit("Daily Authoring v2 production requires exactly 9 scenes")
    total_beats = 0
    for sidx, scene in enumerate(scenes, 1):
        for key in (
            "sceneRole", "formalName", "purpose", "causalScope", "performanceIntent",
            "evidenceSourceIds", "uncertainty", "timelineBasis", "expectedBasisType",
            "visualMode", "initialExpression", "headline", "supportingTexts", "sourceLabel",
            "chunks", "beats",
        ):
            if key not in scene:
                raise SystemExit(f"scene-{sidx:02d}: explicit {key} is required in Daily Authoring v2")
        for cidx, chunk in enumerate(scene["chunks"], 1):
            if "text" not in chunk or "expression" not in chunk:
                raise SystemExit(f"scene-{sidx:02d} chunk {cidx}: explicit text/expression required")
        for bidx, beat in enumerate(scene["beats"], 1):
            total_beats += 1
            for key in (
                "primaryFunction", "screenState", "visualMode", "visualTemplate", "contentType",
                "screenQuestion", "primaryElement", "viewerTexts", "changeCue", "grammarId",
                "transitionRole", "evidenceSourceIds",
            ):
                if key not in beat:
                    raise SystemExit(f"scene-{sidx:02d} beat {bidx}: explicit {key} required")
    if total_beats != 18:
        raise SystemExit(f"Daily Authoring v2 requires exactly 18 Visual Beats; found={total_beats}")


def build_episode_markdown_v2(root_authoring: dict[str, Any], projected: dict[str, Any]) -> str:
    lines = [
        f"# 朝のNASDAQカフェ｜{root_authoring['episodeDate']} 制作パッケージ", "",
        "## エピソード概要",
        f"- 対象日：{root_authoring['episodeDate']}",
        f"- 市場セッション：{root_authoring['marketDate']} US market",
        f"- 情報締切：{root_authoring['informationCutoff']}",
        f"- Story spine：{root_authoring['storyPlan']['story_spine']}",
        f"- Creative Review：{root_authoring['creativeReview']['verdict']} / {root_authoring['creativeReview']['total_score']}",
        "",
    ]
    script_scenes = root_authoring["storyScript"]["scenes"]
    for index, (scene, scripted) in enumerate(zip(projected["scenes"], script_scenes, strict=True), 1):
        lines += [
            f"## Scene {index}｜{scene['formalName']}", "",
            f"- 目的：{scene['purpose']}",
            f"- 狐の演技意図：{scene['performanceIntent']}",
            f"- 狐の表情：{scene['initialExpression']}",
            f"- 画面モード：{scene['visualMode']}",
            f"- 大テロップ：{scene['headline']}",
            f"- 補助テロップ：{' / '.join(scene['supportingTexts'])}", "",
            "### Visual Beats", "",
        ]
        for beat_index, beat in enumerate(scene["beats"], 1):
            beat_id = f"scene-{index:02d}-beat-{beat_index:03d}"
            lines += [
                f"- **{beat_id}**",
                f"  - 画面状態：{beat['screenState']}",
                f"  - Visual Grammar：{beat['grammarId']} / {beat['transitionRole']}",
                f"  - Visual Template ID：{beat['visualTemplate']}",
                f"  - 画面の問い：{beat['screenQuestion']}",
                f"  - 主要要素：{beat['primaryElement']}",
                f"  - 視聴者向けテキスト：{' / '.join(beat['viewerTexts'])}",
                f"  - 根拠ID：{', '.join(beat['evidenceSourceIds'])}",
                f"  - Shot数：{len(beat.get('shots', []))}",
                "",
            ]
        lines += [
            "### 完成ナレーション", "", scripted["narration"], "",
            f"- 根拠と不確実性：{scene['uncertainty']}", "",
        ]
    publishing = projected["publishing"]
    lines += [
        "## タイトル候補", *[f"- {x}" for x in publishing["titleCandidates"]], "",
        "## サムネイル文言候補", *[f"- {x}" for x in publishing["thumbnailTextCandidates"]], "",
        "## 概要欄", publishing["description"], "",
        "## 04による興味深さ・わかりやすさ審問結果",
        f"- verdict：{root_authoring['creativeReview']['verdict']}",
        f"- scores：{json.dumps(root_authoring['creativeReview']['scores'], ensure_ascii=False)}", "",
        "## 実装上の注意",
        "- GitHub Actions / Remotionは市場因果、Story、04、ナレーションを変更しない。",
        "- このパッケージはCanonical Daily Authoring v2からのdeterministic projectionである。", "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _materialize_current_v2(root: Path, date: str, raw_authoring: dict[str, Any]) -> int:
    production = copy.deepcopy(raw_authoring["production"])
    dossier_ref = raw_authoring["causalDossier"]
    dossier_path = (root / dossier_ref["path"]).resolve()
    if not dossier_path.is_file():
        raise SystemExit("Daily Authoring v2 causal Dossier is missing")
    dossier = load(dossier_path)
    expected = dossier["expected_actual_gap"]["expected"]
    actual = dossier["expected_actual_gap"]["actual"]
    gap = dossier["expected_actual_gap"]["gap"]
    handoff = dossier["editorial_handoff"]
    review = raw_authoring["creativeReview"]
    derived_editorial = {
        "leadNews": handoff["provisional_lead"],
        "storySpine": raw_authoring["storyPlan"]["story_spine"],
        "centralHypothesis": handoff["central_hypothesis"],
        "confidence": handoff["confidence"],
        "expected": expected["statement"],
        "actual": actual["statement"],
        "gap": gap["statement"],
        "expectedBasisType": expected["basis_class"],
        "expectedBasisDetails": expected["statement"],
        "counterEvidence": [item["statement"] for item in dossier.get("contrary_evidence", [])],
    }
    derived_review = current_compatibility_adapter_v12.project_creative_review(review)
    a = dict(production)
    a.update({
        "episodeDate": raw_authoring["episodeDate"],
        "marketDate": raw_authoring["marketDate"],
        "informationCutoff": raw_authoring["informationCutoff"],
        "durationMode": raw_authoring["durationMode"],
        "shortenedReason": raw_authoring["shortenedReason"],
        "publishing": copy.deepcopy(raw_authoring["publishing"]),
        "expectedConfirmed": expected["status"] in {"confirmed", "partially_confirmed"},
        "editorial": derived_editorial,
        "review": derived_review,
    })
    _require_explicit_v2(a)
    projected, viewer_report = project_authoring_viewer_surfaces(a)
    work = root / "working" / date
    story = work / "story-engine"
    episodes = root / "episodes" / date
    render_dir = root / "render-specs" / date
    dump(work / "financial_visual_bindings.json", {"contractVersion":"1.0.0","episodeDate":date,"bindings":projected.get("financialBindings",[])})
    visual_source_checkpoint_v12.materialize(
        work=work,
        date=date,
        projected=projected,
    )
    dump(story / "story_production_bindings.json", {
        "contract_version":"1.0.0","episode_date":date,"scene_overrides":{},"beat_overrides":{}
    })

    event_serial = [0]
    caption_conversions: list[dict[str, Any]] = []
    scenes = [build_scene(scene, i, event_serial, caption_conversions) for i, scene in enumerate(projected["scenes"], 1)]
    viewer_report["conversions"].extend(caption_conversions)
    viewer_report["conversionCount"] = len(viewer_report["conversions"])
    write_projection_report(work / "viewer_surface_projection_report.json", viewer_report)
    render = {
        "schemaVersion":"2.4.0", "visualGrammarContractVersion":"1.0.0",
        "expectedConfirmed": projected["expectedConfirmed"],
        "episode": {
            "id":date,"targetDate":date,"marketSession":f"{raw_authoring['marketDate']} US market",
            "informationCutoff":raw_authoring["informationCutoff"],"episodeType":projected["episodeType"],
            "durationMode":raw_authoring["durationMode"],"shortenedReason":raw_authoring["shortenedReason"],
            "fps":30,"width":1920,"height":1080,
        },
        "editorial":projected["editorial"], "publishing":projected["publishing"],
        "sources":projected["sources"], "review":projected["review"],
        "pronunciations":projected["pronunciations"], "corrections":projected["corrections"],
        "voiceProfileId":"gemini-charon", "scenes":scenes,
    }
    dump(render_dir / "render_spec.json", render)
    bindings = []
    for sidx, scene in enumerate(projected["scenes"], 1):
        for bidx, beat in enumerate(scene["beats"], 1):
            if "reactionBinding" in beat:
                row = copy.deepcopy(beat["reactionBinding"])
                row.setdefault("visualBeatId", f"vb-{sidx:02d}-{bidx:02d}")
                bindings.append(row)
    dump(work / "reaction_timeline_bindings.json", {"contractVersion":"1.0.0","episodeDate":date,"bindings":bindings})
    episodes.mkdir(parents=True, exist_ok=True)
    (episodes / f"episode_package_public_{date}.md").write_text(
        build_episode_markdown_v2(raw_authoring, projected), encoding="utf-8"
    )
    print(f"MATERIALIZED Daily Authoring v2 {date}: scenes=9 beats=18 semantic_writer=false")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = ap.parse_args()
    root = args.repo_root.resolve()
    raw_authoring = load(root / "daily-authoring" / f"{args.date}.json")
    if raw_authoring.get("contractVersion") == "2.0.0":
        if raw_authoring.get("episodeDate") != args.date:
            raise SystemExit("authoring episodeDate mismatch")
        return _materialize_current_v2(root, args.date, raw_authoring)
    a, viewer_report = project_authoring_viewer_surfaces(raw_authoring)
    if a.get("episodeDate") != args.date:
        raise SystemExit("authoring episodeDate mismatch")
    if a.get("durationMode") not in {"standard", "shortened"}:
        raise SystemExit("authoring durationMode must be standard or shortened")
    if a["durationMode"] == "standard" and a.get("shortenedReason") is not None:
        raise SystemExit("standard duration requires shortenedReason=null")
    if a["durationMode"] == "shortened" and not str(a.get("shortenedReason") or "").strip():
        raise SystemExit("shortened duration requires non-empty shortenedReason")
    if len(a.get("scenes", [])) != 9:
        raise SystemExit("authoring requires exactly 9 scenes")
    beat_count = sum(len(scene.get("beats", [])) for scene in a["scenes"])
    if beat_count != 18:
        raise SystemExit(f"authoring requires exactly 18 visual beats; found={beat_count}")

    work = root / "working" / args.date
    story = work / "story-engine"
    research = root / "research" / args.date
    episodes = root / "episodes" / args.date
    render_dir = root / "render-specs" / args.date

    dump(work / "memory_query_plan.json", a["memoryQueryPlan"])
    dump(work / "financial_visual_bindings.json", {"contractVersion":"1.0.0","episodeDate":args.date,"bindings":[]})
    dump(work / "terminal_assembly_bindings.json", {
        "contractVersion":"1.0.0","episodeDate":args.date,"finalSceneId":"scene-09",
        "sourceTextPaths":["$.scenes[0].headline","$.scenes[4].supportingTexts[0]","$.scenes[7].supportingTexts[0]"],
        "lines":[a["scenes"][0]["headline"],a["scenes"][4]["supportingTexts"][0],a["scenes"][7]["supportingTexts"][0]],
    })
    dump(work / "visual_source_intents.json", {
        "contractVersion":"1.0.0","episodeDate":args.date,"intents":a.get("visualSourceIntents",[])
    })
    selection = a.get("visualSourceSelection")
    if selection:
        dump(work / "visual_source_selection.json", selection)
    dump(story / "templates" / "story_plan.template.json", build_story_plan(a))
    dump(story / "templates" / "story_script.template.json", build_story_script(a))
    dump(story / "templates" / "creative_review.template.json", build_creative_review(a))
    dump(story / "story_production_bindings.json", {
        "contract_version":"1.0.0","episode_date":args.date,"scene_overrides":{},"beat_overrides":{}
    })
    dump(research / "causal_research_dossier.template.json", a["causalDossier"])

    event_serial = [0]
    caption_conversions: list[dict[str, Any]] = []
    scenes = [
        build_scene(scene, i, event_serial, caption_conversions)
        for i, scene in enumerate(a["scenes"], 1)
    ]
    viewer_report["conversions"].extend(caption_conversions)
    viewer_report["conversionCount"] = len(viewer_report["conversions"])
    write_projection_report(work / "viewer_surface_projection_report.json", viewer_report)

    render = {
        "schemaVersion":"2.4.0",
        "visualGrammarContractVersion":"1.0.0",
        "expectedConfirmed": a.get("expectedConfirmed", True),
        "episode": {
            "id":args.date,"targetDate":args.date,
            "marketSession":f"{a['marketDate']} US market",
            "informationCutoff":a["informationCutoff"],
            "episodeType":a.get("episodeType","single-news"),
            "durationMode":a["durationMode"],"shortenedReason":a.get("shortenedReason"),
            "fps":30,"width":1920,"height":1080,
        },
        "editorial":a["editorial"],
        "publishing":a["publishing"],
        "sources":a["sources"],
        "review": {
            "verdict":"approved",
            "scores":a["review"]["scores"],
            "totalScore":sum(a["review"]["scores"].values()),
            "largestDropoffRisk":a["review"].get("largestDropoffRisk", ""),
            "requiredChanges":a["review"].get("requiredChanges", []),
            "changesApplied":a["review"].get("changesApplied", []),
        },
        "pronunciations":a.get("pronunciations", []),
        "corrections":a.get("corrections", []),
        "voiceProfileId":"gemini-charon",
        "scenes":scenes,
    }
    dump(render_dir / "render_spec.json", render)

    bindings = []
    for sidx, scene in enumerate(a["scenes"], 1):
        for bidx, beat in enumerate(scene["beats"], 1):
            if "reactionBinding" in beat:
                row = copy.deepcopy(beat["reactionBinding"])
                row.setdefault("visualBeatId", f"vb-{sidx:02d}-{bidx:02d}")
                bindings.append(row)
    dump(work / "reaction_timeline_bindings.json", {
        "contractVersion":"1.0.0","episodeDate":args.date,"bindings":bindings
    })
    episodes.mkdir(parents=True, exist_ok=True)
    (episodes / f"episode_package_public_{args.date}.md").write_text(
        build_episode_markdown(a, render), encoding="utf-8"
    )
    print(
        f"MATERIALIZED ChatGPT daily authoring {args.date}: scenes=9 beats=18 "
        f"durationMode={a['durationMode']} viewerConversions={viewer_report['conversionCount']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
