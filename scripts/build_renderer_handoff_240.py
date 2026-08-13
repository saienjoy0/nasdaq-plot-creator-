#!/usr/bin/env python3
"""Extend the hardened handoff with Remotion 2.4 validation lineage."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]

EXTRA_ROLES = {
    "final_episode_contract": "working/{date}/final_episode_contract.json",
    "financial_recipe_plan": "working/{date}/financial_recipe_plan.json",
    "terminal_assembly_binding": "working/{date}/terminal_assembly_bindings.json",
    "financial_visual_consistency_report": "verification/{date}/financial_visual_consistency_report.json",
    "visual_grammar_structural_report": "verification/{date}/visual_grammar_structural_report.json",
    "renderer_validation_report": "verification/{date}/renderer_validation_report.json",
}

VISUAL_DIRECTOR_ROLES = {
    "visual_candidate_catalog": "working/{date}/visual_candidate_catalog.json",
    "visual_direction_plan": "working/{date}/visual_direction_plan.json",
    "visual_direction_compile_report": "verification/{date}/visual_direction_compile_report.json",
}

VISUAL_INTELLIGENCE_ROLES = {
    "visual_candidate_catalog": "working/{date}/visual-intelligence/visual_candidate_catalog.json",
    "visual_direction_plan": "working/{date}/visual-intelligence/visual_direction_plan.json",
    "visual_direction_compile_report": "working/{date}/visual-intelligence/visual_direction_compile_report.json",
}

class RendererHandoff240Error(ValueError):
    pass

def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RendererHandoff240Error(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def _base_hardened(**kwargs):
    module = _load_module(
        "renderer_handoff_hardened_base",
        ROOT / "scripts/build_renderer_handoff_hardened.py",
    )
    return module.build_handoff_hardened(**kwargs)

def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def safe_file(root: Path, relative: str, label: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise RendererHandoff240Error(f"{label} path must be safe and relative")
    resolved = (root.resolve() / path).resolve()
    if root.resolve() not in resolved.parents or not resolved.is_file():
        raise RendererHandoff240Error(f"{label} is missing: {relative}")
    return resolved

def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RendererHandoff240Error(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise RendererHandoff240Error(f"{label} must be an object")
    return value

def _validate_renderer_evidence(
    *, source_root: Path, date: str, renderer_commit: str,
    renderer_contract_version: str,
) -> dict[str, Path]:
    role_paths = dict(EXTRA_ROLES)
    request = load_json(
        safe_file(
            source_root,
            f"working/{date}/production_request.json",
            "production request",
        ),
        "production request",
    )
    visual_intelligence = request.get("visual_intelligence")
    if isinstance(visual_intelligence, dict) and visual_intelligence.get("required") is True:
        role_paths.update(VISUAL_INTELLIGENCE_ROLES)
    elif request.get("visual_director") is not None:
        role_paths.update(VISUAL_DIRECTOR_ROLES)
    extras = {
        role: safe_file(source_root, template.format(date=date), role)
        for role, template in role_paths.items()
    }
    render_spec = safe_file(
        source_root, f"render-specs/{date}/render_spec.json", "render_spec"
    )
    report = load_json(extras["renderer_validation_report"], "renderer validation report")
    if report.get("status") != "PASS":
        raise RendererHandoff240Error("renderer validation report must be PASS")
    renderer = report.get("renderer")
    if not isinstance(renderer, dict):
        raise RendererHandoff240Error("renderer validation binding missing")
    if renderer.get("commit") != renderer_commit:
        raise RendererHandoff240Error("renderer validation commit mismatch")
    if renderer.get("contractVersion") != renderer_contract_version:
        raise RendererHandoff240Error("renderer validation contract mismatch")
    if report.get("renderSpec", {}).get("sha256") != sha256_file(render_spec):
        raise RendererHandoff240Error("renderer validation render spec SHA mismatch")
    if report.get("unresolvedStateCount") != 0:
        raise RendererHandoff240Error("renderer validation has unresolved state")
    preflight = load_json(
        safe_file(
            source_root,
            f"verification/{date}/official_execution_preflight.json",
            "preflight",
        ),
        "preflight",
    )
    renderer_preflight = preflight.get("renderer_validation")
    if not isinstance(renderer_preflight, dict):
        raise RendererHandoff240Error("preflight renderer validation missing")
    if renderer_preflight.get("status") != "pass":
        raise RendererHandoff240Error("preflight renderer validation must pass")
    if renderer_preflight.get("report_sha256") != sha256_file(
        extras["renderer_validation_report"]
    ):
        raise RendererHandoff240Error("preflight renderer report SHA mismatch")
    if "visual_direction_compile_report" in extras:
        direction = load_json(
            extras["visual_direction_compile_report"],
            "Visual Direction compile report",
        )
        if direction.get("semanticDiff") != "PASS":
            raise RendererHandoff240Error(
                "Visual Direction Protected Semantic Diff must PASS"
            )
        expected_direction_sha = preflight.get("artifacts", {}).get(
            "visual_direction_compile_report"
        )
        if expected_direction_sha != sha256_file(
            extras["visual_direction_compile_report"]
        ):
            raise RendererHandoff240Error(
                "preflight Visual Direction report SHA mismatch"
            )
    return extras

def _extend_bundle(
    *, base_result: dict[str, Any], extras: dict[str, Path],
    source_root: Path, bundle_root: Path, date: str,
) -> dict[str, Any]:
    base_bundle = Path(str(base_result["bundle_path"]))
    base_manifest_path = Path(str(base_result["manifest_path"]))
    manifest = load_json(base_manifest_path, "base handoff manifest")
    manifest.pop("bundle_id", None)
    files = list(manifest.get("files", []))
    destinations = {item["destination_path"] for item in files}
    for role, source in sorted(extras.items()):
        destination = f"production/{source.name}"
        if destination in destinations:
            raise RendererHandoff240Error(f"duplicate destination: {destination}")
        destinations.add(destination)
        files.append({
            "role": role,
            "source_path": source.relative_to(source_root).as_posix(),
            "destination_path": destination,
            "sha256": sha256_file(source),
            "size": source.stat().st_size,
            "required": True,
        })
    manifest["files"] = sorted(
        files, key=lambda item: (item["role"], item["destination_path"])
    )
    validation = dict(manifest.get("validation", {}))
    validation["renderer_contract"] = "pass"
    validation["remotion_official_validator"] = "pass"
    manifest["validation"] = validation
    bundle_id = hashlib.sha256(canonical_json(manifest)).hexdigest()
    final_manifest = {
        "contract_version": manifest.pop("contract_version"),
        "bundle_id": bundle_id,
        **manifest,
    }
    target = bundle_root.resolve() / date / bundle_id
    if target.exists():
        existing = load_json(target / "handoff_manifest.json", "existing handoff")
        if existing != final_manifest:
            raise RendererHandoff240Error("existing 2.4 bundle differs")
        return {
            "status": "noop", "bundle_id": bundle_id,
            "bundle_path": str(target),
            "manifest_path": str(target / "handoff_manifest.json"),
        }
    staging = bundle_root.resolve() / date / f".{bundle_id}.staging"
    shutil.rmtree(staging, ignore_errors=True)
    shutil.copytree(base_bundle, staging)
    try:
        for source in extras.values():
            destination = staging / f"production/{source.name}"
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        (staging / "handoff_manifest.json").write_bytes(canonical_json(final_manifest))
        for item in final_manifest["files"]:
            copied = staging / item["destination_path"]
            if not copied.is_file() or sha256_file(copied) != item["sha256"]:
                raise RendererHandoff240Error(
                    f"extended bundle verification failed: {item['destination_path']}"
                )
        staging.replace(target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {
        "status": "created", "bundle_id": bundle_id,
        "bundle_path": str(target),
        "manifest_path": str(target / "handoff_manifest.json"),
    }
def build_handoff_hardened(
    *, source_root: Path, bundle_root: Path, date: str, mode: str,
    plot_commit: str, renderer_commit: str, renderer_contract_version: str,
    approval_path: Path | None = None,
    base_builder: Callable[..., dict[str, Any]] = _base_hardened,
) -> dict[str, Any]:
    if renderer_contract_version != "2.4.0":
        return base_builder(
            source_root=source_root, bundle_root=bundle_root, date=date,
            mode=mode, plot_commit=plot_commit, renderer_commit=renderer_commit,
            renderer_contract_version=renderer_contract_version,
            approval_path=approval_path,
        )
    source_root = source_root.resolve()
    bundle_root = bundle_root.resolve()
    extras = _validate_renderer_evidence(
        source_root=source_root, date=date, renderer_commit=renderer_commit,
        renderer_contract_version=renderer_contract_version,
    )
    temporary_root = bundle_root / ".base-2.4"
    try:
        base = base_builder(
            source_root=source_root, bundle_root=temporary_root, date=date,
            mode=mode, plot_commit=plot_commit, renderer_commit=renderer_commit,
            renderer_contract_version=renderer_contract_version,
            approval_path=approval_path,
        )
        result = _extend_bundle(
            base_result=base, extras=extras, source_root=source_root,
            bundle_root=bundle_root, date=date,
        )
        result["renderer_validation"] = "pass"
        return result
    finally:
        shutil.rmtree(temporary_root, ignore_errors=True)
