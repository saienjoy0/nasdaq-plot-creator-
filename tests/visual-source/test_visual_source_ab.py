from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest

ab = importlib.import_module("verify_visual_source_ab")


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def spec(asset_id: str, role: str = "entity-card") -> dict:
    return {
        "schemaVersion": "2.4.0",
        "episode": {"targetDate": "2026-08-06"},
        "editorial": {"storySpine": "same story"},
        "publishing": {"recommendedTitle": "same title"},
        "sources": [{"sourceId": "source-001"}],
        "review": {"verdict": "approved"},
        "voiceProfileId": "fox-default",
        "scenes": [
            {
                "sceneId": "scene-02",
                "narrationChunks": [
                    {
                        "chunkId": "scene-02-chunk-001",
                        "speechText": "same narration",
                        "captionText": "same narration",
                    }
                ],
                "visualBeats": [
                    {
                        "beatId": "scene-02-beat-001",
                        "visualTemplate": "entity-card-full",
                        "visualGrammarId": "evidence",
                        "transitionRole": "continuation",
                        "objectIds": [],
                        "assetPlacementIds": ["scene-02-placement-entity-001"],
                        "assetState": "ready",
                    }
                ],
                "assetPlacements": [
                    {
                        "placementId": "scene-02-placement-entity-001",
                        "assetId": asset_id,
                        "role": role,
                        "region": "main-stage",
                        "fit": "contain",
                        "focalPoint": None,
                        "opacity": 1,
                        "startChunkId": "scene-02-chunk-001",
                        "endChunkId": "scene-02-chunk-001",
                    }
                ],
            }
        ],
    }


def selected() -> dict:
    return {
        "contractVersion": "1.0.0",
        "episodeDate": "2026-08-06",
        "selectedPath": "primary",
        "selectedAssets": [
            {
                "intentId": "vsi-proof",
                "sceneId": "scene-02",
                "visualBeatId": "vb-02-01",
                "selectedPath": "primary",
                "assetId": "daily-proof",
                "placement": {"placementId": "scene-02-placement-entity-001"},
            }
        ],
    }


def test_only_asset_presentation_changes_pass(tmp_path: Path) -> None:
    baseline = spec("company_amd", "entity-card")
    candidate = spec("daily-proof", "main-media")
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    selected_path = tmp_path / "selected.json"
    report_path = tmp_path / "report.json"
    write_json(baseline_path, baseline)
    write_json(candidate_path, candidate)
    write_json(selected_path, selected())
    report = ab.verify(
        baseline_path=baseline_path,
        candidate_path=candidate_path,
        selected_path=selected_path,
        report_path=report_path,
    )
    assert report["status"] == "PASS"
    assert report["preserved"]["allNonAssetPresentationFields"] is True


def test_narration_change_is_rejected(tmp_path: Path) -> None:
    baseline = spec("company_amd")
    candidate = spec("daily-proof", "main-media")
    candidate = copy.deepcopy(candidate)
    candidate["scenes"][0]["narrationChunks"][0]["speechText"] = "changed narration"
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    selected_path = tmp_path / "selected.json"
    report_path = tmp_path / "report.json"
    write_json(baseline_path, baseline)
    write_json(candidate_path, candidate)
    write_json(selected_path, selected())
    with pytest.raises(ab.VisualSourceABError):
        ab.verify(
            baseline_path=baseline_path,
            candidate_path=candidate_path,
            selected_path=selected_path,
            report_path=report_path,
        )
