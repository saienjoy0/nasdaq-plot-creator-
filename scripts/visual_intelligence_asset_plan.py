#!/usr/bin/env python3
"""Bind Provisional Direction image requirements to existing Visual Source planning.

This validator does not choose Primary/Fallback and does not create images. It only
ensures a Beat declared as image-required has a pre-authored Visual Source Intent
before resolution begins. `possible` may legally proceed without an intent; a
resolved Approved Fallback remains handled by the existing asset resolver.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class VisualIntelligenceAssetPlanError(ValueError):
    pass


def load(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VisualIntelligenceAssetPlanError(f"{label} must be an object")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(
    *, requirements: dict[str, Any], visual_sources: dict[str, Any], episode_date: str
) -> dict[str, Any]:
    if requirements.get("episodeDate") != episode_date:
        raise VisualIntelligenceAssetPlanError("Visual Requirements episodeDate mismatch")
    if visual_sources.get("episodeDate") != episode_date:
        raise VisualIntelligenceAssetPlanError("Visual Source intent episodeDate mismatch")
    reqs = requirements.get("provisionalDirection", {}).get("requirements")
    intents = visual_sources.get("intents")
    if not isinstance(reqs, list) or not isinstance(intents, list):
        raise VisualIntelligenceAssetPlanError("requirements/intents must be arrays")
    intent_beats: dict[str, dict[str, Any]] = {}
    for intent in intents:
        if not isinstance(intent, dict):
            raise VisualIntelligenceAssetPlanError("Visual Source intent must be an object")
        target = intent.get("target")
        beat_id = target.get("visualBeatId") if isinstance(target, dict) else None
        if not isinstance(beat_id, str):
            raise VisualIntelligenceAssetPlanError("Visual Source intent target.visualBeatId missing")
        if beat_id in intent_beats:
            raise VisualIntelligenceAssetPlanError(f"duplicate Visual Source intent for {beat_id}")
        intent_beats[beat_id] = intent
    required_beats: list[str] = []
    missing: list[str] = []
    for requirement in reqs:
        if not isinstance(requirement, dict):
            raise VisualIntelligenceAssetPlanError("Provisional Direction item must be an object")
        beat_id = requirement.get("visualBeatId")
        image_requirement = requirement.get("imageRequirement")
        if image_requirement == "required":
            required_beats.append(str(beat_id))
            if beat_id not in intent_beats:
                missing.append(str(beat_id))
    if missing:
        raise VisualIntelligenceAssetPlanError(
            "image-required Beats lack Primary/Approved Fallback planning: " + ", ".join(missing)
        )
    return {
        "status": "PASS",
        "episodeDate": episode_date,
        "requiredImageBeatCount": len(required_beats),
        "plannedIntentCount": len(intents),
        "requiredImageBeats": required_beats,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", required=True, type=Path)
    parser.add_argument("--visual-source-intents", required=True, type=Path)
    parser.add_argument("--date", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = validate(
            requirements=load(args.requirements, "Visual Requirements"),
            visual_sources=load(args.visual_source_intents, "Visual Source intents"),
            episode_date=args.date,
        )
        result["requirementsSha256"] = sha256_file(args.requirements)
        result["visualSourceIntentsSha256"] = sha256_file(args.visual_source_intents)
        code = 0
    except (OSError, json.JSONDecodeError, VisualIntelligenceAssetPlanError) as exc:
        result = {"status": "FAIL", "episodeDate": args.date, "errors": [str(exc)]}
        code = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
