#!/usr/bin/env python3
"""Machine bridge for visual-intelligence-bridge/1.2.0.

Machine responsibilities only:
- freeze Story semantics into an editorial snapshot
- verify asset resolution / fallback completion
- invoke Renderer vNext Candidate Builder
- validate an AI-B-authored candidate decision
- compile only selected legal Candidate IDs
- preserve Protected Semantic Diff
- materialize frozen shared artifacts and SHA lineage

This module never decides which Candidate is interesting or rewrites Story meaning.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable

import financial_candidate_provider
import renderer_binding

BRIDGE_CONTRACT_VERSION = renderer_binding.BRIDGE_CONTRACT_VERSION
FROZEN_INTERFACE_SHA256 = renderer_binding.FROZEN_INTERFACE_SHA256
CRITIC_STATUSES = {"PASS", "REVISE", "RETURN_TO_STORY", "BLOCKED"}
REALITY_PREFERENCES = {"required", "preferred", "neutral", "avoid"}
IMAGE_REQUIREMENTS = {"required", "possible", "not-required"}


class VisualIntelligenceBridgeError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualIntelligenceBridgeError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualIntelligenceBridgeError(f"{label} must be an object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _beat_ids(render: dict[str, Any]) -> list[str]:
    return [
        beat["beatId"]
        for scene in render.get("scenes", [])
        for beat in scene.get("visualBeats", [])
    ]


def build_editorial_snapshot(render: dict[str, Any]) -> dict[str, Any]:
    """Create a Visual-independent Story snapshot used for invalidation.

    Visual selection/materialization fields are intentionally excluded. Story,
    narration, evidence, uncertainty and Beat semantic cues remain bound.
    """

    scenes: list[dict[str, Any]] = []
    for scene_index, scene in enumerate(render.get("scenes", []), start=1):
        beats: list[dict[str, Any]] = []
        for beat in scene.get("visualBeats", []):
            beats.append({
                key: beat.get(key)
                for key in (
                    "beatId",
                    "startChunkId",
                    "endChunkId",
                    "narrationStartCue",
                    "narrationEndCue",
                    "primaryFunction",
                    "contentType",
                    "screenQuestion",
                    "primaryElement",
                    "viewerTexts",
                    "changeCue",
                    "returnScreenState",
                    "evidenceSourceIds",
                    "expressionChange",
                    "fallback",
                    "financialReturnTarget",
                    "entity",
                    "pictureBook",
                )
                if key in beat
            })
        scenes.append({
            "sceneId": scene.get("sceneId", f"scene-{scene_index:02d}"),
            "narrationChunks": scene.get("narrationChunks", []),
            "visualBeats": beats,
        })
    return {
        "contractVersion": "1.0.0",
        "episodeDate": render.get("episode", {}).get("targetDate"),
        "episode": render.get("episode"),
        "editorial": render.get("editorial"),
        "sources": render.get("sources", []),
        "review": render.get("review"),
        "publishing": render.get("publishing"),
        "scenes": scenes,
    }


def _asset_resolution_state(output_root: Path, date: str) -> dict[str, Any]:
    audit = output_root / "verification" / date / "asset_resolution_log.json"
    if audit.is_file():
        value = load_json(audit, "asset resolution log")
        if value.get("status") != "resolved":
            raise VisualIntelligenceBridgeError("E_VISUAL_ASSET_RESOLUTION_UNRESOLVED")
        logged_date = value.get("episode_date") or value.get("episodeDate")
        if logged_date is not None and logged_date != date:
            raise VisualIntelligenceBridgeError("E_VISUAL_ASSET_RESOLUTION_UNRESOLVED")

        # Current resolver writes a flat record. Keep legacy nested `selection`
        # compatibility during migration, but normalize both to one frozen state.
        selection = value.get("selection")
        if isinstance(selection, dict):
            if selection.get("status") != "resolved" or selection.get("unresolved_count") != 0:
                raise VisualIntelligenceBridgeError("E_VISUAL_ASSET_RESOLUTION_UNRESOLVED")
            selected_path = selection.get("selected_path")
            intent_routes = selection.get("intent_routes", {})
        else:
            if value.get("unresolved_count") != 0:
                raise VisualIntelligenceBridgeError("E_VISUAL_ASSET_RESOLUTION_UNRESOLVED")
            selected_path = value.get("selected_path")
            intent_routes = value.get("intent_routes", {})

        if not isinstance(selected_path, str) or not selected_path.strip():
            raise VisualIntelligenceBridgeError("E_VISUAL_ASSET_RESOLUTION_UNRESOLVED")
        if not isinstance(intent_routes, dict):
            raise VisualIntelligenceBridgeError("E_VISUAL_ASSET_RESOLUTION_UNRESOLVED")
        return {
            "contractVersion": "1.0.0",
            "episodeDate": date,
            "status": "resolved",
            "selectedPath": selected_path,
            "intentRoutes": intent_routes,
            "assetResolutionLogSha256": sha256_file(audit),
        }

    intents_path = output_root / "working" / date / "visual_source_intents.json"
    if not intents_path.is_file():
        raise VisualIntelligenceBridgeError("E_VISUAL_ASSET_RESOLUTION_MISSING")
    intents = load_json(intents_path, "Visual Source intents")
    items = intents.get("intents")
    if items != []:
        raise VisualIntelligenceBridgeError(
            "E_VISUAL_ASSET_RESOLUTION_MISSING: non-empty Primary/Fallback plan requires resolved audit"
        )
    return {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "status": "not-required",
        "selectedPath": "not-required",
        "intentRoutes": {},
        "planningSha256": sha256_file(intents_path),
    }


def _phase1_recent_context(date: str) -> dict[str, Any]:
    return {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "mode": "phase-1",
        "approvedEpisodes": [],
        "status": "unassessed",
        "reason": "Phase 1 does not infer success from unapproved previews",
    }


def _verify_renderer(plot_root: Path, renderer_root: Path, expected_renderer_commit: str) -> dict[str, Any]:
    binding = renderer_binding.verify_renderer_checkout(plot_root, renderer_root)
    actual = binding["renderer"]["commit"]
    if actual != expected_renderer_commit:
        raise VisualIntelligenceBridgeError(
            f"E_VISUAL_RENDERER_BINDING_MISMATCH: expected {expected_renderer_commit} binding {actual}"
        )
    return binding


def _run_renderer(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]],
    renderer_root: Path,
    command: list[str],
) -> None:
    completed = runner(
        command,
        cwd=renderer_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "Renderer Visual Intelligence command failed").strip()
        raise VisualIntelligenceBridgeError(detail)


def _validate_decision(
    *,
    decision: dict[str, Any],
    date: str,
    beat_ids: list[str],
    catalog: dict[str, Any],
) -> None:
    if decision.get("contractVersion") != "1.0.0":
        raise VisualIntelligenceBridgeError("Visual Intelligence decision contractVersion must be 1.0.0")
    if decision.get("bridgeContractVersion") != BRIDGE_CONTRACT_VERSION:
        raise VisualIntelligenceBridgeError("Visual Intelligence decision bridgeContractVersion mismatch")
    if decision.get("episodeDate") != date:
        raise VisualIntelligenceBridgeError("Visual Intelligence decision episodeDate mismatch")

    intent = decision.get("intent")
    if not isinstance(intent, dict) or not isinstance(intent.get("beats"), list):
        raise VisualIntelligenceBridgeError("Visual Intelligence decision intent.beats missing")
    intents = intent["beats"]
    if [item.get("visualBeatId") for item in intents] != beat_ids:
        raise VisualIntelligenceBridgeError("Visual Intent must cover every Beat in Story order")
    for item in intents:
        if not all(isinstance(item.get(key), str) and item[key].strip() for key in (
            "purpose", "audienceBeliefBefore", "audienceBeliefAfter", "visualInformationGain", "editorialReason"
        )):
            raise VisualIntelligenceBridgeError(f"{item.get('visualBeatId')}: incomplete Visual Intent")
        if item.get("realityAnchorPreference") not in REALITY_PREFERENCES:
            raise VisualIntelligenceBridgeError(f"{item.get('visualBeatId')}: invalid realityAnchorPreference")
        if not isinstance(item.get("preferredEvidenceModes"), list):
            raise VisualIntelligenceBridgeError(f"{item.get('visualBeatId')}: preferredEvidenceModes must be an array")

    provisional = decision.get("provisionalDirection")
    if not isinstance(provisional, dict) or not isinstance(provisional.get("requirements"), list):
        raise VisualIntelligenceBridgeError("Visual Intelligence provisionalDirection.requirements missing")
    requirements = provisional["requirements"]
    if [item.get("visualBeatId") for item in requirements] != beat_ids:
        raise VisualIntelligenceBridgeError("Provisional Direction must cover every Beat in Story order")
    for item in requirements:
        if item.get("imageRequirement") not in IMAGE_REQUIREMENTS:
            raise VisualIntelligenceBridgeError(f"{item.get('visualBeatId')}: invalid imageRequirement")
        if not isinstance(item.get("requiredModes"), list) or not isinstance(item.get("reason"), str):
            raise VisualIntelligenceBridgeError(f"{item.get('visualBeatId')}: invalid Provisional Direction")

    director = decision.get("director")
    if not isinstance(director, dict) or not isinstance(director.get("selections"), list):
        raise VisualIntelligenceBridgeError("Visual Intelligence director.selections missing")
    selections = director["selections"]
    if [item.get("visualBeatId") for item in selections] != beat_ids:
        raise VisualIntelligenceBridgeError("Director must select exactly one Candidate for every Beat")
    candidates = catalog.get("candidates")
    if not isinstance(candidates, list):
        raise VisualIntelligenceBridgeError("Visual Candidate Catalog candidates missing")
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
            raise VisualIntelligenceBridgeError(f"{beat_id}: selectedCandidateId is not a legal Candidate")
        alternatives = by_beat.get(beat_id, [])
        strongest = selection.get("strongestAlternativeCandidateId")
        if len(alternatives) == 1:
            if strongest is not None:
                raise VisualIntelligenceBridgeError(f"{beat_id}: single legal Candidate must not invent an alternative")
        else:
            alt = by_id.get(strongest)
            if not isinstance(alt, dict) or alt.get("visualBeatId") != beat_id or strongest == selected_id:
                raise VisualIntelligenceBridgeError(f"{beat_id}: strongest alternative is invalid")
        if not isinstance(selection.get("whySelected"), str) or not isinstance(selection.get("whyNotAlternative"), str):
            raise VisualIntelligenceBridgeError(f"{beat_id}: Director rationale fields missing")

    rounds = decision.get("reviewRounds")
    if not isinstance(rounds, list) or not 1 <= len(rounds) <= 2:
        raise VisualIntelligenceBridgeError("Visual Critic requires one or two review rounds")
    for item in rounds:
        status = item.get("status") if isinstance(item, dict) else None
        if status not in CRITIC_STATUSES:
            raise VisualIntelligenceBridgeError("Visual Critic status is invalid")
        if status == "RETURN_TO_STORY":
            raise VisualIntelligenceBridgeError("E_VISUAL_RETURN_TO_STORY")
        if status == "BLOCKED":
            raise VisualIntelligenceBridgeError("E_VISUAL_BLOCKED")
    if rounds[-1].get("status") != "PASS":
        raise VisualIntelligenceBridgeError("Visual Critic has unresolved findings")


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
    binding = _verify_renderer(plot_root, renderer_root, expected_renderer_commit)
    if render.get("schemaVersion") != "2.4.0":
        raise VisualIntelligenceBridgeError("Visual Intelligence requires render_spec 2.4.0")
    if render.get("episode", {}).get("targetDate") != date:
        raise VisualIntelligenceBridgeError("Visual Intelligence render episodeDate mismatch")

    vi_dir = output_root / "working" / date / "visual-intelligence"
    vi_dir.mkdir(parents=True, exist_ok=True)
    input_render = vi_dir / "visual_direction_input.json"
    editorial_snapshot_path = vi_dir / "editorial_snapshot.json"
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

    editorial_snapshot = build_editorial_snapshot(render)
    write_json(editorial_snapshot_path, editorial_snapshot)
    editorial_snapshot_sha = sha256_file(editorial_snapshot_path)
    asset_state = _asset_resolution_state(output_root, date)
    write_json(asset_state_path, asset_state)
    financial_provider = financial_candidate_provider.build(render)
    write_json(financial_provider_path, financial_provider)
    write_json(recent_context_path, _phase1_recent_context(date))
    write_json(input_render, render)

    build_command = [
        "node", "--import", "tsx", "scripts/visual-director-cli.ts", "build",
        "--spec", str(input_render),
        "--catalog", str(catalog_path),
        "--candidate-builder", "vnext",
        "--editorial-snapshot-sha256", editorial_snapshot_sha,
        "--candidate-input", str(candidate_input_path),
        "--capability-inventory", str(capability_inventory_path),
    ]
    _run_renderer(runner=runner, renderer_root=renderer_root, command=build_command)
    catalog = load_json(catalog_path, "Visual Candidate Catalog")
    if catalog.get("episodeDate") != date:
        raise VisualIntelligenceBridgeError("Visual Candidate Catalog episodeDate mismatch")

    if not decision_path.is_file():
        raise VisualIntelligenceBridgeError(
            "E_VISUAL_INTELLIGENCE_DECISION_REQUIRED: Candidate Catalog is ready; AI-B must author visual_intelligence_decision.json"
        )
    decision = load_json(decision_path, "Visual Intelligence decision")
    beat_ids = _beat_ids(render)
    _validate_decision(decision=decision, date=date, beat_ids=beat_ids, catalog=catalog)

    catalog_sha = canonical_sha(catalog)
    selections = [
        {
            "visualBeatId": item["visualBeatId"],
            "candidateId": item["selectedCandidateId"],
        }
        for item in decision["director"]["selections"]
    ]
    plan = {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "candidateCatalogSha256": catalog_sha,
        "selections": selections,
    }
    write_json(plan_path, plan)
    compile_command = [
        "node", "--import", "tsx", "scripts/visual-director-cli.ts", "compile",
        "--spec", str(input_render),
        "--catalog", str(catalog_path),
        "--plan", str(plan_path),
        "--output", str(compiled_path),
        "--report", str(compile_report_path),
    ]
    _run_renderer(runner=runner, renderer_root=renderer_root, command=compile_command)
    compile_report = load_json(compile_report_path, "Visual Direction compile report")
    if compile_report.get("semanticDiff") != "PASS":
        raise VisualIntelligenceBridgeError("E_VISUAL_SEMANTIC_DIFF_FAIL")
    compiled = load_json(compiled_path, "compiled render")

    warning_report = {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "classification": "editorial-warning-shadow",
        "sourceCompileReportSha256": sha256_file(compile_report_path),
        "warnings": [
            {
                **item,
                "severity": "warning",
                "legacy": {"wouldFail": False},
            }
            for item in compile_report.get("warnings", [])
            if isinstance(item, dict)
        ],
    }
    write_json(warning_report_path, warning_report)
    review = decision["reviewRounds"][-1]
    write_json(review_path, review)

    registry_snapshot_path = renderer_root / binding["renderer"]["registrySnapshotPath"]
    principles_path = plot_root / "skills/nasdaq-cafe-visual-intelligence/references/VISUAL_EDITORIAL_INTELLIGENCE.md"
    if not principles_path.is_file():
        raise VisualIntelligenceBridgeError(f"Visual editorial principles missing: {principles_path}")
    recent_sha = sha256_file(recent_context_path)
    principles_sha = sha256_file(principles_path)
    package = {
        "contractVersion": "1.0.0",
        "bridgeContractVersion": BRIDGE_CONTRACT_VERSION,
        "episodeDate": date,
        "inputs": {
            "editorialSnapshotSha256": editorial_snapshot_sha,
            "rendererCommit": expected_renderer_commit,
            "registrySnapshotSha256": sha256_file(registry_snapshot_path),
            "recentVisualPatternContextSha256": recent_sha,
            "visualEditorialPrinciplesSha256": principles_sha,
        },
        "intent": decision["intent"],
        "provisionalDirection": decision["provisionalDirection"],
        "assetResolution": {"sha256": sha256_file(asset_state_path)},
        "director": {
            "candidateCatalogSha256": catalog_sha,
            "selections": decision["director"]["selections"],
        },
        "reviewRounds": decision["reviewRounds"],
        "final": {
            "status": "PASS",
            "visualDirectionPlanSha256": sha256_file(plan_path),
            "compiledVisualSha256": sha256_file(compiled_path),
            "warningReportSha256": sha256_file(warning_report_path),
            "recentVisualPatternContextSha256": recent_sha,
            "visualEditorialPrinciplesSha256": principles_sha,
            "reviewSha256": sha256_file(review_path),
        },
    }
    write_json(package_path, package)
    return {
        "render": compiled,
        "package_path": package_path,
        "catalog_path": catalog_path,
        "candidate_input_path": candidate_input_path,
        "capability_inventory_path": capability_inventory_path,
        "compile_report_path": compile_report_path,
        "warning_report_path": warning_report_path,
        "financial_provider_path": financial_provider_path,
        "editorial_snapshot_path": editorial_snapshot_path,
    }
