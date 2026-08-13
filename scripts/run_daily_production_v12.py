#!/usr/bin/env python3
"""Contract-versioned Daily Production path for Visual Intelligence v1.2.

Legacy production remains on run_daily_production_hardened.py. Only requests
explicitly bound to visual-intelligence-bridge/1.2.0 use the new forward-only
state order. This keeps historical production artifacts and requests untouched.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import renderer_binding
import run_daily_production_hardened as hardened

VI_STATES = [
    "intake_ready",
    "research_inputs_bound",
    "causal_dossier_valid",
    "editorial_snapshot_valid",
    "visual_requirements_planned",
    "assets_resolved",
    "visual_intelligence_valid",
    "episode_package_final",
    "memory_usage_valid",
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


def load_module():
    return hardened.load_hardened_daily_module()


def _request(module: Any, workspace: Path, date: str) -> dict[str, Any]:
    return module.load_json(module.request_path(workspace, date), "production request")


def _is_vi_request(request: dict[str, Any]) -> bool:
    binding = request.get("visual_intelligence")
    return isinstance(binding, dict) and binding.get("required") is True


def _validate_vi_binding(module: Any, request: dict[str, Any]) -> None:
    binding = request.get("visual_intelligence")
    if not isinstance(binding, dict):
        raise module.DailyProductionError(module.ERROR_CODES["renderer"], "Visual Intelligence binding missing")
    if binding != {
        "required": True,
        "bridge_contract_version": renderer_binding.BRIDGE_CONTRACT_VERSION,
        "frozen_interface_sha256": renderer_binding.FROZEN_INTERFACE_SHA256,
    }:
        raise module.DailyProductionError(module.ERROR_CODES["renderer"], "Visual Intelligence binding mismatch")


def _rebind_request_sha(module: Any, workspace: Path, date: str) -> None:
    req_path = module.request_path(workspace, date)
    st_path = module.state_path(workspace, date)
    state = module.load_json(st_path, "production state")
    new_sha = module.sha256_file(req_path)
    old_sha = state.get("request_sha256")
    state["request_sha256"] = new_sha
    request_rel = req_path.relative_to(workspace.resolve()).as_posix()
    for transition in state.get("transitions", []):
        for evidence in transition.get("evidence", []):
            if evidence.get("path") == request_rel and evidence.get("sha256") == old_sha:
                evidence["sha256"] = new_sha
    module.write_atomic(st_path, state)


def init_request(
    *,
    module: Any,
    workspace: Path,
    date: str,
    daily_source: Path,
    requested_scope: str,
    renderer_commit: str,
    renderer_contract_version: str,
    visual_intelligence_bridge_version: str,
) -> dict[str, Any]:
    if visual_intelligence_bridge_version != renderer_binding.BRIDGE_CONTRACT_VERSION:
        raise module.DailyProductionError(module.ERROR_CODES["renderer"], "unsupported Visual Intelligence bridge version")
    canonical = renderer_binding.load_binding(workspace)
    renderer = canonical["renderer"]
    if renderer_commit != renderer["commit"] or renderer_contract_version != renderer["contractVersion"]:
        raise module.DailyProductionError(module.ERROR_CODES["renderer"], "request Renderer does not match canonical binding")
    result = module.init_request(
        workspace=workspace,
        date=date,
        daily_source=daily_source,
        requested_scope=requested_scope,
        renderer_commit=renderer_commit,
        renderer_contract_version=renderer_contract_version,
    )
    request = _request(module, workspace, date)
    if result.get("status") == "noop":
        _validate_vi_binding(module, request)
        return result
    request["visual_intelligence"] = {
        "required": True,
        "bridge_contract_version": renderer_binding.BRIDGE_CONTRACT_VERSION,
        "frozen_interface_sha256": renderer_binding.FROZEN_INTERFACE_SHA256,
    }
    module.write_atomic(module.request_path(workspace, date), request)
    _rebind_request_sha(module, workspace, date)
    return result


def status(*, module: Any, workspace: Path, date: str) -> dict[str, Any]:
    base = module.status(workspace=workspace, date=date)
    request = _request(module, workspace, date)
    if not _is_vi_request(request):
        return base
    _validate_vi_binding(module, request)
    current = base.get("current_state")
    next_state = VI_STATES[VI_STATES.index(current) + 1] if current in VI_STATES and current != VI_STATES[-1] else None
    return {**base, "next_state": next_state, "visual_intelligence_bridge": renderer_binding.BRIDGE_CONTRACT_VERSION}


def add_transition(
    *,
    module: Any,
    workspace: Path,
    date: str,
    new_state: str,
    evidence_paths: list[Path],
) -> dict[str, Any]:
    request = _request(module, workspace, date)
    if not _is_vi_request(request):
        return module.add_transition(
            workspace=workspace,
            date=date,
            new_state=new_state,
            evidence_paths=evidence_paths,
            allow_multi_step=False,
        )
    current_status = status(module=module, workspace=workspace, date=date)
    if current_status["validation"]["status"] != "pass":
        raise module.DailyProductionError(module.ERROR_CODES["stale"], "; ".join(current_status["validation"]["errors"]))
    if new_state not in VI_STATES:
        raise module.DailyProductionError(module.ERROR_CODES["stale"], f"unknown Visual Intelligence state: {new_state}")
    st_path = module.state_path(workspace, date)
    state = module.load_json(st_path, "production state")
    current = state["current_state"]
    current_index = VI_STATES.index(current)
    new_index = VI_STATES.index(new_state)
    if new_index <= current_index:
        if new_state == current:
            return {"status": "noop", "current_state": current}
        raise module.DailyProductionError(module.ERROR_CODES["stale"], f"state regression is forbidden: {current} -> {new_state}")
    if new_index != current_index + 1:
        raise module.DailyProductionError(
            module.ERROR_CODES["stale"],
            f"state must advance exactly one step: expected {VI_STATES[current_index + 1]}",
        )
    evidence = []
    for path in evidence_paths:
        resolved = module.safe_path(workspace, path, f"{new_state} evidence")
        evidence.append({
            "path": resolved.relative_to(workspace.resolve()).as_posix(),
            "sha256": module.sha256_file(resolved),
        })
    if not evidence:
        raise module.DailyProductionError(module.ERROR_CODES["stale"], f"{new_state} requires evidence")
    state["current_state"] = new_state
    state["transitions"].append({"state": new_state, "evidence": evidence})
    module.write_atomic(st_path, state)
    return {"status": "advanced", "current_state": new_state, "state_path": str(st_path)}


def build_production(*, module: Any, workspace: Path, date: str, episode_package: Path) -> dict[str, Any]:
    request = _request(module, workspace, date)
    if not _is_vi_request(request):
        return module.build_production(workspace=workspace, date=date, episode_package=episode_package)
    current = status(module=module, workspace=workspace, date=date)
    if current["current_state"] != "memory_usage_valid":
        raise module.DailyProductionError(module.ERROR_CODES["package"], "Visual Intelligence build-production requires memory_usage_valid")
    package = module.safe_path(workspace, episode_package, "episode package")
    try:
        built = module.final_builder.build(
            package,
            workspace,
            workspace / "skills/nasdaq-cafe-final-production/contracts/final_production_source_annex.schema.json",
        )
    except Exception as exc:
        raise module.DailyProductionError(module.ERROR_CODES["package"], str(exc)) from exc
    add_transition(
        module=module,
        workspace=workspace,
        date=date,
        new_state="production_package_valid",
        evidence_paths=[Path(path) for path in built["paths"].values()],
    )
    return built


def main(argv: list[str] | None = None) -> int:
    module = load_module()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    p_init = sub.add_parser("init")
    p_init.add_argument("--episode-date", required=True)
    p_init.add_argument("--daily-source-package", required=True, type=Path)
    p_init.add_argument("--requested-scope", choices=["package", "preview"], default="preview")
    p_init.add_argument("--renderer-commit", required=True)
    p_init.add_argument("--renderer-contract-version", required=True)
    p_init.add_argument("--visual-intelligence-bridge-version", required=True)
    p_status = sub.add_parser("status")
    p_status.add_argument("--episode-date", required=True)
    p_advance = sub.add_parser("advance")
    p_advance.add_argument("--episode-date", required=True)
    p_advance.add_argument("--state", required=True, choices=VI_STATES)
    p_advance.add_argument("--evidence", required=True, type=Path, nargs="+")
    p_build = sub.add_parser("build-production")
    p_build.add_argument("--episode-date", required=True)
    p_build.add_argument("--episode-package", required=True, type=Path)
    args = parser.parse_args(argv)
    workspace = args.workspace.resolve()
    try:
        if args.command == "init":
            result = init_request(
                module=module,
                workspace=workspace,
                date=args.episode_date,
                daily_source=args.daily_source_package,
                requested_scope=args.requested_scope,
                renderer_commit=args.renderer_commit,
                renderer_contract_version=args.renderer_contract_version,
                visual_intelligence_bridge_version=args.visual_intelligence_bridge_version,
            )
        elif args.command == "status":
            result = status(module=module, workspace=workspace, date=args.episode_date)
        elif args.command == "advance":
            result = add_transition(
                module=module,
                workspace=workspace,
                date=args.episode_date,
                new_state=args.state,
                evidence_paths=args.evidence,
            )
        elif args.command == "build-production":
            result = build_production(
                module=module,
                workspace=workspace,
                date=args.episode_date,
                episode_package=args.episode_package,
            )
        else:
            raise module.DailyProductionError(module.ERROR_CODES["stale"], "unsupported Visual Intelligence command")
        code = 0
    except module.DailyProductionError as exc:
        result = {"status": "fail", "error_code": exc.code, "errors": [exc.message]}
        code = 1
    sys.stdout.buffer.write(module.canonical_json(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
