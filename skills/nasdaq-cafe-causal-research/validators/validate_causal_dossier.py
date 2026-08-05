#!/usr/bin/env python3
"""Validate a NASDAQ Cafe causal research dossier.

Structural validation uses jsonschema when available. Semantic checks are kept in
this file so the contract can still reject incomplete dossiers in minimal CI.
Passing this validator means the dossier is structurally ready for editorial
review; it does not prove the causal interpretation is correct.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "contracts" / "causal_research_dossier.schema.json"


class ValidationResult:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def passed(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid JSON at {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc


def validate_json_schema(data: Any, schema: Any, result: ValidationResult) -> None:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        result.warn("jsonschema is not installed; full schema validation was skipped")
        return

    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
        location = "/".join(str(part) for part in error.absolute_path) or "$"
        result.error(f"schema:{location}: {error.message}")


def collect_ids(items: Any, key: str) -> set[str]:
    if not isinstance(items, list):
        return set()
    values: set[str] = set()
    for item in items:
        if isinstance(item, dict) and isinstance(item.get(key), str):
            values.add(item[key])
    return values


def referenced_evidence_ids(data: dict[str, Any]) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []

    def add(path: str, values: Any) -> None:
        if isinstance(values, list):
            for value in values:
                if isinstance(value, str):
                    refs.append((path, value))

    for index, question in enumerate(data.get("research_questions", [])):
        if isinstance(question, dict):
            add(f"research_questions/{index}/evidence_ids", question.get("evidence_ids"))

    eag = data.get("expected_actual_gap", {})
    if isinstance(eag, dict):
        expected = eag.get("expected", {})
        actual = eag.get("actual", {})
        if isinstance(expected, dict):
            add("expected_actual_gap/expected/evidence_ids", expected.get("evidence_ids"))
        if isinstance(actual, dict):
            add("expected_actual_gap/actual/evidence_ids", actual.get("evidence_ids"))

    for section in ("timeline", "causal_edges", "contrary_evidence"):
        for index, item in enumerate(data.get(section, [])):
            if isinstance(item, dict):
                add(f"{section}/{index}/evidence_ids", item.get("evidence_ids"))

    for index, hypothesis in enumerate(data.get("alternative_hypotheses", [])):
        if isinstance(hypothesis, dict):
            add(
                f"alternative_hypotheses/{index}/supporting_evidence_ids",
                hypothesis.get("supporting_evidence_ids"),
            )
            add(
                f"alternative_hypotheses/{index}/weakening_evidence_ids",
                hypothesis.get("weakening_evidence_ids"),
            )

    return refs


def semantic_validate(data: Any, result: ValidationResult) -> None:
    if not isinstance(data, dict):
        result.error("root must be an object")
        return

    evidence_ids = collect_ids(data.get("evidence"), "evidence_id")
    if not evidence_ids:
        result.error("no evidence IDs were found")

    for path, evidence_id in referenced_evidence_ids(data):
        if evidence_id not in evidence_ids:
            result.error(f"{path}: unknown evidence ID {evidence_id}")

    contradictions = data.get("contradictions", [])
    if not isinstance(contradictions, list) or not contradictions:
        result.error("at least one contradiction is required")

    questions = data.get("research_questions", [])
    perspectives = {
        question.get("perspective")
        for question in questions
        if isinstance(question, dict)
    }
    required_perspectives = {"official_evidence", "timeline", "counter_hypothesis"}
    missing_perspectives = sorted(required_perspectives - perspectives)
    if missing_perspectives:
        result.error(
            "required research perspectives missing: " + ", ".join(missing_perspectives)
        )

    question_ids = collect_ids(questions, "id")
    for index, question in enumerate(questions if isinstance(questions, list) else []):
        if not isinstance(question, dict):
            continue
        parent = question.get("parent_question_id")
        if parent is not None and parent not in question_ids:
            result.error(
                f"research_questions/{index}/parent_question_id: unknown question ID {parent}"
            )

    edges = data.get("causal_edges", [])
    if not isinstance(edges, list) or not edges:
        result.error("at least one causal edge is required")
    else:
        if not any(
            isinstance(edge, dict) and edge.get("editorially_required") is True
            for edge in edges
        ):
            result.error("at least one causal edge must be marked editorially_required")

        company_direct = any(
            isinstance(edge, dict) and edge.get("scope") == "company_direct"
            for edge in edges
        )
        nasdaq_wide = any(
            isinstance(edge, dict) and edge.get("scope") == "nasdaq_wide"
            for edge in edges
        )
        sector_support = any(
            isinstance(edge, dict) and edge.get("scope") == "sector_support"
            for edge in edges
        )
        if company_direct and not (nasdaq_wide or sector_support):
            result.warn(
                "company-direct material exists without a sector-support or NASDAQ-wide edge; "
                "do not present the company event as the index-wide cause"
            )

    alternatives = data.get("alternative_hypotheses", [])
    if not isinstance(alternatives, list) or not alternatives:
        result.error("at least one alternative hypothesis is required")

    contrary = data.get("contrary_evidence", [])
    if not isinstance(contrary, list) or not contrary:
        result.error("at least one contrary-evidence item is required")

    eag = data.get("expected_actual_gap")
    if isinstance(eag, dict):
        expected = eag.get("expected")
        if isinstance(expected, dict):
            status = expected.get("status")
            basis = expected.get("basis_class")
            evidence = expected.get("evidence_ids")
            if status in {"confirmed", "partially_confirmed"} and not evidence:
                result.error(
                    "confirmed or partially confirmed Expected requires evidence_ids"
                )
            if status == "unconfirmed" and basis != "unconfirmed":
                result.error(
                    "unconfirmed Expected must use basis_class=unconfirmed"
                )

    timeline = data.get("timeline", [])
    if isinstance(timeline, list) and timeline:
        precise_events = [
            item
            for item in timeline
            if isinstance(item, dict) and item.get("precision") in {"exact", "minute"}
        ]
        for index, item in enumerate(precise_events):
            if not item.get("evidence_ids"):
                result.error(
                    f"precise timeline item {index} requires supporting evidence_ids"
                )

    evidence = data.get("evidence", [])
    independence_groups: dict[str, int] = {}
    if isinstance(evidence, list):
        for item in evidence:
            if not isinstance(item, dict):
                continue
            group = item.get("independence_group")
            if isinstance(group, str):
                independence_groups[group] = independence_groups.get(group, 0) + 1
            if item.get("source_tier") == "discovery_only" and item.get("directness") == "direct":
                result.error(
                    f"{item.get('evidence_id', '?')}: discovery-only source cannot be direct evidence"
                )
            if item.get("evidence_class") == "unknown" and item.get("confidence") != "unknown":
                result.error(
                    f"{item.get('evidence_id', '?')}: unknown evidence class must use unknown confidence"
                )

    duplicate_groups = sorted(
        group for group, count in independence_groups.items() if count > 1
    )
    if duplicate_groups:
        result.warn(
            "multiple evidence items share independence groups; confirm they are not counted "
            "as independent sources: " + ", ".join(duplicate_groups)
        )

    handoff = data.get("editorial_handoff")
    if isinstance(handoff, dict):
        confidence = handoff.get("confidence")
        unresolved = handoff.get("unresolved_questions")
        if confidence == "high" and isinstance(unresolved, list) and unresolved:
            result.warn(
                "editorial handoff is high confidence but unresolved questions remain"
            )
        if not handoff.get("company_direct_material"):
            result.warn("editorial handoff has no company-direct material")
        if not handoff.get("nasdaq_wide_material"):
            result.warn(
                "editorial handoff has no NASDAQ-wide material; use the lead as an example, "
                "symbol, or sector comparison rather than an index-wide cause"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args()

    result = ValidationResult()
    try:
        data = load_json(args.dossier)
        schema = load_json(args.schema)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    validate_json_schema(data, schema, result)
    semantic_validate(data, result)

    report = {
        "status": "pass" if result.passed else "fail",
        "errors": result.errors,
        "warnings": result.warnings,
        "dossier": str(args.dossier),
        "schema": str(args.schema),
    }

    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    for warning in result.warnings:
        print(f"WARN: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    print("PASS" if result.passed else "FAIL")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
