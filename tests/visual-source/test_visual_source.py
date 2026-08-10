from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contract_module = load_module("visual_source_contract", "scripts/visual_source_contract.py")
resolver_module = load_module("resolve_visual_sources", "scripts/resolve_visual_sources.py")
selection_module = load_module("select_visual_sources", "scripts/select_visual_sources.py")
projection_module = load_module("visual_source_projection", "scripts/visual_source_projection.py")


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def install_final_contract_schema(tmp_path: Path) -> None:
    source = ROOT / "contracts/final_episode_contract.schema.json"
    target = tmp_path / "contracts/final_episode_contract.schema.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def minimal_contract(tmp_path: Path) -> dict:
    package = tmp_path / "episode.md"
    sidecar = tmp_path / "sidecar.json"
    package.write_text("episode\n", encoding="utf-8")
    sidecar.write_text("{}\n", encoding="utf-8")
    scenes = []
    for number in range(1, 10):
        scene_id = f"scene-{number:02d}"
        beat_id = f"vb-{number:02d}-01"
        scenes.append(
            {
                "sceneId": scene_id,
                "visualBeats": [
                    {
                        "visualBeatId": beat_id,
                        "headline": "headline",
                        "screenQuestion": "question",
                        "startCue": "start",
                        "endCue": "end",
                        "returnTarget": "Data",
                        "fallbackHeadline": "fallback",
                        "fallbackQuestion": "fallback question",
                        "visualGrammar": {
                            "contractVersion": "1.0.0",
                            "grammarId": "evidence",
                            "transitionRole": "continuation",
                            "returnTargetBeatId": None,
                        },
                    }
                ],
            }
        )
    return {
        "contractVersion": "1.1.0",
        "episodeDate": "2026-08-06",
        "episodePackage": {"path": "episode.md", "sha256": "a" * 64},
        "visualGrammarSidecar": {"path": "sidecar.json", "sha256": "b" * 64},
        "visualGrammarContractVersion": "1.0.0",
        "expectedConfirmed": True,
        "scene5CausalExceptionReason": None,
        "review": {"verdict": "approved", "postInquisitionFinal": True, "approvedForProduction": True},
        "sourceRegistry": [
            {"sourceId": "source-001", "title": "Source", "publisher": "Publisher", "sourceType": "official"}
        ],
        "scenes": scenes,
        "financialVisuals": {"annexVersion": "1.0.0", "intents": [], "candidatePlans": []},
    }


def intent_document(primary: dict, fallback: dict) -> dict:
    return {
        "contractVersion": "1.0.0",
        "episodeDate": "2026-08-06",
        "intents": [
            {
                "intentId": "vsi-scene-02-proof",
                "target": {"sceneId": "scene-02", "visualBeatId": "vb-02-01"},
                "presentationClass": "source-document",
                "purpose": "Show the approved source",
                "sourceIds": ["source-001"],
                "placement": {
                    "placementId": "vs-proof-main",
                    "role": "main-media",
                    "region": "main-stage",
                    "fit": "contain",
                    "focalPoint": None,
                },
                "primary": primary,
                "fallback": fallback,
            }
        ],
    }


def existing_candidate(candidate_id: str, asset_id: str) -> dict:
    return {
        "candidateId": candidate_id,
        "assetId": asset_id,
        "sourceKind": "existing-asset",
        "sourceLocator": {"assetId": asset_id},
        "captureMethod": "registry-reference",
        "captureSpec": None,
        "rightsStatus": "cleared",
    }


def test_contract_accepts_reuse_first_existing_assets(tmp_path: Path) -> None:
    contract = minimal_contract(tmp_path)
    visual = intent_document(
        existing_candidate("vsp-proof-primary", "company_amd"),
        existing_candidate("vsp-proof-fallback", "company_nvda"),
    )
    schema = json.loads((ROOT / "contracts/final_episode_contract.schema.json").read_text(encoding="utf-8"))
    updated = contract_module.validate_visual_sources(contract=contract, visual_sources={"contractVersion": "1.0.0", "intents": visual["intents"]}, schema=schema)
    assert updated["visualSources"]["intents"][0]["primary"]["assetId"] == "company_amd"


