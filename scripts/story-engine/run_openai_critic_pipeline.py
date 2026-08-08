#!/usr/bin/env python3
"""Provider-specific entry point for the isolated OpenAI Critic.

This wrapper only supplies the OpenAI adapter environment contract to the generic
zero-call preflight -> isolated orchestrator pipeline. It does not call the model itself.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINNED_IMAGE_RE = re.compile(r"^.+@sha256:[0-9a-f]{64}$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=ROOT)
    ap.add_argument("--request", type=Path, required=True)
    ap.add_argument("--adapter-image", required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--private-key", type=Path, required=True)
    ap.add_argument("--private-key-password-env", required=True)
    ap.add_argument("--key-id", required=True)
    ap.add_argument("--orchestrator-id", required=True)
    ap.add_argument("--orchestrator-run-id")
    ap.add_argument("--timeout-seconds", type=int, default=900)
    ap.add_argument("--allow-overwrite", action="store_true")
    args = ap.parse_args()

    if not PINNED_IMAGE_RE.fullmatch(args.adapter_image):
        print("OpenAI Critic adapter image must be pinned as image@sha256:<digest>", file=sys.stderr)
        return 2
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is required before external Critic execution", file=sys.stderr)
        return 2
    if not os.environ.get(args.private_key_password_env):
        print(f"missing private-key password environment variable: {args.private_key_password_env}", file=sys.stderr)
        return 2

    os.environ.setdefault("OPENAI_CRITIC_MODEL", "gpt-5.6")
    os.environ.setdefault("OPENAI_CRITIC_MAX_OUTPUT_TOKENS", "12000")
    os.environ.setdefault("OPENAI_CRITIC_TIMEOUT_SECONDS", "180")

    root = args.repo_root.resolve()
    command = [
        sys.executable,
        str(root / "scripts/story-engine/run_external_critic_pipeline.py"),
        "--repo-root", str(root),
        "--request", str(args.request),
        "--adapter-image", args.adapter_image,
        "--output-dir", str(args.output_dir),
        "--private-key", str(args.private_key),
        "--private-key-password-env", args.private_key_password_env,
        "--key-id", args.key_id,
        "--orchestrator-id", args.orchestrator_id,
        "--network", "bridge",
        "--timeout-seconds", str(args.timeout_seconds),
    ]
    if args.orchestrator_run_id:
        command += ["--orchestrator-run-id", args.orchestrator_run_id]
    if args.allow_overwrite:
        command.append("--allow-overwrite")
    for name in [
        "OPENAI_API_KEY",
        "OPENAI_CRITIC_MODEL",
        "OPENAI_CRITIC_MAX_OUTPUT_TOKENS",
        "OPENAI_CRITIC_TIMEOUT_SECONDS",
    ]:
        command += ["--pass-env", name]

    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
