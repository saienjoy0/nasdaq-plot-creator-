#!/usr/bin/env python3
"""Project existing Financial Visual evidence into provider metadata.

This adapter deliberately omits selectedVisualTemplateId, selectedPath and other
final editorial-selection fields. It describes only objective financial evidence
and eligibility inputs for the Visual Candidate Builder/Director.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class FinancialCandidateProviderError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _selected_objects(scene: dict[str, Any], beat: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    selected = set(beat.get("objectIds", []))
    return {
        "cards": [item for item in scene.get("cards", []) if item.get("cardId") in selected],
        "numbers": [item for item in scene.get("numbers", []) if item.get("numberId") in selected],
        "nodes": [item for item in scene.get("nodes", []) if item.get("nodeId") in selected],
        "arrows": [item for item in scene.get("arrows", []) if item.get("arrowId") in selected],
    }


def build(render: dict[str, Any]) -> dict[str, Any]:
    episode = render.get("episode")
    if not isinstance(episode, dict) or not isinstance(episode.get("targetDate"), str):
        raise FinancialCandidateProviderError("render episode.targetDate missing")
    beats: list[dict[str, Any]] = []
    for scene in render.get("scenes", []):
        if not isinstance(scene, dict):
            continue
        for beat in scene.get("visualBeats", []):
            if not isinstance(beat, dict):
                continue
            trace = beat.get("financialVisualTrace")
            if not isinstance(trace, dict):
                continue
            inventory = _selected_objects(scene, beat)
            role_cards = {
                role: [card for card in inventory["cards"] if card.get("role") == role]
                for role in ("expected", "actual", "gap")
            }
            reaction = (beat.get("templateConfig") or {}).get("reactionTimeline")
            verified_series = isinstance(reaction, dict) and reaction.get("precision") == "verified-intraday-series"
            beats.append({
                "visualBeatId": beat.get("beatId"),
                "financialIntentId": trace.get("intentId"),
                "recipeId": trace.get("recipeId"),
                "recipePlanSha256": trace.get("recipePlanSha256"),
                "sourceIds": list(trace.get("sourceIds", [])),
                "metricIds": list(trace.get("metricIds", [])),
                "causalStepIds": list(trace.get("causalStepIds", [])),
                "displayOrder": list(trace.get("displayOrder", [])),
                "comparisonBasis": trace.get("comparisonBasis"),
                "reasonCodes": list(trace.get("reasonCodes", [])),
                "metricInventory": inventory["numbers"],
                "expectedActualGap": role_cards,
                "causalInventory": {"nodes": inventory["nodes"], "arrows": inventory["arrows"]},
                "verifiedReactionData": {
                    "available": verified_series,
                    "precision": reaction.get("precision") if isinstance(reaction, dict) else None,
                    "seriesObjectIds": list(reaction.get("seriesObjectIds", [])) if isinstance(reaction, dict) else [],
                },
                "eligibility": {
                    "financialTracePresent": True,
                    "numericMetricCount": sum(1 for item in inventory["numbers"] if isinstance(item.get("numericValue"), (int, float))),
                },
            })
    provider = {
        "contractVersion": "1.0.0",
        "episodeDate": episode["targetDate"],
        "sourceRenderSpecSha256": sha256_json(render),
        "beats": beats,
    }
    forbidden = {"selectedVisualTemplateId", "selectedPath", "selectedPlanId"}
    encoded = json.dumps(provider, ensure_ascii=False)
    for field in forbidden:
        if field in encoded:
            raise FinancialCandidateProviderError(f"provider leaked final selection field: {field}")
    return provider


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
