#!/usr/bin/env python3
"""Staged Visual Intelligence bridge matching the frozen Director→Compile→Critic order."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable

import financial_candidate_provider
import renderer_binding
import visual_intelligence_bridge as base

BRIDGE_CONTRACT_VERSION = base.BRIDGE_CONTRACT_VERSION


class VisualIntelligenceStageError(base.VisualIntelligenceBridgeError):
    pass


def _requirements(vi_dir: Path, date: str, snapshot_sha: str) -> dict[str, Any]:
    path = vi_dir / "visual_requirements.json"
    if not path.is_file():
        raise VisualIntelligenceStageError("E_VISUAL_REQUIREMENTS_MISSING")
    value = base.load_json(path, "Visual Requirements")
    if value.get("contractVersion") != "1.0.0" or value.get("bridgeContractVersion") != BRIDGE_CONTRACT_VERSION:
        raise VisualIntelligenceStageError("Visual Requirements contract mismatch")
    if value.get("episodeDate") != date or value.get("editorialSnapshotSha256") != snapshot_sha:
        raise VisualIntelligenceStageError("E_VISUAL_REQUIREMENTS_STALE")
    return value


def _write_capability_hints(vi_dir: Path, requirements: dict[str, Any]) -> Path:
    rows = requirements.get("provisionalDirection", {}).get("requirements")
    if not isinstance(rows, list):
        raise VisualIntelligenceStageError("Provisional Direction requirements missing")
    beats = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("visualBeatId"), str):
            raise VisualIntelligenceStageError("invalid Provisional Direction requirement")
        modes = row.get("requiredModes")
        if not isinstance(modes, list) or not modes:
            raise VisualIntelligenceStageError(f"{row.get('visualBeatId')}: requiredModes must not be empty")
        beats.append({"visualBeatId": row["visualBeatId"], "capabilities": modes})
    path = vi_dir / "visual_capability_hints.json"
    base.write_json(path, {
        "contractVersion": "1.0.0",
        "episodeDate": requirements["episodeDate"],
        "beats": beats,
    })
    return path


def _validate_director(
    *,
    decision: dict[str, Any],
    requirements: dict[str, Any],
    date: str,
    snapshot_sha: str,
    beat_ids: list[str],
    catalog: dict[str, Any],
) -> None:
    if decision.get("contractVersion") != "1.0.0" or decision.get("bridgeContractVersion") != BRIDGE_CONTRACT_VERSION:
        raise VisualIntelligenceStageError("Visual Intelligence decision contract mismatch")
    if decision.get("episodeDate") != date or decision.get("editorialSnapshotSha256") != snapshot_sha:
        raise VisualIntelligenceStageError("E_VISUAL_DECISION_STALE")
    if decision.get("intent") != requirements.get("intent"):
        raise VisualIntelligenceStageError("Visual Intent drifted after requirements planning")
    if decision.get("provisionalDirection") != requirements.get("provisionalDirection"):
        raise VisualIntelligenceStageError("Provisional Direction drifted after requirements planning")
    director = decision.get("director")
    selections = director.get("selections") if isinstance(director, dict) else None
    if not isinstance(selections, list) or [item.get("visualBeatId") for item in selections] != beat_ids:
        raise VisualIntelligenceStageError("Director must select exactly one Candidate for every Beat")
    candidates = catalog.get("candidates")
    if not isinstance(candidates, list):
        raise VisualIntelligenceStageError("Visual Candidate Catalog candidates missing")
    by_id = {item.get("candidateId"): item for item in candidates if isinstance(item, dict)}
    by_beat: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        if isinstance(candidate, dict):
            by_beat.setdefault(candidate.get("visualBeatId"), []).append(candidate)
    for selection in selections:
        beat_id = selection.get("visualBeatId")
        selected_id = selection.get("selectedCandidateId")
        candidate = by_id.get(selected_id)
        if not isinstance(candidate, dict) or candidate.get("visualBeatId") != beat_id:
            raise VisualIntelligenceStageError(f"{beat_id}: selected Candidate is not legal")
        alternatives = by_beat.get(beat_id, [])
        strongest = selection.get("strongestAlternativeCandidateId")
        if len(alternatives) == 1:
            if strongest is not None:
                raise VisualIntelligenceStageError(f"{beat_id}: single Candidate cannot invent an alternative")
        else:
            alt = by_id.get(strongest)
            if not isinstance(alt, dict) or alt.get("visualBeatId") != beat_id or strongest == selected_id:
                raise VisualIntelligenceStageError(f"{beat_id}: strongest alternative is invalid")
        if not isinstance(selection.get("whySelected"), str) or not selection["whySelected"].strip():
            raise VisualIntelligenceStageError(f"{beat_id}: whySelected missing")
        if not isinstance(selection.get("whyNotAlternative"), str):
            raise VisualIntelligenceStageError(f"{beat_id}: whyNotAlternative missing")


def _validate_review(decision: dict[str, Any]) -> list[dict[str, Any]]:
    rounds = decision.get("reviewRounds")
    if not isinstance(rounds, list) or not rounds:
        raise VisualIntelligenceStageError("E_VISUAL_INTELLIGENCE_REVIEW_REQUIRED")
    if len(rounds) > 2:
        raise VisualIntelligenceStageError("Visual Critic may run at most two rounds")
    for index, item in enumerate(rounds):
        if not isinstance(item, dict):
            raise VisualIntelligenceStageError("Visual Critic round must be an object")
        status = item.get("status")
        if status not in base.CRITIC_STATUSES:
            raise VisualIntelligenceStageError("Visual Critic status invalid")
        if status == "RETURN_TO_STORY":
            raise VisualIntelligenceStageError("E_VISUAL_RETURN_TO_STORY")
        if status == "BLOCKED":
            raise VisualIntelligenceStageError("E_VISUAL_BLOCKED")
        if status == "REVISE" and index == len(rounds) - 1:
            raise VisualIntelligenceStageError("E_VISUAL_INTELLIGENCE_REVIEW_REQUIRED")
    if rounds[-1].get("status") != "PASS":
        raise VisualIntelligenceStageError("E_VISUAL_INTELLIGENCE_REVIEW_REQUIRED")
    return rounds


def prepare_and_compile(
    *,
    render: dict[str, Any],
    output_root: Path,
    date: str,
    renderer_root: Path,
    expected_renderer_commit: str,
    plot_root: Path | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    output_root = output_root.resolve()
    renderer_root = renderer_root.resolve()
    plot_root = (plot_root or Path(__file__).resolve().parents[1]).resolve()
    binding = base._verify_renderer(plot_root, renderer_root, expected_renderer_commit)
    if render.get("schemaVersion") != "2.4.0" or render.get("episode", {}).get("targetDate") != date:
        raise VisualIntelligenceStageError("Visual Intelligence requires canonical render_spec 2.4.0 for the same date")

    vi_dir = output_root / "working" / date / "visual-intelligence"
    vi_dir.mkdir(parents=True, exist_ok=True)
    editorial_snapshot_path = vi_dir / "editorial_snapshot.json"
    if editorial_snapshot_path.is_file():
        snapshot = base.load_json(editorial_snapshot_path, "editorial snapshot")
        if snapshot.get("episodeDate") != date:
            raise VisualIntelligenceStageError("editorial snapshot episodeDate mismatch")
    else:
        base.write_json(editorial_snapshot_path, base.build_editorial_snapshot(render))
    snapshot_sha = base.sha256_file(editorial_snapshot_path)
    requirements = _requirements(vi_dir, date, snapshot_sha)
    hints_path = _write_capability_hints(vi_dir, requirements)

    input_render = vi_dir / "visual_direction_input.json"
    candidate_input_path = vi_dir / "visual_candidate_input.json"
    capability_inventory_path = vi_dir / "visual_capability_inventory.json"
    catalog_path = vi_dir / "visual_candidate_catalog.json"
    asset_state_path = vi_dir / "asset_resolution_state.json"
    financial_provider_path = vi_dir / "financial_candidate_provider.json"
    recent_context_path = vi_dir / "recent_visual_pattern_context.json"
    decision_path = vi_dir / "visual_intelligence_decision.json"
    plan_path = vi_dir / "visual_direction_plan.json"
    compiled_path = vi_dir / "visual_direction_compiled_render.json"
    compile_report_path = vi_dir / "visual_direction_compile_report.json"
    warning_report_path = vi_dir / "visual_editorial_warning_report.json"
    review_path = vi_dir / "visual_plan_review.json"
    package_path = vi_dir / "visual_intelligence_package.json"

    base.write_json(asset_state_path, base._asset_resolution_state(output_root, date))
    financial_candidate_provider.write(financial_provider_path, financial_candidate_provider.build(render))
    base.write_json(recent_context_path, base._phase1_recent_context(date))
    base.write_json(input_render, render)
    base._run_renderer(
        runner=runner,
        renderer_root=renderer_root,
        command=[
            "node", "--import", "tsx", "scripts/visual-director-cli.ts", "build",
            "--spec", str(input_render), "--catalog", str(catalog_path),
            "--hints", str(hints_path), "--candidate-builder", "vnext",
            "--editorial-snapshot-sha256", snapshot_sha,
            "--candidate-input", str(candidate_input_path),
            "--capability-inventory", str(capability_inventory_path),
        ],
    )
    catalog = base.load_json(catalog_path, "Visual Candidate Catalog")
    if not decision_path.is_file():
        raise VisualIntelligenceStageError("E_VISUAL_INTELLIGENCE_DECISION_REQUIRED")
    decision = base.load_json(decision_path, "Visual Intelligence decision")
    beat_ids = base._beat_ids(render)
    _validate_director(
        decision=decision, requirements=requirements, date=date,
        snapshot_sha=snapshot_sha, beat_ids=beat_ids, catalog=catalog,
    )

    catalog_sha = base.canonical_sha(catalog)
    base.write_json(plan_path, {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "candidateCatalogSha256": catalog_sha,
        "selections": [
            {"visualBeatId": item["visualBeatId"], "candidateId": item["selectedCandidateId"]}
            for item in decision["director"]["selections"]
        ],
    })
    base._run_renderer(
        runner=runner,
        renderer_root=renderer_root,
        command=[
            "node", "--import", "tsx", "scripts/visual-director-cli.ts", "compile",
            "--spec", str(input_render), "--catalog", str(catalog_path),
            "--plan", str(plan_path), "--output", str(compiled_path),
            "--report", str(compile_report_path),
        ],
    )
    compile_report = base.load_json(compile_report_path, "Visual Direction compile report")
    if compile_report.get("semanticDiff") != "PASS":
        raise VisualIntelligenceStageError("E_VISUAL_SEMANTIC_DIFF_FAIL")
    warning_report = {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "classification": "editorial-warning-shadow",
        "sourceCompileReportSha256": base.sha256_file(compile_report_path),
        "warnings": [
            {**item, "severity": "warning", "legacy": {"wouldFail": False}}
            for item in compile_report.get("warnings", []) if isinstance(item, dict)
        ],
    }
    base.write_json(warning_report_path, warning_report)

    rounds = _validate_review(decision)
    base.write_json(review_path, rounds[-1])
    registry_snapshot_path = renderer_root / binding["renderer"]["registrySnapshotPath"]
    principles_path = plot_root / "skills/nasdaq-cafe-visual-intelligence/references/VISUAL_EDITORIAL_INTELLIGENCE.md"
    recent_sha = base.sha256_file(recent_context_path)
    principles_sha = base.sha256_file(principles_path)
    package = {
        "contractVersion": "1.0.0",
        "bridgeContractVersion": BRIDGE_CONTRACT_VERSION,
        "episodeDate": date,
        "inputs": {
            "editorialSnapshotSha256": snapshot_sha,
            "rendererCommit": expected_renderer_commit,
            "registrySnapshotSha256": base.sha256_file(registry_snapshot_path),
            "recentVisualPatternContextSha256": recent_sha,
            "visualEditorialPrinciplesSha256": principles_sha,
        },
        "intent": decision["intent"],
        "provisionalDirection": decision["provisionalDirection"],
        "assetResolution": {"sha256": base.sha256_file(asset_state_path)},
        "director": {"candidateCatalogSha256": catalog_sha, "selections": decision["director"]["selections"]},
        "reviewRounds": rounds,
        "final": {
            "status": "PASS",
            "visualDirectionPlanSha256": base.sha256_file(plan_path),
            "compiledVisualSha256": base.sha256_file(compiled_path),
            "warningReportSha256": base.sha256_file(warning_report_path),
            "recentVisualPatternContextSha256": recent_sha,
            "visualEditorialPrinciplesSha256": principles_sha,
            "reviewSha256": base.sha256_file(review_path),
        },
    }
    base.write_json(package_path, package)
    return {
        "render": base.load_json(compiled_path, "compiled render"),
        "package_path": package_path,
        "catalog_path": catalog_path,
        "candidate_input_path": candidate_input_path,
        "capability_inventory_path": capability_inventory_path,
        "compile_report_path": compile_report_path,
        "warning_report_path": warning_report_path,
        "financial_provider_path": financial_provider_path,
        "editorial_snapshot_path": editorial_snapshot_path,
    }
