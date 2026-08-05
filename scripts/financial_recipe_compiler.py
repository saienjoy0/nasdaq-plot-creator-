#!/usr/bin/env python3
"""Compile approved NASDAQ Cafe Financial Visual Candidate Plans.

The compiler never invents editorial meaning or renderer configuration. It only
checks the preferred Candidate Plan against a versioned registry and the data
already approved in the Final Episode Contract. If preferred is ineligible, it
selects the pre-approved fallback. If fallback is invalid, compilation stops.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

import final_episode_contract as final_contract_module


class CompileError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CompileError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CompileError(f"invalid JSON at {path}:{exc.lineno}:{exc.colno}: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise CompileError(f"JSON root must be an object: {path}")
    return payload


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _recipe_pair_reasons(
    intent: dict[str, Any],
    plan: dict[str, Any],
    registry: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    kind_entry = registry.get("intentKinds", {}).get(intent["kind"])
    recipe_entry = registry.get("recipes", {}).get(plan["recipeId"])
    expected_recipe_key = "preferredRecipeId" if plan["path"] == "preferred" else "fallbackRecipeId"
    if not kind_entry or kind_entry.get(expected_recipe_key) != plan["recipeId"]:
        reasons.append("RECIPE_TEMPLATE_PAIR_NOT_ALLOWED")
        return reasons
    if not recipe_entry:
        reasons.append("RECIPE_TEMPLATE_PAIR_NOT_ALLOWED")
        return reasons
    if recipe_entry.get("path") != plan["path"]:
        reasons.append("RECIPE_TEMPLATE_PAIR_NOT_ALLOWED")
    if intent["kind"] not in recipe_entry.get("allowedIntentKinds", []):
        reasons.append("RECIPE_TEMPLATE_PAIR_NOT_ALLOWED")
    if plan["visualTemplateId"] not in recipe_entry.get("allowedVisualTemplateIds", []):
        reasons.append("RECIPE_TEMPLATE_PAIR_NOT_ALLOWED")
    return _unique(reasons)


def _selected_metrics(intent: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {metric["metricId"]: metric for metric in intent["metrics"]}
    return [by_id[metric_id] for metric_id in plan["metricIds"] if metric_id in by_id]


def _selected_steps(intent: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {step["stepId"]: step for step in intent["causalSteps"]}
    return [by_id[step_id] for step_id in plan["causalStepIds"] if step_id in by_id]


def _common_reasons(intent: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if intent.get("status") != "approved":
        reasons.append("INTENT_NOT_APPROVED")
    if intent["chartPolicy"] == "verified-series-only" and intent["dataPrecision"] != "verified-intraday-series":
        reasons.extend(["INTRADAY_SERIES_REQUIRED", "SERIES_DATA_NOT_VERIFIED"])
    if len(_selected_metrics(intent, plan)) != len(plan["metricIds"]):
        reasons.append("PREFERRED_PLAN_INVALID")
    if len(_selected_steps(intent, plan)) != len(plan["causalStepIds"]):
        reasons.append("PREFERRED_PLAN_INVALID")
    return reasons


def _expectation_gap_reasons(intent: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    metrics = _selected_metrics(intent, plan)
    by_role: dict[str, list[dict[str, Any]]] = {}
    for metric in metrics:
        by_role.setdefault(metric["role"], []).append(metric)
    required = ["expected", "actual", "gap"]
    if any(len(by_role.get(role, [])) != 1 for role in required):
        return ["EXPECTED_ACTUAL_GAP_INCOMPLETE"]
    expected, actual, gap = (by_role[role][0] for role in required)
    reasons: list[str] = []
    for field, code in (
        ("entityId", "EXPECTED_ACTUAL_ENTITY_MISMATCH"),
        ("unit", "EXPECTED_ACTUAL_UNIT_MISMATCH"),
        ("currency", "EXPECTED_ACTUAL_CURRENCY_MISMATCH"),
        ("period", "EXPECTED_ACTUAL_PERIOD_MISMATCH"),
    ):
        values = {expected.get(field), actual.get(field), gap.get(field)}
        if len(values) != 1 or None in values:
            reasons.append(code)
    numeric = [expected.get("numericValue"), actual.get("numericValue"), gap.get("numericValue")]
    if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in numeric):
        reasons.append("GAP_VALUE_MISMATCH")
    else:
        calculated = float(actual["numericValue"]) - float(expected["numericValue"])
        tolerance = max(1e-9, abs(calculated) * 1e-9)
        if not math.isclose(float(gap["numericValue"]), calculated, rel_tol=0.0, abs_tol=tolerance):
            reasons.append("GAP_VALUE_MISMATCH")
    return _unique(reasons)


def _expected_anchor_fallback_reasons(intent: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    metrics = _selected_metrics(intent, plan)
    roles = {metric["role"] for metric in metrics}
    if not metrics or not roles.issubset({"expected", "actual", "supporting"}):
        return ["PREFERRED_PLAN_INVALID"]
    if not ({"expected", "actual"} & roles):
        return ["PREFERRED_PLAN_INVALID"]
    comparable = [metric for metric in metrics if metric["role"] in {"expected", "actual"}]
    reasons: list[str] = []
    if len(comparable) == 2:
        for field, code in (
            ("entityId", "EXPECTED_ACTUAL_ENTITY_MISMATCH"),
            ("unit", "EXPECTED_ACTUAL_UNIT_MISMATCH"),
            ("currency", "EXPECTED_ACTUAL_CURRENCY_MISMATCH"),
            ("period", "EXPECTED_ACTUAL_PERIOD_MISMATCH"),
        ):
            values = {metric.get(field) for metric in comparable}
            if len(values) != 1 or None in values:
                reasons.append(code)
    return _unique(reasons)


def _market_snapshot_reasons(intent: dict[str, Any], plan: dict[str, Any], *, fallback: bool) -> list[str]:
    metrics = _selected_metrics(intent, plan)
    minimum = 1 if fallback else 3
    maximum = 4 if fallback else 6
    reasons: list[str] = []
    if not minimum <= len(metrics) <= maximum:
        reasons.append("MARKET_METRIC_COUNT_INVALID")
    units = {metric.get("unit") for metric in metrics}
    if len(units) > 1 or None in units:
        reasons.append("MARKET_UNIT_MISMATCH")
    dates = {metric.get("sessionDate") for metric in metrics}
    if len(dates) > 1 or None in dates:
        reasons.append("SESSION_DATE_MISMATCH")
    if any(not isinstance(metric.get("numericValue"), (int, float)) for metric in metrics):
        reasons.append("PREFERRED_PLAN_INVALID")
    return _unique(reasons)


def _entity_divergence_reasons(intent: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    metrics = _selected_metrics(intent, plan)
    role_map = {metric["role"]: metric for metric in metrics if metric["role"] in {"left-entity", "right-entity"}}
    if set(role_map) != {"left-entity", "right-entity"}:
        return ["PREFERRED_PLAN_INVALID"]
    left, right = role_map["left-entity"], role_map["right-entity"]
    reasons: list[str] = []
    if not left.get("entityId") or left.get("entityId") == right.get("entityId"):
        reasons.append("DIVERGENCE_ENTITY_NOT_DISTINCT")
    if not left.get("sessionDate") or left.get("sessionDate") != right.get("sessionDate"):
        reasons.append("SESSION_DATE_MISMATCH")
    if not left.get("unit") or left.get("unit") != right.get("unit"):
        reasons.append("EXPECTED_ACTUAL_UNIT_MISMATCH")
    if any(not isinstance(metric.get("numericValue"), (int, float)) for metric in (left, right)):
        reasons.append("PREFERRED_PLAN_INVALID")
    return _unique(reasons)


def _macro_reasons(intent: dict[str, Any], plan: dict[str, Any], *, fallback: bool) -> list[str]:
    metrics = _selected_metrics(intent, plan)
    steps = _selected_steps(intent, plan)
    reasons: list[str] = []
    if not fallback:
        anchors = [metric for metric in metrics if metric["role"] == "macro-anchor"]
        if len(anchors) != 1:
            reasons.append("MACRO_ANCHOR_COUNT_INVALID")
    if not 2 <= len(steps) <= 4:
        reasons.append("MACRO_CAUSAL_STEP_COUNT_INVALID")
    return _unique(reasons)


def _source_evidence_reasons(intent: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    if not plan["sourceIds"] or not (plan["metricIds"] or plan["causalStepIds"]):
        return ["SOURCE_EVIDENCE_EMPTY"]
    return []


def _shape_reasons(intent: dict[str, Any], plan: dict[str, Any], *, fallback: bool) -> list[str]:
    kind = intent["kind"]
    if kind == "expectation-gap":
        return _expected_anchor_fallback_reasons(intent, plan) if fallback else _expectation_gap_reasons(intent, plan)
    if kind == "market-snapshot":
        return _market_snapshot_reasons(intent, plan, fallback=fallback)
    if kind == "entity-divergence":
        return _entity_divergence_reasons(intent, plan)
    if kind == "macro-transmission":
        return _macro_reasons(intent, plan, fallback=fallback)
    if kind == "source-evidence":
        return _source_evidence_reasons(intent, plan)
    return ["PREFERRED_PLAN_INVALID"]


def plan_reasons(
    intent: dict[str, Any],
    plan: dict[str, Any],
    registry: dict[str, Any],
    *,
    fallback: bool,
) -> list[str]:
    reasons = []
    reasons.extend(_common_reasons(intent, plan))
    reasons.extend(_recipe_pair_reasons(intent, plan, registry))
    reasons.extend(_shape_reasons(intent, plan, fallback=fallback))
    return _unique(reasons)


def _validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("registryVersion") != "1.0.0":
        raise CompileError("unsupported recipe registry version")
    kinds = registry.get("intentKinds")
    recipes = registry.get("recipes")
    if not isinstance(kinds, dict) or not isinstance(recipes, dict):
        raise CompileError("recipe registry requires intentKinds and recipes objects")
    for kind, pair in kinds.items():
        if not isinstance(pair, dict):
            raise CompileError(f"registry intent kind must be an object: {kind}")
        for key in ("preferredRecipeId", "fallbackRecipeId"):
            recipe_id = pair.get(key)
            if recipe_id not in recipes:
                raise CompileError(f"registry {kind}.{key} references unknown recipe: {recipe_id}")


def _validate_recipe_plan(plan: dict[str, Any], schema: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(schema).iter_errors(plan), key=lambda item: list(item.path))
    if errors:
        formatted = []
        for error in errors:
            location = "$" + "".join(
                f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path
            )
            formatted.append(f"{location}: {error.message}")
        raise CompileError("\n".join(formatted))


def compile_recipe_plan(
    final_contract_path: Path,
    repo_root: Path,
    registry_path: Path,
    recipe_plan_schema_path: Path,
    final_schema_path: Path,
    candidate_schema_path: Path,
) -> dict[str, Any]:
    final_contract_module.validate_contract(
        final_contract_path,
        repo_root,
        final_schema_path,
        candidate_schema_path,
    )
    contract = load_json(final_contract_path)
    registry = load_json(registry_path)
    recipe_plan_schema = load_json(recipe_plan_schema_path)
    _validate_registry(registry)

    visuals = contract["financialVisuals"]
    plan_map = {plan["planId"]: plan for plan in visuals["candidatePlans"]}
    selections = []
    for intent in visuals["intents"]:
        preferred = plan_map[intent["preferredPlanId"]]
        fallback = plan_map[intent["fallbackPlanId"]]
        preferred_reasons = plan_reasons(intent, preferred, registry, fallback=False)
        fallback_reasons = plan_reasons(intent, fallback, registry, fallback=True)
        if fallback_reasons:
            raise CompileError(
                f"FALLBACK_PLAN_INVALID:{intent['intentId']}:" + ",".join(fallback_reasons)
            )
        if preferred_reasons:
            selected = fallback
            selected_path = "fallback"
            eligibility = "fallback-required"
            reason_codes = _unique(preferred_reasons)
            diversity = "required"
        else:
            selected = preferred
            selected_path = "preferred"
            eligibility = "eligible"
            reason_codes = []
            diversity = "not-required"
        target = intent["target"]
        selections.append(
            {
                "intentId": intent["intentId"],
                "sceneId": target["sceneId"],
                "visualBeatId": target["visualBeatId"],
                "eligibility": eligibility,
                "selectedPath": selected_path,
                "selectedPlanId": selected["planId"],
                "selectedPlanSha256": canonical_sha256(selected),
                "selectedRecipeId": selected["recipeId"],
                "selectedVisualTemplateId": selected["visualTemplateId"],
                "templateVariant": selected["templateVariant"],
                "screenState": selected["screenState"],
                "sourceIds": selected["sourceIds"],
                "metricIds": selected["metricIds"],
                "causalStepIds": selected["causalStepIds"],
                "reasonCodes": reason_codes,
                "fallbackDiversityRecheck": diversity,
            }
        )

    try:
        relative_contract_path = final_contract_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise CompileError("final contract path must be inside repo root") from exc
    output = {
        "contractVersion": "1.0.0",
        "episodeDate": contract["episodeDate"],
        "finalEpisodeContract": {
            "path": relative_contract_path,
            "sha256": file_sha256(final_contract_path),
        },
        "episodePackageSha256": contract["episodePackage"]["sha256"],
        "intentContractVersion": "1.1.0",
        "recipeRegistryVersion": registry["registryVersion"],
        "selections": selections,
    }
    _validate_recipe_plan(output, recipe_plan_schema)
    return output


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["compile"])
    parser.add_argument("final_contract", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--registry", type=Path, default=Path("contracts/financial_recipe_registry.json"))
    parser.add_argument("--recipe-plan-schema", type=Path, default=Path("contracts/financial_recipe_plan.schema.json"))
    parser.add_argument("--final-schema", type=Path, default=Path("contracts/final_episode_contract.schema.json"))
    parser.add_argument("--candidate-schema", type=Path, default=Path("contracts/financial_visual_candidate_plan.schema.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        plan = compile_recipe_plan(
            args.final_contract,
            args.repo_root,
            args.registry,
            args.recipe_plan_schema,
            args.final_schema,
            args.candidate_schema,
        )
        write_json_atomic(args.output, plan)
    except (CompileError, final_contract_module.ContractError) as exc:
        print(json.dumps({"status": "FAIL", "errors": str(exc).splitlines()}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps({"status": "PASS", "output": str(args.output), "selectionCount": len(plan["selections"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