def test_resolve_select_and_project_generated_local_image(tmp_path: Path) -> None:
    date = "2026-08-06"
    install_final_contract_schema(tmp_path)
    image_path = tmp_path / "working" / date / "generated" / "proof.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (640, 360), (20, 30, 40)).save(image_path)

    primary = {
        "candidateId": "vsp-proof-primary",
        "assetId": "daily-proof-image",
        "sourceKind": "generated-image",
        "sourceLocator": {"localPath": image_path.relative_to(tmp_path).as_posix()},
        "captureMethod": "local-file-validation",
        "captureSpec": None,
        "rightsStatus": "cleared",
    }
    fallback = existing_candidate("vsp-proof-fallback", "company_amd")
    intents = intent_document(primary, fallback)
    intent_path = tmp_path / "working" / date / "visual_source_intents.json"
    write_json(intent_path, intents)

    contract = minimal_contract(tmp_path)
    contract_path = tmp_path / "working" / date / "final_episode_contract.json"
    write_json(contract_path, contract)
    contract_module.attach_visual_sources(
        contract_path=contract_path,
        intent_path=intent_path,
        schema_path=tmp_path / "contracts/final_episode_contract.schema.json",
    )

    raw_log = tmp_path / "verification" / date / "asset_resolution_raw.json"
    resolved = resolver_module.resolve_all(
        contract_path=contract_path,
        repo_root=tmp_path,
        output_path=raw_log,
        asset_root=tmp_path / "daily-assets",
        collector_root=None,
    )
    assert {(item["path"], item["status"]) for item in resolved["results"]} == {("primary", "ready"), ("fallback", "ready")}

    selection_path = tmp_path / "working" / date / "visual_source_selection.json"
    write_json(selection_path, {"contractVersion": "1.0.0", "episodeDate": date, "selectedPath": "primary"})
    selected_path = tmp_path / "working" / date / "visual_source_selected_assets.json"
    audit_path = tmp_path / "verification" / date / "asset_resolution_log.json"
    selected = selection_module.select(
        contract_path=contract_path,
        resolution_path=raw_log,
        selection_path=selection_path,
        selected_output=selected_path,
        audit_output=audit_path,
    )
    assert selected["selectedPath"] == "primary"
    assert selected["selectedAssets"][0]["assetId"] == "daily-proof-image"

    render = {
        "schemaVersion": "2.4.0",
        "episode": {"targetDate": date},
        "scenes": [
            {
                "sceneId": "scene-02",
                "visualBeats": [
                    {
                        "beatId": "vb-02-01",
                        "visualBeatId": "vb-02-01",
                        "startChunkId": "scene-02-chunk-001",
                        "endChunkId": "scene-02-chunk-001",
                        "evidenceSourceIds": ["source-001"],
                        "assetPlacementIds": [],
                        "assetState": "not-required",
                    }
                ],
                "assetPlacements": [],
            }
        ],
    }
    projection = projection_module.prepare_visual_sources(
        root=tmp_path,
        date=date,
        final_contract_path=contract_path,
        render=render,
    )
    assert render["scenes"][0]["visualBeats"][0]["assetState"] == "ready"
    assert render["scenes"][0]["assetPlacements"][0]["assetId"] == "daily-proof-image"
    catalog = projection_module.build_asset_catalog(render, projection)
    daily = next(item for item in catalog if item["asset_id"] == "daily-proof-image")
    assert daily["status"] == "ready"
    assert daily["sha256"]


def test_user_review_required_cannot_enter_production(tmp_path: Path) -> None:
    date = "2026-08-06"
    contract = minimal_contract(tmp_path)
    primary = {
        "candidateId": "vsp-proof-primary",
        "assetId": "daily-review-image",
        "sourceKind": "official-url",
        "sourceLocator": {"url": "https://example.com/proof.png"},
        "captureMethod": "direct-download",
        "captureSpec": None,
        "rightsStatus": "user-review-required",
    }
    fallback = existing_candidate("vsp-proof-fallback", "company_amd")
    contract["visualSources"] = {"contractVersion": "1.0.0", "intents": intent_document(primary, fallback)["intents"]}
    contract_path = tmp_path / "contract.json"
    write_json(contract_path, contract)
    raw = {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "finalEpisodeContractSha256": selection_module.sha256_file(contract_path),
        "status": "resolved",
        "results": [
            {
                "intentId": "vsi-scene-02-proof",
                "path": "primary",
                "candidateId": "vsp-proof-primary",
                "assetId": "daily-review-image",
                "status": "ready",
                "rightsStatus": "user-review-required",
                "outputPath": "daily-assets/x.png",
                "outputSha256": "c" * 64,
            }
        ],
    }
    raw_path = tmp_path / "raw.json"
    write_json(raw_path, raw)
    selection_path = tmp_path / "selection.json"
    write_json(selection_path, {"contractVersion": "1.0.0", "episodeDate": date, "selectedPath": "primary"})
    try:
        selection_module.select(
            contract_path=contract_path,
            resolution_path=raw_path,
            selection_path=selection_path,
            selected_output=tmp_path / "selected.json",
            audit_output=tmp_path / "audit.json",
        )
    except selection_module.VisualSourceSelectionError as exc:
        assert "E_VISUAL_SOURCE_RIGHTS_UNRESOLVED" in str(exc)
    else:
        raise AssertionError("user-review-required asset must not enter production")
