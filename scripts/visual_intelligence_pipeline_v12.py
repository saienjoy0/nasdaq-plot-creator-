#!/usr/bin/env python3
"""Current v1.2 Visual Intelligence pipeline with temporal artifact separation.

Order is fixed and observable:
Requirements canonical -> Candidate Catalog -> Director Decision canonical -> Compile
-> Critic Review canonical -> VI Package. Existing Renderer Candidate Builder and compiler
remain the executors; this module only owns current orchestration and validation.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable

import financial_candidate_provider
import visual_intelligence_artifacts_v12 as artifacts
import visual_intelligence_bridge as base

BRIDGE_CONTRACT_VERSION = base.BRIDGE_CONTRACT_VERSION


class VisualIntelligenceStageError(base.VisualIntelligenceBridgeError):
    pass


def _write_once(path: Path, value: dict[str, Any], label: str) -> Path:
    try:
        return artifacts.write_once(path, value, label=label)
    except artifacts.VisualIntelligenceArtifactError as exc:
        raise VisualIntelligenceStageError(str(exc)) from exc


def _requirements(vi_dir: Path, *, date: str, snapshot_sha: str) -> dict[str, Any]:
    try:
        path = artifacts.materialize_requirements(vi_dir=vi_dir, date=date)
    except artifacts.VisualIntelligenceArtifactError as exc:
        raise VisualIntelligenceStageError(str(exc)) from exc
    value = base.load_json(path, "Visual Requirements canonical")
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
        if not any(
            candidate.get("capability") in required_modes
            for candidate in by_beat.get(beat_id, [])
        ):
            raise VisualIntelligenceStageError(
                f"E_VISUAL_REQUIRED_MODE_UNAVAILABLE:{beat_id}:required="
                + ",".join(str(item) for item in required_modes)
            )


def _validate_director(
    *,
    decision: dict[str, Any],
    requirements: dict[str, Any],
    date: str,
    snapshot_sha: str,
    requirements_sha: str,
    beat_ids: list[str],
    catalog: dict[str, Any],
    catalog_sha: str,
) -> None:
    if decision.get("contractVersion") != "1.0.0":
        raise VisualIntelligenceStageError("Visual Director contractVersion mismatch")
    if decision.get("bridgeContractVersion") != BRIDGE_CONTRACT_VERSION:
        raise VisualIntelligenceStageError("Visual Director bridgeContractVersion mismatch")
    if decision.get("episodeDate") != date:
        raise VisualIntelligenceStageError("Visual Director episodeDate mismatch")
    if decision.get("editorialSnapshotSha256") != snapshot_sha:
        raise VisualIntelligenceStageError("E_VISUAL_DECISION_STALE: editorial snapshot mismatch")
    if decision.get("visualRequirementsSha256") != requirements_sha:
        raise VisualIntelligenceStageError("E_VISUAL_DECISION_STALE: Visual Requirements SHA mismatch")
    if decision.get("candidateCatalogSha256") != catalog_sha:
        raise VisualIntelligenceStageError("E_VISUAL_DECISION_STALE: Candidate Catalog SHA mismatch")

    intents, directions = _requirements_rows(requirements)
    if [item.get("visualBeatId") for item in intents] != beat_ids:
        raise VisualIntelligenceStageError("Visual Intent must cover every Beat in Story order")
    if [item.get("visualBeatId") for item in directions] != beat_ids:
        raise VisualIntelligenceStageError("Provisional Direction must cover every Beat in Story order")
    intent_by_beat = {item.get("visualBeatId"): item for item in intents}

    selections = decision.get("selections")
    if not isinstance(selections, list):
        raise VisualIntelligenceStageError("Visual Director selections missing")
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
        alternatives = by_beat.get(beat_id, [])
        strongest = selection.get("strongestAlternativeCandidateId")
        if len(alternatives) == 1:
            if strongest is not None:
                raise VisualIntelligenceStageError(
                    f"{beat_id}: single legal Candidate must not invent an alternative"
                )
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
        selected_by_beat[str(beat_id)] = candidate
        selection_by_beat[str(beat_id)] = selection

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


def _validate_critic(review: dict[str, Any], *, date: str, director_sha: str, compiled_sha: str, warning_sha: str) -> list[dict[str, Any]]:
    if review.get("contractVersion") != "1.0.0" or review.get("bridgeContractVersion") != BRIDGE_CONTRACT_VERSION:
        raise VisualIntelligenceStageError("Visual Critic canonical contract mismatch")
    if review.get("episodeDate") != date:
        raise VisualIntelligenceStageError("Visual Critic episodeDate mismatch")
    if review.get("directorDecisionSha256") != director_sha:
        raise VisualIntelligenceStageError("E_VISUAL_CRITIC_STALE: Director Decision SHA mismatch")
    if review.get("compiledVisualSha256") != compiled_sha:
        raise VisualIntelligenceStageError("E_VISUAL_CRITIC_STALE: compiled visual SHA mismatch")
    if review.get("warningReportSha256") != warning_sha:
        raise VisualIntelligenceStageError("E_VISUAL_CRITIC_STALE: warning report SHA mismatch")
    rounds = review.get("reviewRounds")
    if not isinstance(rounds, list) or not rounds or len(rounds) > 2:
        raise VisualIntelligenceStageError("Visual Critic requires one or two review rounds")
    for item in rounds:
        if not isinstance(item, dict):
            raise VisualIntelligenceStageError("Visual Critic round must be an object")
        status = item.get("status")
        if status not in artifacts.CRITIC_STATUSES:
            raise VisualIntelligenceStageError("Visual Critic status invalid")
        if status == "RETURN_TO_STORY":
            raise VisualIntelligenceStageError("E_VISUAL_RETURN_TO_STORY")
        if status == "BLOCKED":
            raise VisualIntelligenceStageError("E_VISUAL_BLOCKED")
    if rounds[-1].get("status") != "PASS":
        raise VisualIntelligenceStageError(
            "E_VISUAL_INTELLIGENCE_REVIEW_REQUIRED: Visual Critic has unresolved findings"
        )
    return rounds


def _candidate_coverage_pause(coverage: dict[str, Any], input_render: Path) -> None:
    if coverage.get("sourceRenderSpecSha256") != base.sha256_file(input_render):
        raise VisualIntelligenceStageError("E_VISUAL_CANDIDATE_COVERAGE_STALE: render SHA mismatch")
    if coverage.get("status") != "UNAVAILABLE":
        raise VisualIntelligenceStageError("E_VISUAL_CANDIDATE_COVERAGE_INVALID: expected UNAVAILABLE")
    unavailable = coverage.get("unavailableBeats")
    if not isinstance(unavailable, list) or not unavailable or not all(isinstance(item, str) for item in unavailable):
        raise VisualIntelligenceStageError("E_VISUAL_CANDIDATE_COVERAGE_INVALID: unavailableBeats missing")
    raise VisualIntelligenceStageError(
        "E_VISUAL_INTELLIGENCE_DECISION_REQUIRED:"
        "E_VISUAL_CANDIDATE_COVERAGE_UNAVAILABLE:"
        + ",".join(unavailable)
    )


def _ensure_candidate_artifacts(
    *,
    vi_dir: Path,
    render: dict[str, Any],
    requirements: dict[str, Any],
    snapshot_sha: str,
    output_root: Path,
    date: str,
    renderer_root: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> tuple[dict[str, Any], Path, Path, Path, Path, Path]:
    input_render = vi_dir / "visual_direction_input.json"
    candidate_input = vi_dir / "visual_candidate_input.json"
    inventory = vi_dir / "visual_capability_inventory.json"
    hints = vi_dir / "visual_capability_hints.json"
    catalog = vi_dir / "visual_candidate_catalog.json"
    coverage_path = vi_dir / "visual_candidate_coverage.json"
    asset_state = vi_dir / "asset_resolution_state.json"
    provider = vi_dir / "financial_candidate_provider.json"
    recent = vi_dir / "recent_visual_pattern_context.json"

    _write_once(input_render, render, "Visual Direction input")
    _write_once(
        hints,
        base._build_capability_hints(requirements=requirements, render=render, date=date),
        "Visual Capability Hints",
    )
    _write_once(asset_state, base._asset_resolution_state(output_root, date), "Asset Resolution State")
    if not provider.is_file():
        financial_candidate_provider.write(provider, financial_candidate_provider.build(render))
    _write_once(recent, base._phase1_recent_context(date), "Recent Visual Pattern Context")

    if coverage_path.is_file():
        coverage = base.load_json(coverage_path, "Visual Candidate Coverage")
        if coverage.get("sourceRenderSpecSha256") != base.sha256_file(input_render):
            raise VisualIntelligenceStageError("E_VISUAL_CANDIDATE_COVERAGE_STALE: render SHA mismatch")
        if coverage.get("status") == "UNAVAILABLE":
            if catalog.is_file():
                raise VisualIntelligenceStageError("E_VISUAL_CANDIDATE_PARTIAL_WRITE: unavailable coverage has Catalog")
            _candidate_coverage_pause(coverage, input_render)
        if coverage.get("status") != "PASS":
            raise VisualIntelligenceStageError("E_VISUAL_CANDIDATE_COVERAGE_INVALID: unsupported status")
        existence = [candidate_input.is_file(), inventory.is_file(), catalog.is_file()]
        if not all(existence):
            raise VisualIntelligenceStageError("E_VISUAL_CANDIDATE_PARTIAL_WRITE")
    else:
        if catalog.is_file():
            catalog.unlink()
        command = [
            "node", "--import", "tsx", "scripts/visual-director-cli.ts", "build",
            "--spec", str(input_render),
            "--catalog", str(catalog),
            "--coverage", str(coverage_path),
            "--hints", str(hints),
            "--candidate-builder", "vnext",
            "--editorial-snapshot-sha256", snapshot_sha,
            "--candidate-input", str(candidate_input),
            "--capability-inventory", str(inventory),
        ]
        completed = runner(
            command,
            cwd=renderer_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode not in (0, 3):
            detail = (
                completed.stderr
                or completed.stdout
                or "Renderer Visual Intelligence candidate build failed"
            ).strip()
            raise VisualIntelligenceStageError(detail)
        if not coverage_path.is_file():
            raise VisualIntelligenceStageError("E_VISUAL_CANDIDATE_COVERAGE_MISSING")
        coverage = base.load_json(coverage_path, "Visual Candidate Coverage")
        if completed.returncode == 3:
            if catalog.is_file():
                raise VisualIntelligenceStageError("E_VISUAL_CANDIDATE_PARTIAL_WRITE: unavailable coverage wrote Catalog")
            _candidate_coverage_pause(coverage, input_render)
        if coverage.get("sourceRenderSpecSha256") != base.sha256_file(input_render):
            raise VisualIntelligenceStageError("E_VISUAL_CANDIDATE_COVERAGE_STALE: render SHA mismatch")
        if coverage.get("status") != "PASS":
            raise VisualIntelligenceStageError("E_VISUAL_CANDIDATE_COVERAGE_INVALID: successful build did not PASS coverage")
        if not candidate_input.is_file() or not inventory.is_file() or not catalog.is_file():
            raise VisualIntelligenceStageError("E_VISUAL_CANDIDATE_PARTIAL_WRITE")

    value = base.load_json(catalog, "Visual Candidate Catalog")
    _validate_catalog_coverage(requirements=requirements, catalog=value)
    return value, catalog, candidate_input, inventory, hints, provider


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
        raise VisualIntelligenceStageError(
            "Visual Intelligence requires canonical render_spec 2.4.0 for the same date"
        )

    vi_dir = output_root / "working" / date / "visual-intelligence"
    vi_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = vi_dir / "editorial_snapshot.json"
    if not snapshot_path.is_file():
        _write_once(snapshot_path, base.build_editorial_snapshot(render), "Editorial Snapshot")
    snapshot = base.load_json(snapshot_path, "Editorial Snapshot")
    if snapshot.get("episodeDate") != date:
        raise VisualIntelligenceStageError("Editorial Snapshot episodeDate mismatch")
    snapshot_sha = base.sha256_file(snapshot_path)

    requirements = _requirements(vi_dir, date=date, snapshot_sha=snapshot_sha)
    requirements_path = vi_dir / artifacts.REQUIREMENTS_CANONICAL
    requirements_sha = base.sha256_file(requirements_path)
    catalog, catalog_path, candidate_input, inventory, hints, provider = _ensure_candidate_artifacts(
        vi_dir=vi_dir,
        render=render,
        requirements=requirements,
        snapshot_sha=snapshot_sha,
        output_root=output_root,
        date=date,
        renderer_root=renderer_root,
        runner=runner,
    )
    catalog_sha = base.sha256_file(catalog_path)
    catalog_content_sha = base.canonical_sha(catalog)

    director_semantic = vi_dir / artifacts.DIRECTOR_SEMANTIC
    if not director_semantic.is_file():
        raise VisualIntelligenceStageError(
            f"E_VISUAL_INTELLIGENCE_DECISION_REQUIRED: Candidate Catalog is ready; AI-B must author {artifacts.DIRECTOR_SEMANTIC}"
        )
    try:
        director_path = artifacts.materialize_director(vi_dir=vi_dir, date=date)
    except artifacts.VisualIntelligenceArtifactError as exc:
        raise VisualIntelligenceStageError(str(exc)) from exc
    director = base.load_json(director_path, "Visual Director Decision canonical")
    _validate_director(
        decision=director,
        requirements=requirements,
        date=date,
        snapshot_sha=snapshot_sha,
        requirements_sha=requirements_sha,
        beat_ids=base._beat_ids(render),
        catalog=catalog,
        catalog_sha=catalog_sha,
    )

    plan = vi_dir / "visual_direction_plan.json"
    compiled = vi_dir / "visual_direction_compiled_render.json"
    compile_report = vi_dir / "visual_direction_compile_report.json"
    warnings = vi_dir / "visual_editorial_warning_report.json"
    compiled_group = [plan.is_file(), compiled.is_file(), compile_report.is_file(), warnings.is_file()]
    if any(compiled_group) and not all(compiled_group):
        raise VisualIntelligenceStageError("E_VISUAL_COMPILE_PARTIAL_WRITE")
    if not all(compiled_group):
        _write_once(
            plan,
            {
                "contractVersion": "1.0.0",
                "episodeDate": date,
                "candidateCatalogSha256": catalog_content_sha,
                "selections": [
                    {
                        "visualBeatId": item["visualBeatId"],
                        "candidateId": item["selectedCandidateId"],
                    }
                    for item in director["selections"]
                ],
            },
            "Visual Direction Plan",
        )
        base._run_renderer(
            runner=runner,
            renderer_root=renderer_root,
            command=[
                "node", "--import", "tsx", "scripts/visual-director-cli.ts", "compile",
                "--spec", str(vi_dir / "visual_direction_input.json"),
                "--catalog", str(catalog_path),
                "--plan", str(plan),
                "--output", str(compiled),
                "--report", str(compile_report),
            ],
        )
        report = base.load_json(compile_report, "Visual Direction compile report")
        if report.get("semanticDiff") != "PASS":
            raise VisualIntelligenceStageError("E_VISUAL_SEMANTIC_DIFF_FAIL")
        _write_once(
            warnings,
            {
                "contractVersion": "1.0.0",
                "episodeDate": date,
                "classification": "editorial-warning-shadow",
                "sourceCompileReportSha256": base.sha256_file(compile_report),
                "warnings": [
                    {**item, "severity": "warning", "legacy": {"wouldFail": False}}
                    for item in report.get("warnings", [])
                    if isinstance(item, dict)
                ],
            },
            "Visual Editorial Warning Report",
        )
    else:
        plan_value = base.load_json(plan, "Visual Direction Plan")
        if plan_value.get("candidateCatalogSha256") != catalog_content_sha:
            raise VisualIntelligenceStageError("E_VISUAL_COMPILE_STALE: Candidate Catalog content SHA mismatch")
        report = base.load_json(compile_report, "Visual Direction compile report")
        if report.get("semanticDiff") != "PASS":
            raise VisualIntelligenceStageError("E_VISUAL_SEMANTIC_DIFF_FAIL")

    critic_semantic = vi_dir / artifacts.CRITIC_SEMANTIC
    if not critic_semantic.is_file():
        raise VisualIntelligenceStageError(
            f"E_VISUAL_INTELLIGENCE_REVIEW_REQUIRED: compiled visual and warnings are ready; AI-B Critic must author {artifacts.CRITIC_SEMANTIC}"
        )
    try:
        critic_path = artifacts.materialize_critic(vi_dir=vi_dir, date=date)
    except artifacts.VisualIntelligenceArtifactError as exc:
        raise VisualIntelligenceStageError(str(exc)) from exc
    critic = base.load_json(critic_path, "Visual Critic Review canonical")
    compiled_sha = base.sha256_file(compiled)
    warning_sha = base.sha256_file(warnings)
    rounds = _validate_critic(
        critic,
        date=date,
        director_sha=base.sha256_file(director_path),
        compiled_sha=compiled_sha,
        warning_sha=warning_sha,
    )

    recent = vi_dir / "recent_visual_pattern_context.json"
    asset_state = vi_dir / "asset_resolution_state.json"
    principles = plot_root / "skills/nasdaq-cafe-visual-intelligence/references/VISUAL_EDITORIAL_INTELLIGENCE.md"
    registry = renderer_root / binding["renderer"]["registrySnapshotPath"]
    package = vi_dir / "visual_intelligence_package.json"
    package_value = {
        "contractVersion": "1.0.0",
        "bridgeContractVersion": BRIDGE_CONTRACT_VERSION,
        "episodeDate": date,
        "inputs": {
            "editorialSnapshotSha256": snapshot_sha,
            "rendererCommit": expected_renderer_commit,
            "registrySnapshotSha256": base.sha256_file(registry),
            "recentVisualPatternContextSha256": base.sha256_file(recent),
            "visualEditorialPrinciplesSha256": base.sha256_file(principles),
            "visualRequirementsSha256": requirements_sha,
            "capabilityHintsSha256": base.sha256_file(hints),
            "visualDirectorDecisionSha256": base.sha256_file(director_path),
        },
        "intent": requirements["intent"],
        "provisionalDirection": requirements["provisionalDirection"],
        "assetResolution": {"sha256": base.sha256_file(asset_state)},
        "director": {
            "candidateCatalogSha256": catalog_sha,
            "selections": director["selections"],
        },
        "critic": {"visualCriticReviewSha256": base.sha256_file(critic_path)},
        "reviewRounds": rounds,
        "final": {
            "status": "PASS",
            "visualDirectionPlanSha256": base.sha256_file(plan),
            "compiledVisualSha256": compiled_sha,
            "warningReportSha256": warning_sha,
            "recentVisualPatternContextSha256": base.sha256_file(recent),
            "visualEditorialPrinciplesSha256": base.sha256_file(principles),
            "criticReviewSha256": base.sha256_file(critic_path),
        },
    }
    _write_once(package, package_value, "Visual Intelligence Package")
    return {
        "render": base.load_json(compiled, "Compiled Visual"),
        "package_path": package,
        "catalog_path": catalog_path,
        "candidate_input_path": candidate_input,
        "capability_inventory_path": inventory,
        "compile_report_path": compile_report,
        "warning_report_path": warnings,
        "financial_provider_path": provider,
        "editorial_snapshot_path": snapshot_path,
        "director_path": director_path,
        "critic_path": critic_path,
    }
