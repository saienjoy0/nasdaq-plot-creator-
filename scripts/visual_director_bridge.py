#!/usr/bin/env python3
"""Run Visual Intelligence 1.2 as a checkpointed pre-render bridge.

Machine responsibilities here are deliberately narrow:
- freeze the exact editorial snapshot;
- ask the pinned Renderer vNext builder for legal candidates;
- project an AI-B-authored editorial selection into a candidate-ID-only plan;
- compile without protected-semantic drift;
- expose mechanical warnings for the independent AI-B critic;
- freeze a SHA-bound Visual Intelligence package only after the critic says PASS.

The bridge never chooses a candidate, never rewrites narration/causality, and never
silently falls back to legacy authored-only production behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

BRIDGE_CONTRACT_VERSION = "visual-intelligence-bridge/1.2.0"


class VisualDirectorBridgeError(ValueError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualDirectorBridgeError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualDirectorBridgeError(f"{label} root must be an object")
    return value


def write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temp = path.with_name(f".{path.name}.visual-intelligence.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise VisualDirectorBridgeError(f"{label} required: {path}")
    return path


def _renderer_head(renderer_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=renderer_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise VisualDirectorBridgeError(
            f"cannot inspect pinned renderer checkout: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _run_renderer(
    renderer_root: Path,
    command: str,
    arguments: list[str],
) -> None:
    cli = renderer_root / "scripts" / "visual-director-cli.ts"
    if not cli.is_file():
        raise VisualDirectorBridgeError(
            f"pinned renderer lacks Visual Director CLI: {cli}"
        )
    result = subprocess.run(
        ["node", "--import", "tsx", str(cli), command, *arguments],
        cwd=renderer_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise VisualDirectorBridgeError(
            f"Visual Director {command} failed: {detail}"
        )


def _require_editorial_input(path: Path, *, date: str, collection: str, label: str) -> dict[str, Any]:
    value = load_json(_require_file(path, label), label)
    if value.get("contractVersion") != "1.0.0" or value.get("episodeDate") != date:
        raise VisualDirectorBridgeError(f"{label} contractVersion/episodeDate mismatch")
    rows = value.get(collection)
    if not isinstance(rows, list):
        raise VisualDirectorBridgeError(f"{label} {collection} must be an array")
    return value


def _ensure_phase1_recent_context(path: Path, *, date: str) -> dict[str, Any]:
    if path.is_file():
        value = load_json(path, "Recent Visual Pattern Context")
        if value.get("episodeDate") != date:
            raise VisualDirectorBridgeError("Recent Visual Pattern Context episodeDate mismatch")
        return value
    value = {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "status": "not-available",
        "reason": "Phase 1 does not require cross-episode approved-pattern retrieval",
        "approvedEpisodes": [],
    }
    write_atomic(path, value)
    return value


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


def _validate_editorial_selection(
    *,
    path: Path,
    date: str,
    catalog: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    selection = load_json(_require_file(path, "Visual Editorial Selection"), "Visual Editorial Selection")
    if selection.get("contractVersion") != "1.0.0" or selection.get("episodeDate") != date:
        raise VisualDirectorBridgeError("Visual Editorial Selection contractVersion/episodeDate mismatch")
    round_number = selection.get("round")
    if round_number not in {1, 2}:
        raise VisualDirectorBridgeError("Visual Editorial Selection round must be 1 or 2")
    rows = selection.get("selections")
    if not isinstance(rows, list) or not rows:
        raise VisualDirectorBridgeError("Visual Editorial Selection selections must be a non-empty array")

    legal = _candidate_map(catalog)
    observed: set[str] = set()
    plan_rows: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise VisualDirectorBridgeError("Visual Editorial Selection row must be an object")
        required = {
            "visualBeatId",
            "selectedCandidateId",
            "strongestAlternativeCandidateId",
            "whySelected",
            "whyNotAlternative",
        }
        if not required.issubset(row):
            raise VisualDirectorBridgeError("Visual Editorial Selection row lacks frozen fields")
        beat = row["visualBeatId"]
        selected = row["selectedCandidateId"]
        alternative = row["strongestAlternativeCandidateId"]
        if not isinstance(beat, str) or not isinstance(selected, str):
            raise VisualDirectorBridgeError("Visual Editorial Selection IDs must be strings")
        if beat in observed:
            raise VisualDirectorBridgeError(f"duplicate Visual Editorial Selection Beat: {beat}")
        candidates = legal.get(beat, set())
        if selected not in candidates:
            raise VisualDirectorBridgeError(f"selected Candidate is not legal: beat={beat} candidate={selected}")
        if len(candidates) > 1:
            if not isinstance(alternative, str) or alternative == selected or alternative not in candidates:
                raise VisualDirectorBridgeError(
                    f"multiple legal Candidates require a valid strongest alternative: beat={beat}"
                )
        elif alternative is not None:
            raise VisualDirectorBridgeError(
                f"single legal Candidate must not invent an alternative: beat={beat}"
            )
        if not isinstance(row["whySelected"], str) or not row["whySelected"]:
            raise VisualDirectorBridgeError(f"whySelected required: beat={beat}")
        if not isinstance(row["whyNotAlternative"], str):
            raise VisualDirectorBridgeError(f"whyNotAlternative must be a string: beat={beat}")
        observed.add(beat)
        plan_rows.append({"visualBeatId": beat, "candidateId": selected})

    expected_beats = set(legal)
    if observed != expected_beats:
        missing = sorted(expected_beats - observed)
        extra = sorted(observed - expected_beats)
        raise VisualDirectorBridgeError(
            f"Visual Editorial Selection must cover Candidate Catalog Beats: missing={missing} extra={extra}"
        )
    plan = {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "candidateCatalogSha256": "",
        "selections": plan_rows,
    }
    return selection, plan


def _validate_review(
    *,
    path: Path,
    date: str,
    round_number: int,
    editorial_snapshot_sha: str,
    catalog_sha: str,
    plan_sha: str,
    compile_report_sha: str,
) -> dict[str, Any]:
    review = load_json(_require_file(path, "Visual Direction Review"), "Visual Direction Review")
    if review.get("contractVersion") != "1.0.0" or review.get("episodeDate") != date:
        raise VisualDirectorBridgeError("Visual Direction Review contractVersion/episodeDate mismatch")
    if review.get("round") != round_number:
        raise VisualDirectorBridgeError("Visual Direction Review round mismatch")
    status = review.get("status")
    if status not in {"PASS", "REVISE", "RETURN_TO_STORY", "BLOCKED"}:
        raise VisualDirectorBridgeError("Visual Direction Review has unknown status")
    expected = {
        "sourceEditorialSnapshotSha256": editorial_snapshot_sha,
        "sourceCandidateCatalogSha256": catalog_sha,
        "sourceVisualDirectionPlanSha256": plan_sha,
        "sourceCompileReportSha256": compile_report_sha,
    }
    for key, value in expected.items():
        if review.get(key) != value:
            raise VisualDirectorBridgeError(f"Visual Direction Review {key} mismatch")
    if status == "REVISE":
        raise VisualDirectorBridgeError("E_VISUAL_DIRECTION_REVISE_REQUIRED: patch candidate selection only, then recompile/re-review")
    if status == "RETURN_TO_STORY":
        raise VisualDirectorBridgeError("E_VISUAL_DIRECTION_RETURN_TO_STORY: regenerate editorial snapshot after Story/04 re-review")
    if status == "BLOCKED":
        raise VisualDirectorBridgeError("E_VISUAL_DIRECTION_BLOCKED: no legal candidate/fallback can provide the required understanding function")
    return review


def _review_rounds(work: Path, *, current_review: dict[str, Any], current_review_path: Path) -> list[dict[str, Any]]:
    round_number = current_review["round"]
    archive = work / f"visual_direction_review_round_{round_number}.json"
    if archive.is_file():
        archived = load_json(archive, f"Visual Direction Review round {round_number}")
        if archived != current_review:
            raise VisualDirectorBridgeError(f"Visual Direction Review round {round_number} archive is immutable")
    else:
        write_atomic(archive, current_review)

    rows: list[dict[str, Any]] = []
    for index in range(1, round_number + 1):
        path = work / f"visual_direction_review_round_{index}.json"
        if not path.is_file():
            raise VisualDirectorBridgeError(f"missing Visual Direction Review round archive: {index}")
        value = load_json(path, f"Visual Direction Review round {index}")
        rows.append(
            {
                "round": index,
                "status": value.get("status"),
                "reviewSha256": sha256_file(path),
            }
        )
    rows[-1]["reviewSha256"] = sha256_file(current_review_path)
    return rows


def prepare_and_compile(
    *,
    render: dict[str, Any],
    output_root: Path,
    date: str,
    renderer_root: Path,
    expected_renderer_commit: str,
    runner: Callable[[Path, str, list[str]], None] = _run_renderer,
    renderer_head: Callable[[Path], str] = _renderer_head,
) -> dict[str, Any]:
    output_root = output_root.resolve()
    renderer_root = renderer_root.resolve()
    observed_commit = renderer_head(renderer_root)
    if observed_commit != expected_renderer_commit:
        raise VisualDirectorBridgeError(
            "Visual Director renderer checkout SHA mismatch: "
            f"expected={expected_renderer_commit} actual={observed_commit}"
        )
    if render.get("episode", {}).get("targetDate") != date:
        raise VisualDirectorBridgeError("Visual Director render episodeDate mismatch")

    work = output_root / "working" / date / "visual-intelligence"
    verification = output_root / "verification" / date
    work.mkdir(parents=True, exist_ok=True)
    verification.mkdir(parents=True, exist_ok=True)

    editorial_snapshot_path = work / "editorial_snapshot.json"
    candidate_input_path = work / "visual_candidate_input.json"
    capability_inventory_path = work / "visual_capability_inventory.json"
    catalog_path = work / "visual_candidate_catalog.json"
    intent_path = work / "visual_intent.json"
    provisional_path = work / "provisional_visual_direction.json"
    selection_path = work / "visual_editorial_selection.json"
    plan_path = work / "visual_direction_plan.json"
    compiled_path = work / "visual_direction_compiled_render.json"
    report_path = work / "visual_direction_compile_report.json"
    warning_path = work / "visual_editorial_warning_report.json"
    review_path = work / "visual_direction_review.json"
    package_path = work / "visual_intelligence_package.json"
    recent_context_path = work / "recent_visual_pattern_context.json"

    write_atomic(editorial_snapshot_path, render)
    editorial_snapshot_sha = sha256_file(editorial_snapshot_path)
    intent = _require_editorial_input(
        intent_path, date=date, collection="beats", label="Visual Intent"
    )
    provisional = _require_editorial_input(
        provisional_path,
        date=date,
        collection="requirements",
        label="Provisional Visual Direction",
    )
    _ensure_phase1_recent_context(recent_context_path, date=date)

    build_arguments = [
        "--spec",
        str(editorial_snapshot_path),
        "--catalog",
        str(catalog_path),
        "--candidate-builder",
        "vnext",
        "--editorial-snapshot-sha256",
        editorial_snapshot_sha,
        "--candidate-input",
        str(candidate_input_path),
        "--capability-inventory",
        str(capability_inventory_path),
    ]
    runner(renderer_root, "build", build_arguments)

    candidate_input = load_json(candidate_input_path, "VisualCandidateInput")
    inventory = load_json(capability_inventory_path, "Capability Inventory")
    catalog = load_json(catalog_path, "Visual Candidate Catalog")
    if candidate_input.get("episodeDate") != date or candidate_input.get("editorialSnapshotSha256") != editorial_snapshot_sha:
        raise VisualDirectorBridgeError("VisualCandidateInput editorial snapshot binding mismatch")
    if inventory.get("episodeDate") != date or inventory.get("visualCandidateInputSha256") != sha256_file(candidate_input_path):
        raise VisualDirectorBridgeError("Capability Inventory VisualCandidateInput binding mismatch")
    if catalog.get("episodeDate") != date or catalog.get("sourceRenderSpecSha256") != editorial_snapshot_sha:
        raise VisualDirectorBridgeError("Visual Candidate Catalog editorial snapshot binding mismatch")
    if not catalog.get("candidates"):
        raise VisualDirectorBridgeError("E_VISUAL_CANDIDATE_CATALOG_EMPTY: vNext produced no legal Candidates")

    if not selection_path.is_file():
        raise VisualDirectorBridgeError(
            "E_VISUAL_DIRECTION_SELECTION_REQUIRED: review visual-intelligence/visual_candidate_catalog.json "
            "with the AI-B Skill and author visual_editorial_selection.json"
        )
    selection, plan = _validate_editorial_selection(
        path=selection_path,
        date=date,
        catalog=catalog,
    )
    plan["candidateCatalogSha256"] = sha256_file(catalog_path)
    write_atomic(plan_path, plan)

    runner(
        renderer_root,
        "compile",
        [
            "--spec",
            str(editorial_snapshot_path),
            "--catalog",
            str(catalog_path),
            "--plan",
            str(plan_path),
            "--output",
            str(compiled_path),
            "--report",
            str(report_path),
        ],
    )
    compiled = load_json(compiled_path, "Visual Director compiled render")
    report = load_json(report_path, "Visual Direction compile report")
    if report.get("semanticDiff") != "PASS":
        raise VisualDirectorBridgeError("Visual Director Protected Semantic Diff did not PASS")
    if report.get("sourceRenderSpecSha256") != editorial_snapshot_sha:
        raise VisualDirectorBridgeError("Visual Direction compile report editorial snapshot binding mismatch")
    warning_report = {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "sourceCompileReportSha256": sha256_file(report_path),
        "warnings": report.get("warnings", []),
    }
    write_atomic(warning_path, warning_report)

    if not review_path.is_file():
        raise VisualDirectorBridgeError(
            "E_VISUAL_DIRECTION_REVIEW_REQUIRED: run the independent AI-B Visual Plan Critic "
            "against the compiled plan and visual_editorial_warning_report.json"
        )
    review = _validate_review(
        path=review_path,
        date=date,
        round_number=selection["round"],
        editorial_snapshot_sha=editorial_snapshot_sha,
        catalog_sha=sha256_file(catalog_path),
        plan_sha=sha256_file(plan_path),
        compile_report_sha=sha256_file(report_path),
    )

    asset_resolution_path = _require_file(
        verification / "asset_resolution_log.json", "Asset Resolution Log"
    )
    principles_path = _require_file(
        output_root
        / "skills/nasdaq-cafe-visual-intelligence/references/VISUAL_EDITORIAL_INTELLIGENCE.md",
        "Visual Editorial Principles",
    )
    registry_path = _require_file(
        renderer_root / "contracts/visual_component_registry_snapshot.json",
        "Renderer Visual Component Registry snapshot",
    )
    review_rounds = _review_rounds(
        work,
        current_review=review,
        current_review_path=review_path,
    )
    package = {
        "contractVersion": "1.0.0",
        "bridgeContractVersion": BRIDGE_CONTRACT_VERSION,
        "episodeDate": date,
        "inputs": {
            "editorialSnapshotSha256": editorial_snapshot_sha,
            "rendererCommit": expected_renderer_commit,
            "registrySnapshotSha256": sha256_file(registry_path),
            "recentVisualPatternContextSha256": sha256_file(recent_context_path),
            "visualEditorialPrinciplesSha256": sha256_file(principles_path),
        },
        "intent": {"beats": intent["beats"]},
        "provisionalDirection": {"requirements": provisional["requirements"]},
        "assetResolution": {"sha256": sha256_file(asset_resolution_path)},
        "director": {
            "candidateCatalogSha256": sha256_file(catalog_path),
            "selections": selection["selections"],
        },
        "reviewRounds": review_rounds,
        "final": {
            "status": "PASS",
            "visualDirectionPlanSha256": sha256_file(plan_path),
            "compiledVisualSha256": sha256_file(compiled_path),
            "warningReportSha256": sha256_file(warning_path),
            "recentVisualPatternContextSha256": sha256_file(recent_context_path),
            "visualEditorialPrinciplesSha256": sha256_file(principles_path),
            "reviewSha256": sha256_file(review_path),
        },
    }
    write_atomic(package_path, package)

    return {
        "render": compiled,
        "catalog_path": catalog_path,
        "plan_path": plan_path,
        "report_path": report_path,
        "input_path": editorial_snapshot_path,
        "candidate_input_path": candidate_input_path,
        "capability_inventory_path": capability_inventory_path,
        "compiled_path": compiled_path,
        "warning_report_path": warning_path,
        "review_path": review_path,
        "package_path": package_path,
        "recent_context_path": recent_context_path,
        "warnings": report.get("warnings", []),
    }
