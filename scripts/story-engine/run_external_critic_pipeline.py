#!/usr/bin/env python3
"""Run zero-call preflight, then the isolated external Critic orchestrator.

This is the operational entry point. It refuses to invoke the Critic adapter unless the
preflight succeeds first.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def append_common(command: list[str], args: argparse.Namespace) -> None:
    command += [
        "--repo-root", str(args.repo_root),
        "--request", str(args.request),
        "--adapter-image", args.adapter_image,
        "--private-key", str(args.private_key),
        "--key-id", args.key_id,
        "--orchestrator-id", args.orchestrator_id,
    ]
    if args.private_key_password_env:
        command += ["--private-key-password-env", args.private_key_password_env]
    for name in args.pass_env:
        command += ["--pass-env", name]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=ROOT)
    ap.add_argument("--request", type=Path, required=True)
    ap.add_argument("--adapter-image", required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--private-key", type=Path, required=True)
    ap.add_argument("--private-key-password-env")
    ap.add_argument("--key-id", required=True)
    ap.add_argument("--orchestrator-id", required=True)
    ap.add_argument("--orchestrator-run-id")
    ap.add_argument("--verifier-id", default="nasdaq-cafe-external-critic-supervisor-v1")
    ap.add_argument("--network", default="bridge", choices=["bridge", "none"])
    ap.add_argument("--pass-env", action="append", default=[])
    ap.add_argument("--timeout-seconds", type=int, default=900)
    ap.add_argument("--allow-overwrite", action="store_true")
    args = ap.parse_args()

    root = args.repo_root.resolve()
    preflight = [sys.executable, str(root / "scripts/story-engine/preflight_external_critic_orchestrator.py")]
    append_common(preflight, args)
    preflight_result = subprocess.run(preflight, check=False, capture_output=True, text=True)
    if preflight_result.returncode != 0:
        sys.stderr.write(preflight_result.stderr)
        return preflight_result.returncode

    try:
        preflight_json = json.loads(preflight_result.stdout)
    except json.JSONDecodeError:
        print("external Critic pipeline failed: preflight did not emit valid JSON", file=sys.stderr)
        return 2
    if preflight_json.get("status") != "pass" or preflight_json.get("mode") != "zero-call":
        print("external Critic pipeline failed: preflight did not PASS zero-call mode", file=sys.stderr)
        return 2

    runner = [sys.executable, str(root / "scripts/story-engine/run_external_critic_orchestrator.py")]
    append_common(runner, args)
    runner += [
        "--output-dir", str(args.output_dir),
        "--network", args.network,
        "--timeout-seconds", str(args.timeout_seconds),
        "--verifier-id", args.verifier_id,
    ]
    if args.orchestrator_run_id:
        runner += ["--orchestrator-run-id", args.orchestrator_run_id]
    if args.allow_overwrite:
        runner.append("--allow-overwrite")

    result = subprocess.run(runner, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
