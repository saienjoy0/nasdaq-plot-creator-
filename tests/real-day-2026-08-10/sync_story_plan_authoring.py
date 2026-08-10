#!/usr/bin/env python3
"""Synchronize frozen H4 Story/Visual authoring with the corrected causal dossier.

TEST ONLY. This is part of fixture authoring, not Daily Production. The successful
wave-2 evidence changes the dossier contradiction wording and adds material timing
counterevidence. Story Engine requires the selected plan and script to preserve those
boundaries exactly. The same corrected authoring must also choose physically distinct
Visual Templates before H2, rather than repairing the render after production starts.
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
    script_path = root / f"working/{DATE}/story-engine/templates/story_script.template.json"
    review_path = root / f"working/{DATE}/story-engine/templates/creative_review.template.json"
    bindings_path = root / f"working/{DATE}/story-engine/story_production_bindings.json"
    dossier = load_json(dossier_path)
    plan = load_json(plan_path)
    script = load_json(script_path)
    review = load_json(review_path)
    bindings = load_json(bindings_path)

    if any(item.get("episode_date") != DATE for item in (dossier, plan, script, review)):
        raise StoryAuthoringSyncError("episode date drift")
    if bindings.get("episode_date") != DATE or bindings.get("contract_version") != "1.0.0":
        raise StoryAuthoringSyncError("story production bindings contract/date drift")

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

    retained = script.get("retained_counterevidence_ids")
    if not isinstance(retained, list):
        raise StoryAuthoringSyncError("story script retained_counterevidence_ids must be an array")
    script["retained_counterevidence_ids"] = sorted(
        {item for item in retained if isinstance(item, str) and item} | material_counter_ids
    )

    claim_05 = next(
        (
            claim
            for scene in script.get("scenes", [])
            if isinstance(scene, dict)
            for claim in scene.get("causal_claims", [])
            if isinstance(claim, dict) and claim.get("claim_id") == "claim-05"
        ),
        None,
    )
    if claim_05 is None:
        raise StoryAuthoringSyncError("claim-05 missing from story script")
    selected_confidence = selected.get("confidence")
    if selected_confidence not in {"low", "medium", "high"}:
        raise StoryAuthoringSyncError("selected angle confidence is invalid")
    claim_05["confidence"] = selected_confidence

    # The corrected authored package is reviewed as the current H4 authoring pass.
    # Creative Review v1.1 permits at most two rounds; old diagnostic round=4 must
    # not leak into the new canonical authoring snapshot.
    try:
        review_round = int(review.get("round", 1))
    except (TypeError, ValueError) as exc:
        raise StoryAuthoringSyncError("creative review round is invalid") from exc
    review["round"] = min(max(review_round, 1), 2)

    beat_overrides = bindings.get("beat_overrides")
    if not isinstance(beat_overrides, dict):
        raise StoryAuthoringSyncError("story production beat_overrides must be an object")

    # Scene 1 ends with an open Hero and the base Scene 2 also starts with a Hero.
    # Three open-hero beats in a row violate the existing Visual Grammar. Use a
    # metric board for the two confirmed BLS facts; the data and narration are unchanged.
    scene2 = beat_overrides.setdefault("scene-02-beat-001", {})
    scene2.update(
        {
            "contentType": "number-comparison",
            "visualMode": "number-comparison",
            "visualTemplate": "metric-comparison-board",
            "templateVariant": "default",
            "visualGrammarId": "evidence",
            "transitionRole": "major-shift",
        }
    )

    # Scene 3 is explicitly Expected / Actual / Gap. The old fixture used another
    # matrix immediately after Scene 2's matrix while declaring major-shift. Restore
    # the authored gap-flow template so the semantic and physical transition agree.
    scene3 = beat_overrides.get("scene-03-beat-001")
    if not isinstance(scene3, dict):
        raise StoryAuthoringSyncError("scene-03-beat-001 authored override is missing")
    scene3.update(
        {
            "contentType": "expected-actual-gap",
            "visualMode": "expected-actual-gap",
            "visualTemplate": "expected-actual-gap-flow",
            "templateVariant": "default",
            "visualGrammarId": "gap",
            "transitionRole": "major-shift",
        }
    )

    plan_digest = write_json(plan_path, plan)
    script_digest = write_json(script_path, script)
    review_digest = write_json(review_path, review)
    bindings_digest = write_json(bindings_path, bindings)
    return {
        "status": "pass",
        "episode_date": DATE,
        "central_contradiction_id": contradiction_id,
        "central_contradiction": plan["central_contradiction"],
        "selected_angle_id": selected_id,
        "material_counterevidence_ids": sorted(material_counter_ids),
        "selected_counterevidence_ids": selected["counterevidence_ids"],
        "script_retained_counterevidence_ids": script["retained_counterevidence_ids"],
        "claim_05_confidence": claim_05["confidence"],
        "creative_review_round": review["round"],
        "visual_authoring": {
            "scene-02-beat-001": {
                "visualTemplate": scene2["visualTemplate"],
                "visualGrammarId": scene2["visualGrammarId"],
                "transitionRole": scene2["transitionRole"],
            },
            "scene-03-beat-001": {
                "visualTemplate": scene3["visualTemplate"],
                "visualGrammarId": scene3["visualGrammarId"],
                "transitionRole": scene3["transitionRole"],
            },
        },
        "story_plan_template_sha256": plan_digest,
        "story_script_template_sha256": script_digest,
        "creative_review_template_sha256": review_digest,
        "story_production_bindings_sha256": bindings_digest,
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
