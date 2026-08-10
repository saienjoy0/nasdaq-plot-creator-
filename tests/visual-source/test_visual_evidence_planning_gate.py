from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load_module("prepare_visual_sources_planning_gate", "scripts/prepare_visual_sources.py")


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_missing_intent_document_is_planning_failure(tmp_path: Path, capsys) -> None:
    code = prepare.main(["--date", "2026-08-06", "--repo-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 2
    assert "E_VISUAL_SOURCE_PLANNING_MISSING" in captured.err


def test_explicit_empty_intents_is_valid_not_required(tmp_path: Path, capsys) -> None:
    date = "2026-08-06"
    write_json(
        tmp_path / "working" / date / "visual_source_intents.json",
        {"contractVersion": "1.0.0", "episodeDate": date, "intents": []},
    )
    code = prepare.main(["--date", date, "--repo-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["status"] == "not-required"
    assert "explicitly completed" in payload["reason"]


def test_empty_intents_does_not_require_selection_file(tmp_path: Path) -> None:
    date = "2026-08-06"
    write_json(
        tmp_path / "working" / date / "visual_source_intents.json",
        {"contractVersion": "1.0.0", "episodeDate": date, "intents": []},
    )
    assert not (tmp_path / "working" / date / "visual_source_selection.json").exists()
    assert prepare.main(["--date", date, "--repo-root", str(tmp_path)]) == 0


def test_nonempty_intents_still_require_explicit_selection(tmp_path: Path, capsys) -> None:
    date = "2026-08-06"
    write_json(
        tmp_path / "working" / date / "visual_source_intents.json",
        {
            "contractVersion": "1.0.0",
            "episodeDate": date,
            "intents": [
                {
                    "intentId": "vsi-scene-02-proof",
                    "target": {"sceneId": "scene-02", "visualBeatId": "vb-02-01"},
                    "presentationClass": "source-document",
                    "purpose": "show approved evidence",
                    "sourceIds": ["source-001"],
                    "placement": {
                        "placementId": "placement-001",
                        "role": "main-media",
                        "region": "main-stage",
                        "fit": "contain",
                        "focalPoint": None,
                    },
                    "primary": {
                        "candidateId": "primary-001",
                        "assetId": "company_amd",
                        "sourceKind": "existing-asset",
                        "sourceLocator": {"assetId": "company_amd"},
                        "captureMethod": "registry-reference",
                        "captureSpec": None,
                        "rightsStatus": "cleared",
                    },
                    "fallback": {
                        "candidateId": "fallback-001",
                        "assetId": "company_nvda",
                        "sourceKind": "existing-asset",
                        "sourceLocator": {"assetId": "company_nvda"},
                        "captureMethod": "registry-reference",
                        "captureSpec": None,
                        "rightsStatus": "cleared",
                    },
                }
            ],
        },
    )
    code = prepare.main(["--date", date, "--repo-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 2
    assert "E_VISUAL_SOURCE_SELECTED_PATH_INVALID" in captured.err


def test_intent_episode_date_mismatch_fails_before_materialization(tmp_path: Path, capsys) -> None:
    write_json(
        tmp_path / "working" / "2026-08-06" / "visual_source_intents.json",
        {"contractVersion": "1.0.0", "episodeDate": "2026-08-05", "intents": []},
    )
    code = prepare.main(["--date", "2026-08-06", "--repo-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 2
    assert "episodeDate mismatch" in captured.err
