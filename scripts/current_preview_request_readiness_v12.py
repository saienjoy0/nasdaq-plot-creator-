#!/usr/bin/env python3
"""PR-only semantic readiness gate for formal Current Preview requests.

This coordinator owns no editorial or Visual Intelligence decisions. It validates the
formal PREVIEW request, mechanically chooses the legal canonical-facade phase from the
presence of the Director semantic artifact, and writes a non-publishing readiness
receipt for PR validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import date as calendar_date
from pathlib import Path
from typing import Any, Callable

READINESS_CONTRACT_VERSION = "1.0.0"
NOT_READY_EXIT = 3


class ReadinessError(RuntimeError):
    pass


@dataclass(frozen=True)
class ValidatedRequest:
    episode_date: str
    request_path: str
    request_sha256: str
    freeze_path: Path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReadinessError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise ReadinessError(f"{label} must be an object")
    return value


def choose_phase(root: Path, date: str) -> str:
    director = (
        root / "working" / date / "visual-intelligence" /
        "visual_director_decision.semantic.json"
    )
    return "compile" if director.is_file() else "prepare"


def classify_facade_outcome(outcome: dict) -> tuple[str, str | None]:
    status = outcome.get("status")
    if status == "PASS":
        return "PASS", None
    if status == "PREPARED":
        return "NOT_READY", outcome.get("requiredAction") or "AUTHOR_VISUAL_INTELLIGENCE_DECISION"
    if status == "REVIEW_REQUIRED":
        return "NOT_READY", "AUTHOR_VISUAL_CRITIC_REVIEW"
    return "FAIL", None


def validate_request(root: Path, request_path: Path) -> ValidatedRequest:
    root = root.resolve()
    request = request_path.resolve() if request_path.is_absolute() else (root / request_path).resolve()
    try:
        request_rel = request.relative_to(root).as_posix()
    except ValueError as exc:
        raise ReadinessError("production request must be inside the workspace") from exc
    if not request.is_file():
        raise ReadinessError(f"production request missing: {request_rel}")

    value = load_object(request, "production request")
    if value.get("confirmation") != "PREVIEW":
        raise ReadinessError("production request confirmation must be PREVIEW")

    episode_date = value.get("episodeDate")
    if not isinstance(episode_date, str):
        raise ReadinessError("production request episodeDate must be YYYY-MM-DD")
    try:
        parsed_date = calendar_date.fromisoformat(episode_date)
    except ValueError as exc:
        raise ReadinessError("production request episodeDate must be YYYY-MM-DD") from exc
    if parsed_date.isoformat() != episode_date:
        raise ReadinessError("production request episodeDate must be YYYY-MM-DD")

    freeze_ref = value.get("semanticFreeze")
    if not isinstance(freeze_ref, dict):
        raise ReadinessError("production request semanticFreeze must be an object")
    expected_freeze_rel = f"semantic-freezes/{episode_date}.json"
    if freeze_ref.get("path") != expected_freeze_rel:
        raise ReadinessError(
            f"Semantic Freeze path must be {expected_freeze_rel}"
        )
    freeze_path = root / expected_freeze_rel
    if not freeze_path.is_file():
        raise ReadinessError(f"Semantic Freeze missing: {expected_freeze_rel}")
    actual_freeze_sha = sha256_file(freeze_path)
    if freeze_ref.get("sha256") != actual_freeze_sha:
        raise ReadinessError("Semantic Freeze SHA mismatch")

    return ValidatedRequest(
        episode_date=episode_date,
        request_path=request_rel,
        request_sha256=sha256_file(request),
        freeze_path=freeze_path,
    )


def invoke_facade(
    *,
    root: Path,
    renderer_root: Path,
    episode_date: str,
    phase: str,
    freeze_path: Path,
    runner: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
) -> dict[str, Any]:
    root = root.resolve()
    renderer_root = renderer_root.resolve()
    outcome_path = root / "verification" / episode_date / "current_production_facade_outcome.json"
    outcome_path.unlink(missing_ok=True)

    command = [
        sys.executable,
        "scripts/current_production_facade_v12.py",
        "--workspace",
        str(root),
        "--renderer-root",
        str(renderer_root),
        "closure",
        "--episode-date",
        episode_date,
        "--phase",
        phase,
        "--semantic-freeze",
        str(freeze_path),
    ]
    print("+", " ".join(command), flush=True)
    completed = runner(command, cwd=root, check=False)
    if completed.returncode != 0:
        return {
            "status": "FAIL",
            "reason": f"canonical Current facade failed with exit code {completed.returncode}",
        }
    if not outcome_path.is_file():
        return {
            "status": "FAIL",
            "reason": "canonical Current facade did not write its outcome",
        }
    return load_object(outcome_path, "canonical Current facade outcome")


def run_readiness(
    *,
    root: Path,
    renderer_root: Path,
    request_path: Path,
    output_path: Path | None = None,
    runner: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
) -> tuple[int, dict[str, Any]]:
    root = root.resolve()
    validated = validate_request(root, request_path)
    phase = choose_phase(root, validated.episode_date)
    outcome = invoke_facade(
        root=root,
        renderer_root=renderer_root,
        episode_date=validated.episode_date,
        phase=phase,
        freeze_path=validated.freeze_path,
        runner=runner,
    )
    state, required_action = classify_facade_outcome(outcome)
    reason = outcome.get("reason") or outcome.get("error")
    if reason is None and isinstance(outcome.get("errors"), list) and outcome["errors"]:
        reason = str(outcome["errors"][0])

    receipt = {
        "contractVersion": READINESS_CONTRACT_VERSION,
        "episodeDate": validated.episode_date,
        "requestPath": validated.request_path,
        "requestSha256": validated.request_sha256,
        "selectedPhase": phase,
        "state": state,
        "facadeStatus": outcome.get("status", "FAIL"),
        "requiredAction": required_action,
        "reason": reason,
        "previewHandoffReady": False,
        "previewPublicationReady": False,
    }
    output = output_path
    if output is None:
        output = root / "verification" / validated.episode_date / "current_preview_request_readiness.json"
    elif not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if state == "PASS":
        return 0, receipt
    if state == "NOT_READY":
        return NOT_READY_EXIT, receipt
    return 2, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--renderer-root", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        code, receipt = run_readiness(
            root=args.workspace,
            renderer_root=args.renderer_root,
            request_path=args.request,
            output_path=args.output,
        )
    except (OSError, ReadinessError) as exc:
        print(
            json.dumps(
                {"contractVersion": READINESS_CONTRACT_VERSION, "state": "FAIL", "reason": str(exc)},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
