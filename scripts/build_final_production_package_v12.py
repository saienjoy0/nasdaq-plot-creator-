#!/usr/bin/env python3
"""Visual Intelligence v1.2 wrapper around the hardened final package builder.

Legacy production remains untouched. For a production request explicitly bound to
visual-intelligence-bridge/1.2.0, this wrapper replaces only the finalizer's
Visual Director bridge call with the v1.2 machine bridge. The Renderer still owns
canonicalization, intraday attachment, referential checks and strict validation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import build_final_production_package_hardened as hardened
import renderer_binding
import visual_intelligence_bridge

ROOT = Path(__file__).resolve().parents[1]


class VisualIntelligenceFinalBuildError(ValueError):
    pass


def _load_request(output_root: Path, date: str) -> dict[str, Any]:
    path = output_root / "working" / date / "production_request.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualIntelligenceFinalBuildError(f"production request invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualIntelligenceFinalBuildError("production request must be an object")
    return value


def _is_v12_request(request: dict[str, Any]) -> bool:
    binding = request.get("visual_intelligence")
    return binding == {
        "required": True,
        "bridge_contract_version": renderer_binding.BRIDGE_CONTRACT_VERSION,
        "frozen_interface_sha256": renderer_binding.FROZEN_INTERFACE_SHA256,
    }


def _persist_visual_intelligence_preflight_binding(
    *,
    output_root: Path,
    date: str,
    repo_root: Path,
    validation: dict[str, Any],
) -> dict[str, Any]:
    """Bind the exact Visual Intelligence PASS into the official preview preflight.

    This augments only v1.2 preflight lineage. Existing episode-memory hardening
    fields are preserved byte-semantically, and no editorial judgment is added.
    """

    preflight_path = output_root / "verification" / date / "official_execution_preflight.json"
    package_path = output_root / "working" / date / "visual-intelligence" / "visual_intelligence_package.json"
    try:
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualIntelligenceFinalBuildError(f"Visual Intelligence preflight binding input invalid: {exc}") from exc
    if not isinstance(preflight, dict) or not isinstance(package, dict):
        raise VisualIntelligenceFinalBuildError("Visual Intelligence preflight/package roots must be objects")
    if validation.get("status") != "PASS":
        raise VisualIntelligenceFinalBuildError("Visual Intelligence validation must PASS before preflight binding")
    inputs = package.get("inputs")
    final = package.get("final")
    if not isinstance(inputs, dict) or not isinstance(final, dict) or final.get("status") != "PASS":
        raise VisualIntelligenceFinalBuildError("Visual Intelligence package is not final PASS")
    binding = renderer_binding.load_binding(repo_root)
    expected_renderer = binding["renderer"]["commit"]
    expected_registry_sha = binding["renderer"]["registrySnapshotSha256"]
    if inputs.get("rendererCommit") != expected_renderer:
        raise VisualIntelligenceFinalBuildError("Visual Intelligence package Renderer SHA drift before preflight")
    if inputs.get("registrySnapshotSha256") != expected_registry_sha:
        raise VisualIntelligenceFinalBuildError("Visual Intelligence package Registry SHA drift before preflight")
    if validation.get("packageSha256") != hardened._load_module(
        "visual_intelligence_preflight_sha_v12",
        ROOT / "scripts/validate_visual_intelligence_package.py",
    ).sha256_file(package_path):
        raise VisualIntelligenceFinalBuildError("Visual Intelligence package SHA drift before preflight")

    record = {
        "contractVersion": "1.0.0",
        "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
        "frozenInterfaceSha256": renderer_binding.FROZEN_INTERFACE_SHA256,
        "status": "PASS",
        "packageSha256": validation["packageSha256"],
        "compiledVisualSha256": validation["compiledVisualSha256"],
        "editorialSnapshotSha256": inputs.get("editorialSnapshotSha256"),
        "rendererCommit": expected_renderer,
        "registrySnapshotSha256": expected_registry_sha,
    }
    preflight["visual_intelligence"] = record
    text = json.dumps(preflight, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = preflight_path.with_name(preflight_path.name + ".visual-intelligence.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(preflight_path)
    return record


def _renderer_finalizer_v12(*, output_root: Path, date: str, renderer_root: Path):
    module = hardened._load_module(
        "renderer_package_finalizer_compat_v12",
        ROOT / "scripts/finalize_renderer_package_compat.py",
    )
    intraday = hardened._load_module(
        "renderer_intraday_series_attachment_v12",
        ROOT / "scripts/remotion_intraday_series.py",
    )
    request = _load_request(output_root, date)
    if not _is_v12_request(request):
        return hardened._real_renderer_finalizer(
            output_root=output_root,
            date=date,
            renderer_root=renderer_root,
        )

    canonical = renderer_binding.verify_renderer_checkout(ROOT, renderer_root)
    requested_renderer = request.get("renderer")
    if not isinstance(requested_renderer, dict):
        raise VisualIntelligenceFinalBuildError("production request renderer binding missing")
    if requested_renderer.get("commit") != canonical["renderer"]["commit"]:
        raise VisualIntelligenceFinalBuildError("production request Renderer commit drift")
    if requested_renderer.get("contract_version") != canonical["renderer"]["contractVersion"]:
        raise VisualIntelligenceFinalBuildError("production request Renderer contract drift")

    render_spec_path = output_root / "render-specs" / date / "render_spec.json"
    runtime_registry = module.base._build_validation_runtime_asset_registry(
        output_root=output_root,
        date=date,
        render_spec_path=render_spec_path,
    )
    previous_registry = os.environ.get("NASDAQ_CAFE_RUNTIME_ASSET_REGISTRY")
    if runtime_registry is not None:
        os.environ["NASDAQ_CAFE_RUNTIME_ASSET_REGISTRY"] = str(runtime_registry)

    original_canonicalize = module.remotion_240_projection.canonicalize_render_spec
    original_prepare = module.visual_director_bridge.prepare_and_compile
    attachment_result: dict[str, Any] = {}

    def canonicalize_with_bound_intraday(
        render: dict[str, Any],
        *,
        episode_date: str,
        reaction_bindings_path: Path,
    ) -> None:
        original_canonicalize(
            render,
            episode_date=episode_date,
            reaction_bindings_path=reaction_bindings_path,
        )
        result = intraday.attach_bound_intraday_series(
            render,
            output_root=output_root,
            episode_date=episode_date,
            reaction_bindings_path=reaction_bindings_path,
        )
        attachment_result.clear()
        attachment_result.update(result)

    def prepare_visual_intelligence(**kwargs):
        return visual_intelligence_bridge.prepare_and_compile(
            **kwargs,
            plot_root=ROOT,
        )

    module.remotion_240_projection.canonicalize_render_spec = canonicalize_with_bound_intraday
    module.visual_director_bridge.prepare_and_compile = prepare_visual_intelligence
    try:
        finalized = module.finalize(
            output_root=output_root,
            date=date,
            renderer_root=renderer_root,
        )
        if attachment_result:
            finalized["intradaySeriesAttachment"] = dict(attachment_result)
        vi_package = output_root / "working" / date / "visual-intelligence" / "visual_intelligence_package.json"
        if not vi_package.is_file():
            raise VisualIntelligenceFinalBuildError("Visual Intelligence package missing after Renderer finalization")
        finalized["visualIntelligence"] = {
            "status": "PASS",
            "packagePath": str(vi_package),
            "packageSha256": hardened._load_module(
                "visual_intelligence_package_validator_v12",
                ROOT / "scripts/validate_visual_intelligence_package.py",
            ).sha256_file(vi_package),
        }
        return finalized
    finally:
        module.remotion_240_projection.canonicalize_render_spec = original_canonicalize
        module.visual_director_bridge.prepare_and_compile = original_prepare
        if previous_registry is None:
            os.environ.pop("NASDAQ_CAFE_RUNTIME_ASSET_REGISTRY", None)
        else:
            os.environ["NASDAQ_CAFE_RUNTIME_ASSET_REGISTRY"] = previous_registry


def build_hardened_v12(
    package: Path,
    output_root: Path,
    schema: Path,
    *,
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    result = hardened.build_hardened(
        package,
        output_root,
        schema,
        repo_root=repo_root,
        renderer_finalizer=_renderer_finalizer_v12,
    )
    date = hardened._production_date(result.get("paths", {}))
    request = _load_request(output_root.resolve(), date)
    if _is_v12_request(request):
        renderer_root_value = os.environ.get("NASDAQ_CAFE_RENDERER_ROOT")
        if not renderer_root_value:
            raise VisualIntelligenceFinalBuildError(
                "NASDAQ_CAFE_RENDERER_ROOT is required for Visual Intelligence final validation"
            )
        validator = hardened._load_module(
            "visual_intelligence_package_validator_post_build",
            ROOT / "scripts/validate_visual_intelligence_package.py",
        )
        validation = validator.validate(
            root=output_root.resolve(),
            date=date,
            renderer_root=Path(renderer_root_value),
        )
        preflight_record = _persist_visual_intelligence_preflight_binding(
            output_root=output_root.resolve(),
            date=date,
            repo_root=repo_root.resolve(),
            validation=validation,
        )
        result["visual_intelligence"] = validation
        result["visual_intelligence_preflight"] = preflight_record
    return result
