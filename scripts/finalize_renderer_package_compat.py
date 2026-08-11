#!/usr/bin/env python3
"""Finalize production with split Visual Grammar 1.1 and Financial 1.0 lineage.

The compatibility finalizer is transactional at the official artifact boundary: all
Financial Visual projection, Remotion 2.4 canonicalization, referential integrity,
and the pinned Renderer validator must pass before mutated production artifacts are
allowed to remain. On failure, every touched official artifact is restored byte-for-byte.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import finalize_renderer_package as base
import financial_final_episode_contract_1_0 as financial_contract_v1
import financial_recipe_compiler as recipe_compiler
import financial_visual_cross_artifact
import remotion_240_projection
import remotion_sequence_policy
import remotion_template_data
import visual_director_bridge


class CompatibilityFinalizationError(ValueError):
    pass


def _validator_adapter(
    contract_path: Path,
    repo_root: Path,
    final_schema_path: Path,
    candidate_schema_path: Path,
    *args,
):
    del final_schema_path, args
    return financial_contract_v1.validate_contract(
        contract_path,
        repo_root,
        candidate_schema_path,
    )


def _compile_recipe_plan_adapter(
    final_contract_path: Path,
    repo_root: Path,
    registry_path: Path,
    recipe_plan_schema_path: Path,
    final_schema_path: Path,
    candidate_schema_path: Path,
) -> dict[str, Any]:
    """Compile Financial 1.0 deterministically without mutating imported modules."""
    _validator_adapter(
        final_contract_path,
        repo_root,
        final_schema_path,
        candidate_schema_path,
    )
    contract = recipe_compiler.load_json(final_contract_path)
    registry = recipe_compiler.load_json(registry_path)
    recipe_plan_schema = recipe_compiler.load_json(recipe_plan_schema_path)
    recipe_compiler._validate_registry(registry)

    visuals = contract["financialVisuals"]
    plan_map = {plan["planId"]: plan for plan in visuals["candidatePlans"]}
    selections: list[dict[str, Any]] = []
    for intent in visuals["intents"]:
        preferred = plan_map[intent["preferredPlanId"]]
        fallback = plan_map[intent["fallbackPlanId"]]
        preferred_reasons = recipe_compiler.plan_reasons(
            intent, preferred, registry, fallback=False
        )
        fallback_reasons = recipe_compiler.plan_reasons(
            intent, fallback, registry, fallback=True
        )
        if fallback_reasons:
            raise recipe_compiler.CompileError(
                f"FALLBACK_PLAN_INVALID:{intent['intentId']}:"
                + ",".join(fallback_reasons)
            )
        if preferred_reasons:
            selected = fallback
            selected_path = "fallback"
            eligibility = "fallback-required"
            reason_codes = recipe_compiler._unique(preferred_reasons)
            diversity = "required"
        else:
            selected = preferred
            selected_path = "preferred"
            eligibility = "eligible"
            reason_codes = []
            diversity = "not-required"
        target = intent["target"]
        selections.append(
            {
                "intentId": intent["intentId"],
                "sceneId": target["sceneId"],
                "visualBeatId": target["visualBeatId"],
                "eligibility": eligibility,
                "selectedPath": selected_path,
                "selectedPlanId": selected["planId"],
                "selectedPlanSha256": recipe_compiler.canonical_sha256(selected),
                "selectedRecipeId": selected["recipeId"],
                "selectedVisualTemplateId": selected["visualTemplateId"],
                "templateVariant": selected["templateVariant"],
                "screenState": selected["screenState"],
                "sourceIds": selected["sourceIds"],
                "metricIds": selected["metricIds"],
                "causalStepIds": selected["causalStepIds"],
                "reasonCodes": reason_codes,
                "fallbackDiversityRecheck": diversity,
            }
        )

    try:
        relative_contract_path = (
            final_contract_path.resolve().relative_to(repo_root.resolve()).as_posix()
        )
    except ValueError as exc:
        raise recipe_compiler.CompileError(
            "final contract path must be inside repo root"
        ) from exc
    output = {
        "contractVersion": "1.0.0",
        "episodeDate": contract["episodeDate"],
        "finalEpisodeContract": {
            "path": relative_contract_path,
            "sha256": recipe_compiler.file_sha256(final_contract_path),
        },
        "episodePackageSha256": contract["episodePackage"]["sha256"],
        "intentContractVersion": "1.1.0",
        "recipeRegistryVersion": registry["registryVersion"],
        "selections": selections,
    }
    recipe_compiler._validate_recipe_plan(output, recipe_plan_schema)
    return output


def _integrate_financial_visuals(
    *,
    output_root: Path,
    financial_contract_path: Path,
    recipe_plan_path: Path,
) -> dict[str, Any]:
    return financial_visual_cross_artifact.integrate(
        final_contract_path=financial_contract_path,
        recipe_plan_path=recipe_plan_path,
        repo_root=output_root,
        production_root=output_root,
        renderer_schema_version="2.4.0",
        final_schema_path=(
            output_root / "contracts/final_episode_contract.schema.json"
        ),
        candidate_schema_path=(
            output_root / "contracts/financial_visual_candidate_plan.schema.json"
        ),
        registry_path=(output_root / "contracts/financial_recipe_registry.json"),
        recipe_plan_schema_path=(
            output_root / "contracts/financial_recipe_plan.schema.json"
        ),
        diversity_schema_path=(
            output_root / "contracts/financial_visual_diversity_report.schema.json"
        ),
        consistency_schema_path=(
            output_root / "contracts/financial_visual_consistency_report.schema.json"
        ),
        diversity_report_path=None,
        compatibility_matrix_path=(
            output_root / "contracts/financial_visual_compatibility_2_4.json"
        ),
        final_contract_validator=_validator_adapter,
        recipe_plan_compiler=_compile_recipe_plan_adapter,
    )


def _validate_referential_integrity(render: dict[str, Any]) -> None:
    """Mirror the pinned Renderer's identifier checks before official validation."""
    source_ids = {
        item.get("sourceId")
        for item in render.get("sources", [])
        if isinstance(item, dict) and isinstance(item.get("sourceId"), str)
    }
    scene_ids: set[str] = set()
    beat_ids: set[str] = set()
    event_ids: set[str] = set()

    def require_sources(ids: list[Any], path: str) -> None:
        for index, source_id in enumerate(ids):
            if source_id not in source_ids:
                raise CompatibilityFinalizationError(
                    f"{path}[{index}]: unknown sourceId: {source_id}"
                )

    editorial = render.get("editorial")
    if isinstance(editorial, dict):
        require_sources(
            list(editorial.get("expectedSourceIds", [])),
            "$.editorial.expectedSourceIds",
        )

    for scene_index, scene in enumerate(render.get("scenes", [])):
        base_path = f"$.scenes[{scene_index}]"
        scene_id = scene.get("sceneId")
        if not isinstance(scene_id, str) or not scene_id:
            raise CompatibilityFinalizationError(f"{base_path}.sceneId: missing")
        if scene_id in scene_ids:
            raise CompatibilityFinalizationError(
                f"{base_path}.sceneId: duplicate ID: {scene_id}"
            )
        scene_ids.add(scene_id)
        require_sources(
            list(scene.get("evidenceSourceIds", [])),
            f"{base_path}.evidenceSourceIds",
        )

        chunk_ids = [item.get("chunkId") for item in scene.get("narrationChunks", [])]
        if any(not isinstance(item, str) or not item for item in chunk_ids):
            raise CompatibilityFinalizationError(
                f"{base_path}.narrationChunks: every chunkId must be non-empty"
            )
        if len(chunk_ids) != len(set(chunk_ids)):
            raise CompatibilityFinalizationError(
                f"{base_path}.narrationChunks: duplicate chunkId"
            )
        chunks = set(chunk_ids)
        card_ids = [item.get("cardId") for item in scene.get("cards", [])]
        number_ids = [item.get("numberId") for item in scene.get("numbers", [])]
        node_ids = [item.get("nodeId") for item in scene.get("nodes", [])]
        arrow_ids = [item.get("arrowId") for item in scene.get("arrows", [])]
        placement_ids = [
            item.get("placementId") for item in scene.get("assetPlacements", [])
        ]
        all_ids = [*card_ids, *number_ids, *node_ids, *arrow_ids, *placement_ids]
        if any(not isinstance(item, str) or not item for item in all_ids):
            raise CompatibilityFinalizationError(
                f"{base_path}.objects: every object ID must be non-empty"
            )
        if len(all_ids) != len(set(all_ids)):
            raise CompatibilityFinalizationError(
                f"{base_path}.objects: duplicate object ID"
            )
        nodes = set(node_ids)
        object_targets = set([*card_ids, *number_ids, *node_ids, *arrow_ids])
        visibility_targets = set([*object_targets, *placement_ids])
        placements = set(placement_ids)

        for arrow_index, arrow in enumerate(scene.get("arrows", [])):
            for field in ("fromNodeId", "toNodeId"):
                target = arrow.get(field)
                if target not in nodes:
                    raise CompatibilityFinalizationError(
                        f"{base_path}.arrows[{arrow_index}].{field}: unknown nodeId: {target}"
                    )

        for event_index, event in enumerate(scene.get("visualEvents", [])):
            event_id = event.get("eventId")
            if not isinstance(event_id, str) or not event_id:
                raise CompatibilityFinalizationError(
                    f"{base_path}.visualEvents[{event_index}].eventId: missing"
                )
            if event_id in event_ids:
                raise CompatibilityFinalizationError(
                    f"{base_path}.visualEvents[{event_index}].eventId: duplicate ID: {event_id}"
                )
            event_ids.add(event_id)
            at_chunk = event.get("atChunkId")
            if at_chunk not in chunks:
                raise CompatibilityFinalizationError(
                    f"{base_path}.visualEvents[{event_index}].atChunkId: unknown chunkId: {at_chunk}"
                )
            if event.get("action") == "set-expression":
                continue
            target_id = event.get("targetId")
            targets = (
                visibility_targets
                if event.get("action") in {"show", "hide"}
                else object_targets
            )
            if target_id not in targets:
                raise CompatibilityFinalizationError(
                    f"{base_path}.visualEvents[{event_index}].targetId: unknown object ID: {target_id}"
                )

        for beat_index, beat in enumerate(scene.get("visualBeats", [])):
            beat_path = f"{base_path}.visualBeats[{beat_index}]"
            beat_id = beat.get("beatId")
            if not isinstance(beat_id, str) or not beat_id:
                raise CompatibilityFinalizationError(f"{beat_path}.beatId: missing")
            if beat_id in beat_ids:
                raise CompatibilityFinalizationError(
                    f"{beat_path}.beatId: duplicate ID: {beat_id}"
                )
            beat_ids.add(beat_id)
            if beat.get("startChunkId") not in chunks:
                raise CompatibilityFinalizationError(
                    f"{beat_path}.startChunkId: unknown chunkId: {beat.get('startChunkId')}"
                )
            if beat.get("endChunkId") not in chunks:
                raise CompatibilityFinalizationError(
                    f"{beat_path}.endChunkId: unknown chunkId: {beat.get('endChunkId')}"
                )
            require_sources(
                list(beat.get("evidenceSourceIds", [])),
                f"{beat_path}.evidenceSourceIds",
            )
            for object_index, object_id in enumerate(beat.get("objectIds", [])):
                if object_id not in object_targets:
                    raise CompatibilityFinalizationError(
                        f"{beat_path}.objectIds[{object_index}]: unknown object ID: {object_id}"
                    )
            for placement_index, placement_id in enumerate(
                beat.get("assetPlacementIds", [])
            ):
                if placement_id not in placements:
                    raise CompatibilityFinalizationError(
                        f"{beat_path}.assetPlacementIds[{placement_index}]: unknown placement ID: {placement_id}"
                    )


