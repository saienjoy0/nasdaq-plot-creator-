#!/usr/bin/env python3
"""Synchronize frozen H4 Story Plan authoring with the corrected causal dossier.

TEST ONLY. This is part of fixture authoring, not Daily Production. The successful
wave-2 evidence changes the dossier contradiction wording and adds material timing
counterevidence. Story Plan v1.2 requires the selected plan to preserve both exactly.
This helper derives those required values from the dossier instead of hard-coding a
second editorial truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DATE = "2026-08-10"


class StoryAuthoringSyncError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StoryAuthoringSyncError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise StoryAuthoringSyncError(f"JSON root must be an object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temp = path.with_name(f".{path.name}.h4-story.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sync(*, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    dossier_path = root / f"research/{DATE}/causal_research_dossier_{DATE}.json"
    plan_path = root / f"working/{DATE}/story-engine/templates/story_plan.template.json"
    dossier = load_json(dossier_path)
    plan = load_json(plan_path)

    if dossier.get("episode_date") != DATE or plan.get("episode_date") != DATE:
        raise StoryAuthoringSyncError("episode date drift")

    contradiction_id = plan.get("central_contradiction_id")
    contradiction = next(
        (
            item
            for item in dossier.get("contradictions", [])
            if isinstance(item, dict) and item.get("id") == contradiction_id
        ),
        None,
    )
    if contradiction is None or not isinstance(contradiction.get("statement"), str):
        raise StoryAuthoringSyncError(
            f"central contradiction missing from dossier: {contradiction_id}"
        )
    plan["central_contradiction"] = contradiction["statement"]

    selected_id = plan.get("selected_angle_id")
    selected = next(
        (
            item
            for item in plan.get("angle_candidates", [])
            if isinstance(item, dict) and item.get("id") == selected_id
        ),
        None,
    )
    if selected is None:
        raise StoryAuthoringSyncError(f"selected angle missing: {selected_id}")

    material_counter_ids = {
        evidence_id
        for item in dossier.get("contrary_evidence", [])
        if isinstance(item, dict) and item.get("effect_on_confidence") == "material"
        for evidence_id in item.get("evidence_ids", [])
        if isinstance(evidence_id, str) and evidence_id
    }
    if not material_counter_ids:
        raise StoryAuthoringSyncError("corrected dossier has no material counterevidence")

    current = selected.get("counterevidence_ids")
    if not isinstance(current, list):
        raise StoryAuthoringSyncError("selected angle counterevidence_ids must be an array")
    selected["counterevidence_ids"] = sorted(
        {item for item in current if isinstance(item, str) and item} | material_counter_ids
    )

    dossier_evidence_ids = {
        item.get("evidence_id")
        for item in dossier.get("evidence", [])
        if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
    }
    unknown = sorted(set(selected["counterevidence_ids"]) - dossier_evidence_ids)
    if unknown:
        raise StoryAuthoringSyncError(
            f"selected angle counterevidence references unknown dossier evidence: {unknown}"
        )

    digest = write_json(plan_path, plan)
    return {
        "status": "pass",
        "episode_date": DATE,
        "central_contradiction_id": contradiction_id,
        "central_contradiction": plan["central_contradiction"],
        "selected_angle_id": selected_id,
        "material_counterevidence_ids": sorted(material_counter_ids),
        "selected_counterevidence_ids": selected["counterevidence_ids"],
        "story_plan_template_sha256": digest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = sync(repo_root=args.repo_root.resolve())
    except StoryAuthoringSyncError as exc:
        print(json.dumps({"status": "fail", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2

    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output
        if not output.is_absolute():
            output = args.repo_root.resolve() / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
