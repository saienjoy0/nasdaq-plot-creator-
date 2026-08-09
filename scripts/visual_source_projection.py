#!/usr/bin/env python3
"""Project an explicit Visual Source selection into existing production fields."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import visual_source_contract


class VisualSourceProjectionError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualSourceProjectionError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualSourceProjectionError(f"{label} root must be an object")
    return value


def _find_beat(render: dict[str, Any], scene_id: str, beat_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    for scene in render.get("scenes", []):
        if scene.get("sceneId") != scene_id:
            continue
        for beat in scene.get("visualBeats", []):
            if beat.get("beatId") == beat_id or beat.get("visualBeatId") == beat_id:
                return scene, beat
    raise VisualSourceProjectionError(f"Visual Source target Beat not found: {scene_id}/{beat_id}")


def _apply_selected_placement(
    *,
    intent_id: str,
    scene: dict[str, Any],
    beat: dict[str, Any],
    placement_config: dict[str, Any],
    asset_id: str,
) -> None:
    placement_id = placement_config["placementId"]
    scene_placements = scene.setdefault("assetPlacements", [])
    existing = next(
        (item for item in scene_placements if item.get("placementId") == placement_id),
        None,
    )
    owned_ids = list(beat.get("assetPlacementIds", []))
    if existing is not None:
        if placement_id not in owned_ids or set(owned_ids) != {placement_id}:
            raise VisualSourceProjectionError(
                f"{intent_id}: replacement placement must be the target Beat's only owned placement"
            )
        existing.update(
            {
                "assetId": asset_id,
                "role": placement_config["role"],
                "region": placement_config["region"],
                "fit": placement_config["fit"],
                "focalPoint": placement_config.get("focalPoint"),
                "opacity": 1,
                "startChunkId": beat["startChunkId"],
                "endChunkId": beat["endChunkId"],
            }
        )
    else:
        if owned_ids:
            raise VisualSourceProjectionError(
                f"{intent_id}: target Beat already owns another external placement"
            )
        scene_placements.append(
            {
                "placementId": placement_id,
                "assetId": asset_id,
                "role": placement_config["role"],
                "region": placement_config["region"],
                "fit": placement_config["fit"],
                "focalPoint": placement_config.get("focalPoint"),
                "opacity": 1,
                "startChunkId": beat["startChunkId"],
                "endChunkId": beat["endChunkId"],
            }
        )
        beat["assetPlacementIds"] = [placement_id]
    beat["assetState"] = "ready"


def prepare_visual_sources(
    *,
    root: Path,
    date: str,
    final_contract_path: Path,
    render: dict[str, Any],
) -> dict[str, Any]:
    root = root.resolve()
    work = root / "working" / date
    intents_path = work / "visual_source_intents.json"
    visual_source_contract.attach_visual_sources(
        contract_path=final_contract_path,
        intent_path=intents_path if intents_path.is_file() else None,
        schema_path=root / "contracts/final_episode_contract.schema.json",
    )
    contract = load_json(final_contract_path, "Final Episode Contract")
    intents = (contract.get("visualSources") or {}).get("intents", [])
    if not intents:
        return {
            "selected_path": "not-required",
            "routes": [],
            "selected_assets": [],
            "asset_overrides": {},
            "has_visual_sources": False,
        }

    selected_path = work / "visual_source_selected_assets.json"
    if not selected_path.is_file():
        raise VisualSourceProjectionError(
            "E_VISUAL_SOURCE_SELECTED_PATH_INVALID: working visual_source_selected_assets.json is required"
        )
    selected = load_json(selected_path, "Visual Source selected assets")
    if selected.get("episodeDate") != date:
        raise VisualSourceProjectionError("Visual Source selected assets episodeDate mismatch")
    if selected.get("finalEpisodeContractSha256") != sha256_file(final_contract_path):
        raise VisualSourceProjectionError("Visual Source selected assets Final Episode Contract SHA mismatch")
    global_path = selected.get("selectedPath")
    if global_path not in {"primary", "fallback"}:
        raise VisualSourceProjectionError("E_VISUAL_SOURCE_SELECTED_PATH_INVALID")
    selected_assets = selected.get("selectedAssets")
    if not isinstance(selected_assets, list) or len(selected_assets) != len(intents):
        raise VisualSourceProjectionError("selected Visual Source asset count mismatch")

    intent_map = {item["intentId"]: item for item in intents}
    seen_intents: set[str] = set()
    overrides: dict[str, dict[str, Any]] = {}
    routes: list[dict[str, Any]] = []
    for item in selected_assets:
        intent_id = item.get("intentId")
        if intent_id not in intent_map or intent_id in seen_intents:
            raise VisualSourceProjectionError(f"invalid selected Visual Source intentId: {intent_id}")
        seen_intents.add(intent_id)
        intent = intent_map[intent_id]
        if item.get("selectedPath") != global_path:
            raise VisualSourceProjectionError(f"{intent_id}: selectedPath disagrees with global path")
        candidate = intent[global_path]
        if item.get("assetId") != candidate["assetId"]:
            raise VisualSourceProjectionError(f"{intent_id}: selected assetId mismatch")
        scene_id = intent["target"]["sceneId"]
        beat_id = intent["target"]["visualBeatId"]
        scene, beat = _find_beat(render, scene_id, beat_id)
        _apply_selected_placement(
            intent_id=intent_id,
            scene=scene,
            beat=beat,
            placement_config=intent["placement"],
            asset_id=candidate["assetId"],
        )

        if candidate["sourceKind"] == "existing-asset":
            overrides[candidate["assetId"]] = {
                "asset_id": candidate["assetId"],
                "path": f"renderer-registry/{candidate['assetId']}",
                "media_type": "image",
                "status": "not-required",
                "sha256": None,
            }
        else:
            output_path = item.get("outputPath")
            output_sha = item.get("outputSha256")
            if not isinstance(output_path, str) or not isinstance(output_sha, str):
                raise VisualSourceProjectionError(f"{intent_id}: selected daily asset lacks path/SHA")
            source = root / output_path
            if not source.is_file() or sha256_file(source) != output_sha:
                raise VisualSourceProjectionError(f"{intent_id}: selected daily asset file/SHA mismatch")
            overrides[candidate["assetId"]] = {
                "asset_id": candidate["assetId"],
                "path": output_path,
                "media_type": "image",
                "status": "ready",
                "sha256": output_sha,
            }
        routes.append(
            {
                "beat_id": beat_id,
                "selected_path": global_path,
                "selected_asset_id": candidate["assetId"],
                "primary_asset_id": intent["primary"]["assetId"],
                "fallback_asset_id": intent["fallback"]["assetId"],
            }
        )

    if seen_intents != set(intent_map):
        raise VisualSourceProjectionError(
            f"selected Visual Source intents incomplete: {sorted(set(intent_map) - seen_intents)}"
        )
    return {
        "selected_path": global_path,
        "routes": routes,
        "selected_assets": selected_assets,
        "asset_overrides": overrides,
        "has_visual_sources": True,
    }


def build_asset_catalog(render: dict[str, Any], projection: dict[str, Any]) -> list[dict[str, Any]]:
    asset_ids = sorted(
        {
            placement["assetId"]
            for scene in render["scenes"]
            for placement in scene.get("assetPlacements", [])
            if isinstance(placement, dict) and isinstance(placement.get("assetId"), str)
        }
    )
    overrides = projection["asset_overrides"]
    catalog = []
    for asset_id in asset_ids:
        if asset_id in overrides:
            catalog.append(overrides[asset_id])
        else:
            catalog.append(
                {
                    "asset_id": asset_id,
                    "path": f"renderer-registry/{asset_id}",
                    "media_type": "image",
                    "status": "not-required",
                    "sha256": None,
                }
            )
    return catalog
