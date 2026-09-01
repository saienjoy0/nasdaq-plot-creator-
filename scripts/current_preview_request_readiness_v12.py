#!/usr/bin/env python3
"""PR-only semantic readiness gate for Current Preview requests.

This coordinator never publishes a Renderer request and never builds a handoff. It
reuses the sole Current facade to expose the next legal ChatGPT semantic checkpoint
before a formal PREVIEW request is allowed to merge into the compile-only main lane.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

READINESS_VERSION = "1.0.0"
NOT_READY_EXIT = 3


class CurrentPreviewReadinessError(RuntimeError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CurrentPreviewReadinessError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise CurrentPreviewReadinessError(f"{label} must be an object")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select_phase(root: Path, date: str) -> str:
    director = (
        root.resolve()
        / "working"
        / date
        / "visual-intelligence"
        / "visual_director_decision.semantic.json"
    )
    return "compile" if director.is_file() else "prepare"


def classify_facade_outcome(outcome: dict[str, Any]) -> dict[str, Any]:
    status = outcome.get("status")
    reason = outcome.get("reason")
    if status == "PASS":
        return {
            "readiness": "PASS",
            "requiredAction": None,
            "reason": reason,
            "exitCode": 0,
        }
    if status == "PREPARED":
        return {
            "readiness": "NOT_READY",
            "requiredAction": outcome.get("requiredAction"),
            "reason": reason,
            "exitCode": NOT_READY_EXIT,
        }
    if status == "REVIEW_REQUIRED":
        return {
            "readiness": "NOT_READY",
            "requiredAction": "AUTHOR_VISUAL_CRITIC_REVIEW",
            "reason": reason,
            "exitCode": NOT_READY_EXIT,
        }
    return {
        "readiness": "FAIL",
        "requiredAction": outcome.get("requiredAction"),
        "reason": reason,
        "exitCode": 2,
    }


def resolve_request(root: Path, request: Path) -> tuple[Path, str, Path]:
    root = root.resolve()
    request_path = request.resolve() if request.is_absolute() else (root / request).resolve()
    if request_path != root and root not in request_path.parents:
        raise CurrentPreviewReadinessError(f"request path escapes workspace: {request}")
    if not request_path.is_file():
        raise CurrentPreviewReadinessError(f"PREVIEW request missing: {request_path}")

    value = load_json(request_path, "PREVIEW request")
    date = value.get("episodeDate")
    if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise CurrentPreviewReadinessError("PREVIEW request episodeDate must be YYYY-MM-DD")
    if value.get("confirmation") != "PREVIEW":
        raise CurrentPreviewReadinessError("request confirmation must be PREVIEW")

    freeze_ref = value.get("semanticFreeze")
    if not isinstance(freeze_ref, dict):
        raise CurrentPreviewReadinessError("PREVIEW request semanticFreeze must be an object")
    freeze_rel = freeze_ref.get("path")
    freeze_sha = freeze_ref.get("sha256")
    expected_rel = f"semantic-freezes/{date}.json"
    if freeze_rel != expected_rel:
        raise CurrentPreviewReadinessError(
            f"PREVIEW request semantic Freeze path must be {expected_rel}"
        )
    if not isinstance(freeze_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", freeze_sha):
        raise CurrentPreviewReadinessError("PREVIEW request semantic Freeze SHA invalid")
    freeze_path = (root / freeze_rel).resolve()
    if root not in freeze_path.parents:
        raise CurrentPreviewReadinessError("Semantic Freeze path escapes workspace")
    if not freeze_path.is_file():
        raise CurrentPreviewReadinessError(f"Semantic Freeze missing: {freeze_path}")
    if sha256_file(freeze_path) != freeze_sha:
        raise CurrentPreviewReadinessError("PREVIEW request semantic Freeze SHA mismatch")
    return request_path, date, freeze_path


def run_facade(
    *,
    root: Path,
    renderer_root: Path,
    date: str,
    phase: str,
    freeze_path: Path,
    runner: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
) -> dict[str, Any]:
    command = [
        sys.executable,
        "scripts/current_production_facade_v12.py",
        "--workspace",
        str(root),
        "--renderer-root",
        str(renderer_root),
        "closure",
        "--episode-date",
        date,
        "--phase",
        phase,
        "--semantic-freeze",
        str(freeze_path),
    ]
    print("+", " ".join(command), flush=True)
    completed = runner(command, cwd=root, check=False)
    outcome_path = root / "verification" / date / "current_production_facade_outcome.json"
    if completed.returncode != 0:
        return {
            "status": "FAIL",
            "requiredAction": None,
            "reason": f"Current facade exited {completed.returncode}",
        }
    if not outcome_path.is_file():
        return {
            "status": "FAIL",
            "requiredAction": None,
            "reason": "Current facade outcome missing",
        }
    return load_json(outcome_path, "Current facade outcome")


def write_receipt(
    *,
    root: Path,
    request_path: Path,
    date: str,
    phase: str,
    outcome: dict[str, Any],
    classified: dict[str, Any],
    output: Path | None,
) -> Path:
    root = root.resolve()
    receipt_path = (
        output.resolve()
        if output is not None and output.is_absolute()
        else root / output
        if output is not None
        else root / "verification" / date / "current_preview_request_readiness.json"
    )
    receipt_path = receipt_path.resolve()
    if root not in receipt_path.parents:
        raise CurrentPreviewReadinessError("readiness output path escapes workspace")
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "contractVersion": READINESS_VERSION,
        "episodeDate": date,
        "request": {
            "path": request_path.relative_to(root).as_posix(),
            "sha256": sha256_file(request_path),
        },
        "selectedPhase": phase,
        "readiness": classified["readiness"],
        "facadeStatus": outcome.get("status"),
        "requiredAction": classified["requiredAction"],
        "reason": classified["reason"],
        "rendererCommit": outcome.get("rendererCommit"),
        "facadeOutcome": f"verification/{date}/current_production_facade_outcome.json",
    }
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return receipt_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--renderer-root", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = args.workspace.resolve()
    try:
        request_path, date, freeze_path = resolve_request(root, args.request)
        phase = select_phase(root, date)
        outcome = run_facade(
            root=root,
            renderer_root=args.renderer_root.resolve(),
            date=date,
            phase=phase,
            freeze_path=freeze_path,
        )
        classified = classify_facade_outcome(outcome)
        write_receipt(
            root=root,
            request_path=request_path,
            date=date,
            phase=phase,
            outcome=outcome,
            classified=classified,
            output=args.output,
        )
        return int(classified["exitCode"])
    except (OSError, CurrentPreviewReadinessError) as exc:
        print(
            json.dumps(
                {
                    "contractVersion": READINESS_VERSION,
                    "readiness": "FAIL",
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
