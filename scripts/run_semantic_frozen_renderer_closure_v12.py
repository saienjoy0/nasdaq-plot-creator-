#!/usr/bin/env python3
"""Run the canonical v1.2 closure only against a committed ChatGPT semantic freeze.

This wrapper is intentionally production-only. Historical/synthetic Visual Intelligence
canaries may continue to call run_daily_renderer_closure_v12.py directly. The canonical
Preview workflow must call this wrapper and therefore cannot silently accept changed
ChatGPT semantic sources or AI-B artifacts authored against a different freeze.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import chatgpt_semantic_freeze
import renderer_binding


class SemanticFrozenClosureError(RuntimeError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SemanticFrozenClosureError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise SemanticFrozenClosureError(f"{label} root must be an object")
    return value


def _gate_path(root: Path, date: str) -> Path:
    path = root / "verification" / date / "renderer_closure_gate_v12.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _renderer_commit(root: Path) -> str:
    binding = renderer_binding.load_binding(root)
    renderer = binding.get("renderer")
    if not isinstance(renderer, dict) or not isinstance(renderer.get("commit"), str):
        raise SemanticFrozenClosureError("canonical Renderer binding is invalid")
    return renderer["commit"]


def write_safe_pause(
    root: Path,
    date: str,
    *,
    required_action: str,
    reason: str,
) -> None:
    value = {
        "contractVersion": "1.0.0",
        "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
        "episodeDate": date,
        "rendererCommit": _renderer_commit(root),
        "status": "PREPARED",
        "reason": reason,
        "requiredAction": required_action,
        "previewRendered": False,
        "finalRendered": False,
    }
    _gate_path(root, date).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(value, ensure_ascii=False, indent=2))


def write_fail(root: Path, date: str, reason: str) -> None:
    value = {
        "contractVersion": "1.0.0",
        "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
        "episodeDate": date,
        "rendererCommit": _renderer_commit(root),
        "status": "FAIL",
        "error": reason,
        "previewRendered": False,
        "finalRendered": False,
    }
    _gate_path(root, date).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(value, ensure_ascii=False, indent=2))


def semantic_binding_pause(
    root: Path,
    date: str,
    *,
    phase: str,
    semantic_freeze_sha256: str,
) -> tuple[str, str] | None:
    """Return a normal semantic pause when AI-B artifacts bind a different freeze."""
    vi = root / "working" / date / "visual-intelligence"
    requirements_path = vi / "visual_requirements.json"
    if requirements_path.is_file():
        requirements = load_json(requirements_path, "Visual Requirements")
        if requirements.get("semanticFreezeSha256") != semantic_freeze_sha256:
            return (
                "AUTHOR_VISUAL_REQUIREMENTS",
                "E_VISUAL_REQUIREMENTS_STALE: semantic freeze SHA mismatch",
            )

    if phase == "compile":
        decision_path = vi / "visual_intelligence_decision.json"
        if not decision_path.is_file():
            if requirements_path.is_file():
                return (
                    "AUTHOR_VISUAL_INTELLIGENCE_DECISION",
                    "E_VISUAL_INTELLIGENCE_DECISION_REQUIRED: Director decision must bind the current semantic freeze",
                )
            return None
        decision = load_json(decision_path, "Visual Intelligence decision")
        if decision.get("semanticFreezeSha256") != semantic_freeze_sha256:
            return (
                "RESELECT_VISUAL_CANDIDATES",
                "E_VISUAL_DECISION_STALE: semantic freeze SHA mismatch",
            )
    return None


def verify_freeze(root: Path, date: str, manifest: Path) -> str:
    try:
        chatgpt_semantic_freeze.verify_manifest(root, date, manifest)
        return chatgpt_semantic_freeze.manifest_sha256(root, manifest)
    except chatgpt_semantic_freeze.SemanticFreezeError as exc:
        raise SemanticFrozenClosureError(str(exc)) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["prepare", "compile"], required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--renderer-root", type=Path, required=True)
    parser.add_argument("--semantic-freeze", type=Path, required=True)
    args = parser.parse_args()

    root = args.repo_root.resolve()
    manifest = args.semantic_freeze
    try:
        freeze_sha = verify_freeze(root, args.date, manifest)
        pause = semantic_binding_pause(
            root,
            args.date,
            phase=args.phase,
            semantic_freeze_sha256=freeze_sha,
        )
        if pause is not None:
            write_safe_pause(root, args.date, required_action=pause[0], reason=pause[1])
            return 0

        command = [
            sys.executable,
            "scripts/run_daily_renderer_closure_v12.py",
            "--phase",
            args.phase,
            "--date",
            args.date,
            "--repo-root",
            str(root),
            "--renderer-root",
            str(args.renderer_root.resolve()),
        ]
        print("+", " ".join(command), flush=True)
        completed = subprocess.run(command, cwd=root, check=False)

        # The underlying closure may generate many derived files, but it is never
        # allowed to mutate the committed ChatGPT semantic authority inputs.
        freeze_sha_after = verify_freeze(root, args.date, manifest)
        if freeze_sha_after != freeze_sha:
            raise SemanticFrozenClosureError(
                "E_CHATGPT_SEMANTIC_FREEZE_STALE: freeze manifest changed during production"
            )

        pause = semantic_binding_pause(
            root,
            args.date,
            phase=args.phase,
            semantic_freeze_sha256=freeze_sha,
        )
        if pause is not None:
            write_safe_pause(root, args.date, required_action=pause[0], reason=pause[1])
            return 0
        return completed.returncode
    except (OSError, SemanticFrozenClosureError, renderer_binding.RendererBindingError) as exc:
        try:
            write_fail(root, args.date, str(exc))
        except Exception:
            print(f"semantic frozen closure failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
