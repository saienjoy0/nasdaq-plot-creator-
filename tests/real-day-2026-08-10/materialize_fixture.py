#!/usr/bin/env python3
"""Materialize the frozen 2026-08-10 regression authoring fixture.

TEST ONLY. This script is not part of Daily Production. It decodes the immutable base
acceptance payload from a pinned historical commit, replaces the stale unavailable
wave-2 fixture with a compact normalized receipt of the verified successful Collector
run, and freezes the corrected ChatGPT-authored Research/Story/Visual inputs.

No runtime production correction is performed after this fixture step. The resulting
workspace must pass the normal Causal Research validator, Story Engine, H2 Pre-TTS
Gate, generic episode assembly, H3 Final Production, and immutable Handoff unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

DATE = "2026-08-10"
RUN_ID = 31357986916

SCENE8_CHUNK1 = (
    "最後に、時系列まで確認します。8時30分ETの発表の1分前から発表分へ、NASDAQの代理として見るQQQは"
    "719.16から720.23、SOXXは541.06から542.40、NVIDIAは219.95から220.31へ上向きました。"
    "だから、弱い雇用から利上げ観測後退、そしてテック買いという市場解釈は、引けだけでなく発表時刻の初動とも整合します。"
    "ただし、1分足は原因そのものを証明しません。MCHPは同じ1分で79.58から79.56とほぼ横ばいでした。"
    "Microchipの大幅高は会社固有材料を別の増幅要因として分ける方が自然です。"
)
SCENE8_CHUNK2 = (
    "僕の結論は中程度の確信で、雇用下振れから利上げリスク低下が主役候補。"
    "Microchip好決算と原油・利回り低下が増幅要因。成長不安と個別の下落銘柄が反対材料です。"
    "悪材料が消えた夜ではなく、どの採点表が優先されたかが変わった夜でした。"
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return value


def load_acceptance_decoder(path: Path):
    spec = importlib.util.spec_from_file_location("h4_acceptance_fixture_decoder", path)
    if not spec or not spec.loader:
        raise SystemExit(f"cannot import base fixture decoder: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _compact_wave2(root: Path) -> str:
    receipt_path = root / "tests/fixtures/real-day-2026-08-10/collector_wave2_success_receipt.json"
    receipt = load(receipt_path)
    if (
        receipt.get("collector_run_id") != RUN_ID
        or receipt.get("status") != "success"
        or receipt.get("acquisition_status") != "success"
    ):
        raise SystemExit("verified Collector wave-2 receipt is not successful")
    series = receipt.get("series")
    if not isinstance(series, list) or len(series) != 4:
        raise SystemExit("verified Collector receipt must contain four minute series")
    expected = {"QQQ.US", "SOXX.US", "MCHP.US", "NVDA.US"}
    if {item.get("symbol") for item in series} != expected:
        raise SystemExit("verified Collector receipt symbol set drift")
    for item in series:
        if (
            item.get("record_count") != 1000
            or item.get("precision") != "verified-intraday-series"
            or item.get("price_basis") != "minute-close"
            or item.get("provider_surface") != "kline-history-fallback"
        ):
            raise SystemExit(f"verified Collector series metadata drift: {item.get('symbol')}")

    research = root / f"research/{DATE}"
    evidence_dir = research / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    request_path = research / "research_acquisition_request_w02.json"
    if sha(request_path) != receipt["request_sha256"]:
        raise SystemExit("base wave-2 request no longer matches verified Collector request")

    result_rows = []
    evidence_refs = []
    request_by_symbol = {
        "QQQ.US": "RA-W2-001",
        "SOXX.US": "RA-W2-002",
        "MCHP.US": "RA-W2-003",
        "NVDA.US": "RA-W2-004",
    }
    for item in series:
        request_id = request_by_symbol[item["symbol"]]
        filename = f"{request_id}_intraday_series.json"
        evidence = {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "requestId": request_id,
            "symbol": item["symbol"],
            "recordCount": 1000,
            "precision": item["precision"],
            "priceBasis": item["price_basis"],
            "timezone": item["timezone"],
            "providerSurface": item["provider_surface"],
            "releaseWindow": item["release_window"],
            "originalCollectorSha256": item["collector_sha256"],
            "normalization": "H4 compact regression fixture; full raw series remains immutable in Collector run 31357986916",
        }
        target = evidence_dir / filename
        digest = write_json(target, evidence)
        evidence_refs.append(
            {
                "requestId": request_id,
                "path": target.relative_to(root).as_posix(),
                "sha256": digest,
            }
        )
        result_rows.append(
            {
                "outputPath": target.relative_to(root).as_posix(),
                "provider": "Longbridge",
                "reason": "",
                "recordCount": 1000,
                "requestId": request_id,
                "sha256": digest,
                "status": "success",
            }
        )

    ir = receipt["source_archive"]
    ir_path = evidence_dir / "RA-W2-005_exact_url_archive.json"
    ir_digest = write_json(
        ir_path,
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "requestId": "RA-W2-005",
            "status": "success",
            "recordCount": 1,
            "originalCollectorSha256": ir["collector_sha256"],
            "source": "Microchip official IR exact-url archive",
            "normalization": "H4 compact regression fixture; original archive remains immutable in Collector run 31357986916",
        },
    )
    evidence_refs.append(
        {
            "requestId": "RA-W2-005",
            "path": ir_path.relative_to(root).as_posix(),
            "sha256": ir_digest,
        }
    )
    result_rows.append(
        {
            "outputPath": ir_path.relative_to(root).as_posix(),
            "provider": "Raw Archive",
            "reason": "",
            "recordCount": 1,
            "requestId": "RA-W2-005",
            "sha256": ir_digest,
            "status": "success",
        }
    )
    result_path = research / "research_acquisition_result_w02.json"
    result_sha = write_json(
        result_path,
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "requestSha256": sha(request_path),
            "results": result_rows,
            "status": "success",
            "wave": 2,
            "fixtureSource": {
                "collectorRunId": RUN_ID,
                "originalRequestSha256": receipt["request_sha256"],
                "originalResultSha256": receipt["result_sha256"],
            },
        },
    )

    supplement_path = research / "research_evidence_supplement_manifest.json"
    supplement = load(supplement_path)
    waves = supplement.get("waves")
    if not isinstance(waves, list) or [item.get("wave") for item in waves] != [1, 2]:
        raise SystemExit("unexpected base supplement wave shape")
    waves[1] = {
        "wave": 2,
        "collectorRunId": RUN_ID,
        "request": {
            "path": request_path.relative_to(root).as_posix(),
            "sha256": sha(request_path),
        },
        "result": {
            "path": result_path.relative_to(root).as_posix(),
            "sha256": result_sha,
        },
        "evidenceFiles": sorted(evidence_refs, key=lambda item: item["requestId"]),
    }
    return write_json(supplement_path, supplement)


def timing_evidence(
    evidence_id: str,
    symbol: str,
    filename: str,
    claim: str,
    limitation: str,
) -> dict[str, Any]:
    return {
        "claim": claim,
        "confidence": "high",
        "directness": "direct",
        "event_timestamp": "2026-08-07T08:30:00-04:00",
        "evidence_class": "fact",
        "evidence_id": evidence_id,
        "independence_group": f"longbridge-wave2-{symbol.lower()}",
        "limitations": limitation,
        "publication_timestamp": None,
        "source_issuer_or_publisher": "Longbridge / NASDAQ Cafe Collector",
        "source_reference": f"research/{DATE}/evidence/{filename}",
        "source_tier": "tier_1",
        "source_title": f"Longbridge verified 1-minute historical series — {symbol}",
        "timezone": "America/New_York",
    }


def _patch_dossier(root: Path, supplement_sha: str) -> dict[str, Any]:
    path = root / f"research/{DATE}/causal_research_dossier_{DATE}.json"
    doc = load(path)
    doc["session"] = {
        "information_cutoff": "2026-08-10T12:15:00+09:00",
        "market_date": "2026-08-07",
        "timezone": "Asia/Tokyo",
    }
    matches = 0
    for item in doc.get("input_provenance", []):
        if item.get("path_or_reference") == f"research/{DATE}/research_evidence_supplement_manifest.json":
            item["version_or_hash"] = supplement_sha
            matches += 1
    if matches != 1:
        raise SystemExit(f"unexpected supplement provenance count: {matches}")

    q4 = next(item for item in doc["research_questions"] if item["id"] == "Q-04")
    q4.update(
        {
            "status": "answered",
            "answer_summary": "8:30 ETの発表分で、QQQは719.16→720.23、SOXXは541.06→542.40へ上向いた。NVIDIAも219.95→220.31、MCHPは79.58→79.56とほぼ横ばいだった。",
            "evidence_ids": ["E-008", "E-010", "E-011", "E-012"],
        }
    )
    existing = {item["evidence_id"]: item for item in doc["evidence"]}
    existing["E-008"] = timing_evidence(
        "E-008",
        "QQQ.US",
        "RA-W2-001_intraday_series.json",
        "2026年8月7日08:29→08:30 ETでQQQの1分足終値は719.16から720.23へ上昇し、08:31は720.531だった。",
        "Longbridge historical intradayの0件時に公式1分Kline historyへフォールバックしたminute-close。NASDAQ全体の直接指数ではなくQQQを代理として使い、雇用統計が上昇の原因だったことを単独では証明しない。",
    )
    existing["E-010"] = timing_evidence(
        "E-010",
        "SOXX.US",
        "RA-W2-002_intraday_series.json",
        "2026年8月7日08:29→08:30 ETでSOXXの1分足終値は541.06から542.40へ上昇し、08:31は544.20だった。",
        "1分Klineのminute-closeによる時系列証拠。半導体上昇の原因や各要因の寄与度を単独では証明しない。",
    )
    existing["E-011"] = timing_evidence(
        "E-011",
        "NVDA.US",
        "RA-W2-004_intraday_series.json",
        "2026年8月7日08:29→08:30 ETでNVIDIAの1分足終値は219.95から220.31へ上昇し、08:31は220.50だった。",
        "1分Klineのminute-closeによる比較証拠。NVIDIA固有材料とマクロ要因の寄与を分離しない。",
    )
    existing["E-012"] = timing_evidence(
        "E-012",
        "MCHP.US",
        "RA-W2-003_intraday_series.json",
        "2026年8月7日08:29→08:30 ETでMCHPの1分足終値は79.58から79.56へ小幅低下し、08:31は79.70だった。",
        "1分Klineのminute-close。MCHPが同じ発表分に広いマクロ反応を示したとは言えず、会社固有材料を別の増幅要因として分けるための反対・比較証拠。",
    )
    ordered = []
    inserted = False
    for item in doc["evidence"]:
        eid = item["evidence_id"]
        if eid in {"E-010", "E-011", "E-012"}:
            continue
        ordered.append(existing[eid])
        if eid == "E-008":
            ordered.extend([existing["E-010"], existing["E-011"], existing["E-012"]])
            inserted = True
    if not inserted:
        ordered.extend([existing["E-008"], existing["E-010"], existing["E-011"], existing["E-012"]])
    doc["evidence"] = ordered

    for item in doc["timeline"]:
        if item["id"] == "T-04":
            item.update(
                {
                    "event": "8:30 ETの発表分でQQQ・SOXX・NVIDIAは上向き、MCHPはほぼ横ばい。発表時刻との初動整合は確認できたが、1分足だけで因果は証明しない。",
                    "evidence_ids": ["E-008", "E-010", "E-011", "E-012"],
                    "precision": "minute",
                    "timestamp_or_window": "2026-08-07 08:29-08:31 ET",
                    "timezone": "America/New_York",
                }
            )
    edge2 = next(item for item in doc["causal_edges"] if item["id"] == "EDGE-02")
    edge2.update(
        {
            "evidence_ids": ["E-003", "E-004", "E-008", "E-010", "E-011"],
            "timing_alignment": "strong",
            "confidence": "medium",
            "mechanism": "金利上昇リスクの後退は長期成長期待を持つテックのバリュエーション逆風を和らげる。Reutersの市場解釈に加え、8:30 ETの発表分でQQQ・SOXX・NVIDIAが上向き、発表時刻との初動整合も確認できた。",
            "strongest_alternative": "1分足は因果を証明せず、原油・利回り低下や好決算も同日に効いているため、雇用だけの寄与度は分離できない。",
        }
    )
    doc["factor_roles"]["unresolved"] = ["各要因の寄与度"]
    alt3 = next(item for item in doc["alternative_hypotheses"] if item["id"] == "ALT-03")
    alt3.update(
        {
            "hypothesis": "8:30 ETの雇用発表と同じ1分にQQQ・SOXX・NVIDIAが上向いた。",
            "status": "credible",
            "supporting_evidence_ids": ["E-008", "E-010", "E-011"],
            "weakening_evidence_ids": ["E-012"],
        }
    )
    for index, item in enumerate(doc["contrary_evidence"]):
        if "分足" in item["statement"]:
            doc["contrary_evidence"][index] = {
                "effect_on_confidence": "material",
                "evidence_ids": ["E-008", "E-010", "E-011", "E-012"],
                "statement": "8:30 ETの1分足はQQQ・SOXX・NVIDIAで上向いたが、1分足だけでは雇用統計が原因と証明できず、MCHPは同じ1分ではほぼ横ばいだった。",
            }
            break
    handoff = doc["editorial_handoff"]
    handoff["causal_spine"] = "雇用予想+8万人→実際-2.3万人→利上げ観測後退→8:30 ETにQQQ・SOXX・NVIDIAが上向き→大型テックへの金利逆風緩和→Microchip好決算と原油・利回り低下が増幅→NASDAQ +1.30%、ただし1分足は因果証明ではなく個別差を残す"
    handoff["exclude_from_narration"] = [
        "8:30 ETの上昇だけで雇用統計が終日上昇の原因と証明できたという断定",
        "MCHPが8:30 ET発表分でQQQ・SOXX・NVIDIAと同じマクロ反応をしたという断定",
        "悪い経済指標なら必ず株が上がるという一般化",
        "Microchip一社がNASDAQを上げたという断定",
        "利下げが決まったという表現",
    ]
    handoff["unresolved_questions"] = ["雇用・原油・決算それぞれの厳密な寄与度"]
    doc["validation"] = {
        "status": "pass",
        "errors": [],
        "warnings": ["1分足は発表時刻との時系列整合を確認する証拠であり、因果や寄与度の単独証明ではない。"],
    }
    write_json(path, doc)
    return doc


def _patch_story(root: Path, dossier: dict[str, Any]) -> None:
    plan_path = root / f"working/{DATE}/story-engine/templates/story_plan.template.json"
    plan = load(plan_path)
    plan["headline_beyond_discovery"] = dossier["editorial_handoff"]["headline_beyond_discovery"]
    plan["story_spine"] = dossier["editorial_handoff"]["causal_spine"] + "。"
    plan["closing_reframe"]["text"] = "弱い雇用そのものが好材料なのではなく、利上げリスク低下が主役候補。8:30 ETのQQQ・SOXX・NVIDIAの初動も整合したが、1分足は因果証明ではなく、Microchipや原油・利回りは増幅要因として分ける。"
    for angle in plan["angle_candidates"]:
        if angle["id"] == "angle-01":
            angle["counterevidence_ids"] = ["E-007", "E-009", "E-012"]
        if angle["id"] == "angle-02":
            angle["counterevidence_ids"] = ["E-002", "E-007", "E-012"]
            angle["evidence_ids"] = ["E-002", "E-003", "E-004", "E-005", "E-008", "E-010", "E-011", "E-009"]
            angle["story_spine"] = plan["story_spine"]
            angle["closing_reframe"] = plan["closing_reframe"]["text"]
    for scene in plan["scenes"]:
        if scene["scene_id"] == "scene-07":
            scene["continuation_reason"] = "発表時刻の初動と個別差まで含めて、結論の境界を最後に引く。"
        elif scene["scene_id"] == "scene-08":
            scene["new_evidence_ids"] = ["E-003", "E-004", "E-008", "E-010", "E-011", "E-012", "E-009"]
            scene["new_meaning"] = "8:30 ETの発表分でQQQ・SOXX・NVIDIAが上向いたため時系列整合は強まった。ただしMCHPは同じ1分でほぼ横ばいで、1分足だけでは因果を証明しない。"
            scene["viewer_belief_after"] = "主因候補・増幅要因・反対材料を、発表時刻の初動まで含めて境界付きで理解できる。"
    selected = next(item for item in plan["angle_candidates"] if item["id"] == plan["selected_angle_id"])
    selected["central_question"] = plan["central_question"]
    selected["opening_promise"] = plan["opening_promise"]
    selected["midpoint_turn_claim"] = plan["midpoint_turn"]["claim"]
    selected["closing_reframe"] = plan["closing_reframe"]["text"]
    selected["story_spine"] = plan["story_spine"]
    write_json(plan_path, plan)

    script_path = root / f"working/{DATE}/story-engine/templates/story_script.template.json"
    script = load(script_path)
    scene8 = next(scene for scene in script["scenes"] if scene["scene_id"] == "scene-08")
    scene8["evidence_ids"] = ["E-003", "E-004", "E-008", "E-010", "E-011", "E-012", "E-009"]
    scene8["narration"] = SCENE8_CHUNK1 + SCENE8_CHUNK2
    claims = {claim["claim_id"]: claim for claim in scene8["causal_claims"]}
    claims["claim-07"].update(
        {
            "claim_type": "fact",
            "confidence": "high",
            "evidence_ids": ["E-008", "E-010", "E-011", "E-012"],
            "scope": "nasdaq_support",
            "statement": "8:30 ETの発表分でQQQ・SOXX・NVIDIAは上向き、MCHPはほぼ横ばいだった。",
        }
    )
    claims["claim-08"]["evidence_ids"] = ["E-003", "E-004", "E-005", "E-006", "E-008", "E-010", "E-011", "E-012", "E-009"]
    claims["claim-08"]["statement"] = "雇用下振れ→利上げ観測後退を主因候補、Microchip・原油・利回りを増幅要因とする整理は、発表時刻の初動とも整合するが、1分足だけで因果は証明しない。"
    write_json(script_path, script)

    review_path = root / f"working/{DATE}/story-engine/templates/creative_review.template.json"
    review = load(review_path)
    review["round"] = max(int(review.get("round", 1)), 4)
    review["verdict"] = "pass"
    review["findings"] = []
    review["immediate_failures"] = []
    write_json(review_path, review)


def _set_grammar(beat: dict[str, Any], grammar_id: str) -> None:
    grammar = beat.get("visualGrammar")
    if not isinstance(grammar, dict):
        raise SystemExit(f"missing visualGrammar: {beat.get('beatId')}")
    grammar["grammarId"] = grammar_id


def _patch_visual_authoring(root: Path) -> None:
    render_path = root / f"render-specs/{DATE}/render_spec.json"
    render = load(render_path)
    scenes = {int(scene["sceneNumber"]): scene for scene in render["scenes"]}
    scenes[2]["causalScope"] = "nasdaq"
    scenes[3]["causalScope"] = "nasdaq"
    scenes[5]["causalScope"] = "multiple"

    def beat(scene_number: int, index: int) -> dict[str, Any]:
        return scenes[scene_number]["visualBeats"][index]

    b = beat(2, 1)
    b["visualTemplate"] = "focus-matrix"
    b["templateVariant"] = "default"
    b["templateConfig"]["variant"] = "default"
    _set_grammar(b, "comparison")

    b = beat(3, 0)
    b["visualTemplate"] = "focus-matrix"
    b["templateVariant"] = "default"
    b["templateConfig"]["variant"] = "default"
    _set_grammar(b, "evidence")
    b = beat(3, 1)
    b["visualTemplate"] = "metric-comparison-board"
    b["templateVariant"] = "default"
    b["templateConfig"]["variant"] = "default"
    _set_grammar(b, "evidence")

    s4 = scenes[4]
    b1 = beat(4, 0)
    b1["visualTemplate"] = "expected-actual-gap-flow"
    b1["templateVariant"] = "default"
    b1["templateConfig"]["variant"] = "default"
    _set_grammar(b1, "gap")
    b1["viewerTexts"] = ["Expected +8万人", "Actual -2.3万人", "Gap -10.3万人"]
    b1["screenQuestion"] = "Expected / Actual / Gapは？"
    b1["primaryElement"] = "Expected → Actual → Gap"
    b1["changeCue"] = "Expected +8万人"
    s4["cards"][0].update({"label": "Expected", "text": "+8万人"})
    s4["cards"][1].update({"label": "Actual", "text": "-2.3万人"})
    b2 = beat(4, 1)
    b2["visualTemplate"] = "text-focus"
    b2["templateVariant"] = "default"
    b2["templateConfig"]["variant"] = "default"
    _set_grammar(b2, "bridge-text")
    b2["objectIds"] = []
    b2["viewerTexts"] = ["利上げ確率 約44%", "前日55% / 1週前67%"]
    b2["screenQuestion"] = "市場の採点表はどう変わった？"
    b2["primaryElement"] = "利上げ観測 67% → 55% → 44%"
    b2["changeCue"] = "利上げ確率 約44%"

    b = beat(5, 2)
    b["visualTemplate"] = "text-focus"
    b["templateVariant"] = "default"
    b["templateConfig"]["variant"] = "default"
    _set_grammar(b, "bridge-text")

    b = beat(6, 1)
    _set_grammar(b, "evidence")

    b = beat(7, 1)
    b["visualTemplate"] = "focus-matrix"
    b["templateVariant"] = "default"
    b["templateConfig"]["variant"] = "default"
    _set_grammar(b, "comparison")

    s8 = scenes[8]
    s8["sourceLabel"] = "BLS / Reuters / Longbridge 1分Kline / Microchip IR"
    s8["uncertainty"] = "1分足は発表時刻との初動整合を確認する証拠であり、雇用統計が終日上昇の原因だったことや各要因の寄与度を単独では証明しない。MCHPは同じ発表分でほぼ横ばいだったため、会社固有材料を別の増幅要因として扱う。"
    s8["timelineBasis"] = "verified-series-plus-official-time-plus-close"
    s8["purpose"] = "発表時刻の実分足と個別差を残して、安全な結論の境界を示す"
    s8["performanceIntent"] = "結論を曖昧にせず、時系列で確認できたことと因果として断定しないことを分ける"
    s8["evidenceSourceIds"] = ["source-003", "source-004", "source-005"]
    s8["cards"][0].update(
        {
            "label": "8:30 ETの実分足",
            "text": "QQQ 719.16→720.23 / SOXX 541.06→542.40 / NVDA 219.95→220.31",
            "sourceId": "source-003",
        }
    )
    s8["cards"][1].update(
        {
            "label": "境界",
            "text": "1分足は因果証明ではない / MCHP 79.58→79.56",
            "sourceId": "source-005",
        }
    )
    b1 = beat(8, 0)
    b1["objectIds"] = ["scene-08-card-001", "scene-08-card-002"]
    b1["viewerTexts"] = [
        "8:30 ET：QQQ・SOXX・NVDAは上向き",
        "MCHPは同じ1分でほぼ横ばい",
        "1分足だけで因果は証明しない",
    ]
    b1["screenQuestion"] = "発表時刻の初動は市場解釈と整合した？"
    b1["primaryElement"] = "8:30 ETの実分足と因果の境界"
    b1["changeCue"] = "8:30 ET：QQQ・SOXX・NVDAは上向き"
    b1["evidenceSourceIds"] = ["source-003", "source-004", "source-005"]
    b2 = beat(8, 1)
    b2["viewerTexts"] = [
        "言える：初動は金利解釈と整合",
        "言わない：1分足だけで終日上昇の原因を断定",
        "分ける：MCHPは会社固有の増幅要因",
    ]
    b2["screenQuestion"] = "どこまでを安全な結論にするか"
    b2["primaryElement"] = "主因候補・増幅要因・反対材料の境界"
    b2["changeCue"] = "言える：初動は金利解釈と整合"
    b2["evidenceSourceIds"] = ["source-003", "source-004", "source-005"]
    write_json(render_path, render)

    bindings_path = root / f"working/{DATE}/story-engine/story_production_bindings.json"
    bindings = load(bindings_path)
    bindings.setdefault("scene_overrides", {}).update(
        {
            "scene-08": {
                "purpose": s8["purpose"],
                "performanceIntent": s8["performanceIntent"],
            }
        }
    )
    overrides = bindings.setdefault("beat_overrides", {})
    for scene_number, beat_index in ((2, 1), (3, 0), (3, 1), (4, 0), (4, 1), (5, 2), (6, 1), (7, 1), (8, 0), (8, 1)):
        authored = beat(scene_number, beat_index)
        overrides[authored["beatId"]] = {
            "screenQuestion": authored.get("screenQuestion"),
            "primaryElement": authored.get("primaryElement"),
            "viewerTexts": authored.get("viewerTexts", []),
            "changeCue": authored.get("changeCue"),
            "contentType": authored.get("contentType"),
            "visualTemplate": authored.get("visualTemplate"),
            "visualMode": authored.get("visualMode"),
            "screenState": authored.get("screenState"),
            "templateVariant": authored.get("templateConfig", {}).get("variant", authored.get("templateVariant")),
            "visualGrammarId": authored["visualGrammar"]["grammarId"],
            "transitionRole": authored["visualGrammar"]["transitionRole"],
        }
    write_json(bindings_path, bindings)


def _patch_public_markdown(root: Path) -> None:
    path = root / f"episodes/{DATE}/episode_package_public_{DATE}.md"
    text = path.read_text(encoding="utf-8")
    replacements = {
        "- 目的：分足欠損と代替要因を残して安全な結論の境界を示す": "- 目的：発表時刻の実分足と個別差を残して、安全な結論の境界を示す",
        "- 狐の演技意図：結論を曖昧にせず、未確認だけをはっきり切り離す": "- 狐の演技意図：結論を曖昧にせず、時系列で確認できたことと因果として断定しないことを分ける",
        "- 前後の接続文：最後に分足欠損と代替要因まで残して、結論の境界を引きます。": "- 前後の接続文：最後に発表時刻の実分足と個別差まで残して、結論の境界を引きます。",
        "  - 入力構造：言える：利上げ観測後退 / 増幅：MCHP・原油 / 未確認：8:30 ET直後の分足": "  - 入力構造：8:30 ETの実分足 / MCHPの逆方向初動 / 1分足は因果証明ではない",
        "  - 入力構造：直後にNASDAQが跳ねた / 悪材料なら必ず上がる": "  - 入力構造：言える：初動整合 / 言わない：因果断定 / 分ける：MCHP固有増幅",
        "- 補助テロップ：8:30 ET直後の分足は未確認": "- 補助テロップ：8:30 ET初動は確認済み / ただし因果証明ではない",
        "- 使用する数字：8:30 ET、NASDAQ +1.30%": "- 使用する数字：8:30 ET、QQQ 719.16→720.23、SOXX 541.06→542.40、NVDA 219.95→220.31、MCHP 79.58→79.56、NASDAQ +1.30%",
        "- 画面で見せる内容：主因候補：利上げ観測後退 / 未確認：8:30 ET直後の分足": "- 画面で見せる内容：確認済み：QQQ・SOXX・NVDAの発表分上昇 / 境界：1分足だけで因果は断定しない / MCHPは固有材料を分離",
        "- 不確実性：瞬間的な価格反応は確認できない": "- 不確実性：発表時刻との初動整合は確認したが、終日上昇の因果や各要因の寄与度は分離できない",
    }
    for old, new in replacements.items():
        if old not in text:
            raise SystemExit(f"public fixture expected text missing: {old}")
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def _remove_stale_generated_outputs(root: Path) -> None:
    for path in (
        root / f"working/{DATE}/story-engine/story_plan.json",
        root / f"working/{DATE}/story-engine/story_script.json",
        root / f"working/{DATE}/story-engine/creative_review.json",
        root / f"working/{DATE}/story-engine/story_engine_acceptance.json",
        root / f"working/{DATE}/story-engine/story_projection_report.json",
        root / f"episodes/{DATE}/episode_package_{DATE}.md",
        root / f"episodes/{DATE}/spoken_script_{DATE}.md",
        root / f"episodes/{DATE}/asset_manifest.json",
    ):
        path.unlink(missing_ok=True)
    verification = root / f"verification/{DATE}"
    if verification.is_dir():
        for child in verification.iterdir():
            if child.is_file():
                child.unlink()
    production_request = root / f"working/{DATE}/production_request.json"
    production_state = root / f"working/{DATE}/production_state.json"
    production_request.unlink(missing_ok=True)
    production_state.unlink(missing_ok=True)


def materialize(root: Path, acceptance_source: Path) -> dict[str, Any]:
    decoder_path = acceptance_source / "scripts/acceptance/materialize_2026_08_10_inputs.py"
    decoder = load_acceptance_decoder(decoder_path)
    decoder.materialize_base(root)
    supplement_sha = _compact_wave2(root)
    dossier = _patch_dossier(root, supplement_sha)
    _patch_story(root, dossier)
    _patch_visual_authoring(root)
    _patch_public_markdown(root)
    _remove_stale_generated_outputs(root)
    return {
        "status": "pass",
        "episode_date": DATE,
        "base_payload_sha256": decoder.BASE_PAYLOAD_SHA256,
        "collector_run_id": RUN_ID,
        "collector_receipt_sha256": sha(root / "tests/fixtures/real-day-2026-08-10/collector_wave2_success_receipt.json"),
        "supplement_sha256": supplement_sha,
        "causal_dossier_sha256": sha(root / f"research/{DATE}/causal_research_dossier_{DATE}.json"),
        "render_authoring_sha256": sha(root / f"render-specs/{DATE}/render_spec.json"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--acceptance-source", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = materialize(args.repo_root.resolve(), args.acceptance_source.resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
