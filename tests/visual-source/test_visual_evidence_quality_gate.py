from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    path = ROOT / "scripts/visual_evidence_quality_gate.py"
    spec = importlib.util.spec_from_file_location("visual_evidence_quality_gate_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load_module()


def source(source_id: str, source_type: str, title: str, used_for: list[str]) -> dict:
    return {
        "sourceId": source_id,
        "sourceType": source_type,
        "title": title,
        "publisher": "Publisher",
        "reference": "https://example.com/source",
        "usedFor": used_for,
    }


def beat(
    beat_id: str,
    source_ids: list[str],
    *,
    primary_function: str = "Evidence",
    visual_template: str = "metric-comparison-board",
    text: str = "確認済みの数字",
) -> dict:
    return {
        "beatId": beat_id,
        "visualBeatId": beat_id,
        "primaryFunction": primary_function,
        "evidenceSourceIds": source_ids,
        "screenQuestion": text,
        "primaryElement": text,
        "viewerTexts": [text],
        "visualTemplate": visual_template,
        "templateVariant": "default",
        "templateConfig": {"variant": "default"},
    }


def render(sources: list[dict], beats: list[dict], numbers: list[dict] | None = None) -> dict:
    return {
        "episode": {"id": "2026-08-10"},
        "sources": sources,
        "scenes": [
            {
                "sceneId": "scene-02",
                "headline": "Evidence",
                "purpose": "Show evidence",
                "timelineBasis": "official source",
                "evidenceSourceIds": sorted({sid for item in beats for sid in item.get("evidenceSourceIds", [])}),
                "numbers": numbers or [],
                "visualBeats": beats,
            }
        ],
    }


def intents(*rows: dict) -> dict:
    return {
        "contractVersion": "1.0.0",
        "episodeDate": "2026-08-10",
        "intents": list(rows),
    }


def intent(source_id: str, beat_id: str = "vb-02-01") -> dict:
    return {
        "intentId": f"vsi-{source_id}",
        "target": {"sceneId": "scene-02", "visualBeatId": beat_id},
        "sourceIds": [source_id],
    }


def codes(report: dict) -> set[str]:
    return {item["code"] for item in report["violations"]}


def test_official_anchor_cannot_silently_be_not_required() -> None:
    doc = render(
        [source("source-002", "official", "Employment Situation — July 2026", ["7月雇用者数"])],
        [beat("vb-02-01", ["source-002"], primary_function="Anchor")],
    )
    report = gate.validate_visual_evidence(render=doc, intents_doc=intents())
    assert report["status"] == "FAIL"
    assert "VE_ORIGINAL_EVIDENCE_NOT_PLANNED" in codes(report)


def test_official_anchor_passes_with_explicit_source_plan() -> None:
    doc = render(
        [source("source-002", "official", "Employment Situation — July 2026", ["7月雇用者数"])],
        [beat("vb-02-01", ["source-002"], primary_function="Anchor")],
    )
    report = gate.validate_visual_evidence(
        render=doc,
        intents_doc=intents(intent("source-002")),
    )
    assert report["status"] == "PASS"


def test_company_earnings_requires_source_plan_even_on_explain_beat() -> None:
    doc = render(
        [
            source(
                "source-004",
                "company",
                "Microchip Technology Announces Financial Results for First Quarter",
                ["Q1売上", "EPS", "次四半期見通し"],
            )
        ],
        [beat("vb-02-01", ["source-004"], primary_function="Explain")],
    )
    report = gate.validate_visual_evidence(render=doc, intents_doc=intents())
    assert "VE_ORIGINAL_EVIDENCE_NOT_PLANNED" in codes(report)


def test_social_source_is_not_a_quota_but_is_required_when_story_cites_it() -> None:
    doc = render(
        [source("source-x", "social-post", "Official X post", ["material company announcement"])],
        [beat("vb-02-01", ["source-x"], primary_function="Compare")],
    )
    report = gate.validate_visual_evidence(render=doc, intents_doc=intents())
    assert "VE_ORIGINAL_EVIDENCE_NOT_PLANNED" in codes(report)


def test_verified_intraday_cannot_be_collapsed_to_card_text() -> None:
    doc = render(
        [source("source-005", "other", "Research Acquisition Result Wave 2", ["QQQの検証済み1分足"])],
        [
            beat(
                "vb-02-01",
                ["source-005"],
                primary_function="Evidence",
                visual_template="verification-matrix",
                text="8:30 ETの1分足で初動を確認",
            )
        ],
    )
    report = gate.validate_visual_evidence(render=doc, intents_doc=intents())
    assert report["status"] == "FAIL"
    assert "VE_VERIFIED_INTRADAY_COLLAPSED_TO_ABSTRACT" in codes(report)


def test_verified_intraday_passes_with_actual_numeric_series() -> None:
    numbers = [
        {"numberId": "qqq-0829", "numericValue": 719.16},
        {"numberId": "qqq-0830", "numericValue": 720.23},
        {"numberId": "qqq-0831", "numericValue": 720.531},
    ]
    series = beat(
        "vb-02-01",
        ["source-005"],
        primary_function="Evidence",
        visual_template="event-reaction-timeline",
        text="8:30 ETの1分足で初動を確認",
    )
    series["templateVariant"] = "verified-series"
    series["templateConfig"] = {
        "variant": "verified-series",
        "reactionTimeline": {
            "precision": "verified-intraday-series",
            "eventOrderIds": ["qqq-0829", "qqq-0830", "qqq-0831"],
            "seriesObjectIds": ["qqq-0829", "qqq-0830", "qqq-0831"],
        },
    }
    doc = render(
        [source("source-005", "other", "Research Acquisition Result Wave 2", ["QQQの検証済み1分足"])],
        [series],
        numbers=numbers,
    )
    report = gate.validate_visual_evidence(render=doc, intents_doc=intents())
    assert report["status"] == "PASS"


def test_intent_cannot_be_attached_to_unrelated_beat() -> None:
    doc = render(
        [
            source("source-002", "official", "Employment Situation", ["雇用"]),
            source("source-004", "company", "Financial Results", ["決算"]),
        ],
        [beat("vb-02-01", ["source-002"], primary_function="Anchor")],
    )
    report = gate.validate_visual_evidence(
        render=doc,
        intents_doc=intents(intent("source-004")),
    )
    assert "VE_INTENT_SOURCE_NOT_BOUND_TO_BEAT" in codes(report)
