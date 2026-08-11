#!/usr/bin/env python3
"""Deterministically validate NASDAQ Cafe Story Plan v1.2 against a causal dossier."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCHEMA = ROOT / "skills/nasdaq-cafe-story-plan/contracts/story_plan.schema.json"


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "pass" if self.ok else "fail",
            "errors": self.errors,
            "warnings": self.warnings,
        }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_path(parts: Iterable[Any]) -> str:
    values = list(parts)
    return ".".join(str(value) for value in values) or "<root>"


def schema_errors(instance: Any, schema_path: Path) -> list[str]:
    try:
        schema = load_json(schema_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"schema: cannot load {schema_path}: {exc}"]
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"story_plan.{json_path(error.absolute_path)}: {error.message}"
        for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    ]


def resolve_repo_file(value: str, repo_root: Path, label: str, errors: list[str]) -> Path | None:
    candidate = Path(value)
    if candidate.is_absolute():
        errors.append(f"{label}: absolute path forbidden: {value}")
        return None
    root = repo_root.resolve()
    resolved = (root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        errors.append(f"{label}: path escapes repository root: {value}")
        return None
    if not resolved.is_file():
        errors.append(f"{label}: referenced file does not exist: {value}")
        return None
    return resolved


def evidence_refs(plan: dict[str, Any]) -> list[tuple[str, list[str]]]:
    refs: list[tuple[str, list[str]]] = []
    for item in plan["naive_explanations"]:
        refs.append((f"naive {item['id']}", item["evidence_ids"]))
    for item in plan["angle_candidates"]:
        refs.append((f"angle {item['id']}", item["evidence_ids"]))
        refs.append((f"angle {item['id']} counterevidence", item["counterevidence_ids"]))
    refs.append(("midpoint_turn", plan["midpoint_turn"]["evidence_ids"]))
    for loop in plan["open_loops"]:
        refs.append((f"open loop {loop['id']}", loop["promised_evidence_ids"]))
    for scene in plan["scenes"]:
        refs.append((scene["scene_id"], scene["new_evidence_ids"]))
    return refs


def scene_number(scene_id: str) -> int:
    return int(scene_id.split("-")[1])


def normalize_question(value: str) -> str:
    return "".join(value.lower().split()).strip("?？。.!！")


def normalize_understanding(value: str) -> str:
    """Normalize only for obvious structural equality checks, never semantic scoring."""
    return "".join(value.lower().split()).strip("?？。.!！,，、:：;；『』「」()（）[]【】")


def confidence_rank(value: str) -> int:
    return {"unknown": 0, "low": 1, "medium": 2, "high": 3}[value]


def validate_story_plan(
    story_plan_path: Path,
    causal_dossier_path: Path,
    *,
    repo_root: Path,
    schema_path: Path = DEFAULT_SCHEMA,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    root = repo_root.resolve()

    for label, supplied in (("story plan", story_plan_path), ("causal dossier", causal_dossier_path)):
        resolved = supplied.resolve()
        if resolved != root and root not in resolved.parents:
            errors.append(f"{label}: supplied path escapes repository root: {supplied}")
        elif not resolved.is_file():
            errors.append(f"{label}: file does not exist: {supplied}")
    if errors:
        return ValidationResult(sorted(set(errors)), warnings)

    try:
        plan = load_json(story_plan_path)
        dossier = load_json(causal_dossier_path)
    except (OSError, json.JSONDecodeError) as exc:
        return ValidationResult([f"cannot read validation input: {exc}"], [])

    errors.extend(schema_errors(plan, schema_path))
    if errors:
        return ValidationResult(sorted(set(errors)), warnings)

    if plan["episode_date"] != dossier.get("episode_date"):
        errors.append(
            f"episode date mismatch: story_plan={plan['episode_date']} dossier={dossier.get('episode_date')}"
        )

    dossier_ref = plan["causal_dossier"]
    resolved_ref = resolve_repo_file(dossier_ref["path"], root, "causal_dossier", errors)
    if resolved_ref:
        if resolved_ref != causal_dossier_path.resolve():
            errors.append("story plan causal_dossier.path does not resolve to supplied dossier")
        actual_sha = sha256_file(resolved_ref)
        if actual_sha != dossier_ref["sha256"]:
            errors.append(
                f"causal dossier SHA-256 mismatch: declared={dossier_ref['sha256']} actual={actual_sha}"
            )

    evidence = {item.get("evidence_id"): item for item in dossier.get("evidence", [])}
    if None in evidence:
        errors.append("dossier contains evidence without evidence_id")
    if len(evidence) != len(dossier.get("evidence", [])):
        errors.append("dossier contains duplicate evidence_id")
    for label, refs in evidence_refs(plan):
        for evidence_id in refs:
            if evidence_id not in evidence:
                errors.append(f"{label}: unknown evidence id {evidence_id}")

    contradictions = {item.get("id"): item for item in dossier.get("contradictions", [])}
    contradiction = contradictions.get(plan["central_contradiction_id"])
    if not contradiction:
        errors.append(
            f"central_contradiction_id not found in dossier: {plan['central_contradiction_id']}"
        )
    elif plan["central_contradiction"] != contradiction.get("statement"):
        errors.append("central_contradiction must exactly preserve the dossier contradiction statement")

    expected_discovery = dossier.get("editorial_handoff", {}).get("headline_beyond_discovery")
    if expected_discovery and plan["headline_beyond_discovery"] != expected_discovery:
        errors.append("headline_beyond_discovery must exactly preserve editorial_handoff value")

    angles = plan["angle_candidates"]
    angle_ids = [item["id"] for item in angles]
    if len(angle_ids) != len(set(angle_ids)):
        errors.append("angle candidate ids must be unique")
    selected = next((item for item in angles if item["id"] == plan["selected_angle_id"]), None)
    if selected is None:
        errors.append("selected_angle_id does not reference an angle candidate")
    else:
        dossier_confidence = dossier.get("editorial_handoff", {}).get("confidence", "unknown")
        if dossier_confidence not in {"high", "medium", "low", "unknown"}:
            errors.append(f"unsupported dossier editorial confidence: {dossier_confidence}")
        elif confidence_rank(selected["confidence"]) > confidence_rank(dossier_confidence):
            errors.append(
                f"selected angle confidence strengthens dossier confidence: {dossier_confidence} -> {selected['confidence']}"
            )

        wide_edges = [edge for edge in dossier.get("causal_edges", []) if edge.get("scope") == "nasdaq_wide"]
        high_wide = any(edge.get("confidence") == "high" for edge in wide_edges)
        if selected["causality_scope"] == "nasdaq_primary" and not high_wide:
            errors.append("nasdaq_primary requires at least one high-confidence nasdaq_wide dossier edge")
        if selected["causality_scope"] == "nasdaq_support" and not wide_edges:
            errors.append("nasdaq_support requires at least one nasdaq_wide dossier edge")
        if selected["causality_scope"] == "sector" and not any(
            edge.get("scope") in {"sector_support", "nasdaq_wide"}
            for edge in dossier.get("causal_edges", [])
        ):
            errors.append("sector scope lacks sector_support or nasdaq_wide dossier evidence")
        if selected["causality_scope"] == "reason_unknown" and selected["confidence"] != "unknown":
            errors.append("reason_unknown selected angle must use unknown confidence")

        if plan["central_question"] != selected["central_question"]:
            errors.append("central_question must match the selected angle")
        if plan["story_spine"] != selected["story_spine"]:
            errors.append("story_spine must match the selected angle")
        if plan["opening_promise"] != selected["opening_promise"]:
            errors.append("opening_promise must match the selected angle")
        if plan["midpoint_turn"]["claim"] != selected["midpoint_turn_claim"]:
            errors.append("midpoint_turn.claim must match the selected angle")
        if plan["closing_reframe"]["text"] != selected["closing_reframe"]:
            errors.append("closing_reframe.text must match the selected angle")

        material_counter_ids = {
            evidence_id
            for item in dossier.get("contrary_evidence", [])
            if item.get("effect_on_confidence") == "material"
            for evidence_id in item.get("evidence_ids", [])
        }
        selected_counter_ids = set(selected["counterevidence_ids"])
        missing_counter = sorted(material_counter_ids - selected_counter_ids)
        if missing_counter:
            errors.append(
                f"selected angle omits material counterevidence ids: {missing_counter}"
            )

    normalized_questions = [normalize_question(item["central_question"]) for item in angles]
    if len(normalized_questions) != len(set(normalized_questions)):
        errors.append("angle candidates must have distinct central questions")

    expected_scene_ids = [f"scene-{i:02d}" for i in range(1, 10)]
    actual_scene_ids = [scene["scene_id"] for scene in plan["scenes"]]
    if actual_scene_ids != expected_scene_ids:
        errors.append(f"scenes must be exactly ordered {expected_scene_ids}")

    formal_roles = [
        "direction_and_conclusion",
        "contradiction",
        "confirmed_facts",
        "expected_actual_gap",
        "global_context",
        "market_reaction",
        "entity_divergence",
        "validation_points",
        "fixed_closing",
    ]
    actual_roles = [scene["formal_role"] for scene in plan["scenes"]]
    if actual_roles != formal_roles:
        errors.append("scene formal roles do not match the fixed 03 nine-scene skeleton")

    # Understanding Progression Contract: Scenes 1-8 must produce a concrete
    # market-understanding payoff. Scene 1-7 must also establish a rational
    # continuation reason. Scene 8 closes the narrative instead of opening one.
    for scene in plan["scenes"][:8]:
        scene_id = scene["scene_id"]
        before = scene["viewer_belief_before"].strip()
        after = scene["viewer_belief_after"].strip()
        if not before:
            errors.append(f"{scene_id}: viewer_belief_before is required")
        if not scene["new_meaning"].strip():
            errors.append(f"{scene_id}: new_meaning payoff is required")
        if not after:
            errors.append(f"{scene_id}: viewer_belief_after is required")
        if before and after and normalize_understanding(before) == normalize_understanding(after):
            errors.append(f"{scene_id}: viewer understanding must change structurally from before to after")

    for scene in plan["scenes"][:7]:
        if not scene["continuation_reason"].strip():
            errors.append(f"{scene['scene_id']}: continuation_reason is required for Scenes 1-7")

    scene_08 = plan["scenes"][7]
    if scene_08["continuation_reason"].strip():
        errors.append("scene-08: continuation_reason must be empty because Scene 8 closes the story")

    # Late-value structural guard. This is intentionally only an obvious-equality
    # check; semantic late value remains an Entertainment Critic responsibility.
    scene_04 = plan["scenes"][3]
    if normalize_understanding(scene_04["viewer_belief_after"]) == normalize_understanding(scene_08["viewer_belief_after"]):
        errors.append("scene-08 understanding must be structurally deeper/different than scene-04 understanding")

    if normalize_understanding(plan["opening_promise"]) == normalize_understanding(plan["closing_reframe"]["text"]):
        errors.append("closing_reframe must not merely repeat the opening_promise")

    closing = plan["scenes"][8]
    if closing["new_evidence_ids"]:
        errors.append("scene-09: fixed closing cannot add new evidence")
    if closing["new_meaning"].strip():
        errors.append("scene-09: fixed closing cannot add new narrative meaning")
    if closing["continuation_reason"].strip():
        errors.append("scene-09: fixed closing cannot leave a continuation reason")
    if closing["connector"] != "closing":
        errors.append("scene-09: connector must be closing")

    # Legacy field name `midpoint_turn` now carries the semantic contract of an
    # evidence-backed Understanding Upgrade. Do not allow an evidence-free turn.
    turn_scene = plan["midpoint_turn"]["scene_id"]
    if turn_scene not in {"scene-04", "scene-05", "scene-06"}:
        errors.append("understanding upgrade must be in scene-04 through scene-06")
    if not plan["midpoint_turn"]["evidence_ids"]:
        errors.append("understanding upgrade must be backed by at least one evidence id")
    if not plan["midpoint_turn"]["what_changes"].strip():
        errors.append("understanding upgrade must state what changes in the explanatory model")
    turn_plan_scene = next((s for s in plan["scenes"] if s["scene_id"] == turn_scene), None)
    if turn_plan_scene:
        if not turn_plan_scene["new_meaning"].strip():
            errors.append(f"{turn_scene}: understanding-upgrade scene must add new meaning")
        if normalize_understanding(turn_plan_scene["viewer_belief_before"]) == normalize_understanding(turn_plan_scene["viewer_belief_after"]):
            errors.append(f"{turn_scene}: understanding-upgrade scene must change viewer understanding")

    if plan["closing_reframe"]["scene_id"] != "scene-08":
        errors.append("closing reframe must occur in scene-08")

    loop_ids: set[str] = set()
    for loop in plan["open_loops"]:
        if loop["id"] in loop_ids:
            errors.append(f"duplicate open loop id: {loop['id']}")
        loop_ids.add(loop["id"])
        open_num = scene_number(loop["open_scene"])
        close_num = scene_number(loop["close_scene"])
        if close_num <= open_num:
            errors.append(f"{loop['id']}: close_scene must come after open_scene")
        if close_num > 8:
            errors.append(f"{loop['id']}: open loops must close by scene-08")

    # A no-new-evidence late section can still be valid if it creates a new
    # interpretation from earlier evidence, so emit only a warning and leave the
    # semantic deletion test to the Critic.
    seen_before_late = {
        evidence_id
        for scene in plan["scenes"][:5]
        for evidence_id in scene["new_evidence_ids"]
    }
    late_evidence = {
        evidence_id
        for scene in plan["scenes"][5:8]
        for evidence_id in scene["new_evidence_ids"]
    }
    if late_evidence and late_evidence.issubset(seen_before_late):
        warnings.append(
            "Scenes 6-8 introduce no structurally new evidence ids; Entertainment Critic must verify that reinterpretation still creates distinct late value"
        )

    if len(angles) < 3:
        errors.append("at least three angle candidates are required")

    return ValidationResult(sorted(set(errors)), sorted(set(warnings)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--story-plan", type=Path, required=True)
    parser.add_argument("--causal-dossier", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_story_plan(
        args.story_plan,
        args.causal_dossier,
        repo_root=args.repo_root,
        schema_path=args.schema,
    )
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