def _transaction_paths(output_root: Path, date: str) -> list[Path]:
    verification = output_root / "verification" / date
    return [
        output_root / "render-specs" / date / "render_spec.json",
        verification / "production_consistency_report.json",
        verification / "official_execution_preflight.json",
        verification / "financial_visual_consistency_report.json",
        verification / "visual_direction_compile_report.json",
        verification / "renderer_validation_report.json",
    ]


def _snapshot(paths: list[Path]) -> dict[Path, bytes | None]:
    return {path: path.read_bytes() if path.is_file() else None for path in paths}


def _restore(snapshot: dict[Path, bytes | None]) -> None:
    for path, content in snapshot.items():
        if content is None:
            path.unlink(missing_ok=True)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(f".{path.name}.rollback")
        temp.write_bytes(content)
        temp.replace(path)


def _persist_renderer_evidence(
    *,
    output_root: Path,
    date: str,
    renderer: dict[str, Any],
    render_spec_path: Path,
    report_path: Path,
    visual_contract_path: Path,
    financial_contract_path: Path,
    terminal_binding_path: Path,
    structural_report_path: Path,
    visual_direction_report_path: Path | None,
) -> None:
    verification = output_root / "verification" / date
    consistency_path = verification / "production_consistency_report.json"
    consistency = base.load_json(consistency_path, "production consistency report")
    renderer_contract = {
        "status": "pass",
        "repository": renderer["repository"],
        "commit": renderer["commit"],
        "contract_version": renderer["contract_version"],
        "render_spec_sha256": base.sha256_file(render_spec_path),
        "validator_report_sha256": base.sha256_file(report_path),
        "visual_final_episode_contract_sha256": base.sha256_file(
            visual_contract_path
        ),
        "financial_final_episode_contract_sha256": base.sha256_file(
            financial_contract_path
        ),
        "terminal_assembly_binding_sha256": base.sha256_file(
            terminal_binding_path
        ),
        "unresolved_states": 0,
    }
    if visual_direction_report_path is not None:
        renderer_contract["visual_direction_compile_report_sha256"] = (
            base.sha256_file(visual_direction_report_path)
        )
    consistency["renderer_contract"] = renderer_contract
    consistency["status"] = "pass"
    consistency["unresolved_states"] = 0
    base.write_atomic(consistency_path, consistency)

    preflight_path = verification / "official_execution_preflight.json"
    preflight = base.load_json(preflight_path, "official execution preflight")
    artifacts = preflight.setdefault("artifacts", {})
    artifacts["render_spec"] = base.sha256_file(render_spec_path)
    artifacts["consistency_report"] = base.sha256_file(consistency_path)
    artifacts["renderer_validation_report"] = base.sha256_file(report_path)
    artifacts["visual_grammar_structural_report"] = base.sha256_file(
        structural_report_path
    )
    if visual_direction_report_path is not None:
        artifacts["visual_direction_compile_report"] = base.sha256_file(
            visual_direction_report_path
        )
    artifacts["visual_final_episode_contract"] = base.sha256_file(
        visual_contract_path
    )
    artifacts["financial_final_episode_contract"] = base.sha256_file(
        financial_contract_path
    )
    artifacts["terminal_assembly_binding"] = base.sha256_file(
        terminal_binding_path
    )
    preflight["renderer_validation"] = {
        **renderer_contract,
        "report_sha256": base.sha256_file(report_path),
    }
    preflight["unresolved_states"] = 0
    preflight["preview_authorized"] = True
    preflight["final_authorized"] = False
    base.write_atomic(preflight_path, preflight)


