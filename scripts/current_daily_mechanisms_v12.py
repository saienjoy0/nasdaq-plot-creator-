#!/usr/bin/env python3
"""Generation-neutral mechanisms used by the current v1.2 control plane.

This module owns only mechanical filesystem/JSON primitives and calls existing
hardened stage executors. It deliberately contains no current state ordering,
request writer, transition policy, or semantic judgment.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import build_renderer_handoff_240 as handoff_v24
import run_real_day_acceptance as acceptance_writer
import run_real_day_acceptance_hardened as acceptance_hardened

ERROR_CODES = {
    "date": "E_DATE_MISMATCH",
    "stale": "E_STALE_INPUT",
    "research": "E_RESEARCH_INVALID",
    "memory": "E_MEMORY_USAGE_INVALID",
    "episode": "E_EPISODE_NOT_FINAL",
    "inquisition": "E_INQUISITION_UNRESOLVED",
    "asset": "E_ASSET_UNRESOLVED",
    "selected_path": "E_SELECTED_PATH_UNRESOLVED",
    "render": "E_RENDER_SPEC_INVALID",
    "package": "E_PACKAGE_MISMATCH",
    "handoff": "E_HANDOFF_INVALID",
    "renderer": "E_RENDERER_CONTRACT_MISMATCH",
    "preview": "E_PREVIEW_FAILED",
    "final": "E_FINAL_NOT_AUTHORIZED",
    "publication": "E_PUBLICATION_NOT_APPROVED",
    "memory_promotion": "E_MEMORY_PROMOTION_BLOCKED",
}


class DailyProductionError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(root: Path, value: str | Path, label: str, *, must_exist: bool = True) -> Path:
    root = root.resolve()
    path = Path(value)
    resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
    if resolved != root and root not in resolved.parents:
        raise DailyProductionError(ERROR_CODES["stale"], f"{label} escapes workspace root: {value}")
    if must_exist and not resolved.is_file():
        raise DailyProductionError(ERROR_CODES["stale"], f"{label} does not exist: {value}")
    return resolved


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DailyProductionError(ERROR_CODES["stale"], f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise DailyProductionError(ERROR_CODES["stale"], f"{label} must be an object")
    return value


def write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(canonical_json(value))
    tmp.replace(path)


def work_dir(workspace: Path, date: str) -> Path:
    return workspace.resolve() / "working" / date


def request_path(workspace: Path, date: str) -> Path:
    return work_dir(workspace, date) / "production_request.json"


def state_path(workspace: Path, date: str) -> Path:
    return work_dir(workspace, date) / "production_state.json"


def validate_date_in_name(date: str, path: Path, label: str) -> None:
    if date not in path.name:
        raise DailyProductionError(
            ERROR_CODES["date"], f"{label} filename must include {date}: {path.name}"
        )


def validate_approval_record(path: Path, workspace: Path, date: str) -> dict[str, Any]:
    resolved = safe_path(workspace, path, "approval record")
    record = load_json(resolved, "approval record")
    if record.get("episode_date") != date:
        raise DailyProductionError(ERROR_CODES["final"], "approval record episode_date mismatch")
    if record.get("status") != "approved":
        raise DailyProductionError(ERROR_CODES["final"], "approval record status must be approved")
    if record.get("final_requested") is not True:
        raise DailyProductionError(
            ERROR_CODES["final"], "approval record final_requested must be true"
        )
    return record


def load_module():
    """Return this mechanical surface without any legacy policy entrypoints."""
    return sys.modules[__name__]


def load_external_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _policy():
    # Delayed import avoids a module-import cycle. Mechanisms only execute an
    # already-decided transition through the current policy owner.
    import run_daily_production_v12 as policy

    return policy


def build_handoff(*, workspace: Path, date: str, bundle_root: Path, plot_commit: str) -> dict[str, Any]:
    policy = _policy()
    current = policy.status(module=sys.modules[__name__], workspace=workspace, date=date)
    if current["current_state"] != "production_package_valid":
        raise DailyProductionError(
            ERROR_CODES["handoff"], "build-handoff requires production_package_valid"
        )
    request = load_json(request_path(workspace, date), "production request")
    renderer = request["renderer"]
    try:
        built = handoff_v24.build_handoff_hardened(
            source_root=workspace,
            bundle_root=bundle_root,
            date=date,
            mode="preview",
            plot_commit=plot_commit,
            renderer_commit=renderer["commit"],
            renderer_contract_version=renderer["contract_version"],
            approval_path=None,
        )
    except Exception as exc:
        raise DailyProductionError(ERROR_CODES["handoff"], str(exc)) from exc

    policy.add_transition(
        module=sys.modules[__name__],
        workspace=workspace,
        date=date,
        new_state="handoff_ready",
        evidence_paths=[Path(built["manifest_path"])],
    )
    return built


def record_preview(
    *,
    workspace: Path,
    date: str,
    daily_source_root: Path,
    bundle_root: Path,
    handoff_manifest: Path,
    renderer_artifact_root: Path,
    technical_report: Path,
    user_review: Path | None,
) -> dict[str, Any]:
    policy = _policy()
    current = policy.status(module=sys.modules[__name__], workspace=workspace, date=date)
    if current["current_state"] not in {
        "handoff_ready",
        "preview_dispatched",
        "preview_ready",
        "user_review_pending",
    }:
        raise DailyProductionError(
            ERROR_CODES["preview"],
            "record-preview requires handoff_ready or a preview state",
        )
    request = load_json(request_path(workspace, date), "production request")
    daily_source = workspace / request["daily_source"]["path"]
    try:
        report = acceptance_hardened.validate_acceptance_hardened(
            episode_date=date,
            daily_source_root=daily_source_root,
            daily_source_path=daily_source,
            bundle_root=bundle_root,
            handoff_manifest_path=handoff_manifest,
            renderer_artifact_root=renderer_artifact_root,
            technical_report_path=technical_report,
            user_review_path=user_review,
        )
        report_paths = acceptance_writer.write_report(
            report, workspace / "verification/real-day-acceptance" / date
        )
    except Exception as exc:
        raise DailyProductionError(ERROR_CODES["preview"], str(exc)) from exc

    evidence = [Path(report_paths["json"]), Path(report_paths["markdown"])]
    state = current["current_state"]
    for target in ("preview_dispatched", "preview_ready", "user_review_pending"):
        if policy.VI_STATES.index(target) > policy.VI_STATES.index(state):
            policy.add_transition(
                module=sys.modules[__name__],
                workspace=workspace,
                date=date,
                new_state=target,
                evidence_paths=evidence,
            )
            state = target
    if report["user_review"]["status"] == "approved":
        policy.add_transition(
            module=sys.modules[__name__],
            workspace=workspace,
            date=date,
            new_state="user_preview_approved",
            evidence_paths=evidence,
        )
    return {
        "status": "recorded",
        "mvp_status": report["mvp_status"],
        "report_paths": report_paths,
    }


def request_final(*, workspace: Path, date: str, approval_record: Path, explicit_final: bool) -> dict[str, Any]:
    """Record Final authorization without mutating the immutable production request."""
    if not explicit_final:
        raise DailyProductionError(ERROR_CODES["final"], "request-final requires --explicit-final")
    policy = _policy()
    current = policy.status(module=sys.modules[__name__], workspace=workspace, date=date)
    if current["current_state"] != "user_preview_approved":
        raise DailyProductionError(
            ERROR_CODES["final"],
            "final may be requested only after user_preview_approved",
        )
    validate_approval_record(approval_record, workspace, date)
    return policy.add_transition(
        module=sys.modules[__name__],
        workspace=workspace,
        date=date,
        new_state="final_requested",
        evidence_paths=[approval_record],
    )
