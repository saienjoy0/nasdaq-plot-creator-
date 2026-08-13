#!/usr/bin/env python3
"""Hard validator for the final visual-intelligence-bridge/1.2.0 package."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import renderer_binding


class VisualIntelligencePackageError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VisualIntelligencePackageError(f"{label} must be an object")
    return value


def validate(*, root: Path, date: str, renderer_root: Path) -> dict[str, Any]:
    root = root.resolve()
    renderer_root = renderer_root.resolve()
    binding = renderer_binding.verify_renderer_checkout(root, renderer_root)
    vi = root / "working" / date / "visual-intelligence"
    package_path = vi / "visual_intelligence_package.json"
    package = load(package_path, "Visual Intelligence package")
    if package.get("contractVersion") != "1.0.0":
        raise VisualIntelligencePackageError("Visual Intelligence package contractVersion mismatch")
    if package.get("bridgeContractVersion") != renderer_binding.BRIDGE_CONTRACT_VERSION:
        raise VisualIntelligencePackageError("Visual Intelligence bridgeContractVersion mismatch")
    if package.get("episodeDate") != date:
        raise VisualIntelligencePackageError("Visual Intelligence episodeDate mismatch")

    requirements_path = vi / "visual_requirements.json"
    requirements = load(requirements_path, "Visual Requirements")
    if package.get("intent") != requirements.get("intent"):
        raise VisualIntelligencePackageError("Visual Intent drifted after requirements planning")
    if package.get("provisionalDirection") != requirements.get("provisionalDirection"):
        raise VisualIntelligencePackageError("Provisional Direction drifted after requirements planning")

    inputs = package.get("inputs")
    if not isinstance(inputs, dict):
        raise VisualIntelligencePackageError("Visual Intelligence inputs missing")
    expected_inputs = {
        "editorialSnapshotSha256": sha256_file(vi / "editorial_snapshot.json"),
        "rendererCommit": binding["renderer"]["commit"],
        "registrySnapshotSha256": sha256_file(renderer_root / binding["renderer"]["registrySnapshotPath"]),
        "recentVisualPatternContextSha256": sha256_file(vi / "recent_visual_pattern_context.json"),
        "visualEditorialPrinciplesSha256": sha256_file(root / "skills/nasdaq-cafe-visual-intelligence/references/VISUAL_EDITORIAL_INTELLIGENCE.md"),
        "visualRequirementsSha256": sha256_file(requirements_path),
        "capabilityHintsSha256": sha256_file(vi / "visual_capability_hints.json"),
    }
    if inputs != expected_inputs:
        raise VisualIntelligencePackageError("Visual Intelligence input lineage mismatch")

    asset = package.get("assetResolution")
    if asset != {"sha256": sha256_file(vi / "asset_resolution_state.json")}:
        raise VisualIntelligencePackageError("Visual Intelligence asset resolution lineage mismatch")

    catalog = load(vi / "visual_candidate_catalog.json", "Visual Candidate Catalog")
    canonical = json.dumps(catalog, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    catalog_sha = hashlib.sha256(canonical).hexdigest()
    director = package.get("director")
    if not isinstance(director, dict) or director.get("candidateCatalogSha256") != catalog_sha:
        raise VisualIntelligencePackageError("Visual Director Candidate Catalog SHA mismatch")

    final = package.get("final")
    if not isinstance(final, dict) or final.get("status") != "PASS":
        raise VisualIntelligencePackageError("Visual Intelligence final status must be PASS")
    expected_final = {
        "status": "PASS",
        "visualDirectionPlanSha256": sha256_file(vi / "visual_direction_plan.json"),
        "compiledVisualSha256": sha256_file(vi / "visual_direction_compiled_render.json"),
        "warningReportSha256": sha256_file(vi / "visual_editorial_warning_report.json"),
        "recentVisualPatternContextSha256": expected_inputs["recentVisualPatternContextSha256"],
        "visualEditorialPrinciplesSha256": expected_inputs["visualEditorialPrinciplesSha256"],
        "reviewSha256": sha256_file(vi / "visual_plan_review.json"),
    }
    if final != expected_final:
        raise VisualIntelligencePackageError("Visual Intelligence final artifact lineage mismatch")

    review_rounds = package.get("reviewRounds")
    if not isinstance(review_rounds, list) or not review_rounds or len(review_rounds) > 2:
        raise VisualIntelligencePackageError("Visual Critic requires one or two review rounds")
    if review_rounds[-1].get("status") != "PASS":
        raise VisualIntelligencePackageError("Visual Critic PASS is missing")
    if any(item.get("status") in {"RETURN_TO_STORY", "BLOCKED"} for item in review_rounds if isinstance(item, dict)):
        raise VisualIntelligencePackageError("Visual Intelligence unresolved return/block state")
    final_review = review_rounds[-1]
    if final_review.get("compiledVisualSha256") != expected_final["compiledVisualSha256"]:
        raise VisualIntelligencePackageError("Visual Critic PASS is stale for compiled visual")
    if final_review.get("warningReportSha256") != expected_final["warningReportSha256"]:
        raise VisualIntelligencePackageError("Visual Critic PASS is stale for warning report")
    if load(vi / "visual_plan_review.json", "Visual Plan review") != final_review:
        raise VisualIntelligencePackageError("Visual Plan review does not match final Critic round")

    return {
        "status": "PASS",
        "episodeDate": date,
        "packageSha256": sha256_file(package_path),
        "compiledVisualSha256": expected_final["compiledVisualSha256"],
        "warningReportSha256": expected_final["warningReportSha256"],
        "visualRequirementsSha256": expected_inputs["visualRequirementsSha256"],
        "capabilityHintsSha256": expected_inputs["capabilityHintsSha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--date", required=True)
    parser.add_argument("--renderer-root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = validate(root=args.root, date=args.date, renderer_root=args.renderer_root)
        code = 0
    except (OSError, json.JSONDecodeError, VisualIntelligencePackageError, renderer_binding.RendererBindingError) as exc:
        result = {"status": "FAIL", "episodeDate": args.date, "errors": [str(exc)]}
        code = 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
