#!/usr/bin/env python3
"""Validate the frozen Visual Intelligence 1.2 package and SHA lineage.

This validator is mechanical. Editorial findings remain LLM-owned; the validator
only verifies that the final review is PASS, selections are legal Candidate IDs,
and every declared input/output SHA points to the exact artifact used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema

import renderer_binding

BRIDGE_VERSION = "visual-intelligence-bridge/1.2.0"


class VisualIntelligenceValidationError(ValueError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualIntelligenceValidationError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualIntelligenceValidationError(f"{label} root must be an object")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise VisualIntelligenceValidationError(f"{label} missing: {path}")
    return path


def _assert_sha(declared: str, path: Path, label: str) -> None:
    actual = sha256_file(require_file(path, label))
    if declared != actual:
        raise VisualIntelligenceValidationError(
            f"{label} SHA mismatch: declared={declared} actual={actual}"
        )


def _candidate_map(catalog: dict[str, Any]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for row in catalog.get("candidates", []):
        if not isinstance(row, dict):
            continue
        beat = row.get("visualBeatId")
        candidate = row.get("candidateId")
        if isinstance(beat, str) and isinstance(candidate, str):
            result.setdefault(beat, set()).add(candidate)
    return result


def validate_package(
    *,
    repo_root: Path,
    date: str,
    renderer_root: Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    renderer_root = Path(renderer_root).resolve()
    work = root / "working" / date / "visual-intelligence"
    verification = root / "verification" / date
    package_path = require_file(work / "visual_intelligence_package.json", "Visual Intelligence package")
    schema_path = require_file(root / "contracts/visual_intelligence_package.schema.json", "Visual Intelligence package schema")
    package = load_json(package_path, "Visual Intelligence package")
    schema = load_json(schema_path, "Visual Intelligence package schema")
    try:
        jsonschema.Draft202012Validator(schema).validate(package)
    except jsonschema.ValidationError as exc:
        raise VisualIntelligenceValidationError(
            f"Visual Intelligence package schema failure: {exc.message}"
        ) from exc

    if package["episodeDate"] != date:
        raise VisualIntelligenceValidationError("Visual Intelligence package episodeDate mismatch")
    if package["bridgeContractVersion"] != BRIDGE_VERSION:
        raise VisualIntelligenceValidationError("Visual Intelligence bridge version mismatch")

    binding = renderer_binding.load_renderer_binding(root)
    if package["inputs"]["rendererCommit"] != binding["rendererCommit"]:
        raise VisualIntelligenceValidationError("Visual Intelligence package Renderer SHA is not the canonical binding")

    editorial_snapshot = work / "editorial_snapshot.json"
    candidate_input = work / "visual_candidate_input.json"
    capability_inventory = work / "visual_capability_inventory.json"
    catalog_path = work / "visual_candidate_catalog.json"
    plan_path = work / "visual_direction_plan.json"
    compiled_path = work / "visual_direction_compiled_render.json"
    compile_report_path = work / "visual_direction_compile_report.json"
    warning_report_path = work / "visual_editorial_warning_report.json"
    recent_context_path = work / "recent_visual_pattern_context.json"
    review_path = work / "visual_direction_review.json"
    principles_path = root / "skills/nasdaq-cafe-visual-intelligence/references/VISUAL_EDITORIAL_INTELLIGENCE.md"
    asset_resolution_path = verification / "asset_resolution_log.json"
    registry_path = renderer_root / binding["registrySnapshotPath"]

    inputs = package["inputs"]
    final = package["final"]
    _assert_sha(inputs["editorialSnapshotSha256"], editorial_snapshot, "editorial snapshot")
    _assert_sha(inputs["registrySnapshotSha256"], registry_path, "Renderer registry snapshot")
    _assert_sha(inputs["recentVisualPatternContextSha256"], recent_context_path, "recent visual pattern context")
    _assert_sha(inputs["visualEditorialPrinciplesSha256"], principles_path, "visual editorial principles")
    _assert_sha(package["assetResolution"]["sha256"], asset_resolution_path, "asset resolution log")
    _assert_sha(package["director"]["candidateCatalogSha256"], catalog_path, "candidate catalog")
    _assert_sha(final["visualDirectionPlanSha256"], plan_path, "visual direction plan")
    _assert_sha(final["compiledVisualSha256"], compiled_path, "compiled visual")
    _assert_sha(final["warningReportSha256"], warning_report_path, "visual editorial warning report")
    _assert_sha(final["recentVisualPatternContextSha256"], recent_context_path, "final recent visual pattern context")
    _assert_sha(final["visualEditorialPrinciplesSha256"], principles_path, "final visual editorial principles")
    _assert_sha(final["reviewSha256"], review_path, "visual direction review")

    candidate_input_value = load_json(candidate_input, "VisualCandidateInput")
    capability_inventory_value = load_json(capability_inventory, "Capability Inventory")
    catalog = load_json(catalog_path, "Candidate Catalog")
    plan = load_json(plan_path, "Visual Direction Plan")
    compile_report = load_json(compile_report_path, "Visual Direction Compile Report")
    warning_report = load_json(warning_report_path, "Visual Editorial Warning Report")
    review = load_json(review_path, "Visual Direction Review")

    editorial_sha = sha256_file(editorial_snapshot)
    candidate_input_sha = sha256_file(candidate_input)
    compile_report_sha = sha256_file(compile_report_path)
    catalog_sha = sha256_file(catalog_path)
    plan_sha = sha256_file(plan_path)

    if candidate_input_value.get("episodeDate") != date or candidate_input_value.get("editorialSnapshotSha256") != editorial_sha:
        raise VisualIntelligenceValidationError("VisualCandidateInput is not bound to the current editorial snapshot")
    if capability_inventory_value.get("episodeDate") != date or capability_inventory_value.get("visualCandidateInputSha256") != candidate_input_sha:
        raise VisualIntelligenceValidationError("Capability Inventory is not bound to VisualCandidateInput")
    if catalog.get("episodeDate") != date or catalog.get("sourceRenderSpecSha256") != editorial_sha:
        raise VisualIntelligenceValidationError("Candidate Catalog is not bound to the current editorial snapshot")
    if plan.get("episodeDate") != date or plan.get("candidateCatalogSha256") != catalog_sha:
        raise VisualIntelligenceValidationError("Visual Direction Plan is not bound to Candidate Catalog")
    if compile_report.get("episodeDate") != date or compile_report.get("sourceRenderSpecSha256") != editorial_sha:
        raise VisualIntelligenceValidationError("Compile Report is not bound to the current editorial snapshot")
    if compile_report.get("semanticDiff") != "PASS":
        raise VisualIntelligenceValidationError("Protected Semantic Diff must PASS")
    if warning_report.get("episodeDate") != date or warning_report.get("sourceCompileReportSha256") != compile_report_sha:
        raise VisualIntelligenceValidationError("Warning Report is not bound to Compile Report")
    if review.get("episodeDate") != date or review.get("status") != "PASS":
        raise VisualIntelligenceValidationError("Visual Direction Review must be PASS for the same episode date")
    for key, expected in (
        ("sourceEditorialSnapshotSha256", editorial_sha),
        ("sourceCandidateCatalogSha256", catalog_sha),
        ("sourceVisualDirectionPlanSha256", plan_sha),
        ("sourceCompileReportSha256", compile_report_sha),
    ):
        if review.get(key) != expected:
            raise VisualIntelligenceValidationError(f"Visual Direction Review {key} mismatch")

    legal = _candidate_map(catalog)
    package_selection = {
        row["visualBeatId"]: row["selectedCandidateId"]
        for row in package["director"]["selections"]
    }
    plan_selection = {
        row.get("visualBeatId"): row.get("candidateId")
        for row in plan.get("selections", [])
        if isinstance(row, dict)
    }
    if package_selection != plan_selection:
        raise VisualIntelligenceValidationError("Editorial Director selections do not match executable Visual Direction Plan")
    for row in package["director"]["selections"]:
        beat = row["visualBeatId"]
        selected = row["selectedCandidateId"]
        alternative = row["strongestAlternativeCandidateId"]
        candidates = legal.get(beat, set())
        if selected not in candidates:
            raise VisualIntelligenceValidationError(f"selected candidate is not legal: beat={beat} candidate={selected}")
        if alternative is not None:
            if alternative == selected or alternative not in candidates:
                raise VisualIntelligenceValidationError(
                    f"strongest alternative is invalid: beat={beat} candidate={alternative}"
                )
        elif len(candidates) > 1:
            raise VisualIntelligenceValidationError(
                f"multiple legal candidates require a strongest alternative: beat={beat}"
            )

    rounds = package.get("reviewRounds", [])
    if not rounds or rounds[-1].get("status") != "PASS":
        raise VisualIntelligenceValidationError("final Visual Intelligence package requires a PASS review round")
    if rounds[-1].get("reviewSha256") != sha256_file(review_path):
        raise VisualIntelligenceValidationError("final review round SHA does not match Visual Direction Review")

    return {
        "status": "PASS",
        "episodeDate": date,
        "bridgeContractVersion": BRIDGE_VERSION,
        "rendererCommit": binding["rendererCommit"],
        "packageSha256": sha256_file(package_path),
        "candidateCount": sum(len(items) for items in legal.values()),
        "selectionCount": len(package_selection),
        "reviewRounds": len(rounds),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--date", required=True)
    parser.add_argument("--renderer-root", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    try:
        result = validate_package(
            repo_root=args.repo_root,
            date=args.date,
            renderer_root=args.renderer_root,
        )
        code = 0
    except (VisualIntelligenceValidationError, renderer_binding.RendererBindingError) as exc:
        result = {"status": "FAIL", "episodeDate": args.date, "error": str(exc)}
        code = 2
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
