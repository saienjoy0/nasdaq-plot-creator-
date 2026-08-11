#!/usr/bin/env python3
"""Apply the evidence-first 2026-08-10 acceptance authoring.

TEST / ACCEPTANCE ONLY. This script does not infer causality or rewrite narration.
It takes the already-approved story and changes only visual authoring:

- BLS Employment Situation: official PDF Primary plus Approved Fallback because BLS
  blocks GitHub-hosted acquisition;
- Microchip Q1 FY27: actual company IR shown as ``news-media`` on the Beat whose
  narration states the results and guidance;
- QQQ 08:29 / 08:30 / 08:31 ET: verified minute closes shown as a real series.

The fixed full-Scene renderer background stays ``mainBackground``. The renderer never
chooses Primary/Fallback and narration/causality are unchanged.
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


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return value


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def visual_candidate(*, candidate_id: str, asset_id: str, source_kind: str, locator: dict[str, Any], capture_method: str, rights_status: str, capture_spec: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "candidateId": candidate_id,
        "assetId": asset_id,
        "sourceKind": source_kind,
        "sourceLocator": locator,
        "captureMethod": capture_method,
        "captureSpec": capture_spec,
        "rightsStatus": rights_status,
    }


def source_intent(*, intent_id: str, scene_id: str, target_beat_id: str, source_id: str, purpose: str, primary: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
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


def patch_microchip_news_media(scene: dict[str, Any]) -> str:
    beat = scene["visualBeats"][0]
    source_ids = [item for item in beat.get("evidenceSourceIds", []) if isinstance(item, str)]
    if "source-004" not in source_ids:
        source_ids.append("source-004")
    beat["evidenceSourceIds"] = source_ids
    scene_ids = [item for item in scene.get("evidenceSourceIds", []) if isinstance(item, str)]
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
    grammar = beat.get("visualGrammar")
    if not isinstance(grammar, dict):
        raise SystemExit("Scene 6 Beat 1 visualGrammar missing")
    grammar["grammarId"] = "evidence"
    beat["visualGrammarId"] = "evidence"

    # The old event showed a BLS/rate/close card while narration was discussing
    # Microchip results. It is no longer an object in this Beat.
    scene["visualEvents"] = [
        event
        for event in scene.get("visualEvents", [])
        if not (isinstance(event, dict) and event.get("targetId") == "scene-06-card-001")
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


def patch_verified_series(scene: dict[str, Any], receipt: dict[str, Any]) -> None:
    beat = scene["visualBeats"][0]
    rows = qqq_release_window(receipt)
    ids = ["scene-08-qqq-0829", "scene-08-qqq-0830", "scene-08-qqq-0831"]
    labels = ["08:29 ET", "08:30 ET", "08:31 ET"]
    numbers = [
        item for item in scene.get("numbers", [])
        if isinstance(item, dict) and (item.get("numberId") or item.get("key")) not in set(ids)
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
                "時系列整合の証拠 / 因果証明ではない",
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
    grammar = beat.get("visualGrammar")
    if not isinstance(grammar, dict):
        raise SystemExit("Scene 8 visualGrammar missing")
    grammar["grammarId"] = "reaction"
    grammar["transitionRole"] = "major-shift"
    beat["visualGrammarId"] = "reaction"
    beat["transitionRole"] = "major-shift"


def apply(root: Path) -> dict[str, Any]:
    render_path = root / f"render-specs/{DATE}/render_spec.json"
    receipt_path = root / "tests/fixtures/real-day-2026-08-10/collector_wave2_success_receipt.json"
    render = load(render_path)
    receipt = load(receipt_path)
    scenes = scene_map(render)

    microchip_beat = patch_microchip_news_media(scenes[6])
    patch_verified_series(scenes[8], receipt)

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
    selection = {"contractVersion": "1.0.0", "episodeDate": DATE, "selectedPath": "fallback"}

    write(render_path, render)
    write(root / f"working/{DATE}/visual_source_intents.json", intents)
    write(root / f"working/{DATE}/visual_source_selection.json", selection)
    return {
        "status": "pass",
        "episodeDate": DATE,
        "renderSpec": render_path.relative_to(root).as_posix(),
        "visualSourceIntentCount": len(intents["intents"]),
        "selectedPath": "fallback",
        "fallbackReason": "BLS blocks GitHub-hosted HTTP acquisition with 403; Microchip real IR remains preserved on fallback route.",
        "microchipVisualBeatId": microchip_beat,
        "verifiedSeries": {
            "symbol": "QQQ.US",
            "precision": "verified-intraday-series",
            "points": qqq_release_window(receipt),
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
