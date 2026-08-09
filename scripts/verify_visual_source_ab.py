#!/usr/bin/env python3
"""Verify that Visual Source changes only approved asset presentation fields.

The baseline spec must be the strict renderer spec produced by the same
materializer before Visual Source projection. The candidate spec is the final
strict renderer spec after the explicit Visual Source selection is projected.
All editorial, narration, publishing, Visual Grammar, Financial Visual,
object ordering, timing cues and non-target presentation fields must remain
byte-semantically identical.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


class VisualSourceABError(ValueError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualSourceABError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualSourceABError(f"{label} root must be an object")
    return value


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(f".{path.name}.visual-source-ab.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _scene_map(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    scenes = spec.get("scenes")
    if not isinstance(scenes, list):
        raise VisualSourceABError("render spec scenes must be an array")
    result: dict[str, dict[str, Any]] = {}
    for scene in scenes:
        if not isinstance(scene, dict) or not isinstance(scene.get("sceneId"), str):
            raise VisualSourceABError("render spec contains invalid scene")
        if scene["sceneId"] in result:
            raise VisualSourceABError(f"duplicate sceneId: {scene['sceneId']}")
        result[scene["sceneId"]] = scene
    return result


def _beat_aliases(beat_id: str) -> set[str]:
    aliases = {beat_id}
    canonical = re.fullmatch(r"vb-(0[1-9])-([0-9]{2})", beat_id)
    if canonical:
        aliases.add(
            f"scene-{canonical.group(1)}-beat-{int(canonical.group(2)):03d}"
        )
    producer = re.fullmatch(r"scene-(0[1-9])-beat-([0-9]{3})", beat_id)
    if producer:
        aliases.add(f"vb-{producer.group(1)}-{int(producer.group(2)):02d}")
    return aliases


def _beat_map(scene: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for beat in scene.get("visualBeats", []):
        if not isinstance(beat, dict) or not isinstance(beat.get("beatId"), str):
            raise VisualSourceABError(f"{scene.get('sceneId')}: invalid Visual Beat")
        ids = {beat["beatId"]}
        if isinstance(beat.get("visualBeatId"), str):
            ids.add(beat["visualBeatId"])
        expanded = set().union(*(_beat_aliases(value) for value in ids))
        for alias in expanded:
            existing = result.get(alias)
            if existing is not None and existing is not beat:
                raise VisualSourceABError(
                    f"{scene.get('sceneId')}: duplicate Visual Beat alias {alias}"
                )
            result[alias] = beat
    return result


def _placement_map(scene: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for placement in scene.get("assetPlacements", []):
        if not isinstance(placement, dict) or not isinstance(placement.get("placementId"), str):
            raise VisualSourceABError(f"{scene.get('sceneId')}: invalid asset placement")
        result[placement["placementId"]] = placement
    return result


def _sanitize(
    spec: dict[str, Any], selected: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    sanitized = copy.deepcopy(spec)
    scenes = _scene_map(sanitized)
    allowed_changes: list[dict[str, Any]] = []
    for item in selected.get("selectedAssets", []):
        if not isinstance(item, dict):
            raise VisualSourceABError("selectedAssets must contain objects")
        scene_id = item.get("sceneId")
        beat_id = item.get("visualBeatId")
        placement = item.get("placement")
        if not isinstance(scene_id, str) or not isinstance(beat_id, str) or not isinstance(placement, dict):
            raise VisualSourceABError("selected asset target/placement is incomplete")
        placement_id = placement.get("placementId")
        if not isinstance(placement_id, str):
            raise VisualSourceABError("selected asset placementId is missing")
        scene = scenes.get(scene_id)
        if scene is None:
            raise VisualSourceABError(f"selected target scene missing: {scene_id}")
        beats = _beat_map(scene)
        beat = beats.get(beat_id)
        if beat is None:
            raise VisualSourceABError(
                f"selected target Beat missing: {scene_id}/{beat_id} "
                f"aliases={sorted(_beat_aliases(beat_id))}"
            )
        placements = _placement_map(scene)
        selected_placement = placements.get(placement_id)
        if selected_placement is None:
            raise VisualSourceABError(
                f"selected placement missing from final spec: {scene_id}/{placement_id}"
            )

        # Remove exactly the fields Visual Source is authorized to change.
        beat["assetPlacementIds"] = ["<VISUAL_SOURCE_PLACEMENT>"]
        beat["assetState"] = "<VISUAL_SOURCE_ASSET_STATE>"
        selected_placement["assetId"] = "<VISUAL_SOURCE_ASSET>"
        selected_placement["role"] = "<VISUAL_SOURCE_ROLE>"
        selected_placement["region"] = "<VISUAL_SOURCE_REGION>"
        selected_placement["fit"] = "<VISUAL_SOURCE_FIT>"
        selected_placement["focalPoint"] = "<VISUAL_SOURCE_FOCAL_POINT>"
        selected_placement["opacity"] = "<VISUAL_SOURCE_OPACITY>"
        selected_placement["startChunkId"] = "<VISUAL_SOURCE_START_CHUNK>"
        selected_placement["endChunkId"] = "<VISUAL_SOURCE_END_CHUNK>"
        allowed_changes.append(
            {
                "sceneId": scene_id,
                "visualBeatId": beat_id,
                "placementId": placement_id,
                "assetId": item.get("assetId"),
                "selectedPath": item.get("selectedPath"),
            }
        )
    return sanitized, allowed_changes


def verify(
    *,
    baseline_path: Path,
    candidate_path: Path,
    selected_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    baseline = load_json(baseline_path, "baseline render spec")
    candidate = load_json(candidate_path, "candidate render spec")
    selected = load_json(selected_path, "Visual Source selected assets")
    if baseline.get("episode", {}).get("targetDate") != candidate.get("episode", {}).get("targetDate"):
        raise VisualSourceABError("baseline/candidate episode date mismatch")
    if selected.get("episodeDate") != candidate.get("episode", {}).get("targetDate"):
        raise VisualSourceABError("selected assets episode date mismatch")

    baseline_sanitized, baseline_targets = _sanitize(baseline, selected)
    candidate_sanitized, candidate_targets = _sanitize(candidate, selected)
    if baseline_targets != candidate_targets:
        raise VisualSourceABError("baseline/candidate target normalization mismatch")

    baseline_sha = sha256_value(baseline_sanitized)
    candidate_sha = sha256_value(candidate_sanitized)
    status = "PASS" if baseline_sanitized == candidate_sanitized else "FAIL"
    errors: list[str] = []
    if status != "PASS":
        errors.append(
            "Visual Source candidate changed fields outside the approved asset presentation boundary"
        )

    report = {
        "contractVersion": "1.0.0",
        "episodeDate": candidate.get("episode", {}).get("targetDate"),
        "status": status,
        "baselinePath": str(baseline_path),
        "candidatePath": str(candidate_path),
        "selectedPath": selected.get("selectedPath"),
        "targetCount": len(candidate_targets),
        "targets": candidate_targets,
        "sanitizedBaselineSha256": baseline_sha,
        "sanitizedCandidateSha256": candidate_sha,
        "preserved": {
            "editorial": baseline.get("editorial") == candidate.get("editorial"),
            "publishing": baseline.get("publishing") == candidate.get("publishing"),
            "sources": baseline.get("sources") == candidate.get("sources"),
            "review": baseline.get("review") == candidate.get("review"),
            "voiceProfileId": baseline.get("voiceProfileId") == candidate.get("voiceProfileId"),
            "sceneOrder": [item.get("sceneId") for item in baseline.get("scenes", [])]
            == [item.get("sceneId") for item in candidate.get("scenes", [])],
            "allNonAssetPresentationFields": status == "PASS",
        },
        "errors": errors,
    }
    write_atomic(report_path, report)
    if status != "PASS":
        raise VisualSourceABError(errors[0])
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--selected-assets", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = verify(
            baseline_path=args.baseline,
            candidate_path=args.candidate,
            selected_path=args.selected_assets,
            report_path=args.report,
        )
        code = 0
    except (VisualSourceABError, OSError, KeyError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "errors": str(exc).splitlines()}
        try:
            write_atomic(args.report, result)
        except OSError:
            pass
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
