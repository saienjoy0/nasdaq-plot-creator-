from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    path = ROOT / "scripts/visual_evidence_coverage.py"
    spec = importlib.util.spec_from_file_location("visual_evidence_coverage", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def base_render(source: dict, beat: dict | None = None) -> dict:
    return {
        "sources": [source],
        "scenes": [
            {
                "sceneId": "scene-02",
                "sceneNumber": 2,
                "sceneRole": "editorial-body",
                "evidenceSourceIds": [source["sourceId"]],
                "visualBeats": [beat or {
                    "beatId": "vb-02-01",
                    "primaryFunction": "Evidence",
                    "evidenceSourceIds": [source["sourceId"]],
                    "visualTemplate": "metric-comparison-board",
                    "templateConfig": {},
                }],
            }
        ],
    }


def test_official_source_requires_visual_source_intent() -> None:
    module = load_module()
    render = base_render({
        "sourceId": "source-002",
        "sourceType": "official",
        "title": "Employment Situation",
        "publisher": "BLS",
        "reference": "https://www.bls.gov/news.release/empsit.nr0.htm",
        "usedFor": ["employment actual"],
    })
    try:
        module.validate_visual_evidence_coverage(render=render, intents=[])
    except module.VisualEvidenceCoverageError as exc:
        assert "E_VISUAL_SOURCE_DOCUMENT_UNCOVERED" in str(exc)
        assert "source-002" in str(exc)
    else:
        raise AssertionError("official source evidence must not silently become not-required")


def test_official_source_is_covered_by_existing_intent_contract() -> None:
    module = load_module()
    render = base_render({
        "sourceId": "source-002",
        "sourceType": "official",
        "title": "Employment Situation",
        "publisher": "BLS",
        "reference": "https://www.bls.gov/news.release/empsit.nr0.htm",
        "usedFor": ["employment actual"],
    })
    module.validate_visual_evidence_coverage(
        render=render,
        intents=[{"intentId": "vsi-001", "sourceIds": ["source-002"]}],
    )


def test_day_specific_company_evidence_requires_visual_source_intent() -> None:
    module = load_module()
    render = base_render({
        "sourceId": "source-004",
        "sourceType": "company",
        "title": "Microchip results",
        "publisher": "Microchip IR",
        "reference": "research/2026-08-10/evidence/RA-W2-005_exact_url_archive.json",
        "usedFor": ["Q1 results"],
    })
    try:
        module.validate_visual_evidence_coverage(render=render, intents=[])
    except module.VisualEvidenceCoverageError as exc:
        assert "E_VISUAL_SOURCE_DOCUMENT_UNCOVERED" in str(exc)
        assert "source-004" in str(exc)
    else:
        raise AssertionError("day-specific company evidence must be covered")


def test_non_evidence_beat_does_not_create_a_source_quota() -> None:
    module = load_module()
    source = {
        "sourceId": "source-002",
        "sourceType": "official",
        "title": "Employment Situation",
        "publisher": "BLS",
        "reference": "https://www.bls.gov/news.release/empsit.nr0.htm",
        "usedFor": ["context"],
    }
    beat = {
        "beatId": "vb-02-01",
        "primaryFunction": "Explain",
        "evidenceSourceIds": ["source-002"],
        "visualTemplate": "causal-lane",
        "templateConfig": {},
    }
    module.validate_visual_evidence_coverage(render=base_render(source, beat), intents=[])


def test_generic_legacy_company_url_does_not_create_new_quota() -> None:
    module = load_module()
    render = base_render({
        "sourceId": "source-002",
        "sourceType": "company-ir",
        "title": "Prior guidance",
        "publisher": "AMD IR",
        "reference": "https://ir.amd.com/news-events/press-releases/detail/1284/example",
        "usedFor": ["prior guidance"],
    })
    module.validate_visual_evidence_coverage(render=render, intents=[])


def test_verified_intraday_source_requires_existing_series_visual() -> None:
    module = load_module()
    source = {
        "sourceId": "source-005",
        "sourceType": "other",
        "title": "Research Acquisition Result Wave 2",
        "publisher": "NASDAQ Cafe Collector / Longbridge",
        "reference": "research/2026-08-10/research_acquisition_result_w02.json",
        "usedFor": ["QQQ、SOXX、MCHP、NVDAの検証済み1分足"],
    }
    render = base_render(source)
    try:
        module.validate_visual_evidence_coverage(render=render, intents=[])
    except module.VisualEvidenceCoverageError as exc:
        assert "E_FINANCIAL_VISUAL_INTRADAY_UNCOVERED" in str(exc)
        assert "source-005" in str(exc)
    else:
        raise AssertionError("verified intraday evidence must use the existing series visual")


def test_verified_intraday_existing_series_visual_is_enough() -> None:
    module = load_module()
    source = {
        "sourceId": "source-005",
        "sourceType": "other",
        "title": "Research Acquisition Result Wave 2",
        "publisher": "NASDAQ Cafe Collector / Longbridge",
        "reference": "research/2026-08-10/research_acquisition_result_w02.json",
        "usedFor": ["QQQ、SOXX、MCHP、NVDAの検証済み1分足"],
    }
    beat = {
        "beatId": "vb-08-01",
        "primaryFunction": "Evidence",
        "evidenceSourceIds": ["source-005"],
        "visualTemplate": "event-reaction-timeline",
        "templateConfig": {
            "reactionTimeline": {
                "precision": "verified-intraday-series",
                "seriesObjectIds": ["qqq-0829", "qqq-0830"],
            }
        },
        "financialVisualTrace": {"sourceIds": ["source-005"]},
    }
    render = base_render(source, beat)
    module.validate_visual_evidence_coverage(render=render, intents=[])


def test_closing_only_source_references_do_not_force_visuals() -> None:
    module = load_module()
    source = {
        "sourceId": "source-002",
        "sourceType": "official",
        "title": "Employment Situation",
        "publisher": "BLS",
        "reference": "https://www.bls.gov/news.release/empsit.nr0.htm",
        "usedFor": ["recap only"],
    }
    render = {
        "sources": [source],
        "scenes": [{
            "sceneId": "scene-09",
            "sceneNumber": 9,
            "sceneRole": "closing-recap-sendoff-goodnight",
            "evidenceSourceIds": ["source-002"],
            "visualBeats": [{"primaryFunction": "Evidence", "evidenceSourceIds": ["source-002"]}],
        }],
    }
    module.validate_visual_evidence_coverage(render=render, intents=[])
