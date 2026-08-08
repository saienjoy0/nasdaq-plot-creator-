#!/usr/bin/env python3
"""Run the NASDAQ Cafe independent Critic in an isolated external container.

This command is intended to run outside GitHub Actions on a trusted orchestrator host.
It exposes only the frozen Critic Request inputs to the Critic container, validates the
returned review, records the execution boundary, signs an Ed25519 attestation with a
private key that must live outside the repository, and emits an orchestrator-signed
Critic execution receipt.

The Critic adapter image contract is intentionally provider-neutral. The image must read:

  NASDAQ_CAFE_CRITIC_REQUEST=/critic/input/critic_request.json
  NASDAQ_CAFE_CRITIC_BUNDLE=/critic/input/bundle_manifest.json

and write one JSON review to:

  NASDAQ_CAFE_CRITIC_REVIEW_OUT=/critic/output/creative_review.json

GitHub Actions may verify the resulting artifacts, but must not run this command with a
private signing key and must not create or rewrite Critic judgments.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
PINNED_IMAGE_RE = re.compile(r"^.+@sha256:[0-9a-f]{64}$")


class OrchestratorError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise OrchestratorError(f"JSON root must be an object: {path}")
    return value


def dump_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("utf-8") + data).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise OrchestratorError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def inside(root: Path, path: Path) -> bool:
    root = root.resolve()
    path = path.resolve()
    return path == root or root in path.parents


def safe_repo_path(root: Path, raw: str, label: str) -> Path:
    value = Path(raw)
    if value.is_absolute():
        raise OrchestratorError(f"{label}: absolute repository path is forbidden: {raw}")
    path = (root / value).resolve()
    if not inside(root, path):
        raise OrchestratorError(f"{label}: path escapes repository: {raw}")
    if not path.is_file():
        raise OrchestratorError(f"{label}: missing file: {raw}")
    return path


def require_repo_directory(root: Path, path: Path, label: str) -> Path:
    value = path if path.is_absolute() else root / path
    value = value.resolve()
    if not inside(root, value):
        raise OrchestratorError(f"{label} must be inside the repository so validators can bind the emitted artifacts")
    value.mkdir(parents=True, exist_ok=True)
    return value


def validate_schema(instance: dict[str, Any], schema_path: Path, label: str) -> None:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    if errors:
        message = "; ".join(
            f"{label}.{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in errors
        )
        raise OrchestratorError(message)


def reconstruct_packed_logical_source(root: Path, packed_row: dict[str, Any]) -> bytes:
    encoding = packed_row.get("encoding")
    if encoding != "gzip+base64-concatenated":
        raise OrchestratorError(
            f"unsupported packed source encoding for {packed_row.get('logical_path')}: {encoding}"
        )
    chunks: list[str] = []
    for index, part in enumerate(packed_row.get("parts", [])):
        part_path = safe_repo_path(root, str(part), f"packed part {index}")
        chunks.append(part_path.read_text(encoding="utf-8").strip())
    try:
        compressed = base64.b64decode("".join(chunks), validate=True)
        raw = gzip.decompress(compressed)
    except Exception as exc:  # noqa: BLE001 - converted to contract failure
        raise OrchestratorError(
            f"failed to reconstruct packed source {packed_row.get('logical_path')}: {exc}"
        ) from exc
    expected_size = packed_row.get("raw_bytes")
    if isinstance(expected_size, int) and len(raw) != expected_size:
        raise OrchestratorError(
            f"packed source size mismatch for {packed_row.get('logical_path')}: {len(raw)} != {expected_size}"
        )
    expected_sha = str(packed_row.get("sha256", ""))
    if sha256_bytes(raw) != expected_sha:
        raise OrchestratorError(
            f"packed source SHA-256 mismatch for {packed_row.get('logical_path')}"
        )
    return raw


def prepare_bundle(
    *,
    repo_root: Path,
    request_path: Path,
    request_schema: Path,
    bundle_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = repo_root.resolve()
    request = load_json(request_path)
    validate_schema(request, request_schema, "critic_request")

    if request["author_invocation_id"] == request["requested_critic_invocation_id"]:
        raise OrchestratorError("Author and requested Critic invocation IDs must differ")
    if request.get("isolation_contract", {}).get("mode") != "separate_invocation":
        raise OrchestratorError("Critic Request must require separate_invocation")

    bundle_dir.mkdir(parents=True, exist_ok=False)
    inputs_dir = bundle_dir / "inputs"
    logical_dir = bundle_dir / "logical_rules"
    inputs_dir.mkdir()
    logical_dir.mkdir()

    shutil.copy2(request_path, bundle_dir / "critic_request.json")

    bundled_inputs: list[dict[str, Any]] = []
    role_sources: dict[str, Path] = {}
    for index, row in enumerate(request.get("inputs", [])):
        role = str(row.get("role", ""))
        if not role or role in role_sources:
            raise OrchestratorError(f"duplicate or empty Critic input role at index {index}: {role!r}")
        source = safe_repo_path(root, str(row.get("path", "")), f"critic input {index}")
        actual_blob = git_blob_sha(source)
        if actual_blob != row.get("git_blob_sha"):
            raise OrchestratorError(f"Git blob SHA mismatch for Critic input role {role}")
        role_sources[role] = source
        suffix = source.suffix if source.suffix else ".bin"
        target = inputs_dir / f"{role}{suffix}"
        shutil.copy2(source, target)
        bundled_inputs.append(
            {
                "role": role,
                "bundled_path": f"inputs/{target.name}",
                "sha256": sha256(target),
                "source_git_blob_sha": actual_blob,
            }
        )

    required_roles = {
        "story_plan_template",
        "story_script_template",
        "draft_episode_package",
        "visual_bindings",
        "fox_bible",
        "editorial_bible",
        "packed_rules_manifest",
    }
    missing = required_roles - set(role_sources)
    if missing:
        raise OrchestratorError(f"Critic Request missing required input roles: {sorted(missing)}")

    packed_manifest = load_json(role_sources["packed_rules_manifest"])
    packed_by_logical = {
        str(row.get("logical_path")): row
        for row in packed_manifest.get("sources", [])
        if isinstance(row, dict) and row.get("logical_path")
    }

    bundled_rules: list[dict[str, Any]] = []
    for row in request.get("logical_rules", []):
        logical_path = str(row.get("logical_path", ""))
        expected_sha = str(row.get("sha256", ""))
        packed_row = packed_by_logical.get(logical_path)
        if not packed_row:
            raise OrchestratorError(f"logical rule is absent from packed source manifest: {logical_path}")
        if packed_row.get("sha256") != expected_sha:
            raise OrchestratorError(f"logical rule SHA differs from packed source manifest: {logical_path}")
        raw = reconstruct_packed_logical_source(root, packed_row)
        target = logical_dir / Path(logical_path).name
        target.write_bytes(raw)
        if sha256(target) != expected_sha:
            raise OrchestratorError(f"materialized logical rule SHA mismatch: {logical_path}")
        bundled_rules.append(
            {
                "logical_path": logical_path,
                "bundled_path": f"logical_rules/{target.name}",
                "sha256": expected_sha,
            }
        )

    manifest = {
        "contract_version": "1.0.0",
        "episode_date": request["episode_date"],
        "author_invocation_id": request["author_invocation_id"],
        "critic_invocation_id": request["requested_critic_invocation_id"],
        "request_sha256": sha256(request_path),
        "request_git_blob_sha": git_blob_sha(request_path),
        "inputs": bundled_inputs,
        "logical_rules": bundled_rules,
        "instruction": request["instruction"],
        "required_review": request["required_review"],
    }
    dump_json(bundle_dir / "bundle_manifest.json", manifest)
    return request, manifest


def validate_review(review_path: Path, request: dict[str, Any]) -> dict[str, Any]:
    review = load_json(review_path)
    required = request["required_review"]
    if review.get("episode_date") != request["episode_date"]:
        raise OrchestratorError("Critic review episode_date mismatch")
    if review.get("reviewer") != "independent_critic":
        raise OrchestratorError("Critic review reviewer must be independent_critic")
    if int(review.get("round", 0)) != int(required["round"]):
        raise OrchestratorError("Critic review round mismatch")
    if review.get("verdict") != required["required_verdict"]:
        raise OrchestratorError("Critic review verdict does not satisfy the frozen request")
    if int(review.get("total_score", 0)) < int(required["minimum_total_score"]):
        raise OrchestratorError("Critic review score is below the frozen request threshold")
    if review.get("immediate_failures"):
        raise OrchestratorError("Critic review contains immediate failures")
    unresolved_critical = [
        item
        for item in review.get("findings", [])
        if isinstance(item, dict)
        and item.get("severity") == "critical"
        and item.get("status") not in {"fixed", "accepted"}
    ]
    if len(unresolved_critical) > int(required["critical_findings_allowed"]):
        raise OrchestratorError("Critic review retains unresolved Critical findings")
    return review


def docker_image_id(image: str) -> str | None:
    result = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def run_adapter_container(
    *,
    bundle_dir: Path,
    staging_output_dir: Path,
    adapter_image: str,
    pass_env: list[str],
    network_mode: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    if not PINNED_IMAGE_RE.fullmatch(adapter_image):
        raise OrchestratorError("--adapter-image must be pinned with @sha256:<64 hex>")
    if shutil.which("docker") is None:
        raise OrchestratorError("docker is required for the production Critic isolation boundary")

    missing_env = [name for name in pass_env if name not in os.environ]
    if missing_env:
        raise OrchestratorError(f"requested adapter environment variables are missing: {missing_env}")

    staging_output_dir.mkdir(parents=True, exist_ok=False)
    cidfile = staging_output_dir.parent / "critic-container.cid"
    if cidfile.exists():
        cidfile.unlink()

    command = [
        "docker",
        "run",
        "--rm",
        "--cidfile",
        str(cidfile),
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges:true",
        "--pids-limit=128",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=64m",
        "--network",
        network_mode,
        "--mount",
        f"type=bind,src={bundle_dir.resolve()},dst=/critic/input,readonly",
        "--mount",
        f"type=bind,src={staging_output_dir.resolve()},dst=/critic/output",
        "--workdir",
        "/critic/output",
        "-e",
        "NASDAQ_CAFE_CRITIC_REQUEST=/critic/input/critic_request.json",
        "-e",
        "NASDAQ_CAFE_CRITIC_BUNDLE=/critic/input/bundle_manifest.json",
        "-e",
        "NASDAQ_CAFE_CRITIC_REVIEW_OUT=/critic/output/creative_review.json",
    ]
    for name in pass_env:
        command.extend(["-e", name])
    command.append(adapter_image)

    started_at = utc_now()
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise OrchestratorError(f"Critic adapter timed out after {timeout_seconds}s") from exc
    finished_at = utc_now()

    container_id = cidfile.read_text(encoding="utf-8").strip() if cidfile.exists() else None
    stdout = result.stdout or b""
    stderr = result.stderr or b""
    runtime = {
        "started_at": started_at,
        "finished_at": finished_at,
        "exit_code": result.returncode,
        "container_id": container_id,
        "adapter_image": adapter_image,
        "adapter_image_id": docker_image_id(adapter_image),
        "network_mode": network_mode,
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_sha256": sha256_bytes(stderr),
        "stdout_bytes": len(stdout),
        "stderr_bytes": len(stderr),
        "repo_mounted": False,
        "input_mount_read_only": True,
        "author_context_mounted": False,
        "passed_environment_names": sorted(pass_env),
    }
    if result.returncode != 0:
        raise OrchestratorError(
            "Critic adapter failed with exit code "
            f"{result.returncode}; stdout_sha256={runtime['stdout_sha256']} stderr_sha256={runtime['stderr_sha256']}"
        )
    return runtime


def load_private_key(path: Path, password_env: str | None) -> Ed25519PrivateKey:
    password: bytes | None = None
    if password_env:
        value = os.environ.get(password_env)
        if value is None:
            raise OrchestratorError(f"private-key password environment variable is missing: {password_env}")
        password = value.encode("utf-8")
    try:
        key = serialization.load_pem_private_key(path.read_bytes(), password=password)
    except Exception as exc:  # noqa: BLE001
        raise OrchestratorError(f"failed to load Ed25519 private key: {exc}") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise OrchestratorError("private signing key must be Ed25519")
    return key


def canonical_attestation_payload(doc: dict[str, Any]) -> bytes:
    payload = {key: value for key, value in doc.items() if key != "signature"}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def emit_signed_artifacts(
    *,
    repo_root: Path,
    request_path: Path,
    request: dict[str, Any],
    review_source: Path,
    runtime: dict[str, Any],
    bundle_manifest: dict[str, Any],
    output_dir: Path,
    private_key_path: Path,
    private_key_password_env: str | None,
    key_id: str,
    orchestrator_id: str,
    orchestrator_run_id: str,
    verifier_id: str,
    allow_overwrite: bool,
) -> dict[str, Path]:
    root = repo_root.resolve()
    if inside(root, private_key_path):
        raise OrchestratorError("private signing key must be outside the repository")
    if request["author_invocation_id"] == request["requested_critic_invocation_id"]:
        raise OrchestratorError("Author and Critic invocation IDs must differ")

    review_target = output_dir / "creative_review.template.json"
    verification_target = output_dir / "critic_external_verification.json"
    attestation_target = output_dir / "critic_orchestrator_attestation.json"
    receipt_target = output_dir / "critic_execution_receipt.json"
    for target in (review_target, verification_target, attestation_target, receipt_target):
        if target.exists() and not allow_overwrite:
            raise OrchestratorError(f"refusing to overwrite existing artifact without --allow-overwrite: {target}")

    review_bytes = review_source.read_bytes()
    review_target.write_bytes(review_bytes)

    verification = {
        "contract_version": "1.0.0",
        "episode_date": request["episode_date"],
        "orchestrator_id": orchestrator_id,
        "orchestrator_run_id": orchestrator_run_id,
        "author_invocation_id": request["author_invocation_id"],
        "critic_invocation_id": request["requested_critic_invocation_id"],
        "isolation_backend": "docker-readonly-bundle",
        "adapter_image": runtime["adapter_image"],
        "adapter_image_id": runtime.get("adapter_image_id"),
        "network_mode": runtime["network_mode"],
        "container_id": runtime.get("container_id"),
        "started_at": runtime["started_at"],
        "finished_at": runtime["finished_at"],
        "exit_code": runtime["exit_code"],
        "request_sha256": sha256(request_path),
        "bundle_manifest_sha256": sha256_bytes(
            (json.dumps(bundle_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        ),
        "review_sha256": sha256(review_target),
        "repo_mounted": runtime["repo_mounted"],
        "input_mount_read_only": runtime["input_mount_read_only"],
        "author_context_mounted": runtime["author_context_mounted"],
        "passed_environment_names": runtime["passed_environment_names"],
        "stdout_sha256": runtime["stdout_sha256"],
        "stderr_sha256": runtime["stderr_sha256"],
        "stdout_bytes": runtime["stdout_bytes"],
        "stderr_bytes": runtime["stderr_bytes"],
    }
    dump_json(verification_target, verification)

    attestation = {
        "contract_version": "1.0.0",
        "episode_date": request["episode_date"],
        "attestation_id": f"critic-att-{uuid.uuid4().hex}",
        "orchestrator_id": orchestrator_id,
        "orchestrator_run_id": orchestrator_run_id,
        "author_invocation_id": request["author_invocation_id"],
        "critic_invocation_id": request["requested_critic_invocation_id"],
        "request_sha256": sha256(request_path),
        "review_sha256": sha256(review_target),
        "execution_boundary": {
            "distinct_execution": True,
            "shared_author_context": False,
            "request_only_input": True,
            "critic_started_after_request_sealed": True,
        },
        "issued_at": utc_now(),
        "verification": {
            "method": "orchestrator_supervisor",
            "verifier_id": verifier_id,
            "verification_record": {
                "path": verification_target.resolve().relative_to(root).as_posix(),
                "sha256": sha256(verification_target),
            },
        },
    }
    private_key = load_private_key(private_key_path.resolve(), private_key_password_env)
    signature = private_key.sign(canonical_attestation_payload(attestation))
    attestation["signature"] = {
        "algorithm": "ed25519",
        "key_id": key_id,
        "signature_base64": base64.b64encode(signature).decode("ascii"),
    }
    dump_json(attestation_target, attestation)

    receipt = {
        "contract_version": "1.0.0",
        "episode_date": request["episode_date"],
        "author_invocation_id": request["author_invocation_id"],
        "critic_invocation_id": request["requested_critic_invocation_id"],
        "isolation_mode": "separate_invocation",
        "author_context_excluded": True,
        "forbidden_author_context_present": False,
        "review_round": int(request["required_review"]["round"]),
        "request": {
            "path": request_path.resolve().relative_to(root).as_posix(),
            "git_blob_sha": git_blob_sha(request_path),
        },
        "review": {
            "path": review_target.resolve().relative_to(root).as_posix(),
            "git_blob_sha": git_blob_sha(review_target),
        },
        "provenance": {
            "orchestrator_id": orchestrator_id,
            "orchestrator_run_id": orchestrator_run_id,
            "attestation_strength": "orchestrator_signed",
            "note": "A trusted external orchestrator ran the Critic in a Docker container with only the sealed request bundle mounted read-only and signed the execution attestation with an out-of-repository Ed25519 key.",
        },
        "attestation": "The Critic ran in a distinct isolated execution after the frozen request was sealed. Author-only context was not mounted or forwarded.",
        "orchestrator_attestation": {
            "path": attestation_target.resolve().relative_to(root).as_posix(),
            "sha256": sha256(attestation_target),
        },
    }
    dump_json(receipt_target, receipt)
    return {
        "review": review_target,
        "verification": verification_target,
        "attestation": attestation_target,
        "receipt": receipt_target,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=ROOT)
    ap.add_argument("--request", type=Path, required=True)
    ap.add_argument("--request-schema", type=Path, default=Path("skills/nasdaq-cafe-story-engine/contracts/critic_request.schema.json"))
    ap.add_argument("--adapter-image", required=True, help="Pinned Critic adapter image, e.g. repo/image@sha256:<digest>")
    ap.add_argument("--output-dir", type=Path, required=True, help="Repository directory for verified public Critic artifacts")
    ap.add_argument("--private-key", type=Path, required=True, help="Ed25519 PEM private key outside the repository")
    ap.add_argument("--private-key-password-env")
    ap.add_argument("--key-id", required=True)
    ap.add_argument("--orchestrator-id", required=True)
    ap.add_argument("--orchestrator-run-id", default=None)
    ap.add_argument("--verifier-id", default="nasdaq-cafe-external-critic-supervisor-v1")
    ap.add_argument("--network", default="bridge", choices=["bridge", "host", "none"])
    ap.add_argument("--pass-env", action="append", default=[], help="Environment variable name to pass to the Critic container; repeat as needed")
    ap.add_argument("--timeout-seconds", type=int, default=900)
    ap.add_argument("--allow-overwrite", action="store_true")
    args = ap.parse_args()

    root = args.repo_root.resolve()
    request_path = args.request if args.request.is_absolute() else root / args.request
    request_path = request_path.resolve()
    if not inside(root, request_path) or not request_path.is_file():
        raise OrchestratorError("--request must resolve to an existing file inside the repository")
    request_schema = args.request_schema if args.request_schema.is_absolute() else root / args.request_schema
    output_dir = require_repo_directory(root, args.output_dir, "--output-dir")
    private_key_path = args.private_key.resolve()
    if inside(root, private_key_path):
        raise OrchestratorError("--private-key must be outside the repository")
    if not private_key_path.is_file():
        raise OrchestratorError("--private-key does not exist")

    run_id = args.orchestrator_run_id or f"critic-run-{uuid.uuid4().hex}"
    with tempfile.TemporaryDirectory(prefix="nasdaq-cafe-critic-") as temp:
        temp_root = Path(temp)
        bundle_dir = temp_root / "bundle"
        staging_output_dir = temp_root / "output"
        request, bundle_manifest = prepare_bundle(
            repo_root=root,
            request_path=request_path,
            request_schema=request_schema.resolve(),
            bundle_dir=bundle_dir,
        )
        runtime = run_adapter_container(
            bundle_dir=bundle_dir,
            staging_output_dir=staging_output_dir,
            adapter_image=args.adapter_image,
            pass_env=list(dict.fromkeys(args.pass_env)),
            network_mode=args.network,
            timeout_seconds=args.timeout_seconds,
        )
        review_source = staging_output_dir / "creative_review.json"
        if not review_source.is_file() or review_source.stat().st_size == 0:
            raise OrchestratorError("Critic adapter did not emit /critic/output/creative_review.json")
        validate_review(review_source, request)
        emitted = emit_signed_artifacts(
            repo_root=root,
            request_path=request_path,
            request=request,
            review_source=review_source,
            runtime=runtime,
            bundle_manifest=bundle_manifest,
            output_dir=output_dir,
            private_key_path=private_key_path,
            private_key_password_env=args.private_key_password_env,
            key_id=args.key_id,
            orchestrator_id=args.orchestrator_id,
            orchestrator_run_id=run_id,
            verifier_id=args.verifier_id,
            allow_overwrite=args.allow_overwrite,
        )

    receipt_validator = load_module(
        "critic_receipt_post_orchestrator",
        root / "scripts/story-engine/validate_critic_execution_receipt.py",
    )
    result = receipt_validator.validate(
        request_path,
        emitted["receipt"],
        repo_root=root,
        request_schema=root / "skills/nasdaq-cafe-story-engine/contracts/critic_request.schema.json",
        receipt_schema=root / "skills/nasdaq-cafe-story-engine/contracts/critic_execution_receipt.schema.json",
        attestation_schema=root / "skills/nasdaq-cafe-story-engine/contracts/critic_orchestrator_attestation.schema.json",
        trust_registry=root / "skills/nasdaq-cafe-story-engine/trust/trusted_critic_orchestrators.json",
        trust_schema=root / "skills/nasdaq-cafe-story-engine/contracts/trusted_critic_orchestrators.schema.json",
    )
    if result["status"] != "pass":
        raise OrchestratorError(
            "emitted orchestrator-signed Critic receipt failed repository trust validation: "
            + "; ".join(item.get("message", "validation failure") for item in result.get("errors", []))
        )

    print(
        json.dumps(
            {
                "status": "pass",
                "episode_date": request["episode_date"],
                "orchestrator_run_id": run_id,
                "adapter_image": args.adapter_image,
                "paths": {name: path.resolve().relative_to(root).as_posix() for name, path in emitted.items()},
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OrchestratorError as exc:
        print(f"external Critic orchestrator failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
