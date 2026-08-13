#!/usr/bin/env python3
"""Staged Visual Intelligence bridge for the frozen Director -> Compile -> Critic order.

This module keeps all current v1.2 machine lineage and candidate-generation behavior,
but deliberately separates AI-B Director selection from the later AI-B Critic review.
Machine code may compile only legal authored Candidate IDs; it never chooses them.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable

import financial_candidate_provider
import visual_intelligence_bridge as base

BRIDGE_CONTRACT_VERSION = base.BRIDGE_CONTRACT_VERSION


class VisualIntelligenceStageError(base.VisualIntelligenceBridgeError):
    pass


def _requirements(vi_dir: Path, *, date: str, snapshot_sha: str) -> dict[str, Any]:
    path = vi_dir / "visual_requirements.json"
    if not path.is_file():
        raise VisualIntelligenceStageError("E_VISUAL_REQUIREMENTS_MISSING")
    value = base.load_json(path, "Visual Requirements")
    if value.get("contractVersion") != "1.0.0":
        raise VisualIntelligenceStageError("Visual Requirements contractVersion mismatch")
    if value.get("bridgeContractVersion") != BRIDGE_CONTRACT_VERSION:
        raise VisualIntelligenceStageError("Visual Requirements bridgeContractVersion mismatch")
    if value.get("episodeDate") != date:
        raise VisualIntelligenceStageError("E_VISUAL_REQUIREMENTS_STALE: episodeDate mismatch")
    if value.get("editorialSnapshotSha256") != snapshot_sha:
        raise VisualIntelligenceStageError("E_VISUAL_REQUIREMENTS_STALE: editorial snapshot mismatch")
    return value


def _requirements_rows(requirements: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    intents = requirements.get("intent", {}).get("beats")
    directions = requirements.get("provisionalDirection", {}).get("requirements")
    if not isinstance(intents, list) or not all(isinstance(item, dict) for item in intents):
        raise VisualIntelligenceStageError("Visual Requirements intent.beats missing")
    if not isinstance(directions, list) or not all(isinstance(item, dict) for item in directions):
        raise VisualIntelligenceStageError("Visual Requirements provisionalDirection.requirements missing")
    return intents, directions


def _validate_catalog_coverage(*, requirements: dict[str, Any], catalog: dict[str, Any]) -> None:
    """Fail before AI-B selection when the Catalog cannot satisfy AI-B required modes."""
    _, directions = _requirements_rows(requirements)
    candidates = catalog.get("candidates")
    if not isinstance(candidates, list):
        raise VisualIntelligenceStageError("Visual Candidate Catalog candidates missing")
    by_beat: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        if isinstance(candidate, dict) and isinstance(candidate.get("visualBeatId"), str):
            by_beat.setdefault(candidate["visualBeatId"], []).append(candidate)
    for row in directions:
        beat_id = row.get("visualBeatId")
        required_modes = row.get("requiredModes")
        if not isinstance(beat_id, str) or not isinstance(required_modes, list) or not required_modes:
            raise VisualIntelligenceStageError(f"{beat_id}: invalid requiredModes")
        legal = [
            candidate
            for candidate in by_beat.get(beat_id, [])
            if candidate.get("capability") in required_modes
        ]
        if not legal:
            raise VisualIntelligenceStageError(
                f"E_VISUAL_REQUIRED_MODE_UNAVAILABLE:{beat_id}:required={','.join(str(item) for item in required_modes)}"
            )


def _validate_director(
    *,
    decision: dict[str, Any],
    requirements: dict[str, Any],
    requirements_sha: str,
    date: str,
    snapshot_sha: str,
    beat_ids: list[str],
    catalog: dict[str, Any],
) -> None:
    if decision.get("contractVersion") != "1.0.0":
        raise VisualIntelligenceStageError("Visual Intelligence decision contractVersion must be 1.0.0")
    if decision.get("bridgeContractVersion") != BRIDGE_CONTRACT_VERSION:
        raise VisualIntelligenceStageError("Visual Intelligence decision bridgeContractVersion mismatch")
    if decision.get("episodeDate") != date:
        raise VisualIntelligenceStageError("Visual Intelligence decision episodeDate mismatch")
    if decision.get("editorialSnapshotSha256") != snapshot_sha:
        raise VisualIntelligenceStageError("E_VISUAL_DECISION_STALE: editorial snapshot mismatch")
    if decision.get("visualRequirementsSha256") != requirements_sha:
        raise VisualIntelligenceStageError("E_VISUAL_DECISION_STALE: Visual Requirements SHA mismatch")
    # Backward-compatible duplicated fields are allowed only when byte-for-byte semantic
    # equivalents of the frozen Requirements. New decisions should bind by SHA instead.
    if "intent" in decision and decision.get("intent") != requirements.get("intent"):
        raise VisualIntelligenceStageError("Visual Intent drifted after requirements planning")
    if (
        "provisionalDirection" in decision
        and decision.get("provisionalDirection") != requirements.get("provisionalDirection")
    ):
        raise VisualIntelligenceStageError("Provisional Direction drifted after requirements planning")

    intents, directions = _requirements_rows(requirements)
    intent_by_beat = {item.get("visualBeatId"): item for item in intents}
    direction_by_beat = {item.get("visualBeatId"): item for item in directions}
    if [item.get("visualBeatId") for item in intents] != beat_ids:
        raise VisualIntelligenceStageError("Visual Intent must cover every Beat in Story order")
    if [item.get("visualBeatId") for item in directions] != beat_ids:
        raise VisualIntelligenceStageError("Provisional Direction must cover every Beat in Story order")

    director = decision.get("director")
    selections = director.get("selections") if isinstance(director, dict) else None
    if not isinstance(selections, list):
        raise VisualIntelligenceStageError("Visual Intelligence director.selections missing")
    if [item.get("visualBeatId") for item in selections if isinstance(item, dict)] != beat_ids:
        raise VisualIntelligenceStageError("Director must select exactly one Candidate for every Beat in Story order")

    candidates = catalog.get("candidates")
    if not isinstance(candidates, list):
        raise VisualIntelligenceStageError("Visual Candidate Catalog candidates missing")
    by_id = {item.get("candidateId"): item for item in candidates if isinstance(item, dict)}
    by_beat: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        if isinstance(candidate, dict) and isinstance(candidate.get("visualBeatId"), str):
            by_beat.setdefault(candidate["visualBeatId"], []).append(candidate)

    selected_by_beat: dict[str, dict[str, Any]] = {}
    selection_by_beat: dict[str, dict[str, Any]] = {}
    for selection in selections:
        if not isinstance(selection, dict):
            raise VisualIntelligenceStageError("Director selection must be an object")
        beat_id = selection.get("visualBeatId")
        selected_id = selection.get("selectedCandidateId")
        candidate = by_id.get(selected_id)
        if not isinstance(candidate, dict) or candidate.get("visualBeatId") != beat_id:
            raise VisualIntelligenceStageError(f"{beat_id}: selectedCandidateId is not a legal Candidate")
        required_modes = direction_by_beat.get(beat_id, {}).get("requiredModes")
        if not isinstance(required_modes, list) or candidate.get("capability") not in required_modes:
            raise VisualIntelligenceStageError(
                f"E_VISUAL_SELECTED_MODE_NOT_REQUIRED:{beat_id}:{candidate.get('capability')}"
            )
        alternatives = by_beat.get(beat_id, [])
        strongest = selection.get("strongestAlternativeCandidateId")
        if len(alternatives) == 1:
            if strongest is not None:
                raise VisualIntelligenceStageError(f"{beat_id}: single legal Candidate must not invent an alternative")
        else:
            alternative = by_id.get(strongest)
            if (
                not isinstance(alternative, dict)
                or alternative.get("visualBeatId") != beat_id
                or strongest == selected_id
            ):
                raise VisualIntelligenceStageError(f"{beat_id}: strongest alternative is invalid")
        if not isinstance(selection.get("whySelected"), str) or not selection["whySelected"].strip():
            raise VisualIntelligenceStageError(f"{beat_id}: whySelected missing")
        if not isinstance(selection.get("whyNotAlternative"), str):
            raise VisualIntelligenceStageError(f"{beat_id}: whyNotAlternative missing")
        selected_by_beat[beat_id] = candidate
        selection_by_beat[beat_id] = selection

    index_by_beat = {beat_id: index for index, beat_id in enumerate(beat_ids)}
    for beat_id in beat_ids:
        intent = intent_by_beat.get(beat_id, {})
        if intent.get("realityAnchorPreference") != "required":
            continue
        candidate = selected_by_beat[beat_id]
        selection = selection_by_beat[beat_id]
        if candidate.get("realityAnchor") is True:
            continue
        dependency_id = selection.get("realityAnchorDependencyBeatId")
        if not isinstance(dependency_id, str) or not dependency_id:
            raise VisualIntelligenceStageError(
                f"E_VISUAL_REQUIRED_REALITY_ANCHOR_MISSING:{beat_id}"
            )
        dependency = selected_by_beat.get(dependency_id)
        if not isinstance(dependency, dict) or dependency.get("realityAnchor") is not True:
            raise VisualIntelligenceStageError(
                f"E_VISUAL_REALITY_ANCHOR_DEPENDENCY_INVALID:{beat_id}:{dependency_id}"
            )
        if index_by_beat.get(dependency_id, 10**9) >= index_by_beat[beat_id]:
            raise VisualIntelligenceStageError(
                f"E_VISUAL_REALITY_ANCHOR_DEPENDENCY_NOT_PRIOR:{beat_id}:{dependency_id}"
            )
        if dependency_id.rsplit("-beat-", 1)[0] != beat_id.rsplit("-beat-", 1)[0]:
            raise VisualIntelligenceStageError(
                f"E_VISUAL_REALITY_ANCHOR_DEPENDENCY_CROSS_SCENE:{beat_id}:{dependency_id}"
            )


def _validate_review(
    decision: dict[str, Any],
    *,
    compiled_sha: str,
    warning_sha: str,
) -> list[dict[str, Any]]:
    rounds = decision.get("reviewRounds")
    if rounds is None:
        raise VisualIntelligenceStageError(
            "E_VISUAL_INTELLIGENCE_REVIEW_REQUIRED: compiled visual and warnings are ready; AI-B Critic must review them"
        )
    if not isinstance(rounds, list) or not rounds:
        raise VisualIntelligenceStageError(
            "E_VISUAL_INTELLIGENCE_REVIEW_REQUIRED: compiled visual and warnings are ready; AI-B Critic must review them"
        )
    if len(rounds) > 2:
        raise VisualIntelligenceStageError("Visual Critic may run at most two rounds")

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(rounds, start=1):
        if not isinstance(item, dict):
            raise VisualIntelligenceStageError("Visual Critic round must be an object")
        status = item.get("status")
        if status not in base.CRITIC_STATUSES:
            raise VisualIntelligenceStageError("Visual Critic status is invalid")
        if item.get("round") not in (None, index):
            raise VisualIntelligenceStageError("Visual Critic round numbering is invalid")
        if status == "RETURN_TO_STORY":
            raise VisualIntelligenceStageError("E_VISUAL_RETURN_TO_STORY")
        if status == "BLOCKED":
            raise VisualIntelligenceStageError("E_VISUAL_BLOCKED")
        normalized.append(item)

    last = normalized[-1]
    if last.get("status") != "PASS":
        raise VisualIntelligenceStageError(
            "E_VISUAL_INTELLIGENCE_REVIEW_REQUIRED: Visual Critic has unresolved findings"
        )
    if last.get("compiledVisualSha256") != compiled_sha:
        raise VisualIntelligenceStageError("E_VISUAL_CRITIC_STALE: compiled visual SHA mismatch")
    if last.get("warningReportSha256") != warning_sha:
        raise VisualIntelligenceStageError("E_VISUAL_CRITIC_STALE: warning report SHA mismatch")
    return normalized


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
    requirements = _requirements(vi_dir, date=date, snapshot_sha=snapshot_sha)
    requirements_path = vi_dir / "visual_requirements.json"
    requirements_sha = base.sha256_file(requirements_path)

    input_render = vi_dir / "visual_direction_input.json"
    candidate_input_path = vi_dir / "visual_candidate_input.json"
    capability_inventory_path = vi_dir / "visual_capability_inventory.json"
    capability_hints_path = vi_dir / "visual_capability_hints.json"
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
    base.write_json(
        capability_hints_path,
        base._build_capability_hints(requirements=requirements, render=render, date=date),
    )

    base._run_renderer(
        runner=runner,
        renderer_root=renderer_root,
        command=[
            "node", "--import", "tsx", "scripts/visual-director-cli.ts", "build",
            "--spec", str(input_render),
            "--catalog", str(catalog_path),
            "--hints", str(capability_hints_path),
            "--candidate-builder", "vnext",
            "--editorial-snapshot-sha256", snapshot_sha,
            "--candidate-input", str(candidate_input_path),
            "--capability-inventory", str(capability_inventory_path),
        ],
    )
    catalog = base.load_json(catalog_path, "Visual Candidate Catalog")
    _validate_catalog_coverage(requirements=requirements, catalog=catalog)
    if not decision_path.is_file():
        raise VisualIntelligenceStageError(
            "E_VISUAL_INTELLIGENCE_DECISION_REQUIRED: Candidate Catalog is ready; AI-B must author visual_intelligence_decision.json"
        )

    decision = base.load_json(decision_path, "Visual Intelligence decision")
    beat_ids = base._beat_ids(render)
    _validate_director(
        decision=decision,
        requirements=requirements,
        requirements_sha=requirements_sha,
        date=date,
        snapshot_sha=snapshot_sha,
        beat_ids=beat_ids,
        catalog=catalog,
    )

    catalog_sha = base.canonical_sha(catalog)
    base.write_json(
        plan_path,
        {
            "contractVersion": "1.0.0",
            "episodeDate": date,
            "candidateCatalogSha256": catalog_sha,
            "selections": [
                {
                    "visualBeatId": item["visualBeatId"],
                    "candidateId": item["selectedCandidateId"],
                }
                for item in decision["director"]["selections"]
            ],
        },
    )
    base._run_renderer(
        runner=runner,
        renderer_root=renderer_root,
        command=[
            "node", "--import", "tsx", "scripts/visual-director-cli.ts", "compile",
            "--spec", str(input_render),
            "--catalog", str(catalog_path),
            "--plan", str(plan_path),
            "--output", str(compiled_path),
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
            for item in compile_report.get("warnings", [])
            if isinstance(item, dict)
        ],
    }
    base.write_json(warning_report_path, warning_report)
    compiled_sha = base.sha256_file(compiled_path)
    warning_sha = base.sha256_file(warning_report_path)

    rounds = _validate_review(
        decision,
        compiled_sha=compiled_sha,
        warning_sha=warning_sha,
    )
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
            "visualRequirementsSha256": requirements_sha,
            "capabilityHintsSha256": base.sha256_file(capability_hints_path),
        },
        "intent": requirements["intent"],
        "provisionalDirection": requirements["provisionalDirection"],
        "assetResolution": {"sha256": base.sha256_file(asset_state_path)},
        "director": {
            "candidateCatalogSha256": catalog_sha,
            "selections": decision["director"]["selections"],
        },
        "reviewRounds": rounds,
        "final": {
            "status": "PASS",
            "visualDirectionPlanSha256": base.sha256_file(plan_path),
            "compiledVisualSha256": compiled_sha,
            "warningReportSha256": warning_sha,
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
