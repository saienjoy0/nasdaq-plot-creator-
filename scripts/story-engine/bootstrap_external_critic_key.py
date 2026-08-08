#!/usr/bin/env python3
"""Generate an encrypted Ed25519 Critic-orchestrator key outside the repository.

This utility is intended to be run on the trusted external orchestrator host. It refuses
private-key paths inside the repository and never modifies the trust registry itself.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[2]


def inside(root: Path, path: Path) -> bool:
    root = root.resolve()
    path = path.resolve()
    return path == root or root in path.parents


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=ROOT)
    ap.add_argument("--private-key-out", type=Path, required=True)
    ap.add_argument("--password-env", required=True)
    ap.add_argument("--key-id", required=True)
    ap.add_argument("--orchestrator-id", required=True)
    args = ap.parse_args()

    root = args.repo_root.resolve()
    private_path = args.private_key_out.expanduser().resolve()
    if inside(root, private_path):
        print("refusing to create Critic private key inside the repository", file=sys.stderr)
        return 2
    if private_path.exists():
        print(f"refusing to overwrite existing private key: {private_path}", file=sys.stderr)
        return 2
    password = os.environ.get(args.password_env)
    if not password or len(password.encode("utf-8")) < 16:
        print("private-key password environment must exist and be at least 16 bytes", file=sys.stderr)
        return 2

    private_key = Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode("utf-8")),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    private_path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(private_path, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(private_pem)
    except Exception:
        try:
            private_path.unlink(missing_ok=True)
        finally:
            raise
    os.chmod(private_path, stat.S_IRUSR | stat.S_IWUSR)

    trust_row = {
        "key_id": args.key_id,
        "orchestrator_id": args.orchestrator_id,
        "algorithm": "ed25519",
        "public_key_pem": public_pem,
        "status": "active",
    }
    print(json.dumps({
        "status": "pass",
        "private_key_path": str(private_path),
        "trust_registry_row": trust_row,
        "next_step": "add only trust_registry_row to trusted_critic_orchestrators.json; never commit the private key",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
