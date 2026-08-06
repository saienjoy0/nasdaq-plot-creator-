#!/usr/bin/env python3
"""Validate the NASDAQ Cafe Final Episode Contract 1.1.0.

This validator is deterministic. It verifies that the post-inquisition Episode
Package, its financial annex, its Visual Grammar annex, the Visual Grammar
sidecar, target Visual Beat IDs, sources, and complete preferred/fallback plans
agree. It never chooses editorial meaning, selects a recipe, or changes text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

import visual_grammar_contract as visual_grammar_module

FINANCIAL_ANNEX_BEGIN = "<!--BEGIN_FINANCIAL_VISUAL_ANNEX-->"
FINANCIAL_ANNEX_END = "<!--END_FINANCIAL_VISUAL_ANNEX-->"
VISUAL_GRAMMAR_ANNEX_BEGIN = "<!--BEGIN_VISUAL_GRAMMAR_ANNEX-->"
VISUAL_GRAMMAR_ANNEX_END = "<!--END_VISUAL_GRAMMAR_ANNEX-->"
# Backward-compatible aliases used by existing tests and tooling.
ANNEX_BEGIN = FINANCIAL_ANNEX_BEGIN
ANNEX_END = FINANCIAL_ANNEX_END
JSON_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
BEAT_MARKER_RE = re.compile(r"<!--VISUAL_BEAT:(scene-0[1-9]):(vb-0[1-9]-[0-9]{2})-->")
SAFE_RELATIVE_RE = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/\-]+$")


class ContractError(ValueError):
    """Raised when Final Episode Contract artifacts disagree."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(
            f"invalid JSON at {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(payload, dict):
        raise ContractError(f"JSON root must be an object: {path}")
    return payload


def _safe_repo_file(repo_root: Path, file_ref: dict[str, Any], label: str) -> Path:
    errors: list[str] = []
    relative = file_ref["path"]
    _require(
        bool(SAFE_RELATIVE_RE.fullmatch(relative)),
        f"{label}.path must be a safe repository-relative path: {relative}",
        errors,
    )
    root_resolved = repo_root.resolve()
    path = (repo_root / relative).resolve()
    _require(
        path == root_resolved or root_resolved in path.parents,
        f"{label}.path escapes repo root: {relative}",
        errors,
    )
    if errors:
        raise ContractError("\n".join(errors))
    if not path.is_file():
        raise ContractError(f"{label} does not exist: {relative}")
    actual_sha = sha256_file(path)
    if actual_sha != file_ref["sha256"]:
        raise ContractError(
            f"{label} SHA mismatch: expected={file_ref['sha256']} actual={actual_sha}"
        )
    return path


def _parse_json_annex(markdown: str, begin: str, end: str, label: str) -> dict[str, Any]:
    begin_count = markdown.count(begin)
    end_count = markdown.count(end)
    if begin_count != 1 or end_count != 1:
        raise ContractError(
            f"{label} annex markers must appear exactly once: "
            f"begin={begin_count} end={end_count}"
        )
    start = markdown.index(begin)
    end_marker = markdown.index(end)
    if end_marker <= start:
        raise ContractError(f"{label} annex end marker appears before begin marker")
    block = markdown[start : end_marker + len(end)]
    fences = list(JSON_FENCE_RE.finditer(block))
    if len(fences) != 1:
        raise ContractError(
            f"{label} annex must contain exactly one JSON fence: found={len(fences)}"
        )
    try:
        annex = json.loads(fences[0].group(1))
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid {label} annex JSON: {exc}") from exc
    if not isinstance(annex, dict):
        raise ContractError(f"{label} annex JSON must be an object")
    return annex


def parse_financial_annex(markdown: str) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    annex = _parse_json_annex(
        markdown,
        FINANCIAL_ANNEX_BEGIN,
        FINANCIAL_ANNEX_END,
        "financial visual",
    )
    markers = [
        (match.group(1), match.group(2))
        for match in BEAT_MARKER_RE.finditer(markdown)
    ]
    return annex, markers


def parse_visual_grammar_annex(markdown: str) -> dict[str, Any]:
    return _parse_json_annex(
        markdown,
        VISUAL_GRAMMAR_ANNEX_BEGIN,
        VISUAL_GRAMMAR_ANNEX_END,
        "Visual Grammar",
    )


