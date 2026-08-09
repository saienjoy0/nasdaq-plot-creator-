#!/usr/bin/env python3
"""Freeze explicit Visual Source selection after candidate resolution.

Selection is a user/ChatGPT-authored decision. This script never chooses a
route; it validates the requested global Primary/Fallback path, rights state,
and resolution evidence, then emits the selected asset projection consumed by
Final Production.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


class VisualSourceSelectionError(ValueError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualSourceSelectionError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualSourceSelectionError(f"{label} root must be an object")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(f".{path.name}.visual-source.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def select(
    *,
    contract_path: Path,
    resolution_path: Path,
    selection_path: Path | None,
    selected_output: Path,
    audit_output: Path,
) -> dict[str, Any]:
    contract = load_json(contract_path, "Final Episode Contract")
    visual_sources = contract.get("visualSources") or {"contractVersion": "1.0.0", "intents": []}
    intents = visual_sources.get("intents", [])
    resolution = load_json(resolution_path, "Visual Source resolution")
    if resolution.get("episodeDate") != contract["episodeDate"]:
        raise VisualSourceSelectionError("resolution episodeDate mismatch")
    if resolution.get("finalEpisodeContractSha256") != sha256_file(contract_path):
        raise VisualSourceSelectionError("resolution Final Episode Contract SHA mismatch")

    if not intents:
        selected_path = "not-required"
        if selection_path and selection_path.is_file():
            selection = load_json(selection_path, "Visual Source selection")
            if selection.get("selectedPath") != "not-required":
                raise VisualSourceSelectionError("empty Visual Source contract requires not-required")
        selected_assets: list[dict[str, Any]] = []
    else:
        if selection_path is None or not selection_path.is_file():
            raise VisualSourceSelectionError("E_VISUAL_SOURCE_SELECTED_PATH_INVALID: selection file is required")
        selection = load_json(selection_path, "Visual Source selection")
        if selection.get("contractVersion") != "1.0.0":
            raise VisualSourceSelectionError("selection contractVersion must be 1.0.0")
        if selection.get("episodeDate") != contract["episodeDate"]:
            raise VisualSourceSelectionError("selection episodeDate mismatch")
        selected_path = selection.get("selectedPath")
        if selected_path not in {"primary", "fallback"}:
            raise VisualSourceSelectionError("E_VISUAL_SOURCE_SELECTED_PATH_INVALID")

        result_map = {
            (item.get("intentId"), item.get("path")): item
            for item in resolution.get("results", [])
            if isinstance(item, dict)
        }
        selected_assets = []
        for intent in intents:
            intent_id = intent["intentId"]
            result = result_map.get((intent_id, selected_path))
            if result is None:
                raise VisualSourceSelectionError(
                    f"E_VISUAL_SOURCE_SELECTED_PATH_INVALID: missing resolution for {intent_id}/{selected_path}"
                )
            if result.get("status") != "ready":
                raise VisualSourceSelectionError(
                    f"E_VISUAL_SOURCE_{selected_path.upper()}_UNRESOLVED: {intent_id}: {result.get('failureReason')}"
                )
            candidate = intent[selected_path]
            rights = result.get("rightsStatus")
            if candidate["sourceKind"] == "existing-asset":
                if rights not in {"cleared", "not-required"}:
                    raise VisualSourceSelectionError(
                        f"E_VISUAL_SOURCE_RIGHTS_UNRESOLVED: {intent_id}/{selected_path}"
                    )
            elif rights != "cleared":
                raise VisualSourceSelectionError(
                    f"E_VISUAL_SOURCE_RIGHTS_UNRESOLVED: {intent_id}/{selected_path} requires cleared"
                )
            selected_assets.append(
                {
                    "intentId": intent_id,
                    "sceneId": intent["target"]["sceneId"],
                    "visualBeatId": intent["target"]["visualBeatId"],
                    "presentationClass": intent["presentationClass"],
                    "selectedPath": selected_path,
                    "candidateId": candidate["candidateId"],
                    "assetId": candidate["assetId"],
                    "sourceKind": candidate["sourceKind"],
                    "rightsStatus": rights,
                    "placement": intent["placement"],
                    "outputPath": result.get("outputPath"),
                    "outputSha256": result.get("outputSha256"),
                    "mimeType": result.get("mimeType"),
                    "width": result.get("width"),
                    "height": result.get("height"),
                }
            )

    selected_document = {
        "contractVersion": "1.0.0",
        "episodeDate": contract["episodeDate"],
        "finalEpisodeContractSha256": sha256_file(contract_path),
        "resolutionLogSha256": sha256_file(resolution_path),
        "selectedPath": selected_path,
        "selectedAssets": selected_assets,
    }
    write_atomic(selected_output, selected_document)

    audit = dict(resolution)
    audit["selection"] = {
        "status": "resolved",
        "selected_path": selected_path,
        "unresolved_count": 0,
        "selected_assets": [item["assetId"] for item in selected_assets],
        "selection_file_sha256": sha256_file(selection_path)
        if selection_path and selection_path.is_file()
        else None,
        "selected_projection_sha256": sha256_file(selected_output),
    }
    audit["status"] = "resolved"
    write_atomic(audit_output, audit)
    return selected_document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--resolution", required=True, type=Path)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--selected-output", required=True, type=Path)
    parser.add_argument("--audit-output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = select(
            contract_path=args.contract,
            resolution_path=args.resolution,
            selection_path=args.selection,
            selected_output=args.selected_output,
            audit_output=args.audit_output,
        )
        code = 0
    except (VisualSourceSelectionError, OSError, KeyError, json.JSONDecodeError) as exc:
        result = {"status": "fail", "errors": str(exc).splitlines()}
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
