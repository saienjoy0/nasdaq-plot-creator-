#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


@dataclass
class Item:
    code: str
    message: str
    path: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return value


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(root: Path, value: str, label: str, errors: list[Item]) -> Path | None:
    root = root.resolve()
    raw = Path(value)
    if raw.is_absolute():
        errors.append(Item("E_PATH", "absolute path forbidden", label))
        return None
    path = (root / raw).resolve()
    if path != root and root not in path.parents:
        errors.append(Item("E_PATH", "path escapes repository root", label))
        return None
    if not path.is_file():
        errors.append(Item("E_PATH", f"missing file: {value}", label))
        return None
    return path


def schema_errors(instance: dict[str, Any], schema_path: Path, label: str) -> list[Item]:
    schema = load(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    out: list[Item] = []
    for err in sorted(validator.iter_errors(instance), key=lambda x: list(x.absolute_path)):
        suffix = ".".join(map(str, err.absolute_path))
        out.append(Item("E_SCHEMA", err.message, f"{label}.{suffix}" if suffix else label))
    return out


def validate(
    request_path: Path,
    receipt_path: Path,
    *,
    repo_root: Path,
    request_schema: Path,
    receipt_schema: Path,
    attestation_schema: Path | None = None,
    trust_registry: Path | None = None,
    trust_schema: Path | None = None,
) -> dict[str, Any]:
    root = repo_root.resolve()
    errors: list[Item] = []
    warnings: list[Item] = []
    try:
        request = load(request_path)
        receipt = load(receipt_path)
    except Exception as exc:
        return {"status": "fail", "errors": [Item("E_JSON", str(exc)).as_dict()], "warnings": []}

    errors += schema_errors(request, request_schema, "request")
    errors += schema_errors(receipt, receipt_schema, "receipt")
    if errors:
        return {"status": "fail", "errors": [x.as_dict() for x in errors], "warnings": []}

    if request["episode_date"] != receipt["episode_date"]:
        errors.append(Item("E_DATE", "request and receipt episode_date differ", "episode_date"))
    if request["author_invocation_id"] != receipt["author_invocation_id"]:
        errors.append(Item("E_AUTHOR_ID", "receipt author_invocation_id does not match request", "author_invocation_id"))
    if request["requested_critic_invocation_id"] != receipt["critic_invocation_id"]:
        errors.append(Item("E_CRITIC_ID", "receipt critic_invocation_id does not match request", "critic_invocation_id"))
    if receipt["author_invocation_id"] == receipt["critic_invocation_id"]:
        errors.append(Item("E_NOT_INDEPENDENT", "Author and Critic invocation IDs must differ", "critic_invocation_id"))
    if receipt["isolation_mode"] != "separate_invocation":
        errors.append(Item("E_ISOLATION", "production critic must use separate_invocation", "isolation_mode"))
    if not receipt["author_context_excluded"] or receipt["forbidden_author_context_present"]:
        errors.append(Item("E_CONTEXT_LEAK", "Author-only context was not excluded", "author_context_excluded"))

    supplied_request = safe(root, receipt["request"]["path"], "receipt.request", errors)
    if supplied_request and supplied_request.resolve() != request_path.resolve():
        errors.append(Item("E_REQUEST_PATH", "receipt does not point to supplied request", "receipt.request.path"))
    if supplied_request and git_blob_sha(supplied_request) != receipt["request"]["git_blob_sha"]:
        errors.append(Item("E_BLOB_SHA", "critic request Git blob SHA mismatch", "receipt.request.git_blob_sha"))

    roles: dict[str, Path] = {}
    for index, item in enumerate(request["inputs"]):
        role = item["role"]
        if role in roles:
            errors.append(Item("E_DUPLICATE_ROLE", f"duplicate critic input role: {role}", f"request.inputs.{index}"))
            continue
        path = safe(root, item["path"], f"request.inputs.{index}", errors)
        if path:
            roles[role] = path
            if git_blob_sha(path) != item["git_blob_sha"]:
                errors.append(Item("E_BLOB_SHA", f"Git blob SHA mismatch for {role}", f"request.inputs.{index}.git_blob_sha"))

    required_roles = {"story_plan_template", "story_script_template", "draft_episode_package", "visual_bindings", "fox_bible", "editorial_bible", "packed_rules_manifest"}
    missing_roles = required_roles - set(roles)
    if missing_roles:
        errors.append(Item("E_INPUT_SET", f"critic request missing required roles: {sorted(missing_roles)}", "request.inputs"))

    packed = roles.get("packed_rules_manifest")
    if packed:
        try:
            packed_doc = load(packed)
            expected = {row["logical_path"]: row["sha256"] for row in packed_doc.get("sources", [])}
            for row in request["logical_rules"]:
                if expected.get(row["logical_path"]) != row["sha256"]:
                    errors.append(Item("E_LOGICAL_RULE_SHA", f"packed source SHA mismatch for {row['logical_path']}", "request.logical_rules"))
        except Exception as exc:
            errors.append(Item("E_LOGICAL_RULES", str(exc), "request.logical_rules"))

    review_path = safe(root, receipt["review"]["path"], "receipt.review", errors)
    if review_path and git_blob_sha(review_path) != receipt["review"]["git_blob_sha"]:
        errors.append(Item("E_BLOB_SHA", "critic review Git blob SHA mismatch", "receipt.review.git_blob_sha"))
    if review_path:
        try:
            review = load(review_path)
            required_review = request["required_review"]
            if review.get("episode_date") != request["episode_date"]:
                errors.append(Item("E_REVIEW_DATE", "critic review date mismatch", "review.episode_date"))
            if review.get("reviewer") != "independent_critic":
                errors.append(Item("E_REVIEWER", "reviewer must be independent_critic", "review.reviewer"))
            if int(review.get("round", 0)) != int(receipt["review_round"]):
                errors.append(Item("E_REVIEW_ROUND", "review round differs from receipt", "review.round"))
            if int(review.get("round", 0)) != int(required_review["round"]):
                errors.append(Item("E_REVIEW_ROUND", "review round differs from request", "review.round"))
            if review.get("verdict") != required_review["required_verdict"]:
                errors.append(Item("E_REVIEW_VERDICT", "review verdict is not PASS", "review.verdict"))
            if int(review.get("total_score", 0)) < int(required_review["minimum_total_score"]):
                errors.append(Item("E_REVIEW_SCORE", "review score is below request minimum", "review.total_score"))
            if review.get("immediate_failures"):
                errors.append(Item("E_REVIEW_FAILURE", "review has immediate failures", "review.immediate_failures"))
            critical = [f for f in review.get("findings", []) if f.get("severity") == "critical" and f.get("status") not in {"fixed", "accepted"}]
            if len(critical) > int(required_review["critical_findings_allowed"]):
                errors.append(Item("E_CRITICAL_FINDING", "review retains Critical findings", "review.findings"))
        except Exception as exc:
            errors.append(Item("E_REVIEW_JSON", str(exc), "receipt.review"))

    strength = receipt["provenance"]["attestation_strength"]
    if strength == "repository_provenance":
        warnings.append(Item("W_NOT_CRYPTOGRAPHIC", "Repository provenance and SHA binding prove artifact separation, not cryptographic proof of a distinct model process.", "receipt.provenance.attestation_strength"))
    elif strength == "orchestrator_signed":
        ref = receipt.get("orchestrator_attestation")
        if not isinstance(ref, dict):
            errors.append(Item("E_ORCHESTRATOR_ATTESTATION", "orchestrator_signed receipt requires orchestrator_attestation", "orchestrator_attestation"))
        else:
            attestation_path = safe(root, ref.get("path", ""), "orchestrator_attestation.path", errors)
            if attestation_path and sha256(attestation_path) != ref.get("sha256"):
                errors.append(Item("E_ORCHESTRATOR_ATTESTATION_SHA", "orchestrator attestation SHA-256 mismatch", "orchestrator_attestation.sha256"))
            if attestation_path:
                attestation_schema = attestation_schema or root / "skills/nasdaq-cafe-story-engine/contracts/critic_orchestrator_attestation.schema.json"
                trust_registry = trust_registry or root / "skills/nasdaq-cafe-story-engine/trust/trusted_critic_orchestrators.json"
                trust_schema = trust_schema or root / "skills/nasdaq-cafe-story-engine/contracts/trusted_critic_orchestrators.schema.json"
                module = load_module(
                    "critic_orchestrator_attestation_validator",
                    root / "scripts/story-engine/validate_critic_orchestrator_attestation.py",
                )
                result = module.validate(
                    attestation_path,
                    repo_root=root,
                    attestation_schema=attestation_schema,
                    trust_registry=trust_registry,
                    trust_schema=trust_schema,
                    expected_request_path=request_path,
                    expected_review_path=review_path,
                )
                if result["status"] != "pass":
                    for item in result.get("errors", []):
                        errors.append(Item("E_ORCHESTRATOR_ATTESTATION", item.get("message", "attestation failed"), item.get("path", "")))
                try:
                    attestation = load(attestation_path)
                    if attestation.get("episode_date") != receipt["episode_date"]:
                        errors.append(Item("E_ORCHESTRATOR_DATE", "attestation episode_date differs from receipt", "orchestrator_attestation"))
                    if attestation.get("author_invocation_id") != receipt["author_invocation_id"]:
                        errors.append(Item("E_ORCHESTRATOR_AUTHOR", "attestation author invocation differs from receipt", "orchestrator_attestation"))
                    if attestation.get("critic_invocation_id") != receipt["critic_invocation_id"]:
                        errors.append(Item("E_ORCHESTRATOR_CRITIC", "attestation critic invocation differs from receipt", "orchestrator_attestation"))
                except Exception as exc:
                    errors.append(Item("E_ORCHESTRATOR_ATTESTATION", str(exc), "orchestrator_attestation"))

    return {
        "contract_version": "1.0.0",
        "episode_date": request.get("episode_date", "unknown"),
        "status": "fail" if errors else "pass",
        "attestation_strength": strength,
        "errors": [x.as_dict() for x in errors],
        "warnings": [x.as_dict() for x in warnings],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--request", type=Path, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--request-schema", type=Path, default=Path("skills/nasdaq-cafe-story-engine/contracts/critic_request.schema.json"))
    ap.add_argument("--receipt-schema", type=Path, default=Path("skills/nasdaq-cafe-story-engine/contracts/critic_execution_receipt.schema.json"))
    ap.add_argument("--attestation-schema", type=Path, default=Path("skills/nasdaq-cafe-story-engine/contracts/critic_orchestrator_attestation.schema.json"))
    ap.add_argument("--trust-registry", type=Path, default=Path("skills/nasdaq-cafe-story-engine/trust/trusted_critic_orchestrators.json"))
    ap.add_argument("--trust-schema", type=Path, default=Path("skills/nasdaq-cafe-story-engine/contracts/trusted_critic_orchestrators.schema.json"))
    args = ap.parse_args()
    root = args.repo_root.resolve()

    def resolve(path: Path) -> Path:
        return path if path.is_absolute() else root / path

    result = validate(
        resolve(args.request),
        resolve(args.receipt),
        repo_root=root,
        request_schema=resolve(args.request_schema),
        receipt_schema=resolve(args.receipt_schema),
        attestation_schema=resolve(args.attestation_schema),
        trust_registry=resolve(args.trust_registry),
        trust_schema=resolve(args.trust_schema),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