def _schema_errors(
    contract: dict[str, Any],
    final_schema: dict[str, Any],
    candidate_schema: dict[str, Any],
) -> list[str]:
    candidate_uri = candidate_schema["$id"]
    registry = Registry().with_resource(
        candidate_uri, Resource.from_contents(candidate_schema)
    )
    validator = Draft202012Validator(final_schema, registry=registry)
    errors: list[str] = []
    for error in sorted(validator.iter_errors(contract), key=lambda item: list(item.path)):
        location = "$"
        if error.path:
            location += "".join(
                f"[{part}]" if isinstance(part, int) else f".{part}"
                for part in error.path
            )
        errors.append(f"{location}: {error.message}")
    return errors


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _validate_plan_refs(plan: dict[str, Any], beat: dict[str, Any], errors: list[str]) -> None:
    prefix = f"episode://{plan['sceneId']}/{plan['visualBeatId']}"
    expected_refs = {
        "startCueRef": f"{prefix}/startCue",
        "endCueRef": f"{prefix}/endCue",
        "returnTargetRef": f"{prefix}/returnTarget",
    }
    headline_suffix = "headline" if plan["path"] == "preferred" else "fallbackHeadline"
    question_suffix = "screenQuestion" if plan["path"] == "preferred" else "fallbackQuestion"
    expected_refs["headlineRef"] = f"{prefix}/{headline_suffix}"
    expected_refs["screenQuestionRef"] = f"{prefix}/{question_suffix}"
    for key, expected in expected_refs.items():
        _require(
            plan[key] == expected,
            f"plan {plan['planId']} {key} must equal {expected}",
            errors,
        )
    if plan["path"] == "preferred":
        _require(bool(beat.get("headline")), f"plan {plan['planId']} preferred headline is empty", errors)
        _require(bool(beat.get("screenQuestion")), f"plan {plan['planId']} preferred question is empty", errors)
    else:
        _require(bool(beat.get("fallbackHeadline")), f"plan {plan['planId']} fallback headline is empty", errors)
        _require(bool(beat.get("fallbackQuestion")), f"plan {plan['planId']} fallback question is empty", errors)


def _sidecar_projection(contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "episodeDate": contract["episodeDate"],
        "visualGrammarContractVersion": contract["visualGrammarContractVersion"],
        "expectedConfirmed": contract["expectedConfirmed"],
        "scene5CausalExceptionReason": contract["scene5CausalExceptionReason"],
        "scenes": [
            {
                "sceneId": scene["sceneId"],
                "visualBeats": [
                    {
                        "visualBeatId": beat["visualBeatId"],
                        "visualGrammar": beat["visualGrammar"],
                    }
                    for beat in scene["visualBeats"]
                ],
            }
            for scene in contract["scenes"]
        ],
    }


