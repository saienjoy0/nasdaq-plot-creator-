#!/usr/bin/env python3
"""Zero-call preflight for the external independent Critic orchestrator.

This command performs no model/API invocation. It validates the frozen request bundle,
Docker availability, digest-pinned adapter image syntax, required environment variable
presence, and the Ed25519 signing identity against the repository trust registry.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]


class PreflightError(RuntimeError):
    pass


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise PreflightError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PreflightError(f"JSON root must be object: {path}")
    return value


def validate_trust_identity(
    *,
    runner,
    repo_root: Path,
    private_key_path: Path,
    private_key_password_env: str | None,
    key_id: str,
    orchestrator_id: str,
    trust_registry: Path,
    trust_schema: Path,
) -> None:
    root = repo_root.resolve()
    key_path = private_key_path.resolve()
    if runner.inside(root, key_path):
        raise PreflightError("private signing key must be outside the repository")
    if not key_path.is_file():
        raise PreflightError("private signing key does not exist")

    registry = load_json(trust_registry)
    schema = load_json(trust_schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(registry), key=lambda e: list(e.absolute_path))
    if errors:
        raise PreflightError("trust registry schema invalid: " + "; ".join(e.message for e in errors))

    candidates = [row for row in registry.get("keys", []) if row.get("key_id") == key_id]
    if len(candidates) != 1:
        raise PreflightError(f"trusted orchestrator key must exist exactly once before model execution: {key_id}")
    trusted = candidates[0]
    if trusted.get("status") != "active":
        raise PreflightError(f"trusted orchestrator key is not active: {key_id}")
    if trusted.get("orchestrator_id") != orchestrator_id:
        raise PreflightError("trusted key orchestrator_id does not match --orchestrator-id")
    if trusted.get("algorithm") != "ed25519":
        raise PreflightError("trusted orchestrator key must use ed25519")

    private_key = runner.load_private_key(key_path, private_key_password_env)
    trusted_public = serialization.load_pem_public_key(trusted["public_key_pem"].encode("utf-8"))
    if not isinstance(trusted_public, Ed25519PublicKey):
        raise PreflightError("trusted public key is not Ed25519")
    expected_raw = trusted_public.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    actual_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    if actual_raw != expected_raw:
        raise PreflightError("private signing key does not match the active trusted public key")


def run_preflight(args: argparse.Namespace) -> dict:
    root = args.repo_root.resolve()
    runner = load_module(
        "external_critic_orchestrator_runner_preflight",
        root / "scripts/story-engine/run_external_critic_orchestrator.py",
    )
    request_path = args.request if args.request.is_absolute() else root / args.request
    request_path = request_path.resolve()
    if not runner.inside(root, request_path) or not request_path.is_file():
        raise PreflightError("--request must resolve to an existing file inside the repository")
    request_schema = args.request_schema if args.request_schema.is_absolute() else root / args.request_schema

    if not runner.PINNED_IMAGE_RE.fullmatch(args.adapter_image):
        raise PreflightError("--adapter-image must be pinned with @sha256:<64 hex>")
    if shutil.which("docker") is None:
        raise PreflightError("docker is required for the isolated Critic production path")
    missing_env = [name for name in args.pass_env if name not in os.environ]
    if missing_env:
        raise PreflightError(f"adapter environment variables are missing: {missing_env}")

    trust_registry = args.trust_registry if args.trust_registry.is_absolute() else root / args.trust_registry
    trust_schema = args.trust_schema if args.trust_schema.is_absolute() else root / args.trust_schema
    validate_trust_identity(
        runner=runner,
        repo_root=root,
        private_key_path=args.private_key,
        private_key_password_env=args.private_key_password_env,
        key_id=args.key_id,
        orchestrator_id=args.orchestrator_id,
        trust_registry=trust_registry.resolve(),
        trust_schema=trust_schema.resolve(),
    )

    with tempfile.TemporaryDirectory(prefix="nasdaq-cafe-critic-preflight-") as temp:
        request, manifest = runner.prepare_bundle(
            repo_root=root,
            request_path=request_path,
            request_schema=request_schema.resolve(),
            bundle_dir=Path(temp) / "bundle",
        )

    return {
        "status": "pass",
        "mode": "zero-call",
        "episode_date": request["episode_date"],
        "author_invocation_id": request["author_invocation_id"],
        "critic_invocation_id": request["requested_critic_invocation_id"],
        "adapter_image": args.adapter_image,
        "orchestrator_id": args.orchestrator_id,
        "key_id": args.key_id,
        "validated_input_roles": sorted(row["role"] for row in manifest["inputs"]),
        "validated_logical_rules": sorted(row["logical_path"] for row in manifest["logical_rules"]),
        "passed_environment_names": sorted(set(args.pass_env)),
    }


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=ROOT)
    ap.add_argument("--request", type=Path, required=True)
    ap.add_argument("--request-schema", type=Path, default=Path("skills/nasdaq-cafe-story-engine/contracts/critic_request.schema.json"))
    ap.add_argument("--adapter-image", required=True)
    ap.add_argument("--private-key", type=Path, required=True)
    ap.add_argument("--private-key-password-env")
    ap.add_argument("--key-id", required=True)
    ap.add_argument("--orchestrator-id", required=True)
    ap.add_argument("--trust-registry", type=Path, default=Path("skills/nasdaq-cafe-story-engine/trust/trusted_critic_orchestrators.json"))
    ap.add_argument("--trust-schema", type=Path, default=Path("skills/nasdaq-cafe-story-engine/contracts/trusted_critic_orchestrators.schema.json"))
    ap.add_argument("--pass-env", action="append", default=[])
    return ap


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = run_preflight(args)
    except (PreflightError, Exception) as exc:  # noqa: BLE001 - CLI boundary
        print(f"external Critic preflight failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
