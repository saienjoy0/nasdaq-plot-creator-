#!/usr/bin/env python3
"""H5-only visual authoring for the 2026-08-10 Information-Gain acceptance path."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

DATE = "2026-08-10"
HERE = Path(__file__).resolve().parent


def mod(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise SystemExit(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return value


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scene(render: dict[str, Any], number: int) -> dict[str, Any]:
    return next(row for row in render["scenes"] if row.get("sceneNumber") == number)


def beat_id(beat: dict[str, Any]) -> str:
    value = beat.get("beatId")
    if not isinstance(value, str) or not value:
        raise SystemExit("beatId missing")
    return value


def visual_beat_id(beat: dict[str, Any]) -> str:
    value = beat.get("visualBeatId") or beat_id(beat)
    if re.fullmatch(r"vb-0[1-9]-[0-9]{2}", value):
        return value
    match = re.fullmatch(r"scene-(0[1-9])-beat-([0-9]{3})", value)
    if match:
        return f"vb-{match.group(1)}-{int(match.group(2)):02d}"
    raise SystemExit(f"unsupported visual beat id: {value}")


def set_grammar(beat: dict[str, Any], grammar_id: str, transition: str) -> None:
    beat["visualGrammar"] = {
        "contractVersion": "1.0.0",
        "grammarId": grammar_id,
        "transitionRole": transition,
        "returnTargetBeatId": None,
    }
    beat["visualGrammarId"] = grammar_id
    beat["transitionRole"] = transition


def sync_override(overrides: dict[str, Any], beat: dict[str, Any], reaction: dict[str, Any] | None = None) -> None:
    grammar = beat.get("visualGrammar")
    if not isinstance(grammar, dict):
        gid = beat.get("visualGrammarId")
        tr = beat.get("transitionRole") or "continuation"
        if not isinstance(gid, str):
            raise SystemExit(f"{beat_id(beat)}: visual grammar missing")
        set_grammar(beat, gid, tr)
        grammar = beat["visualGrammar"]
    override = overrides.setdefault(beat_id(beat), {})
    for key in (
        "screenQuestion", "primaryElement", "viewerTexts", "changeCue", "contentType",
        "visualTemplate", "visualMode", "screenState", "templateVariant",
    ):
        if key in beat:
            override[key] = beat[key]
    override["visualGrammarId"] = grammar["grammarId"]
    override["transitionRole"] = grammar["transitionRole"]
    if reaction is None:
        override.pop("reactionTimelineBinding", None)
    else:
        override["reactionTimelineBinding"] = reaction


def upsert_number(target: dict[str, Any], row: dict[str, Any]) -> None:
    target["numbers"] = [x for x in target.get("numbers", []) if x.get("numberId") != row["numberId"]] + [row]


def series(receipt: dict[str, Any], symbol: str) -> list[dict[str, Any]]:
    row = next(x for x in receipt["series"] if x.get("symbol") == symbol)
    if row.get("precision") != "verified-intraday-series":
        raise SystemExit(f"{symbol}: verified series missing")
    points = row.get("release_window")
    if not isinstance(points, list) or len(points) < 3:
        raise SystemExit(f"{symbol}: release window missing")
    return points[:3]


def release_return(points: list[dict[str, Any]]) -> float:
    return (float(points[1]["close"]) / float(points[0]["close"]) - 1.0) * 100.0


def patch_scene1(render: dict[str, Any], overrides: dict[str, Any]) -> None:
    beat = scene(render, 1)["visualBeats"][1]
    beat.update({
        "screenQuestion": "利上げ観測だけで半導体まで説明できる？",
        "primaryElement": "暫定解：利上げ観測後退 / 未解決：1銘柄の初動",
        "viewerTexts": ["暫定解：利上げ観測後退", "次の検証：8:30 ETの銘柄別初動"],
        "changeCue": "半導体を全部この説明に入れると",
    })
    sync_override(overrides, beat)


def patch_scene6(render: dict[str, Any], overrides: dict[str, Any], reaction_doc: dict[str, Any], receipt: dict[str, Any]) -> dict[str, float]:
    target = scene(render, 6)
    if len(target["visualBeats"]) < 2:
        raise SystemExit("Scene 6 requires two Beats")

    qqq = series(receipt, "QQQ.US")
    ids: list[str] = []
    for index, (label, point) in enumerate(zip(("08:29 ET", "08:30 ET", "08:31 ET"), qqq, strict=True), 1):
        number_id = f"scene-06-qqq-{index:02d}"
        ids.append(number_id)
        value = float(point["close"])
        upsert_number(target, {
            "numberId": number_id, "label": label, "value": str(point["close"]),
            "numericValue": value, "precision": 3, "unit": "",
            "tone": "neutral" if index == 1 else "positive", "comparison": None,
        })
    first = target["visualBeats"][0]
    first.update({
        "contentType": "event-reaction-timeline", "visualTemplate": "event-reaction-timeline",
        "visualMode": "timeline", "screenState": "Chart", "templateVariant": "verified-series",
        "screenQuestion": "BLS 08:30 ET前後、QQQはどう動いた？",
        "primaryElement": "QQQ 実1分足 08:29→08:30→08:31",
        "viewerTexts": ["QQQ 実1分足", "08:29 719.16 → 08:30 720.23 → 08:31 720.531"],
        "changeCue": "8時30分ETの1分足", "objectIds": ids,
        "evidenceSourceIds": ["source-002", "source-005"], "sequencePolicy": "object-order-fallback",
        "templateConfig": {
            "variant": "verified-series", "comparisonBasis": "BLS 08:30 ET発表前後",
            "dataBasis": "Longbridge verified 1-minute Kline minute-close", "laneLabels": [],
            "nodeOrder": [], "outcomeNodeId": None,
            "reactionTimeline": {"precision": "verified-intraday-series", "eventOrderIds": ids, "seriesObjectIds": ids},
        },
    })
    set_grammar(first, "reaction", "major-shift")
    binding = {
        "visualBeatId": visual_beat_id(first), "visualTemplate": "event-reaction-timeline",
        "templateVariant": "verified-series", "precision": "verified-intraday-series",
        "eventOrderIds": ids, "seriesObjectIds": ids,
        "evidenceBasis": "Longbridge verified 1-minute Kline around BLS 08:30 ET. Timing alignment only; not causal proof.",
    }
    sync_override(overrides, first, binding)
    rows = reaction_doc.get("bindings")
    if not isinstance(rows, list):
        raise SystemExit("reaction bindings array missing")
    aliases = {visual_beat_id(first), beat_id(first)}
    rows[:] = [row for row in rows if not (isinstance(row, dict) and row.get("visualBeatId") in aliases)]
    rows.append(binding)

    labels = {"QQQ.US": "QQQ", "SOXX.US": "SOXX", "NVDA.US": "NVIDIA", "MCHP.US": "MCHP"}
    returns: dict[str, float] = {}
    object_ids: list[str] = []
    for symbol in labels:
        label = labels[symbol]
        value = release_return(series(receipt, symbol))
        returns[label] = value
        number_id = f"scene-06-release-{label.lower()}"
        object_ids.append(number_id)
        upsert_number(target, {
            "numberId": number_id, "label": label, "value": f"{value:+.3f}%",
            "numericValue": round(value, 6), "precision": 3, "unit": "%",
            "tone": "positive" if value > 0.01 else "negative" if value < -0.01 else "neutral",
            "comparison": "08:29→08:30 ET",
        })
    second = target["visualBeats"][1]
    second.update({
        "contentType": "index-return-bars", "visualTemplate": "index-return-bars",
        "visualMode": "stock-comparison", "screenState": "Chart", "templateVariant": "zero-baseline",
        "screenQuestion": "同じ1分で4銘柄は同じ反応だった？",
        "primaryElement": "08:29→08:30 ET 1分リターン",
        "viewerTexts": ["QQQ / SOXX / NVIDIA は上向き", "MCHP は -0.025%でほぼ横ばい", "1分足だけでは因果証明しない"],
        "changeCue": "ところがMicrochipは79.58から79.56", "objectIds": object_ids,
        "evidenceSourceIds": ["source-005"], "sequencePolicy": "object-order-fallback",
        "templateConfig": {"variant": "zero-baseline", "comparisonBasis": "08:29→08:30 ETの1分リターン", "dataBasis": "Longbridge verified 1-minute Kline minute-close", "laneLabels": [], "nodeOrder": [], "outcomeNodeId": None},
    })
    set_grammar(second, "reaction", "continuation")
    sync_override(overrides, second)
    return returns


def patch_scene7(render: dict[str, Any], overrides: dict[str, Any]) -> str:
    target = scene(render, 7)
    if len(target["visualBeats"]) < 2:
        raise SystemExit("Scene 7 requires two Beats")
    first = target["visualBeats"][0]
    first.update({
        "contentType": "news-media", "visualTemplate": "news-media", "visualMode": "news-media",
        "screenState": "News", "templateVariant": "default", "screenQuestion": "Microchipは何を発表した？",
        "primaryElement": "Microchip Q1 FY27 公式IR",
        "viewerTexts": ["Microchip Q1 FY27 公式IR", "売上 14.85億ドル / 非GAAP EPS 0.76ドル", "次四半期売上 15.89億〜16.18億ドル"],
        "changeCue": "Microchipには会社固有の材料", "objectIds": [], "evidenceSourceIds": ["source-004"],
        "sequencePolicy": "static", "templateConfig": {"variant": "default", "comparisonBasis": None, "dataBasis": "Microchip Technology official Q1 FY27 investor-relations release", "laneLabels": [], "nodeOrder": [], "outcomeNodeId": None},
    })
    set_grammar(first, "evidence", "major-shift")
    sync_override(overrides, first)

    object_ids: list[str] = []
    for label, value in (("MCHP", 13.89), ("AMD", -1.21), ("Alphabet", -0.96), ("Microsoft", 0.03)):
        number_id = f"scene-07-daily-{label.lower()}"
        object_ids.append(number_id)
        upsert_number(target, {
            "numberId": number_id, "label": label, "value": f"{value:+.2f}%",
            "numericValue": value, "precision": 2, "unit": "%",
            "tone": "positive" if value > 0.01 else "negative" if value < -0.01 else "neutral",
            "comparison": "8/7通常取引",
        })
    second = target["visualBeats"][1]
    second.update({
        "contentType": "diverging-stock-bars", "visualTemplate": "diverging-stock-bars",
        "visualMode": "stock-comparison", "screenState": "Chart", "templateVariant": "center-zero",
        "screenQuestion": "同じテックでも終日は同じ方向だった？",
        "primaryElement": "MCHP +13.89% / AMD・Alphabetは下落",
        "viewerTexts": ["MCHP +13.89%", "AMD -1.21% / Alphabet -0.96%", "Microsoft +0.03%"],
        "changeCue": "一方でAMDは一・二一パーセント下落", "objectIds": object_ids,
        "evidenceSourceIds": ["source-001", "source-004"], "sequencePolicy": "object-order-fallback",
        "templateConfig": {"variant": "center-zero", "comparisonBasis": "8月7日通常取引終値", "dataBasis": "verified close data + Microchip official IR", "laneLabels": [], "nodeOrder": [], "outcomeNodeId": None},
    })
    set_grammar(second, "comparison", "continuation")
    sync_override(overrides, second)
    return visual_beat_id(first)


def patch_scene8(render: dict[str, Any], overrides: dict[str, Any]) -> None:
    target = scene(render, 8)
    if len(target["visualBeats"]) < 2:
        raise SystemExit("Scene 8 requires two Beats")
    first, second = target["visualBeats"][:2]
    first.update({
        "contentType": "verification-matrix", "visualTemplate": "verification-matrix",
        "visualMode": "verification-points", "screenState": "Data", "templateVariant": "strengthen-vs-weaken",
        "screenQuestion": "マクロ仮説を強める材料と弱める材料は？",
        "primaryElement": "利上げ観測後退を中心に境界を残す",
        "viewerTexts": ["強める｜雇用下振れ→利上げ観測後退", "強める｜QQQ・SOXX・NVIDIA初動↑", "弱める｜1分足だけでは因果証明できない", "弱める｜成長不安・AMD/Alphabet下落"],
        "changeCue": "最初の矛盾に戻ります", "objectIds": [], "sequencePolicy": "static",
        "templateConfig": {"variant": "strengthen-vs-weaken", "comparisonBasis": "中心仮説の支持と反対材料", "dataBasis": "approved causal dossier + verified timing evidence", "laneLabels": ["強める", "弱める"], "nodeOrder": [], "outcomeNodeId": None},
    })
    set_grammar(first, "verification", "major-shift")
    sync_override(overrides, first)
    second.update({
        "contentType": "verification-checklist", "visualTemplate": "verification-checklist",
        "visualMode": "verification-points", "screenState": "Data", "templateVariant": "default",
        "screenQuestion": "最後に何を残す？", "primaryElement": "複数エンジンが同じ指数方向へ重なった",
        "viewerTexts": ["主役候補｜雇用→利上げ観測後退", "別エンジン｜Microchip決算", "増幅｜原油・利回り低下", "結論｜違う理由の上昇が同じ方向へ重なった"],
        "changeCue": "原油や利回り低下は増幅要因", "objectIds": [], "sequencePolicy": "static",
        "templateConfig": {"variant": "default", "comparisonBasis": None, "dataBasis": "approved causal dossier", "laneLabels": [], "nodeOrder": [], "outcomeNodeId": None},
    })
    set_grammar(second, "verification", "continuation")
    sync_override(overrides, second)


def main_apply(root: Path) -> dict[str, Any]:
    legacy = mod(HERE / "apply_visual_evidence_first.py", "h5_legacy_visual")
    sync = mod(HERE / "sync_visual_evidence_bindings.py", "h5_legacy_sync")
    render_path = root / f"render-specs/{DATE}/render_spec.json"
    bindings_path = root / f"working/{DATE}/story-engine/story_production_bindings.json"
    reaction_path = root / f"working/{DATE}/reaction_timeline_bindings.json"
    package_path = root / f"episodes/{DATE}/episode_package_public_{DATE}.md"
    receipt = load(root / "tests/fixtures/real-day-2026-08-10/collector_wave2_success_receipt.json")
    render, bindings, reaction_doc = load(render_path), load(bindings_path), load(reaction_path)
    overrides = bindings.setdefault("beat_overrides", {})

    patch_scene1(render, overrides)
    sync.patch_scene5_support_forces(render, overrides)
    legacy.patch_scene4_scorecard_analogy(scene(render, 4), overrides)
    returns = patch_scene6(render, overrides, reaction_doc, receipt)
    microchip_beat = patch_scene7(render, overrides)
    patch_scene8(render, overrides)

    bls_beat = visual_beat_id(scene(render, 2)["visualBeats"][0])
    intents = {
        "contractVersion": "1.0.0", "episodeDate": DATE, "qualityPolicy": "evidence-first-v1",
        "intents": [
            legacy.source_intent(
                intent_id="vsi-20260810-bls-employment", scene_id="scene-02", target_beat_id=bls_beat,
                source_id="source-002", purpose="Show the actual BLS July 2026 Employment Situation; keep the approved source-labelled fallback if BLS blocks runner acquisition.",
                primary=legacy.visual_candidate(candidate_id="vsp-20260810-bls-primary", asset_id="daily-bls-employment-july-2026", source_kind="official-url", locator={"url": legacy.BLS_URL}, capture_method="pdf-page-render", rights_status="cleared", capture_spec={"pageNumber": 1}),
                fallback=legacy.visual_candidate(candidate_id="vsp-20260810-bls-fallback", asset_id="background_scene_news", source_kind="existing-asset", locator={"assetId": "background_scene_news"}, capture_method="registry-reference", rights_status="cleared", capture_spec=None),
            ),
            legacy.source_intent(
                intent_id="vsi-20260810-microchip-ir", scene_id="scene-07", target_beat_id=microchip_beat,
                source_id="source-004", purpose="Show the actual Microchip Q1 FY27 IR while revised Scene 7 resolves the company-specific engine.",
                primary=legacy.visual_candidate(candidate_id="vsp-20260810-microchip-primary", asset_id=legacy.MICROCHIP_PRIMARY_ASSET_ID, source_kind="official-url", locator={"url": legacy.MICROCHIP_URL}, capture_method="webpage-screenshot", rights_status="cleared", capture_spec={"viewport": {"width": 1440, "height": 900}}),
                fallback=legacy.visual_candidate(candidate_id="vsp-20260810-microchip-fallback", asset_id=legacy.MICROCHIP_SECONDARY_ASSET_ID, source_kind="official-url", locator={"url": legacy.MICROCHIP_URL}, capture_method="webpage-screenshot", rights_status="cleared", capture_spec={"viewport": {"width": 1440, "height": 900}}),
            ),
        ],
    }
    dump(render_path, render)
    dump(bindings_path, bindings)
    dump(reaction_path, reaction_doc)
    dump(root / f"working/{DATE}/visual_source_intents.json", intents)
    dump(root / f"working/{DATE}/visual_source_selection.json", {"contractVersion": "1.0.0", "episodeDate": DATE, "selectedPath": "fallback"})
    caption_count = sync.sync_caption_projection(render, package_path)
    return {"status": "pass", "episodeDate": DATE, "storyMeaningChanged": False, "releaseReturns": returns, "visualSourceIntentCount": 2, "selectedPath": "fallback", "captionProjectionCount": caption_count}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = main_apply(args.repo_root.resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