def validate_contract(
    contract_path: Path,
    repo_root: Path,
    final_schema_path: Path,
    candidate_schema_path: Path,
    visual_grammar_registry_path: Path = Path("contracts/visual_grammar_semantics.json"),
    visual_grammar_registry_schema_path: Path = Path("contracts/visual_grammar_semantics.schema.json"),
) -> dict[str, Any]:
    contract = load_json(contract_path)
    final_schema = load_json(final_schema_path)
    candidate_schema = load_json(candidate_schema_path)
    errors = _schema_errors(contract, final_schema, candidate_schema)
    if errors:
        raise ContractError("\n".join(errors))

    package_path = _safe_repo_file(repo_root, contract["episodePackage"], "episodePackage")
    sidecar_path = _safe_repo_file(
        repo_root, contract["visualGrammarSidecar"], "visualGrammarSidecar"
    )
    actual_package_sha = sha256_file(package_path)
    actual_sidecar_sha = sha256_file(sidecar_path)

    markdown = package_path.read_text(encoding="utf-8")
    financial_annex, markers = parse_financial_annex(markdown)
    visual_grammar_annex = parse_visual_grammar_annex(markdown)
    sidecar = load_json(sidecar_path)
    expected_sidecar = _sidecar_projection(contract)

    _require(
        financial_annex == contract["financialVisuals"],
        "financial visual annex does not byte-semantically mirror final contract financialVisuals",
        errors,
    )
    _require(
        financial_annex.get("episodeDate") in {None, contract["episodeDate"]},
        "financial visual annex episodeDate disagrees with final contract",
        errors,
    )
    _require(
        visual_grammar_annex == sidecar,
        "Visual Grammar annex does not byte-semantically mirror sidecar",
        errors,
    )
    _require(
        sidecar == expected_sidecar,
        "Visual Grammar sidecar does not byte-semantically mirror final contract",
        errors,
    )

    module_root = Path(__file__).resolve().parents[1]

    def resolve_contract_support(path: Path) -> Path:
        if path.is_absolute():
            return path
        repo_candidate = repo_root / path
        if repo_candidate.is_file():
            return repo_candidate
        return module_root / path

    registry_path = resolve_contract_support(visual_grammar_registry_path)
    registry_schema_path = resolve_contract_support(
        visual_grammar_registry_schema_path
    )
    registry = load_json(registry_path)
    registry_schema = load_json(registry_schema_path)
    try:
        visual_grammar_module.validate_registry(registry, registry_schema)
        grammar_report = visual_grammar_module.validate_episode(sidecar, registry)
    except visual_grammar_module.VisualGrammarError as exc:
        errors.append(f"Visual Grammar registry invalid: {exc}")
        grammar_report = {"status": "FAIL", "violations": []}
    if grammar_report["status"] != "PASS":
        for violation in grammar_report["violations"]:
            errors.append(
                "Visual Grammar contract violation "
                f"{violation['code']} at {violation['path']}: {violation['message']}"
            )

    scene_ids = [scene["sceneId"] for scene in contract["scenes"]]
    _require(len(scene_ids) == len(set(scene_ids)), "sceneId values must be unique", errors)
    _require(
        set(scene_ids) == {f"scene-{number:02d}" for number in range(1, 10)},
        "scenes must contain scene-01 through scene-09 exactly once",
        errors,
    )

    beat_map: dict[tuple[str, str], dict[str, Any]] = {}
    beat_ids: set[str] = set()
    for scene in contract["scenes"]:
        for beat in scene["visualBeats"]:
            key = (scene["sceneId"], beat["visualBeatId"])
            _require(key not in beat_map, f"duplicate scene/beat pair: {key}", errors)
            _require(
                beat["visualBeatId"] not in beat_ids,
                f"visualBeatId must be globally unique: {beat['visualBeatId']}",
                errors,
            )
            beat_map[key] = beat
            beat_ids.add(beat["visualBeatId"])

    marker_counts: dict[tuple[str, str], int] = {}
    for marker in markers:
        marker_counts[marker] = marker_counts.get(marker, 0) + 1
    for key in beat_map:
        _require(
            marker_counts.get(key, 0) == 1,
            f"Visual Beat marker must appear exactly once for {key}",
            errors,
        )
    for marker, count in marker_counts.items():
        _require(marker in beat_map, f"Markdown contains undeclared Visual Beat marker: {marker}", errors)
        _require(count == 1, f"duplicate Visual Beat marker: {marker}", errors)

    source_ids = [source["sourceId"] for source in contract["sourceRegistry"]]
    _require(len(source_ids) == len(set(source_ids)), "sourceRegistry sourceId values must be unique", errors)
    source_set = set(source_ids)

    visuals = contract["financialVisuals"]
    intents = visuals["intents"]
    plans = visuals["candidatePlans"]
    intent_map = {intent["intentId"]: intent for intent in intents}
    plan_map = {plan["planId"]: plan for plan in plans}
    _require(len(intent_map) == len(intents), "intentId values must be unique", errors)
    _require(len(plan_map) == len(plans), "planId values must be unique", errors)

    referenced_plan_ids: set[str] = set()
    for intent in intents:
        intent_id = intent["intentId"]
        target = intent["target"]
        target_key = (target["sceneId"], target["visualBeatId"])
        _require(
            target_key in beat_map,
            f"intent {intent_id} target Visual Beat does not exist: {target_key}",
            errors,
        )
        _require(
            intent["preferredPlanId"] != intent["fallbackPlanId"],
            f"intent {intent_id} preferred and fallback plan IDs must differ",
            errors,
        )
        declared_sources = set(intent["sourceIds"])
        _require(
            declared_sources.issubset(source_set),
            f"intent {intent_id} references unknown source IDs: {sorted(declared_sources - source_set)}",
            errors,
        )

        metric_ids = [metric["metricId"] for metric in intent["metrics"]]
        step_ids = [step["stepId"] for step in intent["causalSteps"]]
        _require(len(metric_ids) == len(set(metric_ids)), f"intent {intent_id} metricId values must be unique", errors)
        _require(len(step_ids) == len(set(step_ids)), f"intent {intent_id} stepId values must be unique", errors)
        metric_sources = {source for metric in intent["metrics"] for source in metric["sourceIds"]}
        step_sources = {source for step in intent["causalSteps"] for source in step["sourceIds"]}
        used_sources = metric_sources | step_sources
        _require(
            used_sources.issubset(declared_sources),
            f"intent {intent_id} sourceIds omit metric/step sources: {sorted(used_sources - declared_sources)}",
            errors,
        )

        if intent["chartPolicy"] == "verified-series-only":
            _require(
                intent["dataPrecision"] == "verified-intraday-series",
                f"intent {intent_id} verified-series-only requires verified-intraday-series",
                errors,
            )

        for path_name, field in (("preferred", "preferredPlanId"), ("fallback", "fallbackPlanId")):
            plan_id = intent[field]
            referenced_plan_ids.add(plan_id)
            plan = plan_map.get(plan_id)
            if plan is None:
                errors.append(f"intent {intent_id} {path_name} plan not found: {plan_id}")
                continue
            _require(plan["path"] == path_name, f"plan {plan_id} path must be {path_name}", errors)
            _require(plan["intentId"] == intent_id, f"plan {plan_id} intentId mismatch", errors)
            _require((plan["sceneId"], plan["visualBeatId"]) == target_key, f"plan {plan_id} target mismatch", errors)
            _require(
                set(plan["sourceIds"]).issubset(declared_sources),
                f"plan {plan_id} uses undeclared intent sources: {sorted(set(plan['sourceIds']) - declared_sources)}",
                errors,
            )
            _require(
                set(plan["metricIds"]).issubset(set(metric_ids)),
                f"plan {plan_id} references unknown metric IDs: {sorted(set(plan['metricIds']) - set(metric_ids))}",
                errors,
            )
            _require(
                set(plan["causalStepIds"]).issubset(set(step_ids)),
                f"plan {plan_id} references unknown causal step IDs: {sorted(set(plan['causalStepIds']) - set(step_ids))}",
                errors,
            )
            displayed = set(plan["metricIds"]) | set(plan["causalStepIds"])
            _require(
                set(plan["displayOrder"]) == displayed,
                f"plan {plan_id} displayOrder must exactly cover selected metrics/steps",
                errors,
            )
            _require(
                set(plan["highlightObjectIds"]).issubset(displayed),
                f"plan {plan_id} highlights objects outside displayOrder",
                errors,
            )
            beat = beat_map.get(target_key)
            if beat is not None:
                _validate_plan_refs(plan, beat, errors)

    _require(
        set(plan_map) == referenced_plan_ids,
        "candidatePlans must contain only the two declared plans per intent; "
        f"unreferenced={sorted(set(plan_map) - referenced_plan_ids)} "
        f"missing={sorted(referenced_plan_ids - set(plan_map))}",
        errors,
    )

    if errors:
        raise ContractError("\n".join(errors))
    return {
        "status": "PASS",
        "contractVersion": contract["contractVersion"],
        "visualGrammarContractVersion": contract["visualGrammarContractVersion"],
        "episodeDate": contract["episodeDate"],
        "episodePackageSha256": actual_package_sha,
        "visualGrammarSidecarSha256": actual_sidecar_sha,
        "sceneCount": len(scene_ids),
        "visualBeatCount": len(beat_map),
        "semanticGrammarCount": grammar_report["semanticGrammarCount"],
        "majorShiftCount": grammar_report["majorShiftCount"],
        "intentCount": len(intents),
        "candidatePlanCount": len(plans),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--final-schema",
        type=Path,
        default=Path("contracts/final_episode_contract.schema.json"),
    )
    parser.add_argument(
        "--candidate-schema",
        type=Path,
        default=Path("contracts/financial_visual_candidate_plan.schema.json"),
    )
    parser.add_argument(
        "--visual-grammar-registry",
        type=Path,
        default=Path("contracts/visual_grammar_semantics.json"),
    )
    parser.add_argument(
        "--visual-grammar-registry-schema",
        type=Path,
        default=Path("contracts/visual_grammar_semantics.schema.json"),
    )
    args = parser.parse_args(argv)
    try:
        result = validate_contract(
            args.contract,
            args.repo_root,
            args.final_schema,
            args.candidate_schema,
            args.visual_grammar_registry,
            args.visual_grammar_registry_schema,
        )
    except ContractError as exc:
        print(
            json.dumps(
                {"status": "FAIL", "errors": str(exc).splitlines()},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
