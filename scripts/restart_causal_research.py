#!/usr/bin/env python3
"""Invalidate one editorial attempt and restart from the immutable daily intake.

This helper is invoked only by the hardened Daily Production entrypoint. It never
rewinds a public state. A factual/causal Critical finding from 04 authorizes the
current attempt to be archived and invalidated; a fresh request/state is then created
from the exact same daily source and pinned Renderer. Story, visual, and production
artifacts are not edited here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class ResearchRetryError(ValueError):
    pass


CAUSAL_REASON_TYPES = {
    "CAUSALITY_DRIFT",
    "COUNTEREVIDENCE_REMOVED",
    "TIMELINE_DRIFT",
    "NASDAQ_SCOPE_OVERREACH",
}


def _schema_errors(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda item: list(item.path))
    result: list[str] = []
    for error in errors:
        location = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path
        )
        result.append(f"{label}{location}: {error.message}")
    return result


def _next_retry_dir(workspace: Path, date: str) -> tuple[int, Path]:
    root = workspace / "working" / date / "research-retries"
    root.mkdir(parents=True, exist_ok=True)
    existing: list[int] = []
    for path in root.glob("retry-*"):
        if path.is_dir():
            try:
                existing.append(int(path.name.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
    number = max(existing, default=0) + 1
    target = root / f"retry-{number:03d}"
    if target.exists():
        raise ResearchRetryError(f"retry archive already exists: {target}")
    return number, target


def _validate_authorization(
    *,
    daily_module: Any,
    workspace: Path,
    date: str,
    retry_request_path: Path,
    retry_schema_path: Path,
    creative_review_schema_path: Path,
) -> tuple[dict[str, Any], Path, dict[str, Any]]:
    retry_path = daily_module.safe_path(workspace, retry_request_path, "research retry request")
    retry = daily_module.load_json(retry_path, "research retry request")
    retry_schema = daily_module.load_json(retry_schema_path, "research retry request schema")
    retry_errors = _schema_errors(retry, retry_schema, "research retry request")
    if retry_errors:
        raise ResearchRetryError("\n".join(retry_errors))
    if retry.get("episode_date") != date:
        raise ResearchRetryError("research retry request episode_date mismatch")

    review_ref = retry["creative_review"]
    review_path = daily_module.safe_path(workspace, review_ref["path"], "creative review")
    if daily_module.sha256_file(review_path) != review_ref["sha256"]:
        raise ResearchRetryError("creative review SHA mismatch in research retry request")
    review = daily_module.load_json(review_path, "creative review")
    review_schema = daily_module.load_json(creative_review_schema_path, "creative review schema")
    review_errors = _schema_errors(review, review_schema, "creative review")
    if review_errors:
        raise ResearchRetryError("\n".join(review_errors))
    if review.get("episode_date") != date:
        raise ResearchRetryError("creative review episode_date mismatch")
    if review.get("verdict") == "pass":
        raise ResearchRetryError("research retry requires a non-PASS 04 creative review")

    reason = retry["reason_type"]
    if reason == "FACTUAL_ERROR":
        texts = retry.get("immediate_failure_texts", [])
        if not texts:
            raise ResearchRetryError(
                "FACTUAL_ERROR retry requires at least one exact 04 immediate_failure text"
            )
        available = set(review.get("immediate_failures", []))
        missing = [text for text in texts if text not in available]
        if missing:
            raise ResearchRetryError(
                f"FACTUAL_ERROR retry cites immediate failures not present in 04 review: {missing}"
            )
        if retry.get("finding_ids"):
            raise ResearchRetryError("FACTUAL_ERROR retry must use immediate_failure_texts, not finding_ids")
    elif reason in CAUSAL_REASON_TYPES:
        finding_ids = retry.get("finding_ids", [])
        if not finding_ids:
            raise ResearchRetryError(f"{reason} retry requires at least one critical finding_id")
        if retry.get("immediate_failure_texts"):
            raise ResearchRetryError(f"{reason} retry must use finding_ids, not immediate_failure_texts")
        findings = {
            item.get("finding_id"): item
            for item in review.get("findings", [])
            if isinstance(item, dict)
        }
        for finding_id in finding_ids:
            finding = findings.get(finding_id)
            if finding is None:
                raise ResearchRetryError(f"04 finding not found: {finding_id}")
            if finding.get("severity") != "critical":
                raise ResearchRetryError(f"04 finding is not critical: {finding_id}")
            if finding.get("issue_type") != reason:
                raise ResearchRetryError(
                    f"04 finding issue_type mismatch for {finding_id}: "
                    f"{finding.get('issue_type')!r} != {reason!r}"
                )
    else:
        raise ResearchRetryError(f"unsupported research retry reason: {reason}")

    return retry, review_path, review


def restart(
    *,
    daily_module: Any,
    workspace: Path,
    date: str,
    retry_request_path: Path,
    retry_schema_path: Path,
    creative_review_schema_path: Path,
) -> dict[str, Any]:
    workspace = workspace.resolve()
    current = daily_module.status(workspace=workspace, date=date)
    if current["validation"]["status"] != "pass":
        raise ResearchRetryError(
            "current production attempt must be valid before research supersession: "
            + "; ".join(current["validation"].get("errors", []))
        )
    if current["current_state"] != "causal_dossier_valid":
        raise ResearchRetryError(
            "research retry is allowed only while the public state is causal_dossier_valid"
        )

    retry, review_path, _review = _validate_authorization(
        daily_module=daily_module,
        workspace=workspace,
        date=date,
        retry_request_path=retry_request_path,
        retry_schema_path=retry_schema_path,
        creative_review_schema_path=creative_review_schema_path,
    )

    req_path = daily_module.request_path(workspace, date)
    state_path = daily_module.state_path(workspace, date)
    request = daily_module.load_json(req_path, "production request")
    state = daily_module.load_json(state_path, "production state")
    if state.get("invalidated") is True:
        raise ResearchRetryError("current production attempt is already invalidated")

    daily_source = daily_module.safe_path(
        workspace, request["daily_source"]["path"], "daily source"
    )
    retry_source = daily_module.safe_path(
        workspace, retry_request_path, "research retry request"
    )
    number, archive = _next_retry_dir(workspace, date)
    archive.mkdir(parents=True, exist_ok=False)

    archived_request = archive / "superseded_production_request.json"
    archived_state = archive / "superseded_production_state.json"
    archived_review = archive / "creative_review.json"
    archived_retry = archive / "research_retry_request.json"
    archived_invalidated_state = archive / "invalidated_production_state.json"
    receipt_path = archive / "research_retry_receipt.json"

    archived_request.write_bytes(req_path.read_bytes())
    archived_state.write_bytes(state_path.read_bytes())
    archived_review.write_bytes(review_path.read_bytes())
    archived_retry.write_bytes(retry_source.read_bytes())

    invalidated = dict(state)
    invalidated["invalidated"] = True
    daily_module.write_atomic(state_path, invalidated)
    archived_invalidated_state.write_bytes(state_path.read_bytes())

    receipt = {
        "contract_version": "1.0.0",
        "episode_date": date,
        "retry_number": number,
        "reason_type": retry["reason_type"],
        "status": "superseded",
        "previous_current_state": state["current_state"],
        "daily_source": {
            "path": request["daily_source"]["path"],
            "sha256": request["daily_source"]["sha256"],
        },
        "renderer": request["renderer"],
        "superseded_request": {
            "path": archived_request.relative_to(workspace).as_posix(),
            "sha256": daily_module.sha256_file(archived_request),
        },
        "superseded_state": {
            "path": archived_state.relative_to(workspace).as_posix(),
            "sha256": daily_module.sha256_file(archived_state),
        },
        "invalidated_state": {
            "path": archived_invalidated_state.relative_to(workspace).as_posix(),
            "sha256": daily_module.sha256_file(archived_invalidated_state),
        },
        "creative_review": {
            "path": archived_review.relative_to(workspace).as_posix(),
            "sha256": daily_module.sha256_file(archived_review),
        },
        "retry_request": {
            "path": archived_retry.relative_to(workspace).as_posix(),
            "sha256": daily_module.sha256_file(archived_retry),
        },
    }
    daily_module.write_atomic(receipt_path, receipt)

    req_path.unlink()
    state_path.unlink()
    try:
        created = daily_module.init_request(
            workspace=workspace,
            date=date,
            daily_source=daily_source,
            requested_scope=request["requested_scope"],
            renderer_commit=request["renderer"]["commit"],
            renderer_contract_version=request["renderer"]["contract_version"],
        )
        new_state = daily_module.load_json(state_path, "restarted production state")
        new_state["transitions"][0]["evidence"].append(
            {
                "path": receipt_path.relative_to(workspace).as_posix(),
                "sha256": daily_module.sha256_file(receipt_path),
            }
        )
        daily_module.write_atomic(state_path, new_state)
    except Exception:
        req_path.write_bytes(archived_request.read_bytes())
        state_path.write_bytes(archived_invalidated_state.read_bytes())
        raise

    return {
        "status": "restarted",
        "episode_date": date,
        "retry_number": number,
        "reason_type": retry["reason_type"],
        "previous_state": state["current_state"],
        "current_state": "intake_ready",
        "archive": archive.relative_to(workspace).as_posix(),
        "receipt": receipt_path.relative_to(workspace).as_posix(),
        "new_request_status": created["status"],
    }
