from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def module_from(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


acceptance = module_from(
    ROOT / "tests/real-day-2026-08-10/apply_visual_evidence_first.py",
    "visual_evidence_20260810_acceptance",
)
gate = module_from(
    ROOT / "scripts/visual_evidence_quality_gate.py",
    "visual_evidence_quality_gate_acceptance",
)


def visual_beat(beat_id: str, source_ids: list[str], *, function: str = "Evidence") -> dict:
    return {
        "beatId": beat_id,
        "visualBeatId": beat_id,
        "primaryFunction": function,
        "evidenceSourceIds": source_ids,
        "screenQuestion": "確認",
        "primaryElement": "確認",
        "viewerTexts": ["確認"],
        "contentType": "verification-matrix",
        "visualTemplate": "verification-matrix",
        "visualMode": "verification",
        "screenState": "Data",
        "templateVariant": "strengthen-vs-weaken",
        "templateConfig": {"variant": "strengthen-vs-weaken"},
        "sequencePolicy": "explicit",
        "assetPlacementIds": [],
        "assetState": "not-required",
        "startChunkId": f"{beat_id}-start",
        "endChunkId": f"{beat_id}-end",
        "visualGrammar": {
            "contractVersion": "1.0.0",
            "grammarId": "verification",
            "transitionRole": "major-shift",
            "returnTargetBeatId": None,
        },
    }


def scene(number: int, beats: list[dict]) -> dict:
    return {
        "sceneId": f"scene-{number:02d}",
        "sceneNumber": number,
        "headline": f"Scene {number}",
        "purpose": "acceptance",
        "sourceLabel": "acceptance",
        "timelineBasis": "acceptance",
        "evidenceSourceIds": sorted(
            {source_id for beat in beats for source_id in beat.get("evidenceSourceIds", [])}
        ),
        "assetPlacements": [
            {
                "placementId": f"scene-{number:02d}-background",
                "assetId": "mainBackground",
                "role": "background",
                "region": "full-canvas",
                "fit": "cover",
                "focalPoint": None,
                "opacity": 1,
                "startChunkId": None,
                "endChunkId": None,
            }
        ],
        "numbers": [],
        "visualBeats": beats,
    }


def build_render() -> dict:
    scenes = [scene(number, []) for number in range(1, 10)]
    scenes[1]["visualBeats"] = [visual_beat("vb-02-01", ["source-002"], function="Anchor")]
    scenes[1]["evidenceSourceIds"] = ["source-002"]
    scenes[5]["visualBeats"] = [
        visual_beat("vb-06-01", ["source-001"], function="Explain"),
        visual_beat("vb-06-02", ["source-004"], function="Explain"),
    ]
    scenes[5]["evidenceSourceIds"] = ["source-001", "source-004"]
    scene8 = visual_beat("scene-08-beat-001", ["source-005"], function="Evidence")
    scene8["screenQuestion"] = "8:30 ETの1分足で初動を確認"
    scene8["primaryElement"] = "8:30 ETの実分足"
    scene8["viewerTexts"] = ["8:30 ETの1分足"]
    scenes[7]["visualBeats"] = [scene8]
    scenes[7]["evidenceSourceIds"] = ["source-005"]
    scenes[7]["timelineBasis"] = "verified-series-plus-official-time-plus-close"
    return {
        "episode": {"id": "2026-08-10"},
        "sources": [
            {
                "sourceId": "source-001",
                "sourceType": "market-data",
                "title": "Market data",
                "publisher": "Collector",
                "reference": "market",
                "usedFor": ["close"],
            },
            {
                "sourceId": "source-002",
                "sourceType": "official",
                "title": "Employment Situation — July 2026",
                "publisher": "U.S. Bureau of Labor Statistics",
                "reference": acceptance.BLS_URL,
                "usedFor": ["7月雇用者数", "8:30 ET発表時刻"],
            },
            {
                "sourceId": "source-004",
                "sourceType": "company",
                "title": "Microchip Technology Announces Financial Results for First Quarter of Fiscal Year 2027",
                "publisher": "Microchip Technology Investor Relations",
                "reference": acceptance.MICROCHIP_URL,
                "usedFor": ["Q1売上", "EPS", "次四半期見通し"],
            },
            {
                "sourceId": "source-005",
                "sourceType": "other",
                "title": "Research Acquisition Result Wave 2",
                "publisher": "NASDAQ Cafe Collector / Longbridge",
                "reference": "research_acquisition_result_w02.json",
                "usedFor": ["QQQ、SOXX、MCHP、NVDAの検証済み1分足"],
            },
        ],
        "scenes": scenes,
    }


def test_real_20260810_receipt_becomes_fallback_plus_real_ir_and_verified_series(tmp_path: Path) -> None:
    render_path = tmp_path / "render-specs/2026-08-10/render_spec.json"
    render_path.parent.mkdir(parents=True, exist_ok=True)
    render_path.write_text(json.dumps(build_render(), ensure_ascii=False), encoding="utf-8")

    receipt_target = tmp_path / "tests/fixtures/real-day-2026-08-10/collector_wave2_success_receipt.json"
    receipt_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        ROOT / "tests/fixtures/real-day-2026-08-10/collector_wave2_success_receipt.json",
        receipt_target,
    )

    result = acceptance.apply(tmp_path)
    assert result["visualSourceIntentCount"] == 2
    assert result["selectedPath"] == "fallback"
    assert result["approvedFallbackEvidence"] == ["source-002"]
    assert result["realEvidence"] == ["source-004"]
    assert result["reusableBackgrounds"] == []
    assert [item["close"] for item in result["verifiedSeries"]["points"]] == [
        719.16,
        720.23,
        720.531,
    ]

    render = json.loads(render_path.read_text(encoding="utf-8"))
    scene8 = next(scene for scene in render["scenes"] if scene["sceneNumber"] == 8)
    beat8 = scene8["visualBeats"][0]
    assert beat8["visualTemplate"] == "event-reaction-timeline"
    assert beat8["templateConfig"]["variant"] == "verified-series"
    assert beat8["templateConfig"]["reactionTimeline"]["precision"] == "verified-intraday-series"
    series_ids = beat8["templateConfig"]["reactionTimeline"]["seriesObjectIds"]
    assert series_ids == ["scene-08-qqq-0829", "scene-08-qqq-0830", "scene-08-qqq-0831"]
    values = {
        item["numberId"]: item["numericValue"]
        for item in scene8["numbers"]
        if item.get("numberId") in series_ids
    }
    assert [values[item] for item in series_ids] == [719.16, 720.23, 720.531]

    # Renderer 2.4 requires exactly one fixed full-Scene mainBackground. Evidence
    # diversity must be added as main-stage media/plots rather than replacing it.
    for number in (4, 6):
        target = next(scene for scene in render["scenes"] if scene["sceneNumber"] == number)
        backgrounds = [item for item in target["assetPlacements"] if item.get("role") == "background"]
        assert len(backgrounds) == 1
        assert backgrounds[0]["assetId"] == "mainBackground"

    intents_doc = json.loads(
        (tmp_path / "working/2026-08-10/visual_source_intents.json").read_text(encoding="utf-8")
    )
    assert {item["sourceIds"][0] for item in intents_doc["intents"]} == {"source-002", "source-004"}
    assert {item["primary"]["sourceKind"] for item in intents_doc["intents"]} == {"official-url"}
    by_source = {item["sourceIds"][0]: item for item in intents_doc["intents"]}
    assert by_source["source-002"]["fallback"]["sourceKind"] == "existing-asset"
    assert by_source["source-004"]["fallback"]["sourceKind"] == "official-url"
    assert by_source["source-004"]["fallback"]["assetId"] == "daily-microchip-q1-fy27-ir-fallback"

    report = gate.validate_visual_evidence(render=render, intents_doc=intents_doc)
    assert report["status"] == "PASS", report
