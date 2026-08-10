#!/usr/bin/env python3
"""Freeze selected financial visuals across production artifacts.

The Final Episode Contract and Financial Recipe Plan are already approved and
validated. This step applies only the selected Candidate Plan to the derived
render spec, verifies spoken/asset/preflight consistency, requires an explicit
post-fallback diversity report when needed, and updates the official preflight.
It never changes narration, editorial causality, or creates a new fallback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator

import final_episode_contract as final_contract_module
import financial_recipe_compiler as recipe_compiler


class CrossArtifactError(ValueError):
    pass


APPROVED_COMPATIBILITY_MATRICES = {
    "2.3.0": {
        "matrixId": "financial-visual-compat-2026-08",
        "status": "pass",
        "plotCreator": {
            "repository": "saienjoy0/nasdaq-plot-creator-",
            "financialIntentVersion": "1.1.0",
            "financialRecipePlanVersion": "1.0.0",
            "finalEpisodeContractVersion": "1.0.0",
        },
        "renderer": {
            "repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion",
            "renderSpecVersion": "2.3.0",
            "financialTemplateRegistryVersion": "1.0.0",
            "financialVisualTraceVersion": "1.0.0",
        },
    },
    "2.4.0": {
        "matrixId": "financial-visual-compat-2026-08",
        "status": "pass",
        "plotCreator": {
            "repository": "saienjoy0/nasdaq-plot-creator-",
            "financialIntentVersion": "1.1.0",
            "financialRecipePlanVersion": "1.0.0",
            "finalEpisodeContractVersion": "1.0.0",
        },
        "renderer": {
            "repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion",
            "renderSpecVersion": "2.4.0",
            "financialTemplateRegistryVersion": "1.0.0",
            "financialVisualTraceVersion": "1.0.0",
        },
    },
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CrossArtifactError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CrossArtifactError(
            f"{label} invalid JSON at {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise CrossArtifactError(f"{label} root must be an object")
    return value


def load_schema(path: Path) -> dict[str, Any]:
    return load_json(path, "schema")


def validate_compatibility_matrix(
    path: Path,
    renderer_schema_version: str,
) -> tuple[dict[str, Any], str]:
    matrix = load_json(path, "financial visual compatibility matrix")
    approved = APPROVED_COMPATIBILITY_MATRICES.get(renderer_schema_version)
    if approved is None:
        raise CrossArtifactError(
            f"unsupported renderer schema version for financial visual compatibility: {renderer_schema_version}"
        )
    if matrix != approved:
        raise CrossArtifactError(
            "financial visual compatibility matrix does not exactly match the approved cross-repository tuple"
        )
    if matrix["renderer"]["renderSpecVersion"] != renderer_schema_version:
        raise CrossArtifactError(
            "renderer schema version disagrees with financial visual compatibility matrix"
        )
    return matrix, sha256_file(path)


def validate_schema(payload: dict[str, Any], schema: dict[str, Any], label: str) -> None:
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda e: list(e.path))
    if not errors:
        return
    messages = []
    for error in errors:
        location = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path
        )
        messages.append(f"{label}{location}: {error.message}")
    raise CrossArtifactError("\n".join(messages))


def safe_relative(root: Path, path: Path, label: str) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise CrossArtifactError(f"{label} must be inside repository root: {path}") from exc


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def _selection_map(recipe_plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    selections = recipe_plan.get("selections", [])
    result = {selection["intentId"]: selection for selection in selections}
    if len(result) != len(selections):
        raise CrossArtifactError("recipe plan intent selections must be unique")
    return result


def _candidate_map(final_contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    plans = final_contract["financialVisuals"]["candidatePlans"]
    result = {plan["planId"]: plan for plan in plans}
    if len(result) != len(plans):
        raise CrossArtifactError("candidate plan IDs must be unique")
    return result


def _intent_map(final_contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    intents = final_contract["financialVisuals"]["intents"]
    result = {intent["intentId"]: intent for intent in intents}
    if len(result) != len(intents):
        raise CrossArtifactError("intent IDs must be unique")
    return result


def _episode_beat_map(final_contract: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for scene in final_contract["scenes"]:
        for beat in scene["visualBeats"]:
            key = (scene["sceneId"], beat["visualBeatId"])
            if key in result:
                raise CrossArtifactError(f"duplicate Final Episode Visual Beat: {key}")
            result[key] = beat
    return result


def _render_beat_map(render_spec: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for scene in render_spec.get("scenes", []):
        scene_id = scene.get("sceneId")
        for beat in scene.get("visualBeats", []):
            beat_id = beat.get("beatId")
            if isinstance(scene_id, str) and isinstance(beat_id, str):
                key = (scene_id, beat_id)
                if key in result:
                    raise CrossArtifactError(f"duplicate render Visual Beat: {key}")
                result[key] = beat
    return result


def _resolve_public_fields(
    episode_beat: dict[str, Any], selected_path: str
) -> tuple[str, str, str, str, str]:
    if selected_path == "preferred":
        headline = episode_beat["headline"]
        question = episode_beat["screenQuestion"]
    else:
        headline = episode_beat["fallbackHeadline"]
        question = episode_beat["fallbackQuestion"]
    return (
        headline,
        question,
        episode_beat["startCue"],
        episode_beat["endCue"],
        episode_beat["returnTarget"],
    )


def _remove_non_selected_metadata(beat: dict[str, Any]) -> None:
    for key in (
        "candidatePlans", "preferredPlan", "fallbackPlan", "preferredPlanId",
        "fallbackPlanId", "unselectedPlan", "financialVisualIntent"
    ):
        beat.pop(key, None)


def apply_selected_plans(
    final_contract: dict[str, Any],
    recipe_plan: dict[str, Any],
    recipe_plan_sha: str,
    render_spec: dict[str, Any],
    renderer_schema_version: str,
) -> list[dict[str, Any]]:
    intent_map = _intent_map(final_contract)
    candidate_map = _candidate_map(final_contract)
    episode_beats = _episode_beat_map(final_contract)
    render_beats = _render_beat_map(render_spec)
    selections = _selection_map(recipe_plan)
    if set(selections) != set(intent_map):
        raise CrossArtifactError(
            f"recipe plan must select every intent exactly once: missing={sorted(set(intent_map)-set(selections))} extra={sorted(set(selections)-set(intent_map))}"
        )

    traces: list[dict[str, Any]] = []
    for intent_id in sorted(intent_map):
        intent = intent_map[intent_id]
        selection = selections[intent_id]
        selected_plan = candidate_map.get(selection["selectedPlanId"])
        if selected_plan is None:
            raise CrossArtifactError(f"selected Candidate Plan not found: {selection['selectedPlanId']}")
        actual_plan_sha = canonical_sha256(selected_plan)
        if actual_plan_sha != selection["selectedPlanSha256"]:
            raise CrossArtifactError(f"selected Candidate Plan SHA mismatch: {intent_id}")
        expected_plan_id = (
            intent["preferredPlanId"]
            if selection["selectedPath"] == "preferred"
            else intent["fallbackPlanId"]
        )
        if selection["selectedPlanId"] != expected_plan_id:
            raise CrossArtifactError(f"selected path/plan mismatch: {intent_id}")
        target = intent["target"]
        key = (target["sceneId"], target["visualBeatId"])
        if key != (selection["sceneId"], selection["visualBeatId"]):
            raise CrossArtifactError(f"selection target mismatch: {intent_id}")
        episode_beat = episode_beats.get(key)
        render_beat = render_beats.get(key)
        if episode_beat is None or render_beat is None:
            raise CrossArtifactError(f"target Scene/Visual Beat missing from artifacts: {key}")

        for field, selected_field in (
            ("recipeId", "selectedRecipeId"),
            ("visualTemplateId", "selectedVisualTemplateId"),
            ("templateVariant", "templateVariant"),
            ("screenState", "screenState"),
        ):
            if selected_plan[field] != selection[selected_field]:
                raise CrossArtifactError(f"selected plan/recipe plan {field} mismatch: {intent_id}")
        for field in ("sourceIds", "metricIds", "causalStepIds"):
            if selected_plan[field] != selection[field]:
                raise CrossArtifactError(f"selected plan/recipe plan {field} mismatch: {intent_id}")

        headline, question, start_cue, end_cue, return_target = _resolve_public_fields(
            episode_beat, selection["selectedPath"]
        )
        _remove_non_selected_metadata(render_beat)
        render_beat["screenState"] = selection["screenState"]
        render_beat["visualTemplate"] = selection["selectedVisualTemplateId"]
        render_beat["templateVariant"] = selection["templateVariant"]
        causal_step_ids = selection["causalStepIds"]
        render_beat["templateConfig"] = {
            "variant": selection["templateVariant"],
            "comparisonBasis": selected_plan["comparisonBasis"],
            "dataBasis": "financial-recipe-plan",
            "nodeOrder": causal_step_ids[:4],
            "laneLabels": [],
            "outcomeNodeId": causal_step_ids[-1] if causal_step_ids else None,
            "displayOrder": selected_plan["displayOrder"],
            "metricIds": selection["metricIds"],
            "causalStepIds": causal_step_ids,
            "highlightObjectIds": selected_plan["highlightObjectIds"],
        }
        render_beat["objectIds"] = selected_plan["displayOrder"]
        render_beat["evidenceSourceIds"] = selection["sourceIds"]
        render_beat["narrationStartCue"] = start_cue
        render_beat["narrationEndCue"] = end_cue
        render_beat["screenQuestion"] = question
        render_beat["primaryElement"] = headline
        render_beat["financialReturnTarget"] = return_target
        trace = {
            "contractVersion": "1.0.0",
            "intentId": intent_id,
            "selectedPlanId": selection["selectedPlanId"],
            "selectedPlanSha256": selection["selectedPlanSha256"],
            "selectedPath": selection["selectedPath"],
            "recipeId": selection["selectedRecipeId"],
            "recipePlanSha256": recipe_plan_sha,
            "finalEpisodeContractSha256": recipe_plan["finalEpisodeContract"]["sha256"],
            "sourceIds": selection["sourceIds"],
            "metricIds": selection["metricIds"],
            "causalStepIds": selection["causalStepIds"],
            "displayOrder": selected_plan["displayOrder"],
            "comparisonBasis": selected_plan["comparisonBasis"],
            "reasonCodes": selection["reasonCodes"],
        }
        render_beat["financialVisualTrace"] = trace
        traces.append({"sceneId": key[0], "visualBeatId": key[1], **trace})

    render_spec["schemaVersion"] = renderer_schema_version
    render_spec["financialVisualContract"] = {
        "contractVersion": "1.0.0",
        "intentVersion": recipe_plan["intentContractVersion"],
        "recipePlanVersion": recipe_plan["contractVersion"],
        "recipeRegistryVersion": recipe_plan["recipeRegistryVersion"],
        "finalEpisodeContractVersion": final_contract["contractVersion"],
        "recipePlanSha256": recipe_plan_sha,
        "selectionCount": len(traces),
    }
    return traces


def validate_diversity(
    diversity_path: Path | None,
    recipe_plan: dict[str, Any],
    recipe_plan_sha: str,
    schema: dict[str, Any],
) -> tuple[str, dict[str, Any] | None]:
    fallback_count = sum(
        selection["selectedPath"] == "fallback" for selection in recipe_plan["selections"]
    )
    if fallback_count == 0:
        if diversity_path is not None:
            raise CrossArtifactError("diversity report must be omitted when fallback is not selected")
        return "not-required", None
    if diversity_path is None:
        raise CrossArtifactError("fallback selection requires a post-fallback diversity report")
    report = load_json(diversity_path, "diversity report")
    validate_schema(report, schema, "diversity report")
    if report["episodeDate"] != recipe_plan["episodeDate"]:
        raise CrossArtifactError("diversity report episodeDate mismatch")
    if report["recipePlanSha256"] != recipe_plan_sha:
        raise CrossArtifactError("diversity report recipePlanSha256 mismatch")
    return "pass", report


def verify_spoken_script(render_spec: dict[str, Any], spoken: str) -> None:
    expected = [
        chunk["speechText"]
        for scene in render_spec.get("scenes", [])
        for chunk in scene.get("narrationChunks", [])
    ]
    for speech in expected:
        if spoken.count(speech) != 1:
            raise CrossArtifactError(
                f"spoken script must contain each render speech exactly once: {speech!r}"
            )


def verify_asset_manifest(asset_manifest: dict[str, Any], date: str) -> None:
    if asset_manifest.get("episode_date") != date:
        raise CrossArtifactError("asset manifest episode date mismatch")
    if asset_manifest.get("selected_path") not in {"primary", "fallback", "not-required"}:
        raise CrossArtifactError("asset manifest selected path is unresolved")
    ids = [item.get("asset_id") for item in asset_manifest.get("assets", [])]
    if len(ids) != len(set(ids)):
        raise CrossArtifactError("asset manifest contains duplicate asset IDs")


def _artifact_paths(production_root: Path, date: str) -> dict[str, Path]:
    return {
        "spoken_script": production_root / "episodes" / date / f"spoken_script_{date}.md",
        "asset_manifest": production_root / "episodes" / date / "asset_manifest.json",
        "render_spec": production_root / "render-specs" / date / "render_spec.json",
        "consistency_report": production_root / "verification" / date / "production_consistency_report.json",
        "preflight": production_root / "verification" / date / "official_execution_preflight.json",
        "cross_report": production_root / "verification" / date / "financial_visual_consistency_report.json",
    }


def integrate(
    *,
    final_contract_path: Path,
    recipe_plan_path: Path,
    repo_root: Path,
    production_root: Path,
    renderer_schema_version: str,
    final_schema_path: Path,
    candidate_schema_path: Path,
    registry_path: Path,
    recipe_plan_schema_path: Path,
    diversity_schema_path: Path,
    consistency_schema_path: Path,
    diversity_report_path: Path | None = None,
    compatibility_matrix_path: Path | None = None,
    final_contract_validator: Callable[..., Any] | None = None,
    recipe_plan_compiler: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    validate_final = final_contract_validator or final_contract_module.validate_contract
    compile_plan = recipe_plan_compiler or recipe_compiler.compile_recipe_plan
    validate_final(
        final_contract_path,
        repo_root,
        final_schema_path,
        candidate_schema_path,
    )
    expected_recipe_plan = compile_plan(
        final_contract_path,
        repo_root,
        registry_path,
        recipe_plan_schema_path,
        final_schema_path,
        candidate_schema_path,
    )
    actual_recipe_plan = load_json(recipe_plan_path, "financial recipe plan")
    if actual_recipe_plan != expected_recipe_plan:
        raise CrossArtifactError("financial recipe plan is stale or differs from deterministic compilation")

    final_contract = load_json(final_contract_path, "final episode contract")
    recipe_plan_sha = sha256_file(recipe_plan_path)
    if actual_recipe_plan["finalEpisodeContract"]["sha256"] != sha256_file(final_contract_path):
        raise CrossArtifactError("recipe plan Final Episode Contract SHA mismatch")
    if actual_recipe_plan["episodePackageSha256"] != final_contract["episodePackage"]["sha256"]:
        raise CrossArtifactError("recipe plan Episode Package SHA mismatch")

    date = final_contract["episodeDate"]
    if actual_recipe_plan["episodeDate"] != date:
        raise CrossArtifactError("episode date mismatch between Final Contract and Recipe Plan")
    compatibility_matrix_path = compatibility_matrix_path or (
        repo_root / "contracts" / "financial_visual_compatibility.json"
    )
    compatibility_matrix, compatibility_matrix_sha = validate_compatibility_matrix(
        compatibility_matrix_path,
        renderer_schema_version,
    )
    paths = _artifact_paths(production_root, date)
    render_spec = load_json(paths["render_spec"], "render spec")
    spoken = paths["spoken_script"].read_text(encoding="utf-8")
    asset_manifest = load_json(paths["asset_manifest"], "asset manifest")
    consistency = load_json(paths["consistency_report"], "production consistency report")
    preflight = load_json(paths["preflight"], "official execution preflight")
    if consistency.get("status") != "pass" or consistency.get("unresolved_states") != 0:
        raise CrossArtifactError("base production consistency report must pass")
    if preflight.get("status") != "pass" or preflight.get("unresolved_states") != 0:
        raise CrossArtifactError("base preflight must pass")
    if preflight.get("episode_date") != date:
        raise CrossArtifactError("preflight episode date mismatch")
    if render_spec.get("episode", {}).get("targetDate") != date:
        raise CrossArtifactError("render spec episode date mismatch")

    diversity_status, _ = validate_diversity(
        diversity_report_path,
        actual_recipe_plan,
        recipe_plan_sha,
        load_schema(diversity_schema_path),
    )
    traces = apply_selected_plans(
        final_contract,
        actual_recipe_plan,
        recipe_plan_sha,
        render_spec,
        renderer_schema_version,
    )
    verify_spoken_script(render_spec, spoken)
    verify_asset_manifest(asset_manifest, date)

    write_atomic(paths["render_spec"], canonical_json(render_spec))
    render_sha = sha256_file(paths["render_spec"])

    consistency["financial_visuals"] = {
        "status": "pass",
        "final_episode_contract_sha256": sha256_file(final_contract_path),
        "financial_recipe_plan_sha256": recipe_plan_sha,
        "render_spec_sha256": render_sha,
        "selection_count": len(traces),
        "fallback_count": sum(trace["selectedPath"] == "fallback" for trace in traces),
        "fallback_diversity": diversity_status,
        "compatibility_matrix_id": compatibility_matrix["matrixId"],
        "compatibility_matrix_sha256": compatibility_matrix_sha,
        "unresolved_states": 0,
    }
    consistency["status"] = "pass"
    consistency["unresolved_states"] = 0
    write_atomic(paths["consistency_report"], canonical_json(consistency))
    consistency_sha = sha256_file(paths["consistency_report"])

    fallback_count = sum(trace["selectedPath"] == "fallback" for trace in traces)
    report = {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "status": "pass",
        "finalEpisodeContract": {
            "path": safe_relative(repo_root, final_contract_path, "Final Episode Contract"),
            "sha256": sha256_file(final_contract_path),
        },
        "financialRecipePlan": {
            "path": safe_relative(repo_root, recipe_plan_path, "Financial Recipe Plan"),
            "sha256": recipe_plan_sha,
        },
        "compatibilityMatrix": {
            "path": safe_relative(repo_root, compatibility_matrix_path, "Compatibility Matrix"),
            "sha256": compatibility_matrix_sha,
        },
        "episodePackageSha256": final_contract["episodePackage"]["sha256"],
        "renderSpec": {
            "path": safe_relative(production_root, paths["render_spec"], "render spec"),
            "sha256": render_sha,
        },
        "spokenScript": {
            "path": safe_relative(production_root, paths["spoken_script"], "spoken script"),
            "sha256": sha256_file(paths["spoken_script"]),
        },
        "assetManifest": {
            "path": safe_relative(production_root, paths["asset_manifest"], "asset manifest"),
            "sha256": sha256_file(paths["asset_manifest"]),
        },
        "selectionCount": len(traces),
        "fallbackCount": fallback_count,
        "fallbackDiversity": diversity_status,
        "checks": {
            "episodeDate": True,
            "episodePackageSha": True,
            "selectedPlanSha": True,
            "sceneBeat": True,
            "cueText": True,
            "screenState": True,
            "visualTemplate": True,
            "templateVariant": True,
            "objectIds": True,
            "sourceIds": True,
            "displayOrder": True,
            "comparisonBasis": True,
            "compatibilityMatrix": True,
            "selectedPathFreeze": True,
            "nonSelectedPathAbsent": True,
            "spokenScript": True,
            "assetManifest": True,
            "preflight": True,
        },
        "errors": [],
        "unresolvedStates": 0,
    }
    validate_schema(report, load_schema(consistency_schema_path), "consistency report")
    write_atomic(paths["cross_report"], canonical_json(report))
    cross_report_sha = sha256_file(paths["cross_report"])

    artifacts = preflight.setdefault("artifacts", {})
    artifacts["render_spec"] = render_sha
    artifacts["consistency_report"] = consistency_sha
    artifacts["final_episode_contract"] = sha256_file(final_contract_path)
    artifacts["financial_recipe_plan"] = recipe_plan_sha
    artifacts["financial_visual_compatibility"] = compatibility_matrix_sha
    artifacts["financial_visual_consistency_report"] = cross_report_sha
    if diversity_report_path is not None:
        artifacts["financial_visual_diversity_report"] = sha256_file(diversity_report_path)
    preflight["financial_visuals"] = {
        "status": "pass",
        "renderer_schema_version": renderer_schema_version,
        "intent_contract_version": actual_recipe_plan["intentContractVersion"],
        "recipe_plan_version": actual_recipe_plan["contractVersion"],
        "final_episode_contract_version": final_contract["contractVersion"],
        "recipe_registry_version": actual_recipe_plan["recipeRegistryVersion"],
        "compatibility_matrix_id": compatibility_matrix["matrixId"],
        "compatibility_matrix_sha256": compatibility_matrix_sha,
        "recipe_plan_sha256": recipe_plan_sha,
        "consistency_report_sha256": cross_report_sha,
        "selection_count": len(traces),
        "fallback_count": fallback_count,
        "fallback_diversity": diversity_status,
        "unresolved_states": 0,
    }
    preflight["preview_authorized"] = True
    preflight["final_authorized"] = False
    preflight["unresolved_states"] = 0
    write_atomic(paths["preflight"], canonical_json(preflight))

    return {
        "status": "pass",
        "episodeDate": date,
        "selectionCount": len(traces),
        "fallbackCount": fallback_count,
        "fallbackDiversity": diversity_status,
        "rendererSchemaVersion": renderer_schema_version,
        "paths": {key: str(value) for key, value in paths.items()},
        "hashes": {
            "render_spec": render_sha,
            "consistency_report": consistency_sha,
            "financial_visual_consistency_report": cross_report_sha,
            "compatibility_matrix": compatibility_matrix_sha,
            "preflight": sha256_file(paths["preflight"]),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final-contract", required=True, type=Path)
    parser.add_argument("--recipe-plan", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--production-root", required=True, type=Path)
    parser.add_argument("--renderer-schema-version", default="2.3.0")
    parser.add_argument("--diversity-report", type=Path)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--final-schema", type=Path, default=root / "contracts/final_episode_contract.schema.json")
    parser.add_argument("--candidate-schema", type=Path, default=root / "contracts/financial_visual_candidate_plan.schema.json")
    parser.add_argument("--registry", type=Path, default=root / "contracts/financial_recipe_registry.json")
    parser.add_argument("--recipe-plan-schema", type=Path, default=root / "contracts/financial_recipe_plan.schema.json")
    parser.add_argument("--diversity-schema", type=Path, default=root / "contracts/financial_visual_diversity_report.schema.json")
    parser.add_argument("--consistency-schema", type=Path, default=root / "contracts/financial_visual_consistency_report.schema.json")
    parser.add_argument("--compatibility-matrix", type=Path, default=root / "contracts/financial_visual_compatibility.json")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = integrate(
            final_contract_path=args.final_contract,
            recipe_plan_path=args.recipe_plan,
            repo_root=args.repo_root,
            production_root=args.production_root,
            renderer_schema_version=args.renderer_schema_version,
            final_schema_path=args.final_schema,
            candidate_schema_path=args.candidate_schema,
            registry_path=args.registry,
            recipe_plan_schema_path=args.recipe_plan_schema,
            diversity_schema_path=args.diversity_schema,
            consistency_schema_path=args.consistency_schema,
            diversity_report_path=args.diversity_report,
            compatibility_matrix_path=args.compatibility_matrix,
        )
        code = 0
    except (CrossArtifactError, final_contract_module.ContractError, recipe_compiler.CompileError, OSError) as exc:
        result = {"status": "fail", "errors": str(exc).splitlines()}
        code = 2
    text = canonical_json(result)
    if args.report:
        write_atomic(args.report, text)
    else:
        sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
