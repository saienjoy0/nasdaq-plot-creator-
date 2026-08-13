#!/usr/bin/env python3
"""Visual Intelligence v1.2 wrapper around the hardened final package builder.

Legacy production remains untouched. For a request explicitly bound to
visual-intelligence-bridge/1.2.0, the Critic-approved compiled RenderSpec is the
immutable visual authority for build-production. Legacy Financial/package checks
still run, but legacy visual canonicalizers, template materializers, sequence
rewriters, and Visual Director must not redesign that approved visual plan.

The exact approved RenderSpec is then checked by the existing referential and
pinned Renderer validators. Any post-PASS Scene/Beat or visual drift fails closed.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import build_final_production_package_hardened as hardened
import renderer_binding

ROOT = Path(__file__).resolve().parents[1]


class VisualIntelligenceFinalBuildError(ValueError):
    pass


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualIntelligenceFinalBuildError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualIntelligenceFinalBuildError(f"{label} must be an object")
    return value


def _load_request(output_root: Path, date: str) -> dict[str, Any]:
    return _load_json_object(
        output_root / "working" / date / "production_request.json",
        "production request",
    )


def _is_v12_request(request: dict[str, Any]) -> bool:
    binding = request.get("visual_intelligence")
    return binding == {
        "required": True,
        "bridge_contract_version": renderer_binding.BRIDGE_CONTRACT_VERSION,
        "frozen_interface_sha256": renderer_binding.FROZEN_INTERFACE_SHA256,
    }


def _without_legacy_visual_director(request: dict[str, Any]) -> dict[str, Any]:
    """Return a copy that prevents the legacy finalizer from invoking a second Director."""
    result = copy.deepcopy(request)
    result.pop("visual_director", None)
    return result


def _forbid_second_director(*args: Any, **kwargs: Any) -> None:
    del args, kwargs
    raise VisualIntelligenceFinalBuildError(
        "E_VISUAL_INTELLIGENCE_SECOND_DIRECTOR_FORBIDDEN"
    )


def _beat_identity(render: dict[str, Any]) -> list[tuple[str, str]]:
    identity: list[tuple[str, str]] = []
    scenes = render.get("scenes")
    if not isinstance(scenes, list):
        raise VisualIntelligenceFinalBuildError(
            "E_VISUAL_INTELLIGENCE_POST_PASS_BEAT_DRIFT: scenes missing"
        )
    for scene_index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise VisualIntelligenceFinalBuildError(
                "E_VISUAL_INTELLIGENCE_POST_PASS_BEAT_DRIFT:"
                f" scene={scene_index} invalid"
            )
        scene_id = scene.get("sceneId")
        beats = scene.get("visualBeats")
        if not isinstance(scene_id, str) or not isinstance(beats, list):
            raise VisualIntelligenceFinalBuildError(
                "E_VISUAL_INTELLIGENCE_POST_PASS_BEAT_DRIFT:"
                f" scene={scene_index} identity invalid"
            )
        for beat_index, beat in enumerate(beats, start=1):
            if not isinstance(beat, dict) or not isinstance(beat.get("beatId"), str):
                raise VisualIntelligenceFinalBuildError(
                    "E_VISUAL_INTELLIGENCE_POST_PASS_BEAT_DRIFT:"
                    f" scene={scene_id}:beat={beat_index} invalid"
                )
            identity.append((scene_id, beat["beatId"]))
    return identity


def _assert_post_pass_integrity(
    approved: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    """Require build-production to preserve the exact Critic-approved visual authority."""
    approved_scenes = approved.get("scenes")
    candidate_scenes = candidate.get("scenes")
    if not isinstance(approved_scenes, list) or not isinstance(candidate_scenes, list):
        raise VisualIntelligenceFinalBuildError(
            "E_VISUAL_INTELLIGENCE_POST_PASS_BEAT_DRIFT: scenes missing"
        )
    approved_identity = _beat_identity(approved)
    candidate_identity = _beat_identity(candidate)
    if len(approved_scenes) != len(candidate_scenes) or approved_identity != candidate_identity:
        raise VisualIntelligenceFinalBuildError(
            "E_VISUAL_INTELLIGENCE_POST_PASS_BEAT_DRIFT:"
            f" approved={approved_identity} final={candidate_identity}"
        )

    for scene_index, (approved_scene, candidate_scene) in enumerate(
        zip(approved_scenes, candidate_scenes, strict=True),
        start=1,
    ):
        if approved_scene.get("narrationChunks") != candidate_scene.get("narrationChunks"):
            raise VisualIntelligenceFinalBuildError(
                "E_VISUAL_INTELLIGENCE_POST_PASS_SEMANTIC_DRIFT:"
                f" scene={scene_index}:narrationChunks"
            )
        approved_beats = approved_scene.get("visualBeats", [])
        candidate_beats = candidate_scene.get("visualBeats", [])
        for beat_index, (approved_beat, candidate_beat) in enumerate(
            zip(approved_beats, candidate_beats, strict=True),
            start=1,
        ):
            for key in (
                "startChunkId",
                "endChunkId",
                "narrationStartCue",
                "narrationEndCue",
                "primaryFunction",
                "contentType",
                "screenQuestion",
                "primaryElement",
                "viewerTexts",
                "evidenceSourceIds",
            ):
                if approved_beat.get(key) != candidate_beat.get(key):
                    raise VisualIntelligenceFinalBuildError(
                        "E_VISUAL_INTELLIGENCE_POST_PASS_SEMANTIC_DRIFT:"
                        f" scene={scene_index}:beat={beat_index}:field={key}"
                    )
            for key in (
                "screenState",
                "visualMode",
                "visualTemplate",
                "templateVariant",
                "objectIds",
                "assetPlacementIds",
                "returnScreenState",
                "financialReturnTarget",
                "entity",
                "pictureBook",
                "shots",
            ):
                if approved_beat.get(key) != candidate_beat.get(key):
                    raise VisualIntelligenceFinalBuildError(
                        "E_VISUAL_INTELLIGENCE_POST_PASS_VISUAL_DRIFT:"
                        f" scene={scene_index}:beat={beat_index}:field={key}"
                    )

    # No legacy visual transform is allowed on the v1.2 post-PASS path. Runtime asset
    # lookup is external and verified intraday series are already bound before the
    # Director/Critic compile, so the approved RenderSpec itself must remain unchanged.
    if approved != candidate:
        raise VisualIntelligenceFinalBuildError(
            "E_VISUAL_INTELLIGENCE_POST_PASS_VISUAL_DRIFT:"
            " approved compiled RenderSpec changed during build-production"
        )

    return {
        "sceneCount": len(approved_scenes),
        "beatCount": len(approved_identity),
        "beatIdentityPreserved": True,
        "semanticSurfacePreserved": True,
        "visualAuthorityPreserved": True,
        "secondDirectorInvoked": False,
    }


def _load_approved_visual_authority(
    *,
    output_root: Path,
    date: str,
) -> dict[str, Any]:
    vi_dir = output_root / "working" / date / "visual-intelligence"
    verification = output_root / "verification" / date
    compiled_path = vi_dir / "visual_direction_compiled_render.json"
    warning_path = vi_dir / "visual_editorial_warning_report.json"
    package_path = vi_dir / "visual_intelligence_package.json"
    decision_path = vi_dir / "visual_intelligence_decision.json"
    validation_path = verification / "visual_intelligence_validation.json"

    for path, label in (
        (compiled_path, "Critic-approved compiled visual"),
        (warning_path, "Visual warning report"),
        (package_path, "Visual Intelligence package"),
        (decision_path, "Visual Intelligence decision"),
        (validation_path, "Visual Intelligence validation"),
    ):
        if not path.is_file():
            raise VisualIntelligenceFinalBuildError(
                f"E_VISUAL_INTELLIGENCE_POST_PASS_AUTHORITY_MISSING:{label}:{path}"
            )

    compiled = _load_json_object(compiled_path, "Critic-approved compiled visual")
    package = _load_json_object(package_path, "Visual Intelligence package")
    decision = _load_json_object(decision_path, "Visual Intelligence decision")
    validation = _load_json_object(validation_path, "Visual Intelligence validation")

    compiled_sha = _sha256_file(compiled_path)
    warning_sha = _sha256_file(warning_path)
    package_sha = _sha256_file(package_path)
    final = package.get("final")
    rounds = decision.get("reviewRounds")
    last_round = rounds[-1] if isinstance(rounds, list) and rounds else None

    if package.get("episodeDate") != date or not isinstance(final, dict) or final.get("status") != "PASS":
        raise VisualIntelligenceFinalBuildError(
            "E_VISUAL_INTELLIGENCE_POST_PASS_AUTHORITY_INVALID: package is not final PASS"
        )
    if validation.get("episodeDate") != date or validation.get("status") != "PASS":
        raise VisualIntelligenceFinalBuildError(
            "E_VISUAL_INTELLIGENCE_POST_PASS_AUTHORITY_INVALID: validation is not PASS"
        )
    if validation.get("packageSha256") != package_sha:
        raise VisualIntelligenceFinalBuildError(
            "E_VISUAL_INTELLIGENCE_POST_PASS_AUTHORITY_STALE: package SHA mismatch"
        )
    if (
        final.get("compiledVisualSha256") != compiled_sha
        or validation.get("compiledVisualSha256") != compiled_sha
    ):
        raise VisualIntelligenceFinalBuildError(
            "E_VISUAL_INTELLIGENCE_POST_PASS_AUTHORITY_STALE: compiled visual SHA mismatch"
        )
    if (
        final.get("warningReportSha256") != warning_sha
        or validation.get("warningReportSha256") != warning_sha
    ):
        raise VisualIntelligenceFinalBuildError(
            "E_VISUAL_INTELLIGENCE_POST_PASS_AUTHORITY_STALE: warning report SHA mismatch"
        )
    if (
        not isinstance(last_round, dict)
        or last_round.get("status") != "PASS"
        or last_round.get("compiledVisualSha256") != compiled_sha
        or last_round.get("warningReportSha256") != warning_sha
    ):
        raise VisualIntelligenceFinalBuildError(
            "E_VISUAL_INTELLIGENCE_POST_PASS_AUTHORITY_STALE: Critic PASS lineage mismatch"
        )
    if (
        compiled.get("schemaVersion") != "2.4.0"
        or compiled.get("episode", {}).get("targetDate") != date
    ):
        raise VisualIntelligenceFinalBuildError(
            "E_VISUAL_INTELLIGENCE_POST_PASS_AUTHORITY_INVALID: compiled RenderSpec mismatch"
        )

    return {
        "render": compiled,
        "compiledPath": compiled_path,
        "compiledSha256": compiled_sha,
        "warningPath": warning_path,
        "warningSha256": warning_sha,
        "packagePath": package_path,
        "packageSha256": package_sha,
        "catalogPath": vi_dir / "visual_candidate_catalog.json",
        "planPath": vi_dir / "visual_direction_plan.json",
        "compileReportPath": vi_dir / "visual_direction_compile_report.json",
    }


def _write_post_pass_integrity_report(
    *,
    output_root: Path,
    date: str,
    authority: dict[str, Any],
    final_render_path: Path,
    checks: dict[str, Any],
) -> Path:
    final_sha = _sha256_file(final_render_path)
    report = {
        "contractVersion": "1.0.0",
        "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
        "episodeDate": date,
        "status": "PASS",
        "approvedCompiledVisualSha256": authority["compiledSha256"],
        "finalRenderSpecSha256": final_sha,
        **checks,
    }
    path = (
        output_root
        / "verification"
        / date
        / "visual_intelligence_post_pass_integrity.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _persist_visual_intelligence_preflight_binding(
    *,
    output_root: Path,
    date: str,
    repo_root: Path,
    validation: dict[str, Any],
) -> dict[str, Any]:
    """Bind the exact Visual Intelligence PASS and post-PASS authority into preflight."""

    preflight_path = output_root / "verification" / date / "official_execution_preflight.json"
    package_path = (
        output_root
        / "working"
        / date
        / "visual-intelligence"
        / "visual_intelligence_package.json"
    )
    integrity_path = (
        output_root
        / "verification"
        / date
        / "visual_intelligence_post_pass_integrity.json"
    )
    render_spec_path = output_root / "render-specs" / date / "render_spec.json"
    try:
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
        package = json.loads(package_path.read_text(encoding="utf-8"))
        integrity = json.loads(integrity_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualIntelligenceFinalBuildError(
            f"Visual Intelligence preflight binding input invalid: {exc}"
        ) from exc
    if not isinstance(preflight, dict) or not isinstance(package, dict) or not isinstance(integrity, dict):
        raise VisualIntelligenceFinalBuildError(
            "Visual Intelligence preflight/package/integrity roots must be objects"
        )
    if validation.get("status") != "PASS":
        raise VisualIntelligenceFinalBuildError(
            "Visual Intelligence validation must PASS before preflight binding"
        )
    inputs = package.get("inputs")
    final = package.get("final")
    if not isinstance(inputs, dict) or not isinstance(final, dict) or final.get("status") != "PASS":
        raise VisualIntelligenceFinalBuildError(
            "Visual Intelligence package is not final PASS"
        )
    binding = renderer_binding.load_binding(repo_root)
    expected_renderer = binding["renderer"]["commit"]
    expected_registry_sha = binding["renderer"]["registrySnapshotSha256"]
    if inputs.get("rendererCommit") != expected_renderer:
        raise VisualIntelligenceFinalBuildError(
            "Visual Intelligence package Renderer SHA drift before preflight"
        )
    if inputs.get("registrySnapshotSha256") != expected_registry_sha:
        raise VisualIntelligenceFinalBuildError(
            "Visual Intelligence package Registry SHA drift before preflight"
        )
    if validation.get("packageSha256") != _sha256_file(package_path):
        raise VisualIntelligenceFinalBuildError(
            "Visual Intelligence package SHA drift before preflight"
        )
    if (
        integrity.get("status") != "PASS"
        or integrity.get("episodeDate") != date
        or integrity.get("approvedCompiledVisualSha256")
        != validation.get("compiledVisualSha256")
        or integrity.get("finalRenderSpecSha256") != _sha256_file(render_spec_path)
        or integrity.get("secondDirectorInvoked") is not False
    ):
        raise VisualIntelligenceFinalBuildError(
            "Visual Intelligence post-PASS integrity lineage mismatch"
        )

    integrity_sha = _sha256_file(integrity_path)
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
        "postPassIntegritySha256": integrity_sha,
    }
    preflight["visual_intelligence"] = record
    preflight.setdefault("artifacts", {})[
        "visual_intelligence_post_pass_integrity"
    ] = integrity_sha
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
        raise VisualIntelligenceFinalBuildError(
            "production request renderer binding missing"
        )
    if requested_renderer.get("commit") != canonical["renderer"]["commit"]:
        raise VisualIntelligenceFinalBuildError(
            "production request Renderer commit drift"
        )
    if (
        requested_renderer.get("contract_version")
        != canonical["renderer"]["contractVersion"]
    ):
        raise VisualIntelligenceFinalBuildError(
            "production request Renderer contract drift"
        )

    authority = _load_approved_visual_authority(
        output_root=output_root,
        date=date,
    )
    approved_render = authority["render"]
    render_spec_path = output_root / "render-specs" / date / "render_spec.json"
    runtime_registry = module.base._build_validation_runtime_asset_registry(
        output_root=output_root,
        date=date,
        render_spec_path=render_spec_path,
    )
    previous_registry = os.environ.get("NASDAQ_CAFE_RUNTIME_ASSET_REGISTRY")
    if runtime_registry is not None:
        os.environ["NASDAQ_CAFE_RUNTIME_ASSET_REGISTRY"] = str(runtime_registry)

    original_strict_projection = module.base._strict_renderer_projection
    original_canonicalize = module.remotion_240_projection.canonicalize_render_spec
    original_template_materialize = module.remotion_template_data.materialize_template_data
    original_sequence_policy = module.remotion_sequence_policy.resolve_sequence_policies
    original_load_json = module.base.load_json
    original_prepare = module.visual_director_bridge.prepare_and_compile
    original_referential = module._validate_referential_integrity
    request_path = (
        output_root / "working" / date / "production_request.json"
    ).resolve()
    integrity_checks: dict[str, Any] = {}

    def strict_from_approved(*args: Any, **kwargs: Any) -> dict[str, Any]:
        del args, kwargs
        return copy.deepcopy(approved_render)

    def no_post_pass_visual_canonicalize(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        return None

    def no_post_pass_template_materialize(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        return None

    def no_post_pass_sequence_rewrite(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        return None

    def load_without_second_director(path: Path, label: str) -> dict[str, Any]:
        value = original_load_json(path, label)
        if Path(path).resolve() == request_path:
            return _without_legacy_visual_director(value)
        return value

    def validate_approved_render(render: dict[str, Any]) -> None:
        checks = _assert_post_pass_integrity(approved_render, render)
        integrity_checks.clear()
        integrity_checks.update(checks)
        original_referential(render)

    module.base._strict_renderer_projection = strict_from_approved
    module.remotion_240_projection.canonicalize_render_spec = (
        no_post_pass_visual_canonicalize
    )
    module.remotion_template_data.materialize_template_data = (
        no_post_pass_template_materialize
    )
    module.remotion_sequence_policy.resolve_sequence_policies = (
        no_post_pass_sequence_rewrite
    )
    module.base.load_json = load_without_second_director
    module.visual_director_bridge.prepare_and_compile = _forbid_second_director
    module._validate_referential_integrity = validate_approved_render

    try:
        finalized = module.finalize(
            output_root=output_root,
            date=date,
            renderer_root=renderer_root,
        )
        final_render = _load_json_object(
            render_spec_path,
            "final v1.2 RenderSpec",
        )
        final_checks = _assert_post_pass_integrity(approved_render, final_render)
        if integrity_checks and integrity_checks != final_checks:
            raise VisualIntelligenceFinalBuildError(
                "E_VISUAL_INTELLIGENCE_POST_PASS_INTEGRITY_REPORT_DRIFT"
            )
        integrity_path = _write_post_pass_integrity_report(
            output_root=output_root,
            date=date,
            authority=authority,
            final_render_path=render_spec_path,
            checks=final_checks,
        )

        vi_package = authority["packagePath"]
        finalized.setdefault("paths", {})[
            "visual_intelligence_post_pass_integrity"
        ] = str(integrity_path)
        finalized["paths"]["visual_candidate_catalog"] = str(
            authority["catalogPath"]
        )
        finalized["paths"]["visual_direction_plan"] = str(
            authority["planPath"]
        )
        finalized["paths"]["visual_direction_compile_report"] = str(
            authority["compileReportPath"]
        )
        finalized.setdefault("hashes", {})[
            "visual_intelligence_post_pass_integrity"
        ] = _sha256_file(integrity_path)
        for key, path in (
            ("visual_candidate_catalog", authority["catalogPath"]),
            ("visual_direction_plan", authority["planPath"]),
            ("visual_direction_compile_report", authority["compileReportPath"]),
        ):
            if Path(path).is_file():
                finalized["hashes"][key] = _sha256_file(Path(path))
        finalized["visualDirection"] = {
            "status": "pass",
            "semanticDiff": "PASS",
            "source": "critic-approved-compiled-render",
            "secondDirectorInvoked": False,
        }
        finalized["visualIntelligence"] = {
            "status": "PASS",
            "packagePath": str(vi_package),
            "packageSha256": authority["packageSha256"],
            "compiledVisualSha256": authority["compiledSha256"],
            "postPassIntegritySha256": _sha256_file(integrity_path),
        }
        return finalized
    finally:
        module.base._strict_renderer_projection = original_strict_projection
        module.remotion_240_projection.canonicalize_render_spec = original_canonicalize
        module.remotion_template_data.materialize_template_data = (
            original_template_materialize
        )
        module.remotion_sequence_policy.resolve_sequence_policies = (
            original_sequence_policy
        )
        module.base.load_json = original_load_json
        module.visual_director_bridge.prepare_and_compile = original_prepare
        module._validate_referential_integrity = original_referential
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
