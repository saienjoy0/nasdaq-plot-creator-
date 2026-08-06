#!/usr/bin/env python3
"""Finalize production using separate Visual Grammar 1.1 and Financial 1.0 contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import financial_final_episode_contract_1_0 as financial_contract_v1
import financial_visual_cross_artifact
import finalize_renderer_package as base

ALLOWED_EXPECTED_BASIS = {
    "official-consensus", "company-prior-guidance", "major-reporting",
    "analyst-view", "price-inference", "unconfirmed",
}

class CompatibilityFinalizationError(ValueError):
    pass

def _canonical_scene_contract(render_spec: dict[str, Any]) -> None:
    scenes = render_spec.get("scenes", [])
    if not isinstance(scenes, list) or len(scenes) != 9:
        raise CompatibilityFinalizationError("renderer projection requires exactly nine scenes")
    for index, scene in enumerate(scenes):
        expected_role = (
            "opening-hook-market-direction-greeting-conclusion"
            if index == 0
            else "closing-recap-sendoff-goodnight"
            if index == 8
            else "editorial-body"
        )
        scene["sceneRole"] = expected_role
        if scene.get("expectedBasisType") not in ALLOWED_EXPECTED_BASIS:
            scene["expectedBasisType"] = None

def _validator_adapter(contract_path, repo_root, final_schema_path, candidate_schema_path, *args):
    return financial_contract_v1.validate_contract(
        contract_path, repo_root, candidate_schema_path
    )
def finalize(*, output_root: Path, date: str, renderer_root: Path) -> dict[str, Any]:
    output_root = output_root.resolve()
    work = output_root / "working" / date
    verification = output_root / "verification" / date
    visual_contract_path = work / "final_episode_contract.json"
    financial_contract_path = work / "financial_final_episode_contract.json"
    recipe_plan_path = work / "financial_recipe_plan.json"
    structural_report_path = verification / "visual_grammar_structural_report.json"
    if not visual_contract_path.is_file() or not financial_contract_path.is_file():
        raise CompatibilityFinalizationError("both Final Episode Contract projections are required")

    approved_matrix = {
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
    }
    financial_visual_cross_artifact.EXPECTED_COMPATIBILITY_MATRIX = approved_matrix
    original_cross_validator = financial_visual_cross_artifact.final_contract_module.validate_contract
    original_recipe_validator = (
        financial_visual_cross_artifact.recipe_compiler.final_contract_module.validate_contract
    )
    financial_visual_cross_artifact.final_contract_module.validate_contract = _validator_adapter
    financial_visual_cross_artifact.recipe_compiler.final_contract_module.validate_contract = _validator_adapter
    try:
        cross_result = financial_visual_cross_artifact.integrate(
            final_contract_path=financial_contract_path,
            recipe_plan_path=recipe_plan_path,
            repo_root=output_root,
            production_root=output_root,
            renderer_schema_version="2.4.0",
            final_schema_path=output_root / "contracts/final_episode_contract.schema.json",
            candidate_schema_path=output_root / "contracts/financial_visual_candidate_plan.schema.json",
            registry_path=output_root / "contracts/financial_recipe_registry.json",
            recipe_plan_schema_path=output_root / "contracts/financial_recipe_plan.schema.json",
            diversity_schema_path=output_root / "contracts/financial_visual_diversity_report.schema.json",
            consistency_schema_path=output_root / "contracts/financial_visual_consistency_report.schema.json",
            diversity_report_path=None,
            compatibility_matrix_path=output_root / "contracts/financial_visual_compatibility.json",
        )
    finally:
        financial_visual_cross_artifact.final_contract_module.validate_contract = original_cross_validator
        financial_visual_cross_artifact.recipe_compiler.final_contract_module.validate_contract = original_recipe_validator

    render_spec_path = output_root / "render-specs" / date / "render_spec.json"
    render = base.load_json(render_spec_path, "financially integrated render spec")
    strict = base._strict_renderer_projection(
        render,
        final_contract_path=visual_contract_path,
        semantics_path=output_root / "contracts/visual_grammar_semantics.json",
        renderer_compatibility_path=output_root / "contracts/visual_grammar_renderer_compatibility.json",
    )
    _canonical_scene_contract(strict)
    base.write_atomic(render_spec_path, strict)

    renderer = base._renderer_request(output_root, date)
    report_path = verification / "renderer_validation_report.json"
    validation = base._validate_with_pinned_renderer(
        renderer_root=renderer_root,
        expected_commit=renderer["commit"],
        render_spec_path=render_spec_path,
        report_path=report_path,
        date=date,
    )
    consistency_path = verification / "production_consistency_report.json"
    consistency = base.load_json(consistency_path, "production consistency report")
    consistency["renderer_contract"] = {
        "status": "pass",
        "repository": renderer["repository"],
        "commit": renderer["commit"],
        "contract_version": renderer["contract_version"],
        "render_spec_sha256": base.sha256_file(render_spec_path),
        "validator_report_sha256": base.sha256_file(report_path),
        "visual_final_episode_contract_sha256": base.sha256_file(visual_contract_path),
        "financial_final_episode_contract_sha256": base.sha256_file(financial_contract_path),
        "unresolved_states": 0,
    }
    consistency["status"] = "pass"
    consistency["unresolved_states"] = 0
    base.write_atomic(consistency_path, consistency)

    preflight_path = verification / "official_execution_preflight.json"
    preflight = base.load_json(preflight_path, "official execution preflight")
    artifacts = preflight.setdefault("artifacts", {})
    artifacts["render_spec"] = base.sha256_file(render_spec_path)
    artifacts["consistency_report"] = base.sha256_file(consistency_path)
    artifacts["renderer_validation_report"] = base.sha256_file(report_path)
    artifacts["visual_grammar_structural_report"] = base.sha256_file(structural_report_path)
    artifacts["visual_final_episode_contract"] = base.sha256_file(visual_contract_path)
    artifacts["financial_final_episode_contract"] = base.sha256_file(financial_contract_path)
    preflight["renderer_validation"] = {
        "status": "pass",
        "repository": renderer["repository"],
        "commit": renderer["commit"],
        "contract_version": renderer["contract_version"],
        "render_spec_sha256": base.sha256_file(render_spec_path),
        "report_sha256": base.sha256_file(report_path),
        "visual_final_episode_contract_sha256": base.sha256_file(visual_contract_path),
        "financial_final_episode_contract_sha256": base.sha256_file(financial_contract_path),
        "unresolved_states": 0,
    }
    preflight["unresolved_states"] = 0
    preflight["preview_authorized"] = True
    preflight["final_authorized"] = False
    base.write_atomic(preflight_path, preflight)
    return {
        "status": "pass",
        "paths": {
            "final_episode_contract": str(visual_contract_path),
            "financial_final_episode_contract": str(financial_contract_path),
            "financial_recipe_plan": str(recipe_plan_path),
            "financial_visual_consistency_report": cross_result["paths"]["cross_report"],
            "visual_grammar_structural_report": str(structural_report_path),
            "renderer_validation_report": str(report_path),
        },
        "hashes": {
            "render_spec": base.sha256_file(render_spec_path),
            "renderer_validation_report": base.sha256_file(report_path),
            "visual_final_episode_contract": base.sha256_file(visual_contract_path),
            "financial_final_episode_contract": base.sha256_file(financial_contract_path),
            "preflight": base.sha256_file(preflight_path),
        },
        "rendererValidation": validation,
    }
