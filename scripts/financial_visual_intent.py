#!/usr/bin/env python3
"""Validate and deterministically compile NASDAQ Cafe financial visual intents.

This module intentionally does not decide editorial meaning. It accepts an already
approved intent and determines whether the requested financial visualization is
structurally eligible. If eligibility fails, it emits the declared safe fallback.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

CONTRACT_VERSION = "1.0.0"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
INTENT_ID_RE = re.compile(r"^fvi-[a-z0-9][a-z0-9._-]{2,80}$")
SOURCE_RE = re.compile(r"^source-[0-9]{3}$")
SCENE_RE = re.compile(r"^scene-0[1-9]$")

KINDS = {
    "market-snapshot",
    "expectation-gap",
    "entity-divergence",
    "macro-transmission",
    "source-evidence",
}
PREFERRED_BY_KIND = {
    "market-snapshot": "market-pulse-grid",
    "expectation-gap": "earnings-surprise",
    "entity-divergence": "dual-asset-split",
    "macro-transmission": "macro-pressure",
    "source-evidence": "source-receipt",
}
FALLBACKS = {
    "market-snapshot": "opening-contradiction",
    "expectation-gap": "expected-anchor",
    "entity-divergence": "split-opposition",
    "macro-transmission": "causal-build",
    "source-evidence": "news-media",
}
DATA_PRECISIONS = {
    "reported-result",
    "market-close",
    "verified-intraday-series",
    "derived-difference",
    "qualitative-only",
}
CHART_POLICIES = {"no-series", "verified-series-only"}
STATUSES = {"proposed", "approved"}
METRIC_ROLES = {
    "market",
    "expected",
    "actual",
    "gap",
    "left-entity",
    "right-entity",
    "macro-anchor",
    "supporting",
}


class ContractError(ValueError):
    """Raised when an intent violates the structural contract."""


@dataclass(frozen=True)
class CompileDecision:
    intent_id: str
    kind: str
    eligibility: str
    selected_recipe: str
    fallback_recipe: str
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "contractVersion": CONTRACT_VERSION,
            "intentId": self.intent_id,
            "kind": self.kind,
            "eligibility": self.eligibility,
            "selectedRecipe": self.selected_recipe,
            "fallbackRecipe": self.fallback_recipe,
            "reasons": list(self.reasons),
        }


def _expect(condition: bool, path: str, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(f"{path}: {message}")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _validate_string_list(
    value: Any,
    path: str,
    errors: list[str],
    *,
    min_items: int = 0,
    max_items: int,
    pattern: re.Pattern[str] | None = None,
) -> list[str]:
    _expect(isinstance(value, list), path, "must be an array", errors)
    if not isinstance(value, list):
        return []
    _expect(min_items <= len(value) <= max_items, path, f"must contain {min_items}..{max_items} items", errors)
    _expect(len(value) == len(set(value)), path, "must not contain duplicates", errors)
    result: list[str] = []
    for index, item in enumerate(value):
        _expect(isinstance(item, str) and bool(item), f"{path}[{index}]", "must be a non-empty string", errors)
        if isinstance(item, str) and item:
            if pattern is not None:
                _expect(bool(pattern.fullmatch(item)), f"{path}[{index}]", "has an invalid format", errors)
            result.append(item)
    return result


def validate_intent(intent: Any) -> dict[str, Any]:
    errors: list[str] = []
    _expect(isinstance(intent, dict), "$", "must be an object", errors)
    if not isinstance(intent, dict):
        raise ContractError("\n".join(errors))

    allowed = {
        "contractVersion",
        "episodeDate",
        "intentId",
        "kind",
        "sceneIds",
        "metrics",
        "causalSteps",
        "sourceIds",
        "dataPrecision",
        "chartPolicy",
        "preferredRecipe",
        "fallbackRecipe",
        "status",
        "editorialNote",
    }
    required = allowed - {"editorialNote"}
    unknown = sorted(set(intent) - allowed)
    missing = sorted(required - set(intent))
    _expect(not unknown, "$", f"unknown fields: {unknown}", errors)
    _expect(not missing, "$", f"missing required fields: {missing}", errors)

    _expect(intent.get("contractVersion") == CONTRACT_VERSION, "$.contractVersion", f"must equal {CONTRACT_VERSION}", errors)
    _expect(isinstance(intent.get("episodeDate"), str) and bool(DATE_RE.fullmatch(intent["episodeDate"])), "$.episodeDate", "must be YYYY-MM-DD", errors)
    _expect(isinstance(intent.get("intentId"), str) and bool(INTENT_ID_RE.fullmatch(intent["intentId"])), "$.intentId", "has an invalid format", errors)

    kind = intent.get("kind")
    _expect(kind in KINDS, "$.kind", f"must be one of {sorted(KINDS)}", errors)
    _validate_string_list(intent.get("sceneIds"), "$.sceneIds", errors, min_items=1, max_items=3, pattern=SCENE_RE)
    top_source_ids = _validate_string_list(intent.get("sourceIds"), "$.sourceIds", errors, max_items=8, pattern=SOURCE_RE)

    _expect(intent.get("dataPrecision") in DATA_PRECISIONS, "$.dataPrecision", "has an invalid value", errors)
    _expect(intent.get("chartPolicy") in CHART_POLICIES, "$.chartPolicy", "has an invalid value", errors)
    _expect(intent.get("status") in STATUSES, "$.status", "has an invalid value", errors)
    if intent.get("chartPolicy") == "verified-series-only":
        _expect(intent.get("dataPrecision") == "verified-intraday-series", "$.dataPrecision", "verified-series-only requires verified-intraday-series", errors)

    if kind in KINDS:
        _expect(intent.get("preferredRecipe") == PREFERRED_BY_KIND[kind], "$.preferredRecipe", f"must equal {PREFERRED_BY_KIND[kind]} for {kind}", errors)
        _expect(intent.get("fallbackRecipe") == FALLBACKS[kind], "$.fallbackRecipe", f"must equal {FALLBACKS[kind]} for {kind}", errors)

    metrics = intent.get("metrics")
    _expect(isinstance(metrics, list), "$.metrics", "must be an array", errors)
    metric_ids: list[str] = []
    metric_source_ids: set[str] = set()
    if isinstance(metrics, list):
        _expect(len(metrics) <= 6, "$.metrics", "must contain at most 6 items", errors)
        for index, metric in enumerate(metrics):
            path = f"$.metrics[{index}]"
            _expect(isinstance(metric, dict), path, "must be an object", errors)
            if not isinstance(metric, dict):
                continue
            metric_allowed = {
                "metricId",
                "label",
                "role",
                "valueText",
                "numericValue",
                "unit",
                "currency",
                "period",
                "entityId",
                "sessionDate",
                "sourceIds",
            }
            _expect(set(metric) == metric_allowed, path, f"must contain exactly {sorted(metric_allowed)}", errors)
            metric_id = metric.get("metricId")
            _expect(isinstance(metric_id, str) and bool(ID_RE.fullmatch(metric_id)), f"{path}.metricId", "has an invalid format", errors)
            if isinstance(metric_id, str):
                metric_ids.append(metric_id)
            _expect(isinstance(metric.get("label"), str) and 1 <= len(metric["label"]) <= 120, f"{path}.label", "must be 1..120 characters", errors)
            _expect(metric.get("role") in METRIC_ROLES, f"{path}.role", "has an invalid value", errors)
            _expect(isinstance(metric.get("valueText"), str) and 1 <= len(metric["valueText"]) <= 80, f"{path}.valueText", "must be 1..80 characters", errors)
            numeric_value = metric.get("numericValue")
            _expect(numeric_value is None or _is_number(numeric_value), f"{path}.numericValue", "must be a finite number or null", errors)
            for optional_key, limit in (("unit", 40), ("currency", 12), ("period", 80), ("entityId", 80)):
                optional_value = metric.get(optional_key)
                _expect(optional_value is None or isinstance(optional_value, str), f"{path}.{optional_key}", "must be string or null", errors)
                if isinstance(optional_value, str):
                    _expect(len(optional_value) <= limit, f"{path}.{optional_key}", f"must be at most {limit} characters", errors)
            session_date = metric.get("sessionDate")
            _expect(session_date is None or (isinstance(session_date, str) and bool(DATE_RE.fullmatch(session_date))), f"{path}.sessionDate", "must be YYYY-MM-DD or null", errors)
            sources = _validate_string_list(metric.get("sourceIds"), f"{path}.sourceIds", errors, min_items=1, max_items=4, pattern=SOURCE_RE)
            metric_source_ids.update(sources)

    _expect(len(metric_ids) == len(set(metric_ids)), "$.metrics", "metricId values must be unique", errors)

    steps = intent.get("causalSteps")
    _expect(isinstance(steps, list), "$.causalSteps", "must be an array", errors)
    step_ids: list[str] = []
    step_source_ids: set[str] = set()
    if isinstance(steps, list):
        _expect(len(steps) <= 4, "$.causalSteps", "must contain at most 4 items", errors)
        for index, step in enumerate(steps):
            path = f"$.causalSteps[{index}]"
            _expect(isinstance(step, dict), path, "must be an object", errors)
            if not isinstance(step, dict):
                continue
            _expect(set(step) == {"stepId", "label", "sourceIds"}, path, "must contain exactly stepId, label, sourceIds", errors)
            step_id = step.get("stepId")
            _expect(isinstance(step_id, str) and bool(ID_RE.fullmatch(step_id)), f"{path}.stepId", "has an invalid format", errors)
            if isinstance(step_id, str):
                step_ids.append(step_id)
            _expect(isinstance(step.get("label"), str) and 1 <= len(step["label"]) <= 140, f"{path}.label", "must be 1..140 characters", errors)
            sources = _validate_string_list(step.get("sourceIds"), f"{path}.sourceIds", errors, min_items=1, max_items=4, pattern=SOURCE_RE)
            step_source_ids.update(sources)
    _expect(len(step_ids) == len(set(step_ids)), "$.causalSteps", "stepId values must be unique", errors)

    declared = set(top_source_ids)
    referenced = metric_source_ids | step_source_ids
    _expect(referenced.issubset(declared), "$.sourceIds", f"must include every metric/step source: {sorted(referenced - declared)}", errors)

    note = intent.get("editorialNote")
    _expect(note is None or (isinstance(note, str) and len(note) <= 500), "$.editorialNote", "must be null or at most 500 characters", errors)

    if errors:
        raise ContractError("\n".join(errors))
    return intent


def _same_non_null(metrics: Iterable[dict[str, Any]], field: str) -> bool:
    values = [metric.get(field) for metric in metrics]
    return bool(values) and all(value is not None for value in values) and len(set(values)) == 1


def _metric_by_role(metrics: list[dict[str, Any]], role: str) -> list[dict[str, Any]]:
    return [metric for metric in metrics if metric["role"] == role]


def _check_market_snapshot(intent: dict[str, Any]) -> list[str]:
    metrics = intent["metrics"]
    reasons: list[str] = []
    if not 3 <= len(metrics) <= 4:
        reasons.append("market-snapshot requires 3 or 4 metrics")
    if any(metric["numericValue"] is None for metric in metrics):
        reasons.append("every market metric requires numericValue")
    if not _same_non_null(metrics, "sessionDate"):
        reasons.append("market metrics require one shared non-null sessionDate")
    if intent["dataPrecision"] not in {"market-close", "verified-intraday-series"}:
        reasons.append("market-snapshot requires market-close or verified-intraday-series precision")
    return reasons


def _check_expectation_gap(intent: dict[str, Any]) -> list[str]:
    metrics = intent["metrics"]
    reasons: list[str] = []
    expected = _metric_by_role(metrics, "expected")
    actual = _metric_by_role(metrics, "actual")
    gap = _metric_by_role(metrics, "gap")
    if not (len(expected) == len(actual) == len(gap) == 1 and len(metrics) == 3):
        return ["expectation-gap requires exactly expected, actual, and gap metrics"]
    pair = [expected[0], actual[0]]
    for field in ("unit", "currency", "period", "entityId"):
        if not _same_non_null(pair, field):
            reasons.append(f"expected and actual require the same non-null {field}")
    if any(metric["numericValue"] is None for metric in metrics):
        reasons.append("expected, actual, and gap require numericValue")
    else:
        calculated = float(actual[0]["numericValue"]) - float(expected[0]["numericValue"])
        if not math.isclose(calculated, float(gap[0]["numericValue"]), rel_tol=1e-9, abs_tol=1e-6):
            reasons.append("gap numericValue must equal actual minus expected")
    if intent["dataPrecision"] not in {"reported-result", "derived-difference"}:
        reasons.append("expectation-gap requires reported-result or derived-difference precision")
    return reasons


def _check_entity_divergence(intent: dict[str, Any]) -> list[str]:
    metrics = intent["metrics"]
    reasons: list[str] = []
    left = _metric_by_role(metrics, "left-entity")
    right = _metric_by_role(metrics, "right-entity")
    if not (len(left) == len(right) == 1 and 2 <= len(metrics) <= 3):
        return ["entity-divergence requires one left-entity and one right-entity metric"]
    pair = [left[0], right[0]]
    if left[0]["entityId"] is None or right[0]["entityId"] is None or left[0]["entityId"] == right[0]["entityId"]:
        reasons.append("left and right metrics require different non-null entityId values")
    if not _same_non_null(pair, "sessionDate"):
        reasons.append("left and right metrics require one shared non-null sessionDate")
    if not _same_non_null(pair, "unit"):
        reasons.append("left and right metrics require the same non-null unit")
    if any(metric["numericValue"] is None for metric in pair):
        reasons.append("left and right metrics require numericValue")
    if intent["dataPrecision"] not in {"market-close", "verified-intraday-series"}:
        reasons.append("entity-divergence requires market-close or verified-intraday-series precision")
    return reasons


def _check_macro_transmission(intent: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    anchors = _metric_by_role(intent["metrics"], "macro-anchor")
    if len(anchors) != 1:
        reasons.append("macro-transmission requires exactly one macro-anchor metric")
    if not 2 <= len(intent["causalSteps"]) <= 4:
        reasons.append("macro-transmission requires 2 to 4 causalSteps")
    if anchors and anchors[0]["numericValue"] is None and intent["dataPrecision"] != "qualitative-only":
        reasons.append("numeric macro precision requires macro-anchor numericValue")
    return reasons


def _check_source_evidence(intent: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if not 1 <= len(intent["sourceIds"]) <= 3:
        reasons.append("source-evidence requires 1 to 3 sourceIds")
    if intent["metrics"] or intent["causalSteps"]:
        reasons.append("source-evidence must not carry metrics or causalSteps")
    return reasons


CHECKERS = {
    "market-snapshot": _check_market_snapshot,
    "expectation-gap": _check_expectation_gap,
    "entity-divergence": _check_entity_divergence,
    "macro-transmission": _check_macro_transmission,
    "source-evidence": _check_source_evidence,
}


def compile_intent(intent: dict[str, Any]) -> CompileDecision:
    validate_intent(intent)
    reasons = CHECKERS[intent["kind"]](intent)
    approved = intent["status"] == "approved"
    if not approved:
        reasons.insert(0, "intent status is not approved")
    eligible = approved and not reasons
    selected = intent["preferredRecipe"] if eligible else intent["fallbackRecipe"]
    return CompileDecision(
        intent_id=intent["intentId"],
        kind=intent["kind"],
        eligibility="eligible" if eligible else "fallback",
        selected_recipe=selected,
        fallback_recipe=intent["fallbackRecipe"],
        reasons=tuple(reasons),
    )


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    return validate_intent(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate one intent JSON")
    validate_parser.add_argument("input", type=Path)

    compile_parser = subparsers.add_parser("compile", help="compile one intent to a deterministic recipe decision")
    compile_parser.add_argument("input", type=Path)
    compile_parser.add_argument("--output", type=Path)

    args = parser.parse_args(argv)
    try:
        intent = load_json(args.input)
        if args.command == "validate":
            print(json.dumps({"status": "PASS", "intentId": intent["intentId"]}, ensure_ascii=False))
            return 0
        decision = compile_intent(intent).as_dict()
        rendered = json.dumps(decision, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0
    except ContractError as exc:
        print(json.dumps({"status": "FAIL", "errors": str(exc).splitlines()}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
