#!/usr/bin/env python3
"""Validate the renderer-facing Final Episode Financial Visual Contract 1.0.

This is a compatibility validator for the Financial Visual boundary that
predates Visual Grammar inclusion in Final Episode Contract 1.1. It validates
only the financial projection and never changes editorial content.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ANNEX_BEGIN = "<!--BEGIN_FINANCIAL_VISUAL_ANNEX-->"
ANNEX_END = "<!--END_FINANCIAL_VISUAL_ANNEX-->"
JSON_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
BEAT_MARKER_RE = re.compile(r"<!--VISUAL_BEAT:(scene-0[1-9]):(vb-0[1-9]-[0-9]{2})-->")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SOURCE_ID_RE = re.compile(r"^source-[0-9]{3}$")
BEAT_ID_RE = re.compile(r"^vb-0[1-9]-[0-9]{2}$")
SAFE_RELATIVE_RE = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/\-]+$")

ROOT_KEYS = {
    "contractVersion", "episodeDate", "episodePackage", "review",
    "sourceRegistry", "scenes", "financialVisuals",
}
BEAT_KEYS = {
    "visualBeatId", "headline", "screenQuestion", "startCue", "endCue",
    "returnTarget", "fallbackHeadline", "fallbackQuestion",
}
INTENT_KINDS = {
    "market-snapshot", "expectation-gap", "entity-divergence",
    "macro-transmission", "source-evidence",
}

class ContractError(ValueError):
    pass

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_json(path: Path, label: str = "JSON") -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value

def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)

def _parse_annex(markdown: str) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    if markdown.count(ANNEX_BEGIN) != 1 or markdown.count(ANNEX_END) != 1:
        raise ContractError("financial visual annex markers must appear exactly once")
    start = markdown.index(ANNEX_BEGIN)
    end = markdown.index(ANNEX_END)
    if end <= start:
        raise ContractError("financial visual annex marker order is invalid")
    block = markdown[start : end + len(ANNEX_END)]
    fences = list(JSON_FENCE_RE.finditer(block))
    if len(fences) != 1:
        raise ContractError("financial visual annex must contain exactly one JSON fence")
    try:
        annex = json.loads(fences[0].group(1))
    except json.JSONDecodeError as exc:
        raise ContractError(f"financial visual annex invalid: {exc}") from exc
    if not isinstance(annex, dict):
        raise ContractError("financial visual annex must be an object")
    public = markdown[:start] + markdown[end + len(ANNEX_END) :]
    markers = [(m.group(1), m.group(2)) for m in BEAT_MARKER_RE.finditer(public)]
    return annex, markers

def _validate_candidate(plan: dict[str, Any], schema: dict[str, Any], errors: list[str]) -> None:
    for error in sorted(Draft202012Validator(schema).iter_errors(plan), key=lambda e: list(e.path)):
        path = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path
        )
        errors.append(f"candidatePlan{path}: {error.message}")

def _validate_plan_refs(plan: dict[str, Any], beat: dict[str, Any], errors: list[str]) -> None:
    prefix = f"episode://{plan['sceneId']}/{plan['visualBeatId']}"
    suffix_headline = "headline" if plan["path"] == "preferred" else "fallbackHeadline"
    suffix_question = "screenQuestion" if plan["path"] == "preferred" else "fallbackQuestion"
    expected = {
        "headlineRef": f"{prefix}/{suffix_headline}",
        "screenQuestionRef": f"{prefix}/{suffix_question}",
        "startCueRef": f"{prefix}/startCue",
        "endCueRef": f"{prefix}/endCue",
        "returnTargetRef": f"{prefix}/returnTarget",
    }
    for key, value in expected.items():
        _require(plan.get(key) == value, f"plan {plan.get('planId')} {key} mismatch", errors)
    field = "headline" if plan["path"] == "preferred" else "fallbackHeadline"
    question = "screenQuestion" if plan["path"] == "preferred" else "fallbackQuestion"
    _require(bool(beat.get(field)), f"plan {plan.get('planId')} public headline is empty", errors)
    _require(bool(beat.get(question)), f"plan {plan.get('planId')} public question is empty", errors)

def validate_contract(
    contract_path: Path,
    repo_root: Path,
    candidate_schema_path: Path,
) -> dict[str, Any]:
    contract = load_json(contract_path, "financial Final Episode Contract")
    candidate_schema = load_json(candidate_schema_path, "candidate plan schema")
    errors: list[str] = []
    _require(set(contract) == ROOT_KEYS, f"contract root keys mismatch: {sorted(set(contract)^ROOT_KEYS)}", errors)
    _require(contract.get("contractVersion") == "1.0.0", "contractVersion must be 1.0.0", errors)
    _require(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(contract.get("episodeDate", "")))), "episodeDate invalid", errors)
    review = contract.get("review")
    _require(isinstance(review, dict), "review must be an object", errors)
    if isinstance(review, dict):
        _require(review.get("verdict") in {"approved", "approved-with-changes"}, "review verdict invalid", errors)
        _require(review.get("postInquisitionFinal") is True, "review must be post-inquisition final", errors)
        _require(review.get("approvedForProduction") is True, "review must approve production", errors)

    package_ref = contract.get("episodePackage")
    _require(isinstance(package_ref, dict), "episodePackage must be an object", errors)
    package_path: Path | None = None
    if isinstance(package_ref, dict):
        relative = package_ref.get("path")
        _require(isinstance(relative, str) and bool(SAFE_RELATIVE_RE.fullmatch(relative)), "episodePackage.path unsafe", errors)
        if isinstance(relative, str):
            package_path = (repo_root.resolve() / relative).resolve()
            _require(repo_root.resolve() in package_path.parents, "episodePackage.path escapes repository", errors)
            _require(package_path.is_file(), "episode package does not exist", errors)
            if package_path.is_file():
                _require(package_ref.get("sha256") == sha256_file(package_path), "episode package SHA mismatch", errors)
    if errors:
        raise ContractError("\n".join(errors))
    assert package_path is not None
    annex, markers = _parse_annex(package_path.read_text(encoding="utf-8"))
    _require(annex == contract.get("financialVisuals"), "financial annex and contract differ", errors)

    sources = contract.get("sourceRegistry")
    _require(isinstance(sources, list) and bool(sources), "sourceRegistry must be non-empty", errors)
    source_ids: list[str] = []
    if isinstance(sources, list):
        for source in sources:
            _require(isinstance(source, dict), "sourceRegistry item must be an object", errors)
            if not isinstance(source, dict):
                continue
            _require(set(source) == {"sourceId", "title", "publisher", "sourceType"}, "sourceRegistry item keys mismatch", errors)
            source_id = source.get("sourceId")
            _require(isinstance(source_id, str) and bool(SOURCE_ID_RE.fullmatch(source_id)), "sourceId invalid", errors)
            if isinstance(source_id, str):
                source_ids.append(source_id)
            _require(source.get("sourceType") in {"official", "company", "major-media", "analyst", "market-data", "other"}, "sourceType invalid", errors)
        _require(len(source_ids) == len(set(source_ids)), "sourceId values must be unique", errors)
    source_set = set(source_ids)

    scenes = contract.get("scenes")
    _require(isinstance(scenes, list) and len(scenes) == 9, "scenes must contain nine items", errors)
    beat_map: dict[tuple[str, str], dict[str, Any]] = {}
    if isinstance(scenes, list):
        expected_scenes = [f"scene-{index:02d}" for index in range(1, 10)]
        _require([scene.get("sceneId") for scene in scenes if isinstance(scene, dict)] == expected_scenes, "scenes must be ordered scene-01..scene-09", errors)
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            _require(set(scene) == {"sceneId", "visualBeats"}, f"{scene.get('sceneId')} keys mismatch", errors)
            scene_id = scene.get("sceneId")
            beats = scene.get("visualBeats")
            _require(isinstance(beats, list) and bool(beats), f"{scene_id} visualBeats empty", errors)
            if not isinstance(beats, list):
                continue
            for beat in beats:
                _require(isinstance(beat, dict), f"{scene_id} Beat must be an object", errors)
                if not isinstance(beat, dict):
                    continue
                _require(set(beat) == BEAT_KEYS, f"{scene_id}/{beat.get('visualBeatId')} keys mismatch", errors)
                beat_id = beat.get("visualBeatId")
                _require(isinstance(beat_id, str) and bool(BEAT_ID_RE.fullmatch(beat_id)), f"{scene_id} visualBeatId invalid", errors)
                if isinstance(scene_id, str) and isinstance(beat_id, str):
                    key = (scene_id, beat_id)
                    _require(key not in beat_map, f"duplicate Beat {key}", errors)
                    beat_map[key] = beat
                for field in BEAT_KEYS - {"visualBeatId"}:
                    _require(isinstance(beat.get(field), str) and bool(beat[field].strip()), f"{scene_id}/{beat_id} {field} empty", errors)
    marker_counts: dict[tuple[str, str], int] = {}
    for marker in markers:
        marker_counts[marker] = marker_counts.get(marker, 0) + 1
    _require(set(marker_counts) == set(beat_map), "Visual Beat marker set differs from contract", errors)
    _require(all(count == 1 for count in marker_counts.values()), "Visual Beat markers must be unique", errors)

    visuals = contract.get("financialVisuals")
    _require(isinstance(visuals, dict), "financialVisuals must be an object", errors)
    if not isinstance(visuals, dict):
        raise ContractError("\n".join(errors))
    _require(set(visuals) == {"annexVersion", "intents", "candidatePlans"}, "financialVisuals keys mismatch", errors)
    _require(visuals.get("annexVersion") == "1.0.0", "financial annexVersion invalid", errors)
    intents = visuals.get("intents")
    plans = visuals.get("candidatePlans")
    _require(isinstance(intents, list), "intents must be an array", errors)
    _require(isinstance(plans, list), "candidatePlans must be an array", errors)
    if not isinstance(intents, list) or not isinstance(plans, list):
        raise ContractError("\n".join(errors))
    for plan in plans:
        if isinstance(plan, dict):
            _validate_candidate(plan, candidate_schema, errors)
        else:
            errors.append("candidate plan must be an object")
    intent_map = {item.get("intentId"): item for item in intents if isinstance(item, dict)}
    plan_map = {item.get("planId"): item for item in plans if isinstance(item, dict)}
    _require(len(intent_map) == len(intents), "intent IDs must be unique", errors)
    _require(len(plan_map) == len(plans), "plan IDs must be unique", errors)
    referenced: set[str] = set()
    for intent_id, intent in intent_map.items():
        _require(isinstance(intent_id, str) and intent.get("intentContractVersion") == "1.1.0", "intent identity/version invalid", errors)
        _require(intent.get("kind") in INTENT_KINDS, f"intent {intent_id} kind invalid", errors)
        _require(intent.get("status") == "approved", f"intent {intent_id} not approved", errors)
        target = intent.get("target")
        _require(isinstance(target, dict), f"intent {intent_id} target missing", errors)
        target_key = (target.get("sceneId"), target.get("visualBeatId")) if isinstance(target, dict) else (None, None)
        _require(target_key in beat_map, f"intent {intent_id} target missing from contract", errors)
        declared_sources = set(intent.get("sourceIds", []))
        _require(declared_sources.issubset(source_set), f"intent {intent_id} source IDs invalid", errors)
        metric_ids = [metric.get("metricId") for metric in intent.get("metrics", []) if isinstance(metric, dict)]
        step_ids = [step.get("stepId") for step in intent.get("causalSteps", []) if isinstance(step, dict)]
        _require(len(metric_ids) == len(set(metric_ids)), f"intent {intent_id} metric IDs duplicate", errors)
        _require(len(step_ids) == len(set(step_ids)), f"intent {intent_id} step IDs duplicate", errors)
        for path_name, field in (("preferred", "preferredPlanId"), ("fallback", "fallbackPlanId")):
            plan_id = intent.get(field)
            referenced.add(plan_id)
            plan = plan_map.get(plan_id)
            _require(isinstance(plan, dict), f"intent {intent_id} {path_name} plan missing", errors)
            if not isinstance(plan, dict):
                continue
            _require(plan.get("path") == path_name, f"plan {plan_id} path mismatch", errors)
            _require(plan.get("intentId") == intent_id, f"plan {plan_id} intent mismatch", errors)
            _require((plan.get("sceneId"), plan.get("visualBeatId")) == target_key, f"plan {plan_id} target mismatch", errors)
            _require(set(plan.get("sourceIds", [])).issubset(declared_sources), f"plan {plan_id} source IDs invalid", errors)
            _require(set(plan.get("metricIds", [])).issubset(set(metric_ids)), f"plan {plan_id} metric IDs invalid", errors)
            _require(set(plan.get("causalStepIds", [])).issubset(set(step_ids)), f"plan {plan_id} step IDs invalid", errors)
            displayed = set(plan.get("metricIds", [])) | set(plan.get("causalStepIds", []))
            _require(set(plan.get("displayOrder", [])) == displayed, f"plan {plan_id} displayOrder mismatch", errors)
            beat = beat_map.get(target_key)
            if beat is not None:
                _validate_plan_refs(plan, beat, errors)
    _require(set(plan_map) == referenced, "candidatePlans must exactly match declared preferred/fallback plans", errors)
    if errors:
        raise ContractError("\n".join(errors))
    return {
        "status": "PASS", "contractVersion": "1.0.0",
        "episodeDate": contract["episodeDate"],
        "episodePackageSha256": contract["episodePackage"]["sha256"],
        "sceneCount": 9, "visualBeatCount": len(beat_map),
        "intentCount": len(intents), "candidatePlanCount": len(plans),
    }
