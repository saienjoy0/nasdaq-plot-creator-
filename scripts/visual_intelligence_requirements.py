#!/usr/bin/env python3
"""Validate AI-B Visual Intent + Provisional Direction before asset resolution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import renderer_binding


class VisualRequirementsError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VisualRequirementsError("Visual Requirements root must be an object")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def beat_ids(render: dict[str, Any]) -> list[str]:
    return [
        beat["beatId"]
        for scene in render.get("scenes", [])
        for beat in scene.get("visualBeats", [])
    ]


def validate(
    requirements: dict[str, Any],
    render: dict[str, Any],
    date: str,
    *,
    editorial_snapshot_sha256: str,
) -> dict[str, Any]:
    if requirements.get("contractVersion") != "1.0.0":
        raise VisualRequirementsError("Visual Requirements contractVersion must be 1.0.0")
    if requirements.get("bridgeContractVersion") != renderer_binding.BRIDGE_CONTRACT_VERSION:
        raise VisualRequirementsError("Visual Requirements bridgeContractVersion mismatch")
    if requirements.get("episodeDate") != date:
        raise VisualRequirementsError("Visual Requirements episodeDate mismatch")
    if requirements.get("editorialSnapshotSha256") != editorial_snapshot_sha256:
        raise VisualRequirementsError("Visual Requirements editorialSnapshotSha256 mismatch")
    ids = beat_ids(render)
    intent = requirements.get("intent")
    provisional = requirements.get("provisionalDirection")
    if not isinstance(intent, dict) or not isinstance(intent.get("beats"), list):
        raise VisualRequirementsError("Visual Requirements intent.beats missing")
    if not isinstance(provisional, dict) or not isinstance(provisional.get("requirements"), list):
        raise VisualRequirementsError("Visual Requirements provisionalDirection.requirements missing")
    if [item.get("visualBeatId") for item in intent["beats"]] != ids:
        raise VisualRequirementsError("Visual Intent must cover every Beat in Story order")
    if [item.get("visualBeatId") for item in provisional["requirements"]] != ids:
        raise VisualRequirementsError("Provisional Direction must cover every Beat in Story order")
    for item in intent["beats"]:
        required = ("purpose", "audienceBeliefBefore", "audienceBeliefAfter", "visualInformationGain", "editorialReason")
        if any(not isinstance(item.get(key), str) or not item[key].strip() for key in required):
            raise VisualRequirementsError(f"{item.get('visualBeatId')}: incomplete Visual Intent")
        if item.get("realityAnchorPreference") not in {"required", "preferred", "neutral", "avoid"}:
            raise VisualRequirementsError(f"{item.get('visualBeatId')}: invalid realityAnchorPreference")
        if not isinstance(item.get("preferredEvidenceModes"), list):
            raise VisualRequirementsError(f"{item.get('visualBeatId')}: preferredEvidenceModes must be an array")
    for item in provisional["requirements"]:
        if item.get("imageRequirement") not in {"required", "possible", "not-required"}:
            raise VisualRequirementsError(f"{item.get('visualBeatId')}: invalid imageRequirement")
        if not isinstance(item.get("requiredModes"), list) or not isinstance(item.get("reason"), str):
            raise VisualRequirementsError(f"{item.get('visualBeatId')}: invalid Provisional Direction")
    return {
        "status": "PASS",
        "episodeDate": date,
        "beatCount": len(ids),
        "editorialSnapshotSha256": editorial_snapshot_sha256,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", required=True, type=Path)
    parser.add_argument("--render-spec", required=True, type=Path)
    parser.add_argument("--editorial-snapshot", required=True, type=Path)
    parser.add_argument("--date", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = validate(
            load_json(args.requirements),
            load_json(args.render_spec),
            args.date,
            editorial_snapshot_sha256=sha256_file(args.editorial_snapshot),
        )
        code = 0
    except (OSError, json.JSONDecodeError, VisualRequirementsError) as exc:
        result = {"status": "FAIL", "episodeDate": args.date, "errors": [str(exc)]}
        code = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
