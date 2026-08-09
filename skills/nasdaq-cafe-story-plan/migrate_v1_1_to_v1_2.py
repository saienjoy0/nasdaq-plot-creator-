#!/usr/bin/env python3
"""Migrate Story Plan v1.1 field names into a v1.2 review candidate.

This adapter is mechanical. Its output is not an editorial PASS: the resulting
continuation reasons still require the normal Story Plan / 04 meaning review.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

PROCEDURAL_MARKERS = ("次に", "続いて", "確認", "整理", "見ていく", "見ます")


def classify_continuation(text: str) -> str:
    value = text.strip()
    if not value:
        return "empty"
    if any(marker in value for marker in PROCEDURAL_MARKERS):
        return "procedural_review_required"
    if value.endswith(("?", "？")):
        return "question"
    return "semantic_review_required"


def migrate(source: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if source.get("contract_version") != "1.1.0":
        raise ValueError("source Story Plan must use contract_version 1.1.0")

    target = copy.deepcopy(source)
    target["contract_version"] = "1.2.0"
    scene_reports: list[dict[str, Any]] = []

    scenes = target.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 9:
        raise ValueError("source Story Plan must contain exactly nine scenes")

    for index, scene in enumerate(scenes, start=1):
        if "remaining_question" not in scene:
            raise ValueError(f"scene-{index:02d} missing remaining_question")
        old = str(scene.pop("remaining_question") or "")
        continuation = old if index <= 7 else ""
        scene["continuation_reason"] = continuation
        scene_reports.append({
            "scene_id": scene.get("scene_id", f"scene-{index:02d}"),
            "legacy_remaining_question": old,
            "migrated_continuation_reason": continuation,
            "classification": classify_continuation(continuation),
            "closure_discarded_legacy_text": old if index in {8, 9} and old else "",
        })

    report = {
        "migration": "story_plan_v1.1_to_v1.2",
        "status": "review_required",
        "reason": "Mechanical field migration cannot determine whether belief change, payoff, or continuation quality is editorially natural.",
        "scene_reports": scene_reports,
    }
    return target, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    source = json.loads(args.input.read_text(encoding="utf-8"))
    target, report = migrate(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(target, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
