#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker


@dataclass
class Item:
    code: str
    message: str
    path: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return value


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


def canonical_signed_payload(attestation: dict[str, Any]) -> bytes:
    payload = {key: value for key, value in attestation.items() if key != "signature"}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def validate(
    attestation_path: Path,
    *,
    repo_root: Path,
    attestation_schema: Path,
    trust_registry: Path,
    trust_schema: Path,
    verification_schema: Path | None = None,
    expected_request_path: Path | None = None,
    expected_review_path: Path | None = None,
) -> dict[str, Any]:
    root = repo_root.resolve()
    errors: list[Item] = []
    warnings: list[Item] = []
    try:
        attestation = load(attestation_path)
        registry = load(trust_registry)
    except Exception as exc:
        return {"status": "fail", "errors": [Item("E_JSON", str(exc)).as_dict()], "warnings": []}

    errors += schema_errors(attestation, attestation_schema, "attestation")
    errors += schema_errors(registry, trust_schema, "trust_registry")
    if errors:
        return {"status": "fail", "errors": [x.as_dict() for x in errors], "warnings": []}

    if attestation["author_invocation_id"] == attestation["critic_invocation_id"]:
        errors.append(Item("E_NOT_INDEPENDENT", "Author and Critic invocation IDs must differ", "critic_invocation_id"))

    if expected_request_path is not None:
        request_path = expected_request_path.resolve()
        if not request_path.is_file():
            errors.append(Item("E_REQUEST", "expected request does not exist", "request_sha256"))
        elif sha256(request_path) != attestation["request_sha256"]:
            errors.append(Item("E_REQUEST_SHA", "attestation request SHA-256 mismatch", "request_sha256"))

    if expected_review_path is not None:
        review_path = expected_review_path.resolve()
        if not review_path.is_file():
            errors.append(Item("E_REVIEW", "expected review does not exist", "review_sha256"))
        elif sha256(review_path) != attestation["review_sha256"]:
            errors.append(Item("E_REVIEW_SHA", "attestation review SHA-256 mismatch", "review_sha256"))

    record_ref = attestation["verification"]["verification_record"]
    record_path = safe(root, record_ref["path"], "verification.verification_record.path", errors)
    record: dict[str, Any] | None = None
    if record_path and sha256(record_path) != record_ref["sha256"]:
        errors.append(Item("E_VERIFICATION_RECORD_SHA", "verification record SHA-256 mismatch", "verification.verification_record.sha256"))
    if record_path:
        try:
            record = load(record_path)
        except Exception as exc:
            errors.append(Item("E_VERIFICATION_RECORD", str(exc), "verification.verification_record"))

    if record is not None and attestation["verification"].get("method") == "orchestrator_supervisor":
        verification_schema = verification_schema or root / "skills/nasdaq-cafe-story-engine/contracts/critic_external_verification.schema.json"
        errors += schema_errors(record, verification_schema, "verification_record")
        comparisons = {
            "episode_date": attestation["episode_date"],
            "orchestrator_id": attestation["orchestrator_id"],
            "orchestrator_run_id": attestation["orchestrator_run_id"],
            "author_invocation_id": attestation["author_invocation_id"],
            "critic_invocation_id": attestation["critic_invocation_id"],
            "request_sha256": attestation["request_sha256"],
            "review_sha256": attestation["review_sha256"],
        }
        for key, expected in comparisons.items():
            if record.get(key) != expected:
                errors.append(Item("E_VERIFICATION_BINDING", f"verification record {key} differs from attestation", f"verification_record.{key}"))
        if record.get("isolation_backend") != "docker-readonly-bundle":
            errors.append(Item("E_ISOLATION_BACKEND", "production Critic verification must use docker-readonly-bundle", "verification_record.isolation_backend"))
        if record.get("repo_mounted") is not False:
            errors.append(Item("E_REPO_MOUNTED", "repository must not be mounted into Critic execution", "verification_record.repo_mounted"))
        if record.get("input_mount_read_only") is not True:
            errors.append(Item("E_INPUT_MOUNT", "Critic input mount must be read-only", "verification_record.input_mount_read_only"))
        if record.get("author_context_mounted") is not False:
            errors.append(Item("E_CONTEXT_LEAK", "Author context must not be mounted into Critic execution", "verification_record.author_context_mounted"))
        if record.get("exit_code") != 0:
            errors.append(Item("E_CRITIC_EXIT", "Critic execution must exit with code 0", "verification_record.exit_code"))

    signature = attestation["signature"]
    key_id = signature["key_id"]
    candidates = [row for row in registry["keys"] if row.get("key_id") == key_id]
    if len(candidates) != 1:
        errors.append(Item("E_TRUST_KEY", f"trusted key not found exactly once: {key_id}", "signature.key_id"))
        key = None
    else:
        key = candidates[0]
        if key.get("status") != "active":
            errors.append(Item("E_TRUST_KEY_REVOKED", f"trusted key is not active: {key_id}", "signature.key_id"))
        if key.get("orchestrator_id") != attestation["orchestrator_id"]:
            errors.append(Item("E_ORCHESTRATOR_KEY", "key orchestrator_id differs from attestation", "orchestrator_id"))
        if key.get("algorithm") != "ed25519" or signature.get("algorithm") != "ed25519":
            errors.append(Item("E_ALGORITHM", "only ed25519 is accepted", "signature.algorithm"))

    if not errors and key is not None:
        try:
            public_key = serialization.load_pem_public_key(key["public_key_pem"].encode("utf-8"))
            if not isinstance(public_key, Ed25519PublicKey):
                errors.append(Item("E_PUBLIC_KEY", "trusted key is not Ed25519", "trust_registry.keys"))
            else:
                raw_signature = base64.b64decode(signature["signature_base64"], validate=True)
                public_key.verify(raw_signature, canonical_signed_payload(attestation))
        except (ValueError, TypeError, InvalidSignature) as exc:
            errors.append(Item("E_SIGNATURE", f"Ed25519 signature verification failed: {exc}", "signature.signature_base64"))

    return {
        "contract_version": "1.0.0",
        "episode_date": attestation.get("episode_date", "unknown"),
        "status": "fail" if errors else "pass",
        "attestation_id": attestation.get("attestation_id"),
        "orchestrator_id": attestation.get("orchestrator_id"),
        "orchestrator_run_id": attestation.get("orchestrator_run_id"),
        "errors": [x.as_dict() for x in errors],
        "warnings": [x.as_dict() for x in warnings],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--attestation", type=Path, required=True)
    ap.add_argument("--attestation-schema", type=Path, default=Path("skills/nasdaq-cafe-story-engine/contracts/critic_orchestrator_attestation.schema.json"))
    ap.add_argument("--trust-registry", type=Path, default=Path("skills/nasdaq-cafe-story-engine/trust/trusted_critic_orchestrators.json"))
    ap.add_argument("--trust-schema", type=Path, default=Path("skills/nasdaq-cafe-story-engine/contracts/trusted_critic_orchestrators.schema.json"))
    ap.add_argument("--verification-schema", type=Path, default=Path("skills/nasdaq-cafe-story-engine/contracts/critic_external_verification.schema.json"))
    ap.add_argument("--request", type=Path)
    ap.add_argument("--review", type=Path)
    args = ap.parse_args()
    root = args.repo_root.resolve()

    def resolve(path: Path | None) -> Path | None:
        if path is None:
            return None
        return path if path.is_absolute() else root / path

    result = validate(
        resolve(args.attestation),
        repo_root=root,
        attestation_schema=resolve(args.attestation_schema),
        trust_registry=resolve(args.trust_registry),
        trust_schema=resolve(args.trust_schema),
        verification_schema=resolve(args.verification_schema),
        expected_request_path=resolve(args.request),
        expected_review_path=resolve(args.review),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
