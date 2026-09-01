#!/usr/bin/env python3
"""Thin canonical entry facade for NASDAQ Cafe current-v1.2 production.

The facade owns no editorial or stage logic. It verifies/normalizes the current entry
request, invokes the existing semantic-frozen closure and current control plane, and
emits one machine-readable outcome for Production, Canary, Manual and E2E callers.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import renderer_binding
import current_production_resume_v12

FACADE_VERSION = "1.0.0"
NORMAL_PAUSE = {"PREPARED", "REVIEW_REQUIRED"}


class CurrentProductionFacadeError(RuntimeError):
    pass


def load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CurrentProductionFacadeError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise CurrentProductionFacadeError(f"{label} must be an object")
    return value


def invoke(
    command: list[str],
    *,
    cwd: Path,
    runner: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
) -> int:
    print("+", " ".join(command), flush=True)
    completed = runner(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise CurrentProductionFacadeError(
            f"stage command failed ({completed.returncode}): {' '.join(command)}"
        )
    return completed.returncode


def run_closure(
    *,
    root: Path,
    renderer_root: Path,
    date: str,
    phase: str,
    semantic_freeze: Path,
    build_handoff_on_pass: bool,
    bundle_root: Path,
    plot_commit: str | None,
    runner: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
) -> dict[str, Any]:
    root = root.resolve()
    renderer_root = renderer_root.resolve()
    renderer_binding.verify_renderer_checkout(root, renderer_root)
    freeze = semantic_freeze.resolve() if semantic_freeze.is_absolute() else (root / semantic_freeze).resolve()
    if not freeze.is_file():
        raise CurrentProductionFacadeError(f"Semantic Freeze missing: {freeze}")

    invoke(
        [
            sys.executable,
            "scripts/run_semantic_frozen_renderer_closure_v12.py",
            "--phase",
            phase,
            "--date",
            date,
            "--repo-root",
            str(root),
            "--renderer-root",
            str(renderer_root),
            "--semantic-freeze",
            str(freeze),
        ],
        cwd=root,
        runner=runner,
    )
    gate_path = root / "verification" / date / "renderer_closure_gate_v12.json"
    gate = load(gate_path, "current Renderer closure gate")
    status = gate.get("status")
    if status not in {"PASS", *NORMAL_PAUSE}:
        raise CurrentProductionFacadeError(f"unexpected current closure status: {status!r}")

    handoff_ready = current_production_resume_v12.has_reached(root, date, "handoff_ready")
    if status == "PASS" and build_handoff_on_pass:
        if not plot_commit:
            raise CurrentProductionFacadeError("--plot-commit is required when building handoff")
        if not handoff_ready:
            invoke(
                [
                    sys.executable,
                    "scripts/run_daily_production_v12.py",
                    "--workspace",
                    str(root),
                    "build-handoff",
                    "--episode-date",
                    date,
                    "--bundle-root",
                    str(bundle_root),
                    "--plot-commit",
                    plot_commit,
                ],
                cwd=root,
                runner=runner,
            )
        handoff_ready = True

    outcome = {
        "facadeVersion": FACADE_VERSION,
        "episodeDate": date,
        "phase": phase,
        "status": status,
        "requiredAction": gate.get("requiredAction"),
        "reason": gate.get("reason") or gate.get("error"),
        "previewHandoffReady": handoff_ready,
        "rendererCommit": gate.get("rendererCommit"),
        "closureGate": gate_path.relative_to(root).as_posix(),
    }
    outcome_path = root / "verification" / date / "current_production_facade_outcome.json"
    outcome_path.write_text(
        json.dumps(outcome, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--renderer-root", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    closure = sub.add_parser("closure")
    closure.add_argument("--episode-date", required=True)
    closure.add_argument("--phase", choices=["prepare", "compile"], required=True)
    closure.add_argument("--semantic-freeze", type=Path, required=True)
    closure.add_argument("--build-handoff-on-pass", action="store_true")
    closure.add_argument("--bundle-root", type=Path, default=Path("production-bundles"))
    closure.add_argument("--plot-commit")

    args = parser.parse_args()
    root = args.workspace.resolve()
    try:
        if args.command != "closure":
            raise CurrentProductionFacadeError(f"unsupported command: {args.command}")
        result = run_closure(
            root=root,
            renderer_root=args.renderer_root,
            date=args.episode_date,
            phase=args.phase,
            semantic_freeze=args.semantic_freeze,
            build_handoff_on_pass=args.build_handoff_on_pass,
            bundle_root=args.bundle_root,
            plot_commit=args.plot_commit,
        )
        code = 0
    except (
        OSError,
        CurrentProductionFacadeError,
        renderer_binding.RendererBindingError,
        current_production_resume_v12.CurrentProductionResumeError,
    ) as exc:
        result = {
            "facadeVersion": FACADE_VERSION,
            "status": "FAIL",
            "errors": [str(exc)],
        }
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
