#!/usr/bin/env python3
"""Apply evidence-first and measured-diversity authoring for 2026-08-10 acceptance.

TEST / ACCEPTANCE ONLY. This script does not infer causality or rewrite narration.
It takes the already-approved story and changes only visual authoring:

- BLS Employment Situation: official PDF Primary plus Approved Fallback because BLS
  blocks GitHub-hosted acquisition;
- Microchip Q1 FY27: actual company IR shown as ``news-media`` on the Beat whose
  narration states the results and guidance;
- QQQ 08:29 / 08:30 / 08:31 ET: verified minute closes shown as a real series;
- measured visual diversity: Scene 1 breaks the duplicated OpenHero surface, Scene 4
  turns the already-authored scorecard analogy into a physical visual change, and
  Scene 8 is split at sentence boundaries so no single visual surface is held for
  roughly 30 seconds.

The fixed full-Scene renderer background stays ``mainBackground``. The renderer never
chooses Primary/Fallback or visual semantics. Approved narration and causal meaning are
preserved byte-for-byte when narration chunks are concatenated.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

DATE = "2026-08-10"
BLS_URL = "https://www.bls.gov/news.release/pdf/empsit.pdf"
MICROCHIP_URL = (
    "https://ir.microchip.com/news-events/press-releases/detail/1409/"
    "microchip-technology-announces-financial-results-for-first-quarter-of-fiscal-year-2027"
)
MICROCHIP_PRIMARY_ASSET_ID = "daily-microchip-q1-fy27-ir"
MICROCHIP_SECONDARY_ASSET_ID = "daily-microchip-q1-fy27-ir-secondary"
SENTENCE_RE = re.compile(r".*?(?:[。！？!?](?:[」』】）)]*)|$)")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return value


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def segment(text: str, count: int) -> list[str]:
    if count <= 0:
        raise SystemExit("chunk count must be positive")
    if count == 1:
        return [text]
    parts = [m.group(0) for m in SENTENCE_RE.finditer(text) if m.group(0)] or [text]
    if len(parts) < count:
        cuts = [round(len(text) * i / count) for i in range(count + 1)]
        result = [text[cuts[i] : cuts[i + 1]] for i in range(count)]
    else:
        target = len(text) / count
        result: list[str] = []
        current = ""
        remaining_groups = count
        for idx, part in enumerate(parts):
            remaining_parts = len(parts) - idx
            if current and len(result) < count - 1 and (
                len(current) >= target or remaining_parts == remaining_groups - 1
            ):
                result.append(current)
                current = ""
                remaining_groups -= 1
            current += part
        result.append(current)
        while len(result) < count:
            result.append("")
        if len(result) > count:
            result[count - 1] = "".join(result[count - 1 :])
            result = result[:count]
    if "".join(result) != text:
        raise SystemExit("narration segmentation changed approved text")
    return result


def beat_id(beat: dict[str, Any]) -> str:
    value = beat.get("visualBeatId") or beat.get("beatId")
    if not isinstance(value, str) or not value:
        raise SystemExit("Visual Beat ID missing")
    return value


def canonical_visual_beat_id(value: str) -> str:
    if re.fullmatch(r"vb-0[1-9]-[0-9]{2}", value):
        return value
    match = re.fullmatch(r"scene-(0[1-9])-beat-([0-9]{3})", value)
    if match:
        return f"vb-{match.group(1)}-{int(match.group(2)):02d}"
    raise SystemExit(f"unsupported Visual Beat ID alias: {value}")


def authoring_beat_id(beat: dict[str, Any], scene_number: int, beat_number: int) -> str:
    value = beat.get("beatId")
    if isinstance(value, str) and value.startswith("scene-"):
        return value
    return f"scene-{scene_number:02d}-beat-{beat_number:03d}"


def scene_map(render: dict[str, Any]) -> dict[int, dict[str, Any]]:
    result = {
        scene["sceneNumber"]: scene
        for scene in render.get("scenes", [])
        if isinstance(scene, dict) and isinstance(scene.get("sceneNumber"), int)
    }
    missing = sorted(set(range(1, 10)) - set(result))
    if missing:
        raise SystemExit(f"missing scenes: {missing}")
    return result


def set_grammar(beat: dict[str, Any], grammar_id: str) -> None:
    grammar = beat.get("visualGrammar")
    if not isinstance(grammar, dict):
        grammar = {
            "contractVersion": "1.0.0",
            "grammarId": grammar_id,
            "transitionRole": beat.get("transitionRole", "continuation"),
            "returnTargetBeatId": None,
        }
        beat["visualGrammar"] = grammar
    else:
        grammar["grammarId"] = grammar_id
    beat["visualGrammarId"] = grammar_id


def sync_override(
    overrides: dict[str, Any], key: str, beat: dict[str, Any], *, reaction: dict[str, Any] | None = None
) -> None:
    override = overrides.setdefault(key, {})
    for field in (
        "screenQuestion",
        "primaryElement",
        "viewerTexts",
        "changeCue",
        "contentType",
        "visualTemplate",
        "visualMode",
        "screenState",
        "templateVariant",
        "visualGrammarId",
        "transitionRole",
    ):
        if field in beat:
            override[field] = beat[field]
    grammar = beat.get("visualGrammar")
    if isinstance(grammar, dict):
        override["visualGrammarId"] = grammar.get("grammarId")
        override["transitionRole"] = grammar.get("transitionRole")
    if reaction is None:
        override.pop("reactionTimelineBinding", None)
    else:
        override["reactionTimelineBinding"] = reaction


def visual_candidate(
    *,
    candidate_id: str,
    asset_id: str,
    source_kind: str,
    locator: dict[str, Any],
    capture_method: str,
    rights_status: str,
    capture_spec: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "candidateId": candidate_id,
        "assetId": asset_id,
        "sourceKind": source_kind,
        "sourceLocator": locator,
        "captureMethod": capture_method,
        "captureSpec": capture_spec,
        "rightsStatus": rights_status,
    }


def source_intent(
    *,
    intent_id: str,
    scene_id: str,
    target_beat_id: str,
    source_id: str,
    purpose: str,
    primary: dict[str, Any],
    fallback: dict[str, Any],
) -> dict[str, Any]:
    return {
        "intentId": intent_id,
        "target": {"sceneId": scene_id, "visualBeatId": target_beat_id},
        "presentationClass": "source-document",
        "purpose": purpose,
        "sourceIds": [source_id],
        "placement": {
            "placementId": f"{intent_id}-placement",
            "role": "main-media",
            "region": "main-stage",
            "fit": "contain",
            "focalPoint": None,
        },
        "primary": primary,
        "fallback": fallback,
    }


def patch_scene1_evidence_boundary(scene: dict[str, Any], overrides: dict[str, Any]) -> None:
    beat = scene["visualBeats"][1]
    key = authoring_beat_id(beat, 1, 2)
    beat.update(
        {
            "contentType": "evidence-boundary",
            "visualTemplate": "evidence-boundary",
            "visualMode": "text-focus",
            "screenState": "Data",
            "templateVariant": "confirmed-vs-unconfirmed",
            "screenQuestion": "何を原因と呼ばないか",
            "primaryElement": "雇用悪化そのもの ≠ 株高の原因",
            "viewerTexts": [
                "雇用悪化そのもの ≠ 買い材料",
                "主役候補：利上げ観測後退",
                "増幅：半導体・原油・金利",
            ],
            "changeCue": "主役候補：利上げ観測後退",
        }
    )
    config = beat.get("templateConfig")
    if not isinstance(config, dict):
        raise SystemExit("Scene 1 Beat 2 templateConfig missing")
    config.clear()
    config.update(
        {
            "variant": "confirmed-vs-unconfirmed",
            "comparisonBasis": "原因と市場解釈を分ける",
            "dataBasis": "Reuters market interpretation",
            "laneLabels": ["言わない", "主役候補"],
            "nodeOrder": [],
            "outcomeNodeId": None,
        }
    )
    set_grammar(beat, "evidence")
    sync_override(overrides, key, beat)


def patch_scene4_scorecard_analogy(scene: dict[str, Any], overrides: dict[str, Any]) -> None:
    beat = scene["visualBeats"][1]
    key = authoring_beat_id(beat, 4, 2)
    beat.update(
        {
            "contentType": "analogy-steps",
            "visualTemplate": "analogy-steps",
            "visualMode": "causal-diagram",
            "screenState": "Data",
            "templateVariant": "left-to-right",
            "screenQuestion": "同じ悪材料でも採点表が違うと何が変わる？",
            "primaryElement": "景気の採点表 → 金利の採点表 → 大型テック",
            "viewerTexts": [
                "景気の採点表：赤点",
                "金利の採点表：利上げリスク↓",
                "大型テック：逆風が和らぐ",
            ],
            "changeCue": "景気の採点表 → 金利の採点表",
            "objectIds": [],
            "sequencePolicy": "explicit",
        }
    )
    config = beat.get("templateConfig")
    if not isinstance(config, dict):
        raise SystemExit("Scene 4 Beat 2 templateConfig missing")
    config.clear()
    config.update(
        {
            "variant": "left-to-right",
            "comparisonBasis": "同じ雇用下振れを景気と金利の2つの採点表で読む",
            "dataBasis": "Reuters market interpretation",
            "laneLabels": [],
            "nodeOrder": [],
            "outcomeNodeId": None,
        }
    )
    set_grammar(beat, "analogy")
    sync_override(overrides, key, beat)


def patch_microchip_news_media(scene: dict[str, Any]) -> str:
    beat = scene["visualBeats"][0]
    source_ids = [
        item for item in beat.get("evidenceSourceIds", []) if isinstance(item, str)
    ]
    if "source-004" not in source_ids:
        source_ids.append("source-004")
    beat["evidenceSourceIds"] = source_ids
    scene_ids = [
        item for item in scene.get("evidenceSourceIds", []) if isinstance(item, str)
    ]
    if "source-004" not in scene_ids:
        scene_ids.append("source-004")
    scene["evidenceSourceIds"] = scene_ids

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
    set_grammar(beat, "evidence")

    scene["visualEvents"] = [
        event
        for event in scene.get("visualEvents", [])
        if not (
            isinstance(event, dict) and event.get("targetId") == "scene-06-card-001"
        )
    ]
    return canonical_visual_beat_id(beat_id(beat))


def qqq_release_window(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    for item in receipt.get("series", []):
        if isinstance(item, dict) and item.get("symbol") == "QQQ.US":
            if item.get("precision") != "verified-intraday-series":
                raise SystemExit("QQQ receipt is not verified-intraday-series")
            rows = item.get("release_window")
            if not isinstance(rows, list) or len(rows) < 3:
                raise SystemExit("QQQ release window missing")
            return rows[:3]
    raise SystemExit("QQQ series missing from verified Collector receipt")


def patch_verified_series(scene: dict[str, Any], receipt: dict[str, Any]) -> list[str]:
    beat = scene["visualBeats"][0]
    rows = qqq_release_window(receipt)
    ids = ["scene-08-qqq-0829", "scene-08-qqq-0830", "scene-08-qqq-0831"]
    labels = ["08:29 ET", "08:30 ET", "08:31 ET"]
    numbers = [
        item
        for item in scene.get("numbers", [])
        if isinstance(item, dict)
        and (item.get("numberId") or item.get("key")) not in set(ids)
    ]
    for object_id, label, row in zip(ids, labels, rows):
        close = float(row["close"])
        numbers.append(
            {
                "numberId": object_id,
                "label": label,
                "value": f"{close:.3f}".rstrip("0").rstrip("."),
                "numericValue": close,
                "precision": 3,
                "unit": "",
                "tone": "positive" if label != "08:29 ET" else "neutral",
                "comparison": None,
            }
        )
    scene["numbers"] = numbers
    beat.update(
        {
            "contentType": "event-reaction-timeline",
            "visualTemplate": "event-reaction-timeline",
            "visualMode": "timeline",
            "screenState": "Chart",
            "templateVariant": "verified-series",
            "objectIds": ids,
            "sequencePolicy": "object-order-fallback",
            "screenQuestion": "8:30 ETの発表前後でQQQはどう動いた？",
            "primaryElement": "QQQ 実1分足｜08:29 → 08:30 → 08:31 ET",
            "changeCue": "QQQ 実1分足",
            "viewerTexts": [
                "QQQ 実1分足",
                "08:29 719.16 → 08:30 720.23 → 08:31 720.531",
                "SOXX・NVIDIAも発表分で上向き",
            ],
            "templateConfig": {
                "comparisonBasis": "BLS 08:30 ET発表前後",
                "dataBasis": "Longbridge verified 1-minute Kline minute-close",
                "laneLabels": [],
                "nodeOrder": [],
                "outcomeNodeId": None,
                "variant": "verified-series",
                "reactionTimeline": {
                    "precision": "verified-intraday-series",
                    "eventOrderIds": ids,
                    "seriesObjectIds": ids,
                },
            },
        }
    )
    set_grammar(beat, "reaction")
    beat["visualGrammar"]["transitionRole"] = "major-shift"
    beat["visualGrammarId"] = "reaction"
    beat["transitionRole"] = "major-shift"
    return ids


def scene8_card(
    card_id: str, title: str, lines: list[tuple[str, str]]
) -> dict[str, Any]:
    return {
        "cardId": card_id,
        "role": None,
        "title": title,
        "lines": [
            {"label": label, "value": value, "tone": "neutral"}
            for label, value in lines
        ],
    }


def base_scene8_beat(index: int, evidence_source_ids: list[str]) -> dict[str, Any]:
    transition = "major-shift" if index == 1 else "continuation"
    return {
        "beatId": f"scene-08-beat-{index:03d}",
        "visualBeatId": f"scene-08-beat-{index:03d}",
        "startChunkId": f"scene-08-chunk-{index:03d}",
        "endChunkId": f"scene-08-chunk-{index:03d}",
        "narrationStartCue": "placeholder",
        "narrationEndCue": "placeholder",
        "primaryFunction": "Evidence",
        "transitionRole": transition,
        "finalHoldMs": 500,
        "assetPlacementIds": [],
        "assetState": "not-required",
        "returnScreenState": None,
        "evidenceSourceIds": evidence_source_ids,
        "expressionChange": None,
        "fallback": None,
        "entity": None,
        "pictureBook": None,
        "sequencePolicy": "explicit",
    }


def patch_scene8_measured_diversity(
    scene: dict[str, Any],
    receipt: dict[str, Any],
    story_narration: str,
    overrides: dict[str, Any],
) -> None:
    qqq_ids = patch_verified_series(scene, receipt)
    old_beats = scene.get("visualBeats", [])
    if len(old_beats) < 2:
        raise SystemExit("Scene 8 requires the existing two approved Beats")
    old_chunks = scene.get("narrationChunks", [])
    if len(old_chunks) != 2:
        raise SystemExit("Scene 8 expected two authored narration chunks before diversity split")
    pieces = segment(story_narration, 4)
    expressions = [
        old_chunks[0].get("expression", "通常"),
        old_chunks[0].get("expression", "通常"),
        old_chunks[-1].get("expression", "通常"),
        old_chunks[-1].get("expression", "通常"),
    ]
    scene["narrationChunks"] = [
        {
            "chunkId": f"scene-08-chunk-{index:03d}",
            "speechText": piece,
            "captionText": piece,
            "expression": expressions[index - 1],
            "pauseAfterMs": 80 if index < 4 else 200,
        }
        for index, piece in enumerate(pieces, start=1)
    ]
    if "".join(chunk["speechText"] for chunk in scene["narrationChunks"]) != story_narration:
        raise SystemExit("Scene 8 diversity split changed narration")

    evidence_ids = list(
        dict.fromkeys(
            [
                item
                for beat in old_beats[:2]
                for item in beat.get("evidenceSourceIds", [])
                if isinstance(item, str)
            ]
        )
    )

    beat1 = base_scene8_beat(1, evidence_ids)
    beat1.update(
        {
            "contentType": "event-reaction-timeline",
            "visualTemplate": "event-reaction-timeline",
            "visualMode": "timeline",
            "screenState": "Chart",
            "templateVariant": "verified-series",
            "screenQuestion": "8:30 ETの発表前後でQQQはどう動いた？",
            "primaryElement": "QQQ 実1分足｜08:29 → 08:30 → 08:31 ET",
            "viewerTexts": [
                "QQQ 実1分足",
                "08:29 719.16 → 08:30 720.23 → 08:31 720.531",
                "SOXX・NVIDIAも発表分で上向き",
            ],
            "changeCue": "QQQ 実1分足",
            "objectIds": qqq_ids,
            "sequencePolicy": "object-order-fallback",
            "visualGrammarId": "reaction",
            "visualGrammar": {
                "contractVersion": "1.0.0",
                "grammarId": "reaction",
                "transitionRole": "major-shift",
                "returnTargetBeatId": None,
            },
            "templateConfig": {
                "variant": "verified-series",
                "comparisonBasis": "BLS 08:30 ET発表前後",
                "dataBasis": "Longbridge verified 1-minute Kline minute-close",
                "laneLabels": [],
                "nodeOrder": [],
                "outcomeNodeId": None,
                "reactionTimeline": {
                    "precision": "verified-intraday-series",
                    "eventOrderIds": qqq_ids,
                    "seriesObjectIds": qqq_ids,
                },
            },
        }
    )

    beat2 = base_scene8_beat(2, evidence_ids)
    beat2.update(
        {
            "contentType": "evidence-boundary",
            "visualTemplate": "evidence-boundary",
            "visualMode": "text-focus",
            "screenState": "Data",
            "templateVariant": "confirmed-vs-unconfirmed",
            "screenQuestion": "初動整合と因果証明の境界は？",
            "primaryElement": "初動は整合 / 1分足だけでは因果証明しない",
            "viewerTexts": [
                "整合：QQQ・SOXX・NVIDIA ↑",
                "境界：1分足 ≠ 因果証明",
                "反対材料：MCHP 79.58 → 79.56",
            ],
            "changeCue": "1分足 ≠ 因果証明",
            "objectIds": ["scene-08-card-002"],
            "visualGrammarId": "evidence",
            "visualGrammar": {
                "contractVersion": "1.0.0",
                "grammarId": "evidence",
                "transitionRole": "continuation",
                "returnTargetBeatId": None,
            },
            "templateConfig": {
                "variant": "confirmed-vs-unconfirmed",
                "comparisonBasis": "発表時刻の整合と因果の境界",
                "dataBasis": "verified 1-minute series + contrary MCHP timing",
                "laneLabels": ["整合", "境界"],
                "nodeOrder": [],
                "outcomeNodeId": None,
            },
        }
    )

    cards = [item for item in scene.get("cards", []) if isinstance(item, dict)]
    card_map = {item.get("cardId"): item for item in cards if item.get("cardId")}
    card_map["scene-08-card-002"] = scene8_card(
        "scene-08-card-002",
        "初動と境界",
        [("因果", "1分足は因果証明ではない"), ("MCHP", "79.58 → 79.56")],
    )
    card_map["scene-08-card-003"] = scene8_card(
        "scene-08-card-003",
        "主役候補と増幅",
        [("主役候補", "雇用→利上げリスク↓"), ("増幅", "Microchip・原油・利回り")],
    )
    card_map["scene-08-card-004"] = scene8_card(
        "scene-08-card-004",
        "反対材料と結論",
        [("反対材料", "成長不安・個別下落"), ("結論", "採点表の優先順位が変化")],
    )
    preserved = [
        item
        for item in cards
        if item.get("cardId")
        not in {"scene-08-card-002", "scene-08-card-003", "scene-08-card-004"}
    ]
    scene["cards"] = preserved + [
        card_map["scene-08-card-002"],
        card_map["scene-08-card-003"],
        card_map["scene-08-card-004"],
    ]

    beat3 = base_scene8_beat(3, evidence_ids)
    beat3.update(
        {
            "contentType": "verification-checklist",
            "visualTemplate": "verification-checklist",
            "visualMode": "verification-points",
            "screenState": "Data",
            "templateVariant": "default",
            "screenQuestion": "主役候補と増幅要因をどう分ける？",
            "primaryElement": "主役候補・増幅要因を分離",
            "viewerTexts": [
                "主役候補：雇用→利上げリスク↓",
                "分ける：Microchipは会社固有材料",
                "増幅：原油・利回り↓",
            ],
            "changeCue": "主役候補：雇用→利上げリスク↓",
            "objectIds": ["scene-08-card-003"],
            "visualGrammarId": "verification",
            "visualGrammar": {
                "contractVersion": "1.0.0",
                "grammarId": "verification",
                "transitionRole": "continuation",
                "returnTargetBeatId": None,
            },
            "templateConfig": {
                "variant": "default",
                "comparisonBasis": None,
                "dataBasis": "approved causal dossier + verified timing",
                "laneLabels": [],
                "nodeOrder": [],
                "outcomeNodeId": None,
            },
        }
    )

    beat4 = base_scene8_beat(4, evidence_ids)
    beat4.update(
        {
            "contentType": "verification-matrix",
            "visualTemplate": "verification-matrix",
            "visualMode": "verification",
            "screenState": "Data",
            "templateVariant": "strengthen-vs-weaken",
            "screenQuestion": "結論を弱める材料まで残すと？",
            "primaryElement": "反対材料を残した最終境界",
            "viewerTexts": [
                "反対材料：成長不安・個別下落",
                "確信度：中程度",
                "結論：採点表の優先順位が変わった夜",
            ],
            "changeCue": "反対材料：成長不安・個別下落",
            "objectIds": ["scene-08-card-004"],
            "visualGrammarId": "verification",
            "visualGrammar": {
                "contractVersion": "1.0.0",
                "grammarId": "verification",
                "transitionRole": "continuation",
                "returnTargetBeatId": None,
            },
            "templateConfig": {
                "variant": "strengthen-vs-weaken",
                "comparisonBasis": "中心仮説を強める/弱める材料",
                "dataBasis": "approved causal dossier",
                "laneLabels": ["強める", "弱める"],
                "nodeOrder": [],
                "outcomeNodeId": None,
            },
        }
    )

    scene["visualBeats"] = [beat1, beat2, beat3, beat4]
    scene["visualEvents"] = [
        event
        for event in scene.get("visualEvents", [])
        if not (
            isinstance(event, dict)
            and event.get("eventId") in {"event-023", "event-024"}
        )
    ]
    scene["visualEvents"].extend(
        [
            {
                "eventId": "event-023",
                "atChunkId": "scene-08-chunk-003",
                "timing": "chunk-start",
                "offsetMs": 0,
                "action": "show",
                "targetId": "scene-08-card-003",
                "motionPreset": "rise-soft",
                "durationMs": 560,
                "easingPreset": "smooth-out",
                "expression": None,
            },
            {
                "eventId": "event-024",
                "atChunkId": "scene-08-chunk-004",
                "timing": "chunk-start",
                "offsetMs": 0,
                "action": "show",
                "targetId": "scene-08-card-004",
                "motionPreset": "rise-soft",
                "durationMs": 560,
                "easingPreset": "smooth-out",
                "expression": None,
            },
        ]
    )
    for key in [key for key in list(overrides) if key.startswith("scene-08-beat-")]:
        overrides.pop(key, None)
    for index, beat in enumerate(scene["visualBeats"], start=1):
        key = f"scene-08-beat-{index:03d}"
        reaction = None
        if index == 1:
            reaction = {
                "visualBeatId": "vb-08-01",
                "visualTemplate": "event-reaction-timeline",
                "templateVariant": "verified-series",
                "precision": "verified-intraday-series",
                "eventOrderIds": qqq_ids,
                "seriesObjectIds": qqq_ids,
                "evidenceBasis": (
                    "Longbridge verified 1-minute Kline minute-close around the "
                    "2026-08-07 08:30 ET BLS release. Timing alignment evidence only; "
                    "not causal proof."
                ),
            }
        sync_override(overrides, key, beat, reaction=reaction)


def markdown_beat_block(key: str, beat: dict[str, Any]) -> str:
    viewer = " / ".join(str(value) for value in beat.get("viewerTexts", []))
    evidence = ", ".join(str(value) for value in beat.get("evidenceSourceIds", [])) or "not-required"
    return (
        f"- **{key}**\n"
        "  - 開始合図：placeholder\n"
        "  - 終了合図：placeholder\n"
        f"  - 主要視覚機能：{beat.get('primaryFunction', 'Evidence')}\n"
        f"  - 画面状態：{beat.get('screenState', 'Data')}\n"
        f"  - Visual Grammar：{beat.get('visualGrammarId')} / {beat.get('transitionRole', 'continuation')}\n"
        f"  - Visual Template ID：{beat.get('visualTemplate')}\n"
        f"  - Template Variant：{beat.get('templateVariant', 'default')}\n"
        f"  - 入力構造：{viewer}\n"
        f"  - 画面の問い：{beat.get('screenQuestion', '')}\n"
        f"  - 主要要素：{beat.get('primaryElement', '')}\n"
        f"  - 視聴者向けテキスト：{viewer}\n"
        "  - 使用アセットID：not-required\n"
        "  - アセット状態：not-required\n"
        "  - 表示後の復帰先：該当なし\n"
        "  - Primary / Approved Fallback：not-required\n"
        "  - selected_path：not-required\n"
        f"  - 根拠ID：{evidence}\n"
    )


def replace_scene8_visual_beats(md: str, beats: list[dict[str, Any]]) -> str:
    pattern = re.compile(
        r"(?ms)(##\s+(?:B8\.\s+)?Scene\s+8(?:｜|\|).*?^### Visual Beats\s*\n)(.*?)(?=^### 完成ナレーション)"
    )
    match = pattern.search(md)
    if not match:
        raise SystemExit("Scene 8 Visual Beats block missing")
    body = "\n".join(
        markdown_beat_block(f"scene-08-beat-{index:03d}", beat)
        for index, beat in enumerate(beats, start=1)
    )
    return md[: match.start(2)] + body + "\n" + md[match.end(2) :]


def apply(root: Path) -> dict[str, Any]:
    render_path = root / f"render-specs/{DATE}/render_spec.json"
    receipt_path = root / "tests/fixtures/real-day-2026-08-10/collector_wave2_success_receipt.json"
    story_path = root / f"working/{DATE}/story-engine/story_script.json"
    bindings_path = root / f"working/{DATE}/story-engine/story_production_bindings.json"
    package_path = root / f"episodes/{DATE}/episode_package_public_{DATE}.md"

    render = load(render_path)
    receipt = load(receipt_path)
    story = load(story_path)
    bindings = load(bindings_path)
    package = package_path.read_text(encoding="utf-8")
    overrides = bindings.setdefault("beat_overrides", {})
    scenes = scene_map(render)

    patch_scene1_evidence_boundary(scenes[1], overrides)
    patch_scene4_scorecard_analogy(scenes[4], overrides)
    microchip_beat = patch_microchip_news_media(scenes[6])

    scene8_narration = next(
        item["narration"]
        for item in story.get("scenes", [])
        if isinstance(item, dict) and item.get("scene_id") == "scene-08"
    )
    patch_scene8_measured_diversity(scenes[8], receipt, scene8_narration, overrides)
    package = replace_scene8_visual_beats(package, scenes[8]["visualBeats"])

    scene2_beat = canonical_visual_beat_id(beat_id(scenes[2]["visualBeats"][0]))
    intents = {
        "contractVersion": "1.0.0",
        "episodeDate": DATE,
        "qualityPolicy": "evidence-first-v1",
        "intents": [
            source_intent(
                intent_id="vsi-20260810-bls-employment",
                scene_id="scene-02",
                target_beat_id=scene2_beat,
                source_id="source-002",
                purpose=(
                    "Primary is page 1 of the actual BLS July 2026 Employment Situation PDF. "
                    "Approved Fallback preserves the BLS numbers/source label on the news surface "
                    "when BLS blocks GitHub-hosted acquisition."
                ),
                primary=visual_candidate(
                    candidate_id="vsp-20260810-bls-primary",
                    asset_id="daily-bls-employment-july-2026",
                    source_kind="official-url",
                    locator={"url": BLS_URL},
                    capture_method="pdf-page-render",
                    capture_spec={"pageNumber": 1},
                    rights_status="cleared",
                ),
                fallback=visual_candidate(
                    candidate_id="vsp-20260810-bls-fallback",
                    asset_id="background_scene_news",
                    source_kind="existing-asset",
                    locator={"assetId": "background_scene_news"},
                    capture_method="registry-reference",
                    capture_spec=None,
                    rights_status="cleared",
                ),
            ),
            source_intent(
                intent_id="vsi-20260810-microchip-ir",
                scene_id="scene-06",
                target_beat_id=microchip_beat,
                source_id="source-004",
                purpose=(
                    "Show the actual Microchip Q1 FY27 IR release while the approved narration states "
                    "its results and next-quarter guidance. The fallback route uses the same official "
                    "page with a distinct production-safe asset ID so a BLS-only technical failure "
                    "does not discard the real IR."
                ),
                primary=visual_candidate(
                    candidate_id="vsp-20260810-microchip-primary",
                    asset_id=MICROCHIP_PRIMARY_ASSET_ID,
                    source_kind="official-url",
                    locator={"url": MICROCHIP_URL},
                    capture_method="webpage-screenshot",
                    capture_spec={"viewport": {"width": 1440, "height": 900}},
                    rights_status="cleared",
                ),
                fallback=visual_candidate(
                    candidate_id="vsp-20260810-microchip-fallback",
                    asset_id=MICROCHIP_SECONDARY_ASSET_ID,
                    source_kind="official-url",
                    locator={"url": MICROCHIP_URL},
                    capture_method="webpage-screenshot",
                    capture_spec={"viewport": {"width": 1440, "height": 900}},
                    rights_status="cleared",
                ),
            ),
        ],
    }
    selection = {
        "contractVersion": "1.0.0",
        "episodeDate": DATE,
        "selectedPath": "fallback",
    }

    write(render_path, render)
    write(bindings_path, bindings)
    package_path.write_text(package, encoding="utf-8")
    write(root / f"working/{DATE}/visual_source_intents.json", intents)
    write(root / f"working/{DATE}/visual_source_selection.json", selection)
    return {
        "status": "pass",
        "episodeDate": DATE,
        "renderSpec": render_path.relative_to(root).as_posix(),
        "visualSourceIntentCount": len(intents["intents"]),
        "selectedPath": "fallback",
        "fallbackReason": (
            "BLS blocks GitHub-hosted HTTP acquisition with 403; Microchip real IR "
            "remains preserved on fallback route."
        ),
        "microchipVisualBeatId": microchip_beat,
        "verifiedSeries": {
            "symbol": "QQQ.US",
            "precision": "verified-intraday-series",
            "points": qqq_release_window(receipt),
        },
        "measuredDiversityAuthoring": {
            "scene1Beat2Template": "evidence-boundary",
            "scene4Beat2Template": "analogy-steps",
            "scene8NarrationChunkCount": 4,
            "scene8VisualBeatCount": 4,
            "narrationChanged": False,
        },
        "realEvidence": ["source-004"],
        "approvedFallbackEvidence": ["source-002"],
        "reusableBackgrounds": [],
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
