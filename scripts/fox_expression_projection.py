#!/usr/bin/env python3
"""Project authored fox expressions to exact pinned Renderer asset placements."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return value


def load_renderer_expression_asset_map() -> dict[str, str]:
    """Load expression -> assetId authority from the exact pinned Renderer checkout."""
    renderer_root_raw = os.environ.get("NASDAQ_CAFE_RENDERER_ROOT")
    if not renderer_root_raw:
        raise SystemExit("NASDAQ_CAFE_RENDERER_ROOT is required for fox expression projection")
    renderer_root = Path(renderer_root_raw).resolve()
    expression_path = renderer_root / "config" / "fox-expression-map.json"
    asset_manifest_path = renderer_root / "config" / "asset-manifest.json"
    if not expression_path.is_file():
        raise SystemExit(f"renderer fox expression map missing: {expression_path}")
    if not asset_manifest_path.is_file():
        raise SystemExit(f"renderer asset manifest missing: {asset_manifest_path}")

    expression_doc = _load(expression_path)
    rows = expression_doc.get("expressions")
    if not isinstance(rows, dict) or not rows:
        raise SystemExit("renderer fox expression map must contain non-empty expressions object")
    asset_doc = _load(asset_manifest_path)
    assets = asset_doc.get("assets")
    if not isinstance(assets, dict):
        raise SystemExit("renderer asset manifest must contain assets object")

    result: dict[str, str] = {}
    for expression, row in rows.items():
        if not isinstance(expression, str) or not isinstance(row, dict):
            raise SystemExit("renderer fox expression map contains an invalid entry")
        if row.get("fallback") is True:
            continue
        asset_id = row.get("assetId")
        if not isinstance(asset_id, str) or not asset_id:
            raise SystemExit(f"renderer fox expression assetId missing: {expression}")
        if asset_id not in assets:
            raise SystemExit(
                f"renderer fox expression asset is not present in asset manifest: {expression} -> {asset_id}"
            )
        result[expression] = asset_id
    if not result:
        raise SystemExit("renderer fox expression map has no production expressions")
    return result


def ensure_fox_expression_placements(
    scene: dict[str, Any],
    expression_asset_map: dict[str, str],
) -> int:
    """Add one fixed Renderer-owned placement for every authored expression in a Scene."""
    expressions: list[str] = []
    initial = scene.get("initialExpression")
    if isinstance(initial, str):
        expressions.append(initial)
    for chunk in scene.get("narrationChunks", []):
        if isinstance(chunk, dict) and isinstance(chunk.get("expression"), str):
            expressions.append(chunk["expression"])
    for event in scene.get("visualEvents", []):
        if (
            isinstance(event, dict)
            and event.get("action") == "set-expression"
            and isinstance(event.get("expression"), str)
        ):
            expressions.append(event["expression"])
    for beat in scene.get("visualBeats", []):
        if not isinstance(beat, dict):
            continue
        for shot in beat.get("shots") or []:
            if isinstance(shot, dict) and isinstance(shot.get("foxExpression"), str):
                expressions.append(shot["foxExpression"])

    required_asset_ids: list[str] = []
    for expression in dict.fromkeys(expressions):
        asset_id = expression_asset_map.get(expression)
        if asset_id is None:
            raise SystemExit(f"unsupported authored fox expression in pinned renderer: {expression}")
        required_asset_ids.append(asset_id)

    placements = scene.setdefault("assetPlacements", [])
    if not isinstance(placements, list):
        raise SystemExit(f"{scene.get('sceneId')}: assetPlacements must be a list")
    added = 0
    for asset_id in dict.fromkeys(required_asset_ids):
        matches = [
            row
            for row in placements
            if isinstance(row, dict)
            and row.get("role") == "fox-expression"
            and row.get("assetId") == asset_id
        ]
        if len(matches) > 1:
            raise SystemExit(
                f"{scene.get('sceneId')}: duplicate fox-expression placements for {asset_id}"
            )
        if matches:
            matches[0].update({
                "role": "fox-expression",
                "region": "fox-left",
                "fit": "contain",
                "opacity": 1,
                "startChunkId": None,
                "endChunkId": None,
            })
            continue
        placements.append({
            "placementId": f"{scene.get('sceneId')}-placement-{asset_id}",
            "assetId": asset_id,
            "role": "fox-expression",
            "region": "fox-left",
            "fit": "contain",
            "opacity": 1,
            "startChunkId": None,
            "endChunkId": None,
        })
        added += 1
    return added
