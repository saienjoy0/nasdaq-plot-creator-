#!/usr/bin/env python3
"""Contract-versioned Daily Production path for Visual Intelligence v1.2.

Legacy production remains on run_daily_production_hardened.py. Only requests
explicitly bound to visual-intelligence-bridge/1.2.0 use this forward-only state
order. Existing Story/04/Renderer hard gates are preserved rather than bypassed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import build_final_production_package_v12 as final_v12
import current_daily_mechanisms_v12 as current_mechanisms
import renderer_binding

ROOT = Path(__file__).resolve().parents[1]
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
    return current_mechanisms.load_module()


def _request(module: Any, workspace: Path, date: str) -> dict[str, Any]:
    return module.load_json(module.request_path(workspace, date), "production request")


def _is_vi_request(request: dict[str, Any]) -> bool:
    binding = request.get("visual_intelligence")
    return isinstance(binding, dict) and binding.get("required") is True


def _validate_vi_binding(module: Any, request: dict[str, Any]) -> None:
    binding = request.get("visual_intelligence")
    expected = {
        "required": True,
        "bridge_contract_version": renderer_binding.BRIDGE_CONTRACT_VERSION,
        "frozen_interface_sha256": renderer_binding.FROZEN_INTERFACE_SHA256,
    }
    if binding != expected:
        raise module.DailyProductionError(
            module.ERROR_CODES["renderer"], "Visual Intelligence binding mismatch"
        )


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
    semantic_freeze_path: Path,
    semantic_freeze_sha256: str,
) -> dict[str, Any]:
    workspace = workspace.resolve()
    if visual_intelligence_bridge_version != renderer_binding.BRIDGE_CONTRACT_VERSION:
        raise module.DailyProductionError(
            module.ERROR_CODES["renderer"], "unsupported Visual Intelligence bridge version"
        )
    canonical = renderer_binding.load_binding(workspace)
    renderer = canonical["renderer"]
    if (
        renderer_commit != renderer["commit"]
        or renderer_contract_version != renderer["contractVersion"]
    ):
        raise module.DailyProductionError(
            module.ERROR_CODES["renderer"],
            "request Renderer does not match canonical binding",
        )

    daily_source = module.safe_path(workspace, daily_source, "daily source")
    module.validate_date_in_name(date, daily_source, "daily source")
    if daily_source.stat().st_size == 0:
        raise module.DailyProductionError(
            module.ERROR_CODES["stale"], "daily source must be non-empty"
        )
    if requested_scope not in {"package", "preview"}:
        raise module.DailyProductionError(
            module.ERROR_CODES["final"],
            "initial requested_scope may only be package or preview",
        )
    freeze = module.safe_path(workspace, semantic_freeze_path, "semantic freeze")
    actual_freeze_sha = module.sha256_file(freeze)
    if semantic_freeze_sha256 != actual_freeze_sha:
        raise module.DailyProductionError(
            module.ERROR_CODES["stale"],
            "semantic freeze SHA does not match request input",
        )

    req_path = module.request_path(workspace, date)
    st_path = module.state_path(workspace, date)
    if req_path.exists() or st_path.exists():
        existing = status(module=module, workspace=workspace, date=date)
        if existing["validation"]["status"] != "pass":
            raise module.DailyProductionError(
                module.ERROR_CODES["stale"],
                "existing current request/state is stale or invalid",
            )
        request = _request(module, workspace, date)
        _validate_vi_binding(module, request)
        expected_freeze = {
            "path": freeze.relative_to(workspace).as_posix(),
            "sha256": actual_freeze_sha,
        }
        if request.get("semantic_freeze") != expected_freeze:
            raise module.DailyProductionError(
                module.ERROR_CODES["stale"],
                "existing current request binds a different Semantic Freeze",
            )
        return {"status": "noop", **existing}

    request = {
        "contract_version": "1.2.0",
        "episode_date": date,
        "requested_scope": requested_scope,
        "daily_source": {
            "path": daily_source.relative_to(workspace).as_posix(),
            "sha256": module.sha256_file(daily_source),
        },
        "semantic_freeze": {
            "path": freeze.relative_to(workspace).as_posix(),
            "sha256": actual_freeze_sha,
        },
        "renderer": {
            "repository": renderer_binding.RENDERER_REPOSITORY,
            "commit": renderer_commit,
            "contract_version": renderer_contract_version,
            "registry_snapshot_sha256": renderer["registrySnapshotSha256"],
        },
        "visual_director": {"required": True, "contract_version": "1.0.0"},
        "visual_intelligence": {
            "required": True,
            "bridge_contract_version": renderer_binding.BRIDGE_CONTRACT_VERSION,
            "frozen_interface_sha256": renderer_binding.FROZEN_INTERFACE_SHA256,
        },
        "approvals": {
            "preview_requested": requested_scope == "preview",
            "final_requested": False,
            "memory_promotion_requested": False,
        },
    }
    module.write_atomic(req_path, request)
    request_sha = module.sha256_file(req_path)
    state = {
        "contract_version": "1.2.0",
        "episode_date": date,
        "current_state": "intake_ready",
        "request_sha256": request_sha,
        "daily_source_sha256": request["daily_source"]["sha256"],
        "invalidated": False,
        "transitions": [
            {
                "state": "intake_ready",
                "evidence": [
                    request["daily_source"],
                    {
                        "path": req_path.relative_to(workspace).as_posix(),
                        "sha256": request_sha,
                    },
                    request["semantic_freeze"],
                ],
            }
        ],
    }
    module.write_atomic(st_path, state)
    return {
        "status": "created",
        "request_path": str(req_path),
        "state_path": str(st_path),
        "current_state": "intake_ready",
    }


def status(*, module: Any, workspace: Path, date: str) -> dict[str, Any]:
    workspace = workspace.resolve()
    req_path = module.request_path(workspace, date)
    st_path = module.state_path(workspace, date)
    request = module.load_json(req_path, "production request")
    state = module.load_json(st_path, "production state")
    errors: list[str] = []
    if request.get("episode_date") != date or state.get("episode_date") != date:
        errors.append("request/state episode date mismatch")
    if module.sha256_file(req_path) != state.get("request_sha256"):
        errors.append("production request SHA changed")
    try:
        _validate_vi_binding(module, request)
    except module.DailyProductionError as exc:
        errors.append(exc.message)

    try:
        daily_source = module.safe_path(
            workspace,
            request.get("daily_source", {}).get("path", ""),
            "daily source",
        )
        daily_sha = module.sha256_file(daily_source)
        if daily_sha != request.get("daily_source", {}).get("sha256"):
            errors.append("daily source SHA changed from production request")
        if daily_sha != state.get("daily_source_sha256"):
            errors.append("daily source SHA changed from production state")
        freeze = module.safe_path(
            workspace,
            request.get("semantic_freeze", {}).get("path", ""),
            "semantic freeze",
        )
        if module.sha256_file(freeze) != request.get("semantic_freeze", {}).get("sha256"):
            errors.append("Semantic Freeze SHA changed from production request")
    except module.DailyProductionError as exc:
        errors.append(exc.message)

    try:
        canonical = renderer_binding.load_binding(workspace)
        renderer = canonical["renderer"]
        requested_renderer = request.get("renderer", {})
        if requested_renderer.get("commit") != renderer["commit"]:
            errors.append("production request Renderer commit drifted from canonical binding")
        if requested_renderer.get("contract_version") != renderer["contractVersion"]:
            errors.append("production request Renderer contract drifted from canonical binding")
        if (
            requested_renderer.get("registry_snapshot_sha256")
            != renderer["registrySnapshotSha256"]
        ):
            errors.append("production request Registry SHA drifted from canonical binding")
    except renderer_binding.RendererBindingError as exc:
        errors.append(str(exc))

    for t_index, transition in enumerate(state.get("transitions", [])):
        for e_index, evidence in enumerate(transition.get("evidence", [])):
            try:
                path = module.safe_path(
                    workspace,
                    evidence.get("path", ""),
                    f"transitions[{t_index}].evidence[{e_index}]",
                )
            except module.DailyProductionError as exc:
                errors.append(exc.message)
                continue
            if module.sha256_file(path) != evidence.get("sha256"):
                errors.append(
                    f"transitions[{t_index}].evidence[{e_index}] SHA mismatch: "
                    f"{evidence.get('path')}"
                )

    current = state.get("current_state")
    next_state = (
        VI_STATES[VI_STATES.index(current) + 1]
        if current in VI_STATES and current != VI_STATES[-1]
        else None
    )
    return {
        "episode_date": date,
        "current_state": current,
        "next_state": next_state,
        "requested_scope": request.get("requested_scope"),
        "validation": {
            "status": "pass" if not errors and not state.get("invalidated") else "fail",
            "errors": errors,
        },
        "visual_intelligence_bridge": renderer_binding.BRIDGE_CONTRACT_VERSION,
    }


def _evidence_by_name(paths: list[Path]) -> dict[str, list[Path]]:
    grouped: dict[str, list[Path]] = {}
    for path in paths:
        grouped.setdefault(path.name, []).append(path)
    return grouped


def _require_one(
    *,
    module: Any,
    grouped: dict[str, list[Path]],
    name: str,
    code: str,
    message: str,
) -> Path:
    matches = grouped.get(name, [])
    if len(matches) != 1:
        raise module.DailyProductionError(code, message)
    return matches[0]


def _validate_story_final_gate(
    *, module: Any, workspace: Path, date: str, evidence_paths: list[Path]
) -> None:
    acceptance_paths = [p for p in evidence_paths if p.name == "story_engine_acceptance.json"]
    package_paths = [
        p
        for p in evidence_paths
        if p.name.startswith("episode_package_") and p.suffix == ".md"
    ]
    projection_paths = [p for p in evidence_paths if p.name == "story_projection_report.json"]
    visual_gate_paths = [p for p in evidence_paths if p.name == "pre_tts_visual_gate.json"]
    if len(acceptance_paths) != 1:
        raise module.DailyProductionError(
            module.ERROR_CODES["stale"],
            "episode_package_final requires exactly one Story Engine v1.1 acceptance",
        )
    if len(package_paths) != 1:
        raise module.DailyProductionError(
            module.ERROR_CODES["episode"],
            "episode_package_final requires exactly one final episode package",
        )
    if len(projection_paths) != 1:
        raise module.DailyProductionError(
            module.ERROR_CODES["package"],
            "episode_package_final requires exactly one story_projection_report.json",
        )
    if len(visual_gate_paths) != 1:
        raise module.DailyProductionError(
            module.ERROR_CODES["render"],
            "episode_package_final requires exactly one pre_tts_visual_gate.json",
        )
    acceptance_validator = current_mechanisms.load_external_module(
        "story_engine_acceptance_v12_gate",
        ROOT / "scripts/story-engine/validate_story_engine_acceptance_v1_1.py",
    )
    result = acceptance_validator.validate_acceptance(
        acceptance_paths[0],
        repo_root=workspace,
        require_production=True,
        allow_uncertified_production=True,
    )
    if result["status"] != "pass":
        messages = "; ".join(
            item.get("message", "Story Engine acceptance failed")
            for item in result.get("errors", [])
        )
        raise module.DailyProductionError(
            module.ERROR_CODES["inquisition"],
            f"Story Engine v1.1 production gate failed: {messages}",
        )
    projection = module.load_json(projection_paths[0], "Story Engine projection report")
    if projection.get("episode_date") != date or projection.get("status") != "pass":
        raise module.DailyProductionError(
            module.ERROR_CODES["package"],
            "Story Engine projection report must be PASS for the same episode date",
        )
    visual_gate = module.load_json(visual_gate_paths[0], "Pre-TTS Visual Gate report")
    if (
        visual_gate.get("episodeDate") != date
        or visual_gate.get("status") != "PASS"
        or visual_gate.get("violations") != []
    ):
        raise module.DailyProductionError(
            module.ERROR_CODES["render"],
            "Pre-TTS Visual Gate must be PASS with zero violations for the same episode date",
        )


def _validate_vi_transition(
    *,
    module: Any,
    workspace: Path,
    date: str,
    new_state: str,
    evidence_paths: list[Path],
) -> None:
    grouped = _evidence_by_name(evidence_paths)
    vi_dir = workspace / "working" / date / "visual-intelligence"
    if new_state == "causal_dossier_valid":
        dossier_name = f"causal_research_dossier_{date}.json"
        dossier = _require_one(
            module=module, grouped=grouped, name=dossier_name, code=module.ERROR_CODES["stale"],
            message="causal_dossier_valid requires exactly one current Causal Dossier",
        )
        receipt = _require_one(
            module=module, grouped=grouped, name="causal_dossier_validation.json", code=module.ERROR_CODES["stale"],
            message="causal_dossier_valid requires exactly one SHA-bound Causal Dossier validation receipt",
        )
        verifier = current_mechanisms.load_external_module(
            "causal_dossier_receipt_v12_gate", ROOT / "scripts/materialize_causal_research.py"
        )
        try:
            value = verifier.verify_validation_receipt(workspace, date, receipt)
        except Exception as exc:
            raise module.DailyProductionError(module.ERROR_CODES["stale"], f"Causal Dossier validation receipt failed: {exc}") from exc
        if value.get("dossier", {}).get("path") != dossier.relative_to(workspace).as_posix() or value.get("dossier", {}).get("sha256") != module.sha256_file(dossier):
            raise module.DailyProductionError(module.ERROR_CODES["stale"], "Causal Dossier receipt does not bind supplied Dossier")
    elif new_state == "editorial_snapshot_valid":
        snapshot = _require_one(
            module=module,
            grouped=grouped,
            name="editorial_snapshot.json",
            code=module.ERROR_CODES["stale"],
            message="editorial_snapshot_valid requires exactly one editorial_snapshot.json",
        )
        value = module.load_json(snapshot, "editorial snapshot")
        if value.get("episodeDate") != date:
            raise module.DailyProductionError(
                module.ERROR_CODES["date"], "editorial snapshot episodeDate mismatch"
            )
        acceptance = _require_one(
            module=module, grouped=grouped, name="editorial_semantic_acceptance.json", code=module.ERROR_CODES["stale"],
            message="editorial_snapshot_valid requires Editorial Semantic Acceptance",
        )
        projection = _require_one(
            module=module, grouped=grouped, name="story_projection_report.json", code=module.ERROR_CODES["stale"],
            message="editorial_snapshot_valid requires WS-4 Story identity report",
        )
        freeze_candidates = [p for p in evidence_paths if p.parent.name == "semantic-freezes" and p.suffix == ".json"]
        if len(freeze_candidates) != 1:
            raise module.DailyProductionError(module.ERROR_CODES["stale"], "editorial_snapshot_valid requires exactly one Semantic Freeze")
        freeze_path = freeze_candidates[0]
        acceptance_module = current_mechanisms.load_external_module(
            "editorial_semantic_acceptance_v12_gate", ROOT / "scripts/validate_editorial_semantic_boundary.py"
        )
        freeze_module = current_mechanisms.load_external_module(
            "chatgpt_semantic_freeze_v12_state_gate", ROOT / "scripts/chatgpt_semantic_freeze.py"
        )
        try:
            accepted = acceptance_module.verify_acceptance(workspace, date, acceptance)
            freeze = freeze_module.verify_manifest(workspace, date, freeze_path)
        except Exception as exc:
            raise module.DailyProductionError(module.ERROR_CODES["stale"], f"editorial semantic lineage failed: {exc}") from exc
        if freeze.get("contractVersion") != "1.2.0":
            raise module.DailyProductionError(module.ERROR_CODES["stale"], "current-v1.2 production requires Semantic Freeze 1.2.0")
        if freeze.get("editorialSemanticAcceptance", {}).get("sha256") != module.sha256_file(acceptance):
            raise module.DailyProductionError(module.ERROR_CODES["stale"], "Semantic Freeze binds a different Editorial Semantic Acceptance")
        report = module.load_json(projection, "Story projection report")
        if report.get("status") != "pass" or report.get("episode_date") != date:
            raise module.DailyProductionError(module.ERROR_CODES["stale"], "WS-4 Story identity report must PASS for the same date")
        if report.get("source_daily_authoring_sha256") != freeze.get("canonicalAuthoring", {}).get("sha256"):
            raise module.DailyProductionError(module.ERROR_CODES["stale"], "WS-4 report is stale against frozen Daily Authoring")
    elif new_state == "visual_requirements_planned":
        requirements = _require_one(
            module=module,
            grouped=grouped,
            name="visual_requirements.json",
            code=module.ERROR_CODES["render"],
            message="visual_requirements_planned requires visual_requirements.json",
        )
        report = _require_one(
            module=module,
            grouped=grouped,
            name="visual_requirements_validation.json",
            code=module.ERROR_CODES["render"],
            message="visual_requirements_planned requires visual_requirements_validation.json",
        )
        validation = module.load_json(report, "Visual Requirements validation")
        snapshot = vi_dir / "editorial_snapshot.json"
        if validation.get("status") != "PASS" or validation.get("episodeDate") != date:
            raise module.DailyProductionError(
                module.ERROR_CODES["render"], "Visual Requirements validation must PASS"
            )
        if validation.get("editorialSnapshotSha256") != module.sha256_file(snapshot):
            raise module.DailyProductionError(
                module.ERROR_CODES["stale"], "Visual Requirements validation uses stale editorial snapshot"
            )
        requirement_doc = module.load_json(requirements, "Visual Requirements")
        if requirement_doc.get("editorialSnapshotSha256") != module.sha256_file(snapshot):
            raise module.DailyProductionError(
                module.ERROR_CODES["stale"], "Visual Requirements are stale after Story change"
            )
    elif new_state == "visual_intelligence_valid":
        package = _require_one(
            module=module,
            grouped=grouped,
            name="visual_intelligence_package.json",
            code=module.ERROR_CODES["render"],
            message="visual_intelligence_valid requires visual_intelligence_package.json",
        )
        report = _require_one(
            module=module,
            grouped=grouped,
            name="visual_intelligence_validation.json",
            code=module.ERROR_CODES["render"],
            message="visual_intelligence_valid requires visual_intelligence_validation.json",
        )
        validation = module.load_json(report, "Visual Intelligence validation")
        if (
            validation.get("status") != "PASS"
            or validation.get("episodeDate") != date
            or validation.get("packageSha256") != module.sha256_file(package)
        ):
            raise module.DailyProductionError(
                module.ERROR_CODES["render"], "Visual Intelligence validation/package lineage mismatch"
            )
        package_value = module.load_json(package, "Visual Intelligence package")
        snapshot = vi_dir / "editorial_snapshot.json"
        if package_value.get("final", {}).get("status") != "PASS":
            raise module.DailyProductionError(
                module.ERROR_CODES["render"], "Visual Intelligence final status must be PASS"
            )
        if package_value.get("inputs", {}).get("editorialSnapshotSha256") != module.sha256_file(snapshot):
            raise module.DailyProductionError(
                module.ERROR_CODES["stale"], "Visual Intelligence PASS is stale after Story change"
            )
    elif new_state == "episode_package_final":
        _validate_story_final_gate(
            module=module,
            workspace=workspace,
            date=date,
            evidence_paths=evidence_paths,
        )


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
        raise module.DailyProductionError(
            module.ERROR_CODES["stale"],
            "current-v1.2 control plane requires Visual Intelligence binding",
        )
    current_status = status(module=module, workspace=workspace, date=date)
    if current_status["validation"]["status"] != "pass":
        raise module.DailyProductionError(
            module.ERROR_CODES["stale"],
            "; ".join(current_status["validation"]["errors"]),
        )
    if new_state not in VI_STATES:
        raise module.DailyProductionError(
            module.ERROR_CODES["stale"], f"unknown Visual Intelligence state: {new_state}"
        )
    st_path = module.state_path(workspace, date)
    state = module.load_json(st_path, "production state")
    current = state["current_state"]
    current_index = VI_STATES.index(current)
    new_index = VI_STATES.index(new_state)
    if new_index <= current_index:
        if new_state == current:
            return {"status": "noop", "current_state": current}
        raise module.DailyProductionError(
            module.ERROR_CODES["stale"], f"state regression is forbidden: {current} -> {new_state}"
        )
    if new_index != current_index + 1:
        raise module.DailyProductionError(
            module.ERROR_CODES["stale"],
            f"state must advance exactly one step: expected {VI_STATES[current_index + 1]}",
        )
    resolved_paths = [
        module.safe_path(workspace, path, f"{new_state} evidence")
        for path in evidence_paths
    ]
    if not resolved_paths:
        raise module.DailyProductionError(
            module.ERROR_CODES["stale"], f"{new_state} requires evidence"
        )
    _validate_vi_transition(
        module=module,
        workspace=workspace,
        date=date,
        new_state=new_state,
        evidence_paths=resolved_paths,
    )
    evidence = [
        {
            "path": path.relative_to(workspace.resolve()).as_posix(),
            "sha256": module.sha256_file(path),
        }
        for path in resolved_paths
    ]
    state["current_state"] = new_state
    state["transitions"].append({"state": new_state, "evidence": evidence})
    module.write_atomic(st_path, state)
    return {"status": "advanced", "current_state": new_state, "state_path": str(st_path)}


def build_production(
    *, module: Any, workspace: Path, date: str, episode_package: Path
) -> dict[str, Any]:
    request = _request(module, workspace, date)
    if not _is_vi_request(request):
        return module.build_production(
            workspace=workspace, date=date, episode_package=episode_package
        )
    current = status(module=module, workspace=workspace, date=date)
    if current["current_state"] != "memory_usage_valid":
        raise module.DailyProductionError(
            module.ERROR_CODES["package"],
            "Visual Intelligence build-production requires memory_usage_valid",
        )
    package = module.safe_path(workspace, episode_package, "episode package")
    try:
        built = final_v12.build_hardened_v12(
            package,
            workspace,
            workspace
            / "skills/nasdaq-cafe-final-production/contracts/final_production_source_annex.schema.json",
            repo_root=workspace,
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
    p_init.add_argument("--semantic-freeze-path", required=True, type=Path)
    p_init.add_argument("--semantic-freeze-sha256", required=True)

    p_status = sub.add_parser("status")
    p_status.add_argument("--episode-date", required=True)

    p_advance = sub.add_parser("advance")
    p_advance.add_argument("--episode-date", required=True)
    p_advance.add_argument("--state", required=True, choices=VI_STATES)
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
                module=module,
                workspace=workspace,
                date=args.episode_date,
                daily_source=args.daily_source_package,
                requested_scope=args.requested_scope,
                renderer_commit=args.renderer_commit,
                renderer_contract_version=args.renderer_contract_version,
                visual_intelligence_bridge_version=args.visual_intelligence_bridge_version,
                semantic_freeze_path=args.semantic_freeze_path,
                semantic_freeze_sha256=args.semantic_freeze_sha256,
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
        elif args.command == "build-handoff":
            result = module.build_handoff(
                workspace=workspace,
                date=args.episode_date,
                bundle_root=args.bundle_root,
                plot_commit=args.plot_commit,
            )
        elif args.command == "record-preview":
            result = module.record_preview(
                workspace=workspace,
                date=args.episode_date,
                daily_source_root=args.daily_source_root,
                bundle_root=args.bundle_root,
                handoff_manifest=args.handoff_manifest,
                renderer_artifact_root=args.renderer_artifact_root,
                technical_report=args.technical_report,
                user_review=args.user_review,
            )
        elif args.command == "request-final":
            result = module.request_final(
                workspace=workspace,
                date=args.episode_date,
                approval_record=args.approval_record,
                explicit_final=args.explicit_final,
            )
        else:
            raise module.DailyProductionError(
                module.ERROR_CODES["stale"], "unsupported Visual Intelligence command"
            )
        code = 0
    except module.DailyProductionError as exc:
        result = {"status": "fail", "error_code": exc.code, "errors": [exc.message]}
        code = 1
    sys.stdout.buffer.write(module.canonical_json(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
