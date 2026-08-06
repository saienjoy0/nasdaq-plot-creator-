#!/usr/bin/env python3
"""Validate NASDAQ Cafe Visual Grammar declarations and the VG-0 registry.

VG-0 is deliberately editorially passive. It validates an explicit declaration
and verifies a declared Grammar/Stage pair. It never infers a grammar from scene
number, narration text, metric sign, entity type, or item count.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

CONTRACT_VERSION = "1.0.0"
GRAMMAR_IDS = {
    "contradiction",
    "evidence",
    "gap",
    "causal",
    "reaction",
    "comparison",
    "verification",
    "assembly",
}
GRAMMAR_PHASES = {"establish", "develop", "resolve"}
TRANSITION_ROLES = {"continue", "major-shift", "return", "close"}
STAGE_BY_GRAMMAR = {
    "contradiction": "contradiction-stage",
    "evidence": "evidence-stage",
    "gap": "gap-stage",
    "causal": "causal-stage",
    "reaction": "reaction-stage",
    "comparison": "comparison-stage",
    "verification": "verification-stage",
    "assembly": "assembly-stage",
}


class ContractError(ValueError):
    """Raised when a Visual Grammar contract is invalid."""

    def __init__(self, code: str, path: str, message: str) -> None:
        super().__init__(f"{code} {path}: {message}")
        self.code = code
        self.path = path
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


@dataclass(frozen=True)
class CompatibilityDecision:
    grammar_id: str
    stage_id: str
    compatible: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "contractVersion": CONTRACT_VERSION,
            "grammarId": self.grammar_id,
            "stageId": self.stage_id,
            "compatible": self.compatible,
        }


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError("FILE_NOT_FOUND", "$", str(path)) from exc
    except json.JSONDecodeError as exc:
        raise ContractError(
            "INVALID_JSON",
            "$",
            f"{path}:{exc.lineno}:{exc.colno}: {exc.msg}",
        ) from exc
    if not isinstance(value, dict):
        raise ContractError("ROOT_NOT_OBJECT", "$", f"{path} must contain an object")
    return value


def _json_path(error: Any) -> str:
    path = "$"
    for part in error.path:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path


def validate_schema_instance(
    instance: dict[str, Any], schema: dict[str, Any], *, code: str
) -> dict[str, Any]:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: (list(error.path), error.message),
    )
    if errors:
        first = errors[0]
        raise ContractError(code, _json_path(first), first.message)
    return instance


def validate_registry(
    registry: dict[str, Any], registry_schema: dict[str, Any]
) -> dict[str, Any]:
    validate_schema_instance(registry, registry_schema, code="REGISTRY_SCHEMA_INVALID")

    grammar_ids = [item["grammarId"] for item in registry["grammars"]]
    if len(grammar_ids) != len(set(grammar_ids)):
        raise ContractError(
            "REGISTRY_DUPLICATE_GRAMMAR", "$.grammars", "grammarId must be unique"
        )
    actual_grammars = set(grammar_ids)
    if actual_grammars != GRAMMAR_IDS:
        raise ContractError(
            "REGISTRY_GRAMMAR_SET_MISMATCH",
            "$.grammars",
            f"missing={sorted(GRAMMAR_IDS - actual_grammars)} extra={sorted(actual_grammars - GRAMMAR_IDS)}",
        )

    phases = set(registry["grammarPhases"])
    if phases != GRAMMAR_PHASES:
        raise ContractError(
            "REGISTRY_PHASE_SET_MISMATCH",
            "$.grammarPhases",
            f"missing={sorted(GRAMMAR_PHASES - phases)} extra={sorted(phases - GRAMMAR_PHASES)}",
        )

    transitions = set(registry["transitionRoles"])
    if transitions != TRANSITION_ROLES:
        raise ContractError(
            "REGISTRY_TRANSITION_SET_MISMATCH",
            "$.transitionRoles",
            f"missing={sorted(TRANSITION_ROLES - transitions)} extra={sorted(transitions - TRANSITION_ROLES)}",
        )

    compatibility = registry["stageCompatibility"]
    compatibility_ids = [item["grammarId"] for item in compatibility]
    if len(compatibility_ids) != len(set(compatibility_ids)):
        raise ContractError(
            "REGISTRY_DUPLICATE_COMPATIBILITY",
            "$.stageCompatibility",
            "grammarId must be unique",
        )
    if set(compatibility_ids) != GRAMMAR_IDS:
        raise ContractError(
            "REGISTRY_COMPATIBILITY_SET_MISMATCH",
            "$.stageCompatibility",
            "stageCompatibility must cover every grammar exactly once",
        )

    for index, item in enumerate(compatibility):
        grammar_id = item["grammarId"]
        allowed = item["allowedStageIds"]
        expected = [STAGE_BY_GRAMMAR[grammar_id]]
        if allowed != expected:
            raise ContractError(
                "REGISTRY_STAGE_MAP_MISMATCH",
                f"$.stageCompatibility[{index}].allowedStageIds",
                f"{grammar_id} must map to {expected}",
            )

    return registry


def validate_declaration(
    declaration: dict[str, Any], declaration_schema: dict[str, Any]
) -> dict[str, Any]:
    return validate_schema_instance(
        declaration, declaration_schema, code="VISUAL_GRAMMAR_INVALID"
    )


def check_compatibility(
    grammar_id: str, stage_id: str, registry: dict[str, Any]
) -> CompatibilityDecision:
    if grammar_id not in GRAMMAR_IDS:
        raise ContractError(
            "GRAMMAR_UNKNOWN", "$.grammarId", f"unknown grammarId: {grammar_id}"
        )
    row = next(
        item
        for item in registry["stageCompatibility"]
        if item["grammarId"] == grammar_id
    )
    if stage_id not in row["allowedStageIds"]:
        raise ContractError(
            "GRAMMAR_STAGE_INCOMPATIBLE",
            "$.stageId",
            f"{stage_id} is not allowed for {grammar_id}; allowed={row['allowedStageIds']}",
        )
    return CompatibilityDecision(grammar_id, stage_id, True)


def _load_valid_registry(args: argparse.Namespace) -> dict[str, Any]:
    registry = load_json(args.registry)
    registry_schema = load_json(args.registry_schema)
    return validate_registry(registry, registry_schema)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("contracts/visual_grammar_registry.json"),
    )
    parser.add_argument(
        "--registry-schema",
        type=Path,
        default=Path("contracts/visual_grammar_registry.schema.json"),
    )
    parser.add_argument(
        "--declaration-schema",
        type=Path,
        default=Path("contracts/visual_grammar.schema.json"),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("registry")

    declaration_parser = subparsers.add_parser("declaration")
    declaration_parser.add_argument("declaration", type=Path)

    compatibility_parser = subparsers.add_parser("compatibility")
    compatibility_parser.add_argument("grammar_id")
    compatibility_parser.add_argument("stage_id")

    args = parser.parse_args(argv)

    try:
        registry = _load_valid_registry(args)
        if args.command == "registry":
            result: dict[str, Any] = {
                "contractVersion": CONTRACT_VERSION,
                "status": "PASS",
                "grammarCount": len(registry["grammars"]),
                "stageCompatibilityCount": len(registry["stageCompatibility"]),
            }
        elif args.command == "declaration":
            declaration = validate_declaration(
                load_json(args.declaration), load_json(args.declaration_schema)
            )
            result = {
                "contractVersion": CONTRACT_VERSION,
                "status": "PASS",
                "visualGrammar": declaration,
            }
        else:
            result = {
                "status": "PASS",
                **check_compatibility(
                    args.grammar_id, args.stage_id, registry
                ).as_dict(),
            }
    except ContractError as exc:
        print(
            json.dumps(
                {"status": "FAIL", "violation": exc.as_dict()},
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
