#!/usr/bin/env python3
"""Safe daily operational entry point for 朝のNASDAQカフェ.

This CLI manages deterministic production state. It never selects the lead,
decides market causality, writes narration, performs the 04 inquisition,
generates images, chooses Primary/Fallback, or automatically starts final.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_final_production_package as final_builder
import build_renderer_handoff as handoff_builder
import run_real_day_acceptance as acceptance_runner

STATES = [
    "intake_ready",
    "research_inputs_bound",
    "causal_dossier_valid",
    "episode_package_final",
    "memory_usage_valid",
    "assets_resolved",
    "production_package_valid",
    "handoff_ready",
    "preview_dispatched",
    "preview_ready",
    "user_review_pending",
    "user_preview_approved",
    "final_requested",
    "final_completed",
    "publication_approved",
    "memory_promoted",
]

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
        raise DailyProductionError(ERROR_CODES["date"], f"{label} filename must include {date}: {path.name}")


def init_request(*, workspace: Path, date: str, daily_source: Path, requested_scope: str, renderer_commit: str, renderer_contract_version: str) -> dict[str, Any]:
    workspace = workspace.resolve()
    daily_source = safe_path(workspace, daily_source, "daily source")
    validate_date_in_name(date, daily_source, "daily source")
    if daily_source.stat().st_size == 0:
        raise DailyProductionError(ERROR_CODES["stale"], "daily source must be non-empty")
    if requested_scope not in {"package", "preview"}:
        raise DailyProductionError(ERROR_CODES["final"], "initial requested_scope may only be package or preview")
    if len(renderer_commit) != 40:
        raise DailyProductionError(ERROR_CODES["renderer"], "renderer commit must be a 40-character SHA")
    try:
        int(renderer_commit, 16)
    except ValueError as exc:
        raise DailyProductionError(ERROR_CODES["renderer"], "renderer commit must be hexadecimal") from exc

    req_path = request_path(workspace, date)
    st_path = state_path(workspace, date)
    if req_path.exists() or st_path.exists():
        existing = status(workspace=workspace, date=date)
        if existing["validation"]["status"] == "pass":
            return {"status": "noop", **existing}
        raise DailyProductionError(ERROR_CODES["stale"], "existing production request/state is stale or invalid")

    request = {
        "contract_version": "1.0.0",
        "episode_date": date,
        "requested_scope": requested_scope,
        "daily_source": {"path": daily_source.relative_to(workspace).as_posix(), "sha256": sha256_file(daily_source)},
        "renderer": {
            "repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion",
            "commit": renderer_commit,
            "contract_version": renderer_contract_version,
        },
        "approvals": {
            "preview_requested": requested_scope == "preview",
            "final_requested": False,
            "memory_promotion_requested": False,
        },
    }
    write_atomic(req_path, request)
    state = {
        "contract_version": "1.0.0",
        "episode_date": date,
        "current_state": "intake_ready",
        "request_sha256": sha256_file(req_path),
        "daily_source_sha256": request["daily_source"]["sha256"],
        "invalidated": False,
        "transitions": [{
            "state": "intake_ready",
            "evidence": [
                {"path": request["daily_source"]["path"], "sha256": request["daily_source"]["sha256"]},
                {"path": req_path.relative_to(workspace).as_posix(), "sha256": sha256_file(req_path)},
            ],
        }],
    }
    write_atomic(st_path, state)
    return {"status": "created", "request_path": str(req_path), "state_path": str(st_path), "current_state": "intake_ready"}


def verify_evidence(workspace: Path, state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for t_index, transition in enumerate(state.get("transitions", [])):
        for e_index, evidence in enumerate(transition.get("evidence", [])):
            try:
                path = safe_path(workspace, evidence.get("path", ""), f"transitions[{t_index}].evidence[{e_index}]")
            except DailyProductionError as exc:
                errors.append(exc.message)
                continue
            actual = sha256_file(path)
            if actual != evidence.get("sha256"):
                errors.append(
                    f"transitions[{t_index}].evidence[{e_index}] SHA mismatch: "
                    f"{evidence.get('path')} declared={evidence.get('sha256')} actual={actual}"
                )
    return errors


def status(*, workspace: Path, date: str) -> dict[str, Any]:
    workspace = workspace.resolve()
    req_path = request_path(workspace, date)
    st_path = state_path(workspace, date)
    request = load_json(req_path, "production request")
    state = load_json(st_path, "production state")
    errors: list[str] = []
    if request.get("episode_date") != date or state.get("episode_date") != date:
        errors.append("request/state episode date mismatch")
    if sha256_file(req_path) != state.get("request_sha256"):
        errors.append("production request SHA changed")
    daily_source = safe_path(workspace, request.get("daily_source", {}).get("path", ""), "daily source")
    current_daily_sha = sha256_file(daily_source)
    if current_daily_sha != request.get("daily_source", {}).get("sha256"):
        errors.append("daily source SHA changed from production request")
    if current_daily_sha != state.get("daily_source_sha256"):
        errors.append("daily source SHA changed from production state")
    errors.extend(verify_evidence(workspace, state))
    current = state.get("current_state")
    next_state = STATES[STATES.index(current) + 1] if current in STATES and current != STATES[-1] else None
    return {
        "episode_date": date,
        "current_state": current,
        "next_state": next_state,
        "requested_scope": request.get("requested_scope"),
        "validation": {"status": "pass" if not errors and not state.get("invalidated") else "fail", "errors": errors},
    }


def add_transition(*, workspace: Path, date: str, new_state: str, evidence_paths: list[Path], allow_multi_step: bool = False) -> dict[str, Any]:
    current_status = status(workspace=workspace, date=date)
    if current_status["validation"]["status"] != "pass":
        raise DailyProductionError(ERROR_CODES["stale"], "; ".join(current_status["validation"]["errors"]))
    st_path = state_path(workspace, date)
    state = load_json(st_path, "production state")
    current = state["current_state"]
    if new_state not in STATES:
        raise DailyProductionError(ERROR_CODES["stale"], f"unknown state: {new_state}")
    current_index = STATES.index(current)
    new_index = STATES.index(new_state)
    if new_index <= current_index:
        if new_state == current:
            return {"status": "noop", "current_state": current}
        raise DailyProductionError(ERROR_CODES["stale"], f"state regression is forbidden: {current} -> {new_state}")
    if not allow_multi_step and new_index != current_index + 1:
        raise DailyProductionError(ERROR_CODES["stale"], f"state must advance exactly one step: expected {STATES[current_index + 1]}")
    evidence = []
    for path in evidence_paths:
        resolved = safe_path(workspace, path, f"{new_state} evidence")
        evidence.append({"path": resolved.relative_to(workspace.resolve()).as_posix(), "sha256": sha256_file(resolved)})
    if not evidence:
        raise DailyProductionError(ERROR_CODES["stale"], f"{new_state} requires evidence")
    state["current_state"] = new_state
    state["transitions"].append({"state": new_state, "evidence": evidence})
    write_atomic(st_path, state)
    return {"status": "advanced", "current_state": new_state, "state_path": str(st_path)}


def validate_approval_record(path: Path, workspace: Path, date: str) -> dict[str, Any]:
    resolved = safe_path(workspace, path, "approval record")
    record = load_json(resolved, "approval record")
    if record.get("episode_date") != date:
        raise DailyProductionError(ERROR_CODES["final"], "approval record episode_date mismatch")
    if record.get("status") != "approved":
        raise DailyProductionError(ERROR_CODES["final"], "approval record status must be approved")
    if record.get("final_requested") is not True:
        raise DailyProductionError(ERROR_CODES["final"], "approval record final_requested must be true")
    return record


def request_final(*, workspace: Path, date: str, approval_record: Path, explicit_final: bool) -> dict[str, Any]:
    if not explicit_final:
        raise DailyProductionError(ERROR_CODES["final"], "request-final requires --explicit-final")
    current = status(workspace=workspace, date=date)
    if current["current_state"] != "user_preview_approved":
        raise DailyProductionError(ERROR_CODES["final"], "final may be requested only after user_preview_approved")
    validate_approval_record(approval_record, workspace, date)
    result = add_transition(
        workspace=workspace, date=date, new_state="final_requested",
        evidence_paths=[approval_record], allow_multi_step=False,
    )
    req_path = request_path(workspace, date)
    request = load_json(req_path, "production request")
    request["approvals"]["final_requested"] = True
    write_atomic(req_path, request)
    state = load_json(state_path(workspace, date), "production state")
    state["request_sha256"] = sha256_file(req_path)
    request_rel = req_path.relative_to(workspace.resolve()).as_posix()
    for transition in state["transitions"]:
        for evidence in transition.get("evidence", []):
            if evidence.get("path") == request_rel:
                evidence["sha256"] = state["request_sha256"]
    write_atomic(state_path(workspace, date), state)
    return result


def build_production(*, workspace: Path, date: str, episode_package: Path) -> dict[str, Any]:
    current = status(workspace=workspace, date=date)
    if current["current_state"] != "assets_resolved":
        raise DailyProductionError(ERROR_CODES["package"], "build-production requires assets_resolved")
    package = safe_path(workspace, episode_package, "episode package")
    try:
        built = final_builder.build(
            package,
            workspace,
            workspace / "skills/nasdaq-cafe-final-production/contracts/final_production_source_annex.schema.json",
        )
    except Exception as exc:
        raise DailyProductionError(ERROR_CODES["package"], str(exc)) from exc
    add_transition(
        workspace=workspace, date=date, new_state="production_package_valid",
        evidence_paths=[Path(path) for path in built["paths"].values()],
    )
    return built


def build_handoff(*, workspace: Path, date: str, bundle_root: Path, plot_commit: str) -> dict[str, Any]:
    current = status(workspace=workspace, date=date)
    if current["current_state"] != "production_package_valid":
        raise DailyProductionError(ERROR_CODES["handoff"], "build-handoff requires production_package_valid")
    request = load_json(request_path(workspace, date), "production request")
    renderer = request["renderer"]
    try:
        built = handoff_builder.build_handoff(
            source_root=workspace, bundle_root=bundle_root, date=date, mode="preview",
            plot_commit=plot_commit, renderer_commit=renderer["commit"],
            renderer_contract_version=renderer["contract_version"], approval_path=None,
        )
    except Exception as exc:
        raise DailyProductionError(ERROR_CODES["handoff"], str(exc)) from exc
    add_transition(
        workspace=workspace, date=date, new_state="handoff_ready",
        evidence_paths=[Path(built["manifest_path"])], allow_multi_step=False,
    )
    return built


def record_preview(*, workspace: Path, date: str, daily_source_root: Path, bundle_root: Path, handoff_manifest: Path, renderer_artifact_root: Path, technical_report: Path, user_review: Path | None) -> dict[str, Any]:
    current = status(workspace=workspace, date=date)
    if current["current_state"] not in {"handoff_ready", "preview_dispatched", "preview_ready", "user_review_pending"}:
        raise DailyProductionError(ERROR_CODES["preview"], "record-preview requires handoff_ready or a preview state")
    request = load_json(request_path(workspace, date), "production request")
    daily_source = workspace / request["daily_source"]["path"]
    try:
        report = acceptance_runner.validate_acceptance(
            episode_date=date, daily_source_root=daily_source_root, daily_source_path=daily_source,
            bundle_root=bundle_root, handoff_manifest_path=handoff_manifest,
            renderer_artifact_root=renderer_artifact_root, technical_report_path=technical_report,
            user_review_path=user_review,
        )
        report_paths = acceptance_runner.write_report(
            report, workspace / "verification/real-day-acceptance" / date
        )
    except Exception as exc:
        raise DailyProductionError(ERROR_CODES["preview"], str(exc)) from exc
    evidence = [Path(report_paths["json"]), Path(report_paths["markdown"])]
    state = current["current_state"]
    for target in ["preview_dispatched", "preview_ready", "user_review_pending"]:
        if STATES.index(target) > STATES.index(state):
            add_transition(workspace=workspace, date=date, new_state=target, evidence_paths=evidence)
            state = target
    if report["user_review"]["status"] == "approved":
        add_transition(workspace=workspace, date=date, new_state="user_preview_approved", evidence_paths=evidence)
    return {"status": "recorded", "mvp_status": report["mvp_status"], "report_paths": report_paths}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--episode-date", required=True)
    p_init.add_argument("--daily-source-package", required=True, type=Path)
    p_init.add_argument("--requested-scope", choices=["package", "preview"], default="preview")
    p_init.add_argument("--renderer-commit", required=True)
    p_init.add_argument("--renderer-contract-version", required=True)

    p_status = sub.add_parser("status")
    p_status.add_argument("--episode-date", required=True)

    p_advance = sub.add_parser("advance")
    p_advance.add_argument("--episode-date", required=True)
    p_advance.add_argument("--state", required=True, choices=STATES)
    p_advance.add_argument("--evidence", required=True, type=Path, nargs="+")

    p_build = sub.add_parser("build-production")
    p_build.add_argument("--episode-date", required=True)
    p_build.add_argument("--episode-package", required=True, type=Path)

    p_handoff = sub.add_parser("build-handoff")
    p_handoff.add_argument("--episode-date", required=True)
    p_handoff.add_argument("--bundle-root", required=True, type=Path)
    p_handoff.add_argument("--plot-commit", required=True)

    p_preview = sub.add_parser("record-preview")
    p_preview.add_argument("--episode-date", required=True)
    p_preview.add_argument("--daily-source-root", required=True, type=Path)
    p_preview.add_argument("--bundle-root", required=True, type=Path)
    p_preview.add_argument("--handoff-manifest", required=True, type=Path)
    p_preview.add_argument("--renderer-artifact-root", required=True, type=Path)
    p_preview.add_argument("--technical-report", required=True, type=Path)
    p_preview.add_argument("--user-review", type=Path)

    p_final = sub.add_parser("request-final")
    p_final.add_argument("--episode-date", required=True)
    p_final.add_argument("--approval-record", required=True, type=Path)
    p_final.add_argument("--explicit-final", action="store_true")

    args = parser.parse_args(argv)
    workspace = args.workspace.resolve()
    try:
        if args.command == "init":
            result = init_request(
                workspace=workspace, date=args.episode_date, daily_source=args.daily_source_package,
                requested_scope=args.requested_scope, renderer_commit=args.renderer_commit,
                renderer_contract_version=args.renderer_contract_version,
            )
        elif args.command == "status":
            result = status(workspace=workspace, date=args.episode_date)
        elif args.command == "advance":
            result = add_transition(
                workspace=workspace, date=args.episode_date,
                new_state=args.state, evidence_paths=args.evidence,
            )
        elif args.command == "build-production":
            result = build_production(
                workspace=workspace, date=args.episode_date,
                episode_package=args.episode_package,
            )
        elif args.command == "build-handoff":
            result = build_handoff(
                workspace=workspace, date=args.episode_date,
                bundle_root=args.bundle_root, plot_commit=args.plot_commit,
            )
        elif args.command == "record-preview":
            result = record_preview(
                workspace=workspace, date=args.episode_date,
                daily_source_root=args.daily_source_root, bundle_root=args.bundle_root,
                handoff_manifest=args.handoff_manifest,
                renderer_artifact_root=args.renderer_artifact_root,
                technical_report=args.technical_report, user_review=args.user_review,
            )
        elif args.command == "request-final":
            result = request_final(
                workspace=workspace, date=args.episode_date,
                approval_record=args.approval_record,
                explicit_final=args.explicit_final,
            )
        else:
            raise DailyProductionError(ERROR_CODES["stale"], "unsupported command")
        code = 0
    except DailyProductionError as exc:
        result = {"status": "fail", "error_code": exc.code, "errors": [exc.message]}
        code = 1
    sys.stdout.buffer.write(canonical_json(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
