#!/usr/bin/env python3
"""Validate the ChatGPT-owned editorial semantic boundary before Semantic Freeze.

The canonical daily-authoring v2 file already contains final Story Plan, Story Script,
Creative Review, and presentation authoring. This preflight adds no meaning. It verifies
Research lineage, projects temporary validator inputs with only file-linkage changes,
runs the existing official Story/04 validators, checks presentation alignment, and
publishes a SHA-bound Editorial Semantic Acceptance atomically.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import materialize_causal_research
import remotion_template_variant


class EditorialSemanticBoundaryError(ValueError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EditorialSemanticBoundaryError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise EditorialSemanticBoundaryError(f"{label} root must be an object")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def projected_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def projected_sha(value: Any) -> str:
    return hashlib.sha256(projected_bytes(value)).hexdigest()


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(payload)
    tmp.replace(path)


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write_bytes(
        path,
        (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )


def repo_ref(root: Path, path: Path) -> dict[str, str]:
    root = root.resolve()
    path = path.resolve()
    if path != root and root not in path.parents:
        raise EditorialSemanticBoundaryError(f"path escapes repository root: {path}")
    if not path.is_file():
        raise EditorialSemanticBoundaryError(f"missing file: {path}")
    return {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}


def resolve_ref(root: Path, binding: dict[str, Any], label: str) -> Path:
    if not isinstance(binding, dict):
        raise EditorialSemanticBoundaryError(f"{label} binding missing")
    raw = binding.get("path")
    if not isinstance(raw, str) or not raw:
        raise EditorialSemanticBoundaryError(f"{label}.path missing")
    path = Path(raw)
    if path.is_absolute():
        raise EditorialSemanticBoundaryError(f"{label}.path must be repository-relative")
    root = root.resolve()
    resolved = (root / path).resolve()
    if resolved != root and root not in resolved.parents:
        raise EditorialSemanticBoundaryError(f"{label}.path escapes repository root")
    if not resolved.is_file():
        raise EditorialSemanticBoundaryError(f"{label} missing: {raw}")
    actual = sha256_file(resolved)
    if binding.get("sha256") != actual:
        raise EditorialSemanticBoundaryError(
            f"{label}.sha256 mismatch: declared={binding.get('sha256')} actual={actual}"
        )
    return resolved


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise EditorialSemanticBoundaryError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _schema_resource(path: Path) -> tuple[str, Resource[Any]]:
    schema = load_json(path, f"schema {path}")
    schema_id = schema.get("$id")
    if not isinstance(schema_id, str) or not schema_id:
        raise EditorialSemanticBoundaryError(f"schema has no $id: {path}")
    return schema_id, Resource.from_contents(schema)


def daily_authoring_registry(root: Path) -> Registry[Any]:
    paths = (
        root / "skills/nasdaq-cafe-story-plan/contracts/story_plan.schema.json",
        root / "skills/nasdaq-cafe-story-authoring/contracts/story_script.schema.json",
        root / "skills/nasdaq-cafe-entertainment-critic/contracts/creative_review.schema.json",
    )
    registry: Registry[Any] = Registry()
    for path in paths:
        uri, resource = _schema_resource(path)
        registry = registry.with_resource(uri, resource)
    return registry


def validate_daily_authoring_schema(root: Path, authoring: dict[str, Any]) -> list[str]:
    schema_path = root / "contracts/chatgpt_daily_authoring_v2.schema.json"
    schema = load_json(schema_path, "Daily Authoring v2 schema")
    validator = Draft202012Validator(
        schema,
        registry=daily_authoring_registry(root),
        format_checker=FormatChecker(),
    )
    return [
        f"daily-authoring.{'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(authoring), key=lambda item: list(item.absolute_path))
    ]


def _expected_story_plan_ref(root: Path, date: str, story_plan: dict[str, Any]) -> dict[str, str]:
    return {
        "path": f"working/{date}/story-engine/story_plan.json",
        "sha256": projected_sha(story_plan),
    }


def verify_embedded_linkage(root: Path, date: str, authoring: dict[str, Any]) -> None:
    dossier = authoring["causalDossier"]
    dossier_ref = {"path": dossier["path"], "sha256": dossier["sha256"]}
    if authoring["storyPlan"].get("causal_dossier") != dossier_ref:
        raise EditorialSemanticBoundaryError("storyPlan.causal_dossier differs from canonical Dossier binding")
    expected_plan_ref = _expected_story_plan_ref(root, date, authoring["storyPlan"])
    if authoring["storyScript"].get("story_plan") != expected_plan_ref:
        raise EditorialSemanticBoundaryError(
            "storyScript.story_plan must bind the deterministic post-Freeze Story Plan projection"
        )
    if authoring["storyScript"].get("causal_dossier") != dossier_ref:
        raise EditorialSemanticBoundaryError("storyScript.causal_dossier differs from canonical Dossier binding")


def validate_production_alignment(authoring: dict[str, Any], dossier: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    plan_scenes = authoring["storyPlan"].get("scenes", [])
    script_scenes = authoring["storyScript"].get("scenes", [])
    production = authoring["production"]
    prod_scenes = production.get("scenes", [])
    if not (len(plan_scenes) == len(script_scenes) == len(prod_scenes) == 9):
        return ["Story Plan, Story Script, and production must each contain exactly 9 Scenes"]
    beat_count = sum(len(scene.get("beats", [])) for scene in prod_scenes if isinstance(scene, dict))
    if beat_count != 18:
        errors.append(f"production must contain exactly 18 Visual Beats; found={beat_count}")

    evidence_ids = {
        item.get("evidence_id")
        for item in dossier.get("evidence", [])
        if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
    }
    source_ids = {
        item.get("sourceId")
        for item in production.get("sources", [])
        if isinstance(item, dict) and isinstance(item.get("sourceId"), str)
    }
    for index, (plan_scene, script_scene, prod_scene) in enumerate(
        zip(plan_scenes, script_scenes, prod_scenes, strict=True), 1
    ):
        scene_id = f"scene-{index:02d}"
        if plan_scene.get("scene_id") != scene_id or script_scene.get("scene_id") != scene_id:
            errors.append(f"{scene_id}: Story Scene identity mismatch")
        if plan_scene.get("formal_role") != script_scene.get("formal_role"):
            errors.append(f"{scene_id}: Story formal roles differ")
        if plan_scene.get("connector") != script_scene.get("connection_to_previous"):
            errors.append(f"{scene_id}: Story connector differs between Plan and Script")
        if plan_scene.get("new_evidence_ids", []) != script_scene.get("evidence_ids", []):
            errors.append(f"{scene_id}: Story evidence IDs differ between Plan and Script")
        chunks = prod_scene.get("chunks")
        if not isinstance(chunks, list) or not chunks:
            errors.append(f"{scene_id}: production chunks missing")
        else:
            narration = "\n\n".join(
                str(chunk.get("text", "")) for chunk in chunks if isinstance(chunk, dict)
            )
            if narration != script_scene.get("narration"):
                errors.append(f"{scene_id}: production narration differs from canonical Story Script")
        for beat_index, beat in enumerate(prod_scene.get("beats", []), 1):
            beat_path = f"{scene_id}-beat-{beat_index:03d}"
            if not isinstance(beat, dict):
                errors.append(f"{scene_id} beat {beat_index}: invalid Beat object")
                continue
            for required in (
                "primaryFunction", "screenState", "visualMode", "visualTemplate",
                "contentType", "screenQuestion", "primaryElement", "viewerTexts",
                "changeCue", "grammarId", "transitionRole", "evidenceSourceIds",
            ):
                if required not in beat:
                    errors.append(f"{scene_id} beat {beat_index}: explicit {required} is required")
            try:
                remotion_template_variant.validate_pre_visual_intelligence_variant(
                    beat.get("visualTemplate"),
                    beat.get("variant"),
                    path=beat_path,
                )
            except remotion_template_variant.TemplateVariantError as exc:
                errors.append(str(exc))
            for evidence_id in beat.get("evidenceSourceIds", []):
                if evidence_id.startswith("E-") and evidence_id not in evidence_ids:
                    errors.append(f"{scene_id} beat {beat_index}: unknown evidence {evidence_id}")
                elif not evidence_id.startswith("E-") and source_ids and evidence_id not in source_ids:
                    errors.append(f"{scene_id} beat {beat_index}: unknown source {evidence_id}")
    return errors


def _projection_script(authoring: dict[str, Any], *, plan_ref: dict[str, str]) -> dict[str, Any]:
    script = copy.deepcopy(authoring["storyScript"])
    script["story_plan"] = plan_ref
    return script


def _write_validation_projections(root: Path, date: str, authoring: dict[str, Any]) -> tuple[Path, Path, Path]:
    directory = root / "verification" / date / "editorial-semantic-preflight"
    plan_path = directory / "story_plan.json"
    script_path = directory / "story_script.json"
    review_path = directory / "creative_review.json"
    atomic_write_bytes(plan_path, projected_bytes(authoring["storyPlan"]))
    preflight_plan_ref = repo_ref(root, plan_path)
    script_projection = _projection_script(authoring, plan_ref=preflight_plan_ref)
    atomic_write_bytes(script_path, projected_bytes(script_projection))
    atomic_write_bytes(review_path, projected_bytes(authoring["creativeReview"]))
    return plan_path, script_path, review_path


def _contract_binding(root: Path, role: str, relative: str) -> dict[str, str]:
    path = root / relative
    return {"role": role, **repo_ref(root, path)}


def contract_bindings(root: Path, dossier: dict[str, Any]) -> list[dict[str, str]]:
    dossier_schema = (
        "skills/nasdaq-cafe-causal-research/contracts/causal_research_dossier_v0.3.schema.json"
        if dossier.get("contract_version") == "0.3.0"
        else "skills/nasdaq-cafe-causal-research/contracts/causal_research_dossier_v0.2.schema.json"
    )
    pairs = [
        ("daily-authoring-schema", "contracts/chatgpt_daily_authoring_v2.schema.json"),
        ("semantic-acceptance-schema", "contracts/editorial_semantic_acceptance.schema.json"),
        ("dossier-schema", dossier_schema),
        ("dossier-receipt-schema", "skills/nasdaq-cafe-causal-research/contracts/causal_dossier_validation_receipt.schema.json"),
        ("dossier-validator", "skills/nasdaq-cafe-causal-research/validators/validate_causal_research_dossier.py"),
        ("dossier-receipt-verifier", "scripts/materialize_causal_research.py"),
        ("canon-manifest-verifier", "scripts/canon_manifest.py"),
        ("canon-manifest-schema", "contracts/canon_manifest.schema.json"),
        ("story-plan-schema", "skills/nasdaq-cafe-story-plan/contracts/story_plan.schema.json"),
        ("story-plan-validator", "skills/nasdaq-cafe-story-plan/validators/validate_story_plan.py"),
        ("story-script-schema", "skills/nasdaq-cafe-story-authoring/contracts/story_script.schema.json"),
        ("story-bundle-validator", "scripts/story-engine/validate_story_engine_bundle.py"),
        ("creative-review-schema", "skills/nasdaq-cafe-entertainment-critic/contracts/creative_review.schema.json"),
        ("template-variant-policy", "scripts/remotion_template_variant.py"),
        ("semantic-boundary-validator", "scripts/validate_editorial_semantic_boundary.py"),
    ]
    return [_contract_binding(root, role, path) for role, path in pairs]


def _validate_acceptance_schema(root: Path, acceptance: dict[str, Any]) -> list[str]:
    schema = load_json(root / "contracts/editorial_semantic_acceptance.schema.json", "acceptance schema")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"acceptance.{'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in validator.iter_errors(acceptance)
    ]


def validate_boundary(root: Path, date: str, authoring_path: Path) -> dict[str, Any]:
    root = root.resolve()
    authoring_path = authoring_path.resolve()
    authoring = load_json(authoring_path, "Canonical Daily Authoring v2")
    errors = validate_daily_authoring_schema(root, authoring)
    if errors:
        raise EditorialSemanticBoundaryError("; ".join(errors))
    if authoring.get("contractVersion") != "2.0.0" or authoring.get("episodeDate") != date:
        raise EditorialSemanticBoundaryError("Canonical Daily Authoring v2 contract/date mismatch")

    dossier_path = resolve_ref(
        root,
        {"path": authoring["causalDossier"]["path"], "sha256": authoring["causalDossier"]["sha256"]},
        "causalDossier",
    )
    receipt_path = resolve_ref(root, authoring["causalDossier"]["validation"], "causalDossier.validation")
    materialize_causal_research.verify_validation_receipt(root, date, receipt_path)
    dossier = load_json(dossier_path, "Causal Dossier")
    if dossier.get("episode_date") != date:
        raise EditorialSemanticBoundaryError("Causal Dossier episode_date mismatch")

    verify_embedded_linkage(root, date, authoring)
    alignment_errors = validate_production_alignment(authoring, dossier)
    if alignment_errors:
        raise EditorialSemanticBoundaryError("; ".join(alignment_errors))

    plan_path, script_path, review_path = _write_validation_projections(root, date, authoring)
    plan_validator = load_module(
        "editorial_boundary_story_plan_validator",
        root / "skills/nasdaq-cafe-story-plan/validators/validate_story_plan.py",
    )
    plan_result = plan_validator.validate_story_plan(
        plan_path,
        dossier_path,
        repo_root=root,
        schema_path=root / "skills/nasdaq-cafe-story-plan/contracts/story_plan.schema.json",
    )
    if not plan_result.ok:
        raise EditorialSemanticBoundaryError("Story Plan validation failed: " + "; ".join(plan_result.errors))

    bundle_validator = load_module(
        "editorial_boundary_story_bundle_validator",
        root / "scripts/story-engine/validate_story_engine_bundle.py",
    )
    bundle_result = bundle_validator.validate_bundle(
        script_path,
        plan_path,
        dossier_path,
        story_contracts_dir=root / "skills/nasdaq-cafe-story-authoring/contracts",
        critic_contracts_dir=root / "skills/nasdaq-cafe-entertainment-critic/contracts",
        repo_root=root,
        review_path=review_path,
    )
    if not bundle_result.ok:
        raise EditorialSemanticBoundaryError("Story/04 validation failed: " + "; ".join(bundle_result.errors))
    review = authoring["creativeReview"]
    if review.get("verdict") != "pass" or int(review.get("total_score", 0)) < 25:
        raise EditorialSemanticBoundaryError("Creative Review must PASS with score >=25")

    canon_manifest_module = load_module("editorial_boundary_canon_manifest", root / "scripts/canon_manifest.py")
    canon_binding = canon_manifest_module.manifest_binding(root, canon_manifest_module.DEFAULT_MANIFEST)

    acceptance = {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "status": "PASS",
        "authoring": {**repo_ref(root, authoring_path), "semanticSha256": canonical_sha(authoring)},
        "causalDossier": repo_ref(root, dossier_path),
        "causalDossierValidation": repo_ref(root, receipt_path),
        "canonManifest": canon_binding,
        "storySubdocuments": {
            "storyPlan": {"jsonPointer": "/storyPlan", "semanticSha256": canonical_sha(authoring["storyPlan"])},
            "storyScript": {"jsonPointer": "/storyScript", "semanticSha256": canonical_sha(authoring["storyScript"])},
            "creativeReview": {"jsonPointer": "/creativeReview", "semanticSha256": canonical_sha(authoring["creativeReview"])},
        },
        "validationProjections": {
            "storyPlan": repo_ref(root, plan_path),
            "storyScript": repo_ref(root, script_path),
            "creativeReview": repo_ref(root, review_path),
        },
        "contractBindings": contract_bindings(root, dossier),
        "errors": [],
    }
    acceptance_errors = _validate_acceptance_schema(root, acceptance)
    if acceptance_errors:
        raise EditorialSemanticBoundaryError("; ".join(acceptance_errors))
    return acceptance


def verify_acceptance(root: Path, date: str, acceptance_path: Path) -> dict[str, Any]:
    root = root.resolve()
    acceptance = load_json(acceptance_path, "Editorial Semantic Acceptance")
    if acceptance.get("status") != "PASS" or acceptance.get("episodeDate") != date:
        raise EditorialSemanticBoundaryError("Editorial Semantic Acceptance must PASS for the same episode")
    schema_errors = _validate_acceptance_schema(root, acceptance)
    if schema_errors:
        raise EditorialSemanticBoundaryError("; ".join(schema_errors))
    authoring_path = resolve_ref(root, acceptance["authoring"], "acceptance.authoring")
    authoring = load_json(authoring_path, "Canonical Daily Authoring v2")
    if acceptance["authoring"].get("semanticSha256") != canonical_sha(authoring):
        raise EditorialSemanticBoundaryError("acceptance.authoring semanticSha256 is stale")
    dossier_path = resolve_ref(root, acceptance["causalDossier"], "acceptance.causalDossier")
    receipt_path = resolve_ref(root, acceptance["causalDossierValidation"], "acceptance.causalDossierValidation")
    materialize_causal_research.verify_validation_receipt(root, date, receipt_path)
    canon_manifest_module = load_module("editorial_boundary_canon_manifest_verify", root / "scripts/canon_manifest.py")
    current_canon = canon_manifest_module.manifest_binding(root, canon_manifest_module.DEFAULT_MANIFEST)
    if acceptance.get("canonManifest") != current_canon:
        raise EditorialSemanticBoundaryError("Editorial Semantic Acceptance canonManifest is stale")
    story_bindings = acceptance["storySubdocuments"]
    for key, pointer in (("storyPlan", "/storyPlan"), ("storyScript", "/storyScript"), ("creativeReview", "/creativeReview")):
        binding = story_bindings[key]
        if binding.get("jsonPointer") != pointer or binding.get("semanticSha256") != canonical_sha(authoring[key]):
            raise EditorialSemanticBoundaryError(f"acceptance.storySubdocuments.{key} is stale")

    projections = acceptance.get("validationProjections", {})
    plan_projection_path = resolve_ref(root, projections["storyPlan"], "acceptance.validationProjections.storyPlan")
    script_projection_path = resolve_ref(root, projections["storyScript"], "acceptance.validationProjections.storyScript")
    review_projection_path = resolve_ref(root, projections["creativeReview"], "acceptance.validationProjections.creativeReview")
    projected_plan = load_json(plan_projection_path, "accepted Story Plan validation projection")
    projected_script = load_json(script_projection_path, "accepted Story Script validation projection")
    projected_review = load_json(review_projection_path, "accepted Creative Review validation projection")
    if projected_plan != authoring["storyPlan"]:
        raise EditorialSemanticBoundaryError("accepted Story Plan validation projection drifted")
    expected_script_projection = _projection_script(authoring, plan_ref=repo_ref(root, plan_projection_path))
    if projected_script != expected_script_projection:
        raise EditorialSemanticBoundaryError("accepted Story Script validation projection drifted")
    if projected_review != authoring["creativeReview"]:
        raise EditorialSemanticBoundaryError("accepted Creative Review validation projection drifted")

    dossier = load_json(dossier_path, "Causal Dossier")
    expected_bindings = contract_bindings(root, dossier)
    if acceptance.get("contractBindings") != expected_bindings:
        raise EditorialSemanticBoundaryError("Editorial Semantic Acceptance contractBindings are stale")
    return acceptance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--authoring", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    output = args.output or Path("verification") / args.date / "editorial_semantic_acceptance.json"
    output = output if output.is_absolute() else root / output
    try:
        if args.verify:
            verify_path = args.verify if args.verify.is_absolute() else root / args.verify
            acceptance = verify_acceptance(root, args.date, verify_path)
            payload = {"status": "PASS", "episodeDate": args.date, "acceptanceSha256": sha256_file(verify_path)}
        else:
            authoring = args.authoring or Path("daily-authoring") / f"{args.date}.json"
            authoring = authoring if authoring.is_absolute() else root / authoring
            acceptance = validate_boundary(root, args.date, authoring)
            atomic_write_json(output, acceptance)
            payload = {"status": "PASS", "episodeDate": args.date, "acceptance": output.relative_to(root).as_posix(), "acceptanceSha256": sha256_file(output)}
        code = 0
    except (OSError, EditorialSemanticBoundaryError, materialize_causal_research.ResearchMaterializationError) as exc:
        if not args.verify:
            failure = {
                "contractVersion": "1.0.0",
                "episodeDate": args.date,
                "status": "FAIL",
                "error": str(exc),
            }
            atomic_write_json(output, failure)
        payload = {"status": "FAIL", "episodeDate": args.date, "error": str(exc)}
        code = 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