def finalize(
    *,
    output_root: Path,
    date: str,
    renderer_root: Path,
) -> dict[str, Any]:
    output_root = output_root.resolve()
    work = output_root / "working" / date
    verification = output_root / "verification" / date
    visual_contract_path = work / "final_episode_contract.json"
    financial_contract_path = work / "financial_final_episode_contract.json"
    recipe_plan_path = work / "financial_recipe_plan.json"
    reaction_bindings_path = work / "reaction_timeline_bindings.json"
    terminal_binding_path = work / "terminal_assembly_bindings.json"
    structural_report_path = verification / "visual_grammar_structural_report.json"
    for path, label in (
        (visual_contract_path, "Visual Grammar Final Episode Contract"),
        (financial_contract_path, "Financial Final Episode Contract"),
        (recipe_plan_path, "Financial Recipe Plan"),
        (reaction_bindings_path, "reaction timeline bindings"),
        (terminal_binding_path, "terminal assembly bindings"),
        (structural_report_path, "Visual Grammar structural report"),
    ):
        if not path.is_file():
            raise CompatibilityFinalizationError(f"{label} is required: {path}")

    snapshot = _snapshot(_transaction_paths(output_root, date))
    try:
        cross_result = _integrate_financial_visuals(
            output_root=output_root,
            financial_contract_path=financial_contract_path,
            recipe_plan_path=recipe_plan_path,
        )
        render_spec_path = output_root / "render-specs" / date / "render_spec.json"
        render = base.load_json(render_spec_path, "financially integrated render spec")
        strict = base._strict_renderer_projection(
            render,
            final_contract_path=visual_contract_path,
            semantics_path=(output_root / "contracts/visual_grammar_semantics.json"),
            renderer_compatibility_path=(
                output_root / "contracts/visual_grammar_renderer_compatibility.json"
            ),
        )
        remotion_240_projection.canonicalize_render_spec(
            strict,
            episode_date=date,
            reaction_bindings_path=reaction_bindings_path,
        )
        terminal_binding = base.load_json(
            terminal_binding_path,
            "terminal assembly bindings",
        )
        if terminal_binding.get("episodeDate") != date:
            raise CompatibilityFinalizationError(
                "terminal assembly bindings episodeDate mismatch"
            )
        remotion_template_data.materialize_template_data(
            strict,
            terminal_binding=terminal_binding,
        )
        remotion_sequence_policy.resolve_sequence_policies(strict)
        renderer = base._renderer_request(output_root, date)
        request = base.load_json(
            output_root / "working" / date / "production_request.json",
            "production request",
        )
        visual_direction: dict[str, Any] | None = None
        visual_director_binding = request.get("visual_director")
        if visual_director_binding is not None:
            if visual_director_binding != {
                "required": True,
                "contract_version": "1.0.0",
            }:
                raise CompatibilityFinalizationError(
                    "production request Visual Director binding is invalid"
                )
            try:
                visual_direction = visual_director_bridge.prepare_and_compile(
                    render=strict,
                    output_root=output_root,
                    date=date,
                    renderer_root=renderer_root,
                    expected_renderer_commit=renderer["commit"],
                )
            except visual_director_bridge.VisualDirectorBridgeError as exc:
                raise CompatibilityFinalizationError(str(exc)) from exc
            strict = visual_direction["render"]
        _validate_referential_integrity(strict)
        base.write_atomic(render_spec_path, strict)

        report_path = verification / "renderer_validation_report.json"
        validation = base._validate_with_pinned_renderer(
            renderer_root=renderer_root,
            expected_commit=renderer["commit"],
            render_spec_path=render_spec_path,
            report_path=report_path,
            date=date,
        )
        _persist_renderer_evidence(
            output_root=output_root,
            date=date,
            renderer=renderer,
            render_spec_path=render_spec_path,
            report_path=report_path,
            visual_contract_path=visual_contract_path,
            financial_contract_path=financial_contract_path,
            terminal_binding_path=terminal_binding_path,
            structural_report_path=structural_report_path,
            visual_direction_report_path=(
                visual_direction["report_path"] if visual_direction else None
            ),
        )
        preflight_path = verification / "official_execution_preflight.json"
        result = {
            "status": "pass",
            "paths": {
                "final_episode_contract": str(visual_contract_path),
                "financial_final_episode_contract": str(financial_contract_path),
                "financial_recipe_plan": str(recipe_plan_path),
                "terminal_assembly_binding": str(terminal_binding_path),
                "financial_visual_consistency_report": (
                    cross_result["paths"]["cross_report"]
                ),
                "visual_grammar_structural_report": str(structural_report_path),
                "renderer_validation_report": str(report_path),
            },
            "hashes": {
                "render_spec": base.sha256_file(render_spec_path),
                "renderer_validation_report": base.sha256_file(report_path),
                "visual_final_episode_contract": base.sha256_file(
                    visual_contract_path
                ),
                "financial_final_episode_contract": base.sha256_file(
                    financial_contract_path
                ),
                "terminal_assembly_binding": base.sha256_file(
                    terminal_binding_path
                ),
                "preflight": base.sha256_file(preflight_path),
            },
            "rendererValidation": validation,
        }
        if visual_direction:
            result["paths"]["visual_candidate_catalog"] = str(
                visual_direction["catalog_path"]
            )
            result["paths"]["visual_direction_plan"] = str(
                visual_direction["plan_path"]
            )
            result["paths"]["visual_direction_compile_report"] = str(
                visual_direction["report_path"]
            )
            result["hashes"]["visual_candidate_catalog"] = base.sha256_file(
                visual_direction["catalog_path"]
            )
            result["hashes"]["visual_direction_plan"] = base.sha256_file(
                visual_direction["plan_path"]
            )
            result["hashes"]["visual_direction_compile_report"] = (
                base.sha256_file(visual_direction["report_path"])
            )
            result["visualDirection"] = {
                "status": "pass",
                "semanticDiff": "PASS",
                "warnings": visual_direction["warnings"],
            }
        return result
    except Exception:
        _restore(snapshot)
        raise
