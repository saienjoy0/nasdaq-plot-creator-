#!/usr/bin/env python3
"""Project an explicit Visual Source selection into existing production fields."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import resolve_visual_sources
import select_visual_sources
import verify_visual_source_ab
import visual_evidence_quality_gate
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


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(f".{path.name}.visual-source.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _beat_aliases(beat_id: str) -> set[str]:
    aliases = {beat_id}
    match = re.fullmatch(r"vb-(0[1-9])-([0-9]{2})", beat_id)
    if match:
        scene_number = match.group(1)
        beat_number = int(match.group(2))
        aliases.add(f"scene-{scene_number}-beat-{beat_number:03d}")
    match = re.fullmatch(r"scene-(0[1-9])-beat-([0-9]{3})", beat_id)
    if match:
        scene_number = match.group(1)
        beat_number = int(match.group(2))
        aliases.add(f"vb-{scene_number}-{beat_number:02d}")
    return aliases


def _find_beat(render: dict[str, Any], scene_id: str, beat_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    aliases = _beat_aliases(beat_id)
    for scene in render.get("scenes", []):
        if scene.get("sceneId") != scene_id:
            continue
        for beat in scene.get("visualBeats", []):
            values = {beat.get("beatId"), beat.get("visualBeatId")}
            if aliases.intersection(item for item in values if isinstance(item, str)):
                return scene, beat
    raise VisualSourceProjectionError(
        f"Visual Source target Beat not found: {scene_id}/{beat_id} aliases={sorted(aliases)}"
    )


def _existing_asset_is_exact_current_placement(
    *,
    intent_id: str,
    scene: dict[str, Any],
    beat: dict[str, Any],
    placement_config: dict[str, Any],
    asset_id: str,
) -> bool:
    """Return true only when an existing reusable asset is already the exact Beat placement."""
    placement_id = placement_config["placementId"]
    existing = next(
        (
            item
            for item in scene.get("assetPlacements", [])
            if item.get("placementId") == placement_id
        ),
        None,
    )
    if existing is None or existing.get("assetId") != asset_id:
        return False
    owned_ids = list(beat.get("assetPlacementIds", []))
    if placement_id not in owned_ids or set(owned_ids) != {placement_id}:
        raise VisualSourceProjectionError(
            f"{intent_id}: existing fallback placement must be the target Beat's only owned placement"
        )
    if beat.get("assetState") != "ready":
        raise VisualSourceProjectionError(
            f"{intent_id}: existing fallback placement is not already production-ready"
        )
    return True


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


def _rebind_selection_to_final_contract(
    *, root: Path, date: str, final_contract_path: Path
) -> Path:
    """Resolve/select again only when the persisted selection is not bound to the final contract.

    The selection decision itself stays in visual_source_selection.json. This function does not
    choose a path; it only recomputes mechanical resolution against the exact post-Story contract.
    """
    work = root / "working" / date
    verification = root / "verification" / date
    selection_path = work / "visual_source_selection.json"
    if not selection_path.is_file():
        raise VisualSourceProjectionError(
            "E_VISUAL_SOURCE_SELECTED_PATH_INVALID: visual_source_selection.json is required"
        )
    selected_output = work / "visual_source_selected_assets.json"
    current_sha = sha256_file(final_contract_path)
    if selected_output.is_file():
        selected = load_json(selected_output, "Visual Source selected assets")
        if selected.get("finalEpisodeContractSha256") == current_sha:
            return selected_output

    raw_resolution = verification / "asset_resolution_raw.json"
    audit_output = verification / "asset_resolution_log.json"
    collector_root = None
    if os.environ.get("NASDAQ_CAFE_COLLECTOR_ROOT"):
        collector_root = Path(os.environ["NASDAQ_CAFE_COLLECTOR_ROOT"])
    try:
        resolve_visual_sources.resolve_all(
            contract_path=final_contract_path,
            repo_root=root,
            output_path=raw_resolution,
            asset_root=root / "daily-assets",
            collector_root=collector_root,
        )
        select_visual_sources.select(
            contract_path=final_contract_path,
            resolution_path=raw_resolution,
            selection_path=selection_path,
            selected_output=selected_output,
            audit_output=audit_output,
        )
    except (
        OSError,
        KeyError,
        json.JSONDecodeError,
        resolve_visual_sources.VisualSourceResolutionError,
        select_visual_sources.VisualSourceSelectionError,
    ) as exc:
        raise VisualSourceProjectionError(str(exc)) from exc
    return selected_output


def _run_ab_gate(
    *, root: Path, date: str, baseline_render: dict[str, Any], candidate_render: dict[str, Any], selected_path: Path
) -> None:
    verification = root / "verification" / date
    baseline_path = verification / "visual_source_ab_baseline_render.json"
    candidate_path = verification / "visual_source_ab_candidate_render.json"
    report_path = verification / "visual_source_ab_report.json"
    write_json(baseline_path, baseline_render)
    write_json(candidate_path, candidate_render)
    try:
        verify_visual_source_ab.verify(
            baseline_path=baseline_path,
            candidate_path=candidate_path,
            selected_path=selected_path,
            report_path=report_path,
        )
    except (verify_visual_source_ab.VisualSourceABError, OSError, KeyError, json.JSONDecodeError) as exc:
        raise VisualSourceProjectionError(f"E_VISUAL_SOURCE_AB_DRIFT: {exc}") from exc


def _run_evidence_quality_gate(
    *, root: Path, date: str, render: dict[str, Any], intents_path: Path
) -> None:
    try:
        intents_doc = visual_evidence_quality_gate.load_json(
            intents_path, "Visual Source intents"
        )
        report = visual_evidence_quality_gate.validate_visual_evidence(
            render=render,
            intents_doc=intents_doc,
        )
    except (
        OSError,
        json.JSONDecodeError,
        visual_evidence_quality_gate.VisualEvidenceQualityError,
    ) as exc:
        raise VisualSourceProjectionError(str(exc)) from exc
    report_path = root / "verification" / date / "visual_evidence_quality_gate.json"
    write_json(report_path, report)
    if report.get("status") != "PASS":
        raise VisualSourceProjectionError(
            "\n".join(
                f"{item['code']} {item['path']}: {item['message']}"
                for item in report.get("violations", [])
            )
        )


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
    if not intents_path.is_file():
        raise VisualSourceProjectionError(
            "E_VISUAL_SOURCE_PLANNING_MISSING: visual_source_intents.json is required even when no Visual Source is needed"
        )

    # Enforce the visual meaning against the final post-Story render, not only the
    # earlier prepare step. This prevents acceptance or assembly paths from silently
    # bypassing evidence-first planning.
    _run_evidence_quality_gate(
        root=root,
        date=date,
        render=render,
        intents_path=intents_path,
    )

    visual_source_contract.attach_visual_sources(
        contract_path=final_contract_path,
        intent_path=intents_path,
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

    selected_path = _rebind_selection_to_final_contract(
        root=root, date=date, final_contract_path=final_contract_path
    )
    selected = load_json(selected_path, "Visual Source selected assets")
    if selected.get("episodeDate") != date:
        raise VisualSourceProjectionError("Visual Source selected assets episodeDate mismatch")
    if selected.get("finalEpisodeContractSha256") != sha256_file(final_contract_path):
        raise VisualSourceProjectionError("Visual Source selected assets Final Episode Contract SHA mismatch")
    global_path = selected.get("selectedPath")
    if global_path not in {"primary", "fallback", "mixed"}:
        raise VisualSourceProjectionError("E_VISUAL_SOURCE_SELECTED_PATH_INVALID")
    selected_assets = selected.get("selectedAssets")
    if not isinstance(selected_assets, list) or len(selected_assets) != len(intents):
        raise VisualSourceProjectionError("selected Visual Source asset count mismatch")

    baseline_render = copy.deepcopy(render)
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
        intent_path = item.get("selectedPath")
        if intent_path not in {"primary", "fallback"}:
            raise VisualSourceProjectionError(f"{intent_id}: selectedPath is invalid")
        if global_path != "mixed" and intent_path != global_path:
            raise VisualSourceProjectionError(f"{intent_id}: selectedPath disagrees with summary path")
        candidate = intent[intent_path]
        if item.get("assetId") != candidate["assetId"]:
            raise VisualSourceProjectionError(f"{intent_id}: selected assetId mismatch")
        scene_id = intent["target"]["sceneId"]
        beat_id = intent["target"]["visualBeatId"]
        scene, beat = _find_beat(render, scene_id, beat_id)
        preserve_existing = (
            candidate["sourceKind"] == "existing-asset"
            and _existing_asset_is_exact_current_placement(
                intent_id=intent_id,
                scene=scene,
                beat=beat,
                placement_config=intent["placement"],
                asset_id=candidate["assetId"],
            )
        )
        if not preserve_existing:
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
                "selected_path": intent_path,
                "selected_asset_id": candidate["assetId"],
                "primary_asset_id": intent["primary"]["assetId"],
                "fallback_asset_id": intent["fallback"]["assetId"],
            }
        )

    if seen_intents != set(intent_map):
        raise VisualSourceProjectionError(
            f"selected Visual Source intents incomplete: {sorted(set(intent_map) - seen_intents)}"
        )

    _run_ab_gate(
        root=root,
        date=date,
        baseline_render=baseline_render,
        candidate_render=copy.deepcopy(render),
        selected_path=selected_path,
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
