#!/usr/bin/env python3
"""Audit whether Visual Grammar is closed across the Final Episode Contract.

The audit records deterministic contract facts and validates the representative
fixture. It does not generate or infer Visual Grammar decisions.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import final_episode_contract


class AuditError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AuditError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AuditError(
            f"invalid JSON at {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise AuditError(f"JSON root must be an object: {path}")
    return value


def audit(
    *,
    repo_root: Path,
    fixture_path: Path,
    final_schema_path: Path,
    candidate_schema_path: Path,
    registry_path: Path,
    registry_schema_path: Path,
) -> dict[str, Any]:
    schema = load_json(final_schema_path)
    root_required = set(schema.get("required", []))
    beat_required = set(
        schema.get("$defs", {}).get("visualBeat", {}).get("required", [])
    )
    checks = {
        "finalContractVersionIs1_1_0": (
            schema.get("properties", {})
            .get("contractVersion", {})
            .get("const")
            == "1.1.0"
        ),
        "visualGrammarSidecarRequired": "visualGrammarSidecar" in root_required,
        "visualGrammarRootVersionRequired": (
            "visualGrammarContractVersion" in root_required
        ),
        "visualGrammarRequiredOnEveryBeat": "visualGrammar" in beat_required,
        "expectedConfirmedExplicit": "expectedConfirmed" in root_required,
        "scene5ExceptionExplicit": "scene5CausalExceptionReason" in root_required,
    }
    failures = [name for name, passed in checks.items() if not passed]
    fixture_result: dict[str, Any] | None = None
    if not failures:
        try:
            fixture_result = final_episode_contract.validate_contract(
                fixture_path,
                repo_root,
                final_schema_path,
                candidate_schema_path,
                registry_path,
                registry_schema_path,
            )
        except final_episode_contract.ContractError as exc:
            failures.extend(str(exc).splitlines())
    return {
        "reportVersion": "1.0.0",
        "status": "PASS" if not failures else "FAIL",
        "scope": "VG-1 Final Episode Contract closure",
        "checks": checks,
        "fixture": fixture_result,
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path(
            "tests/final-episode-contract/fixtures/final_episode_contract.valid.json"
        ),
    )
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
        "--registry",
        type=Path,
        default=Path("contracts/visual_grammar_semantics.json"),
    )
    parser.add_argument(
        "--registry-schema",
        type=Path,
        default=Path("contracts/visual_grammar_semantics.schema.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit(
            repo_root=args.repo_root,
            fixture_path=args.fixture,
            final_schema_path=args.final_schema,
            candidate_schema_path=args.candidate_schema,
            registry_path=args.registry,
            registry_schema_path=args.registry_schema,
        )
    except AuditError as exc:
        result = {
            "reportVersion": "1.0.0",
            "status": "FAIL",
            "scope": "VG-1 Final Episode Contract closure",
            "checks": {},
            "fixture": None,
            "failures": str(exc).splitlines(),
        }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
