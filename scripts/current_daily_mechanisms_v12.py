#!/usr/bin/env python3
"""Generation-neutral mechanisms used by the current v1.2 control plane.

The module exposes filesystem/JSON primitives plus hardened stage executors. It does
not own current state ordering, request creation, transition policy, or semantic
judgment. Those remain in ``run_daily_production_v12.py``.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import build_renderer_handoff_240 as handoff_v24
import run_daily_production as base
import run_real_day_acceptance as acceptance_writer
import run_real_day_acceptance_hardened as acceptance_hardened

DailyProductionError = base.DailyProductionError
ERROR_CODES = base.ERROR_CODES
canonical_json = base.canonical_json
sha256_file = base.sha256_file
safe_path = base.safe_path
load_json = base.load_json
write_atomic = base.write_atomic
work_dir = base.work_dir
request_path = base.request_path
state_path = base.state_path
validate_date_in_name = base.validate_date_in_name
validate_approval_record = base.validate_approval_record


def load_module():
    """Return the mechanical surface without exposing legacy policy entrypoints."""
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
    # Delayed import avoids a module-import cycle.  Mechanisms call policy only to
    # record the already-decided forward-only transition; they do not choose it.
    import run_daily_production_v12 as policy

    return policy


def _refresh_handoff_preflight_evidence(*, workspace: Path, date: str) -> bool:
    """Mechanical compatibility bridge for the old handoff preflight writer.

    PR-2 removes this once the preflight has one canonical writer. Until then, only
    the already-validated handoff hardening fields may justify a SHA refresh.
    """
    workspace = workspace.resolve()
    st_path = state_path(workspace, date)
    if not st_path.is_file():
        return False
    state = load_json(st_path, "production state")
    if state.get("current_state") != "production_package_valid":
        return False
    preflight_path = workspace / f"verification/{date}/official_execution_preflight.json"
    if not preflight_path.is_file():
        return False
    relative = preflight_path.relative_to(workspace).as_posix()
    matches: list[dict[str, Any]] = []
    for transition in state.get("transitions", []):
        for evidence in transition.get("evidence", []):
            if evidence.get("path") == relative:
                matches.append(evidence)
    if len(matches) != 1:
        return False
    evidence = matches[0]
    actual_sha = sha256_file(preflight_path)
    if evidence.get("sha256") == actual_sha:
        return False
    preflight = load_json(preflight_path, "handoff-updated preflight")
    hardening = preflight.get("episode_memory_hardening")
    required = {
        "pre_build": "pass",
        "public_artifacts": "pass",
        "handoff_recheck": "pass",
    }
    if not isinstance(hardening, dict) or any(
        hardening.get(key) != expected for key, expected in required.items()
    ):
        return False
    evidence["sha256"] = actual_sha
    state.setdefault("evidence_rebindings", []).append(
        {
            "path": relative,
            "sha256": actual_sha,
            "reason": "compatibility: handoff_recheck_persisted",
        }
    )
    write_atomic(st_path, state)
    return True


def build_handoff(*, workspace: Path, date: str, bundle_root: Path, plot_commit: str) -> dict[str, Any]:
    policy = _policy()
    current = policy.status(module=sys.modules[__name__], workspace=workspace, date=date)
    if current["current_state"] != "production_package_valid":
        raise DailyProductionError(ERROR_CODES["handoff"], "build-handoff requires production_package_valid")
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

    # Existing handoff hardening may persist one verified preflight update. Keep
    # this compatibility repair isolated here until PR-2 removes the multi-writer.
    _refresh_handoff_preflight_evidence(workspace=workspace, date=date)
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
