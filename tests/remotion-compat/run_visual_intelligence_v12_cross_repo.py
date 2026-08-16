#!/usr/bin/env python3
"""Synthetic cross-repo acceptance for visual-intelligence-bridge/1.2.0.

This test makes no editorial recommendation. It uses the Renderer's current synthetic
fixture and an identity-preserving authored selection only to prove the frozen order:
requirements -> Candidate generation -> Director -> Compile/Warnings -> Critic -> PASS.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_visual_intelligence_package as package_validator  # noqa: E402
import visual_intelligence_bridge as base_bridge  # noqa: E402
import visual_intelligence_bridge_staged as staged_bridge  # noqa: E402

# Exact enum from the pinned Renderer's visual_candidate_catalog.schema.json.
# Synthetic acceptance is deliberately capability-broad: it validates machinery,
# not a fake editorial preference that could accidentally outlaw the fixture's
# authored identity Candidate.
SUPPORTED_CAPABILITIES = [
    "source-document",
    "quote-social",
    "time-series",
    "comparison-set",
    "gap",
    "causal-graph",
    "entity",
    "image-media",
    "verification",
    "text-only",
]


def generate_current_fixture(renderer_root: Path) -> dict:
    script = (
        "import {makeCurrentVisualDirectorFixture} from "
        "'./scripts/test-support/current-visual-grammar-fixture.ts';"
        "process.stdout.write(JSON.stringify(makeCurrentVisualDirectorFixture()));"
    )
    completed = subprocess.run(
        ["node", "--import", "tsx", "--input-type=module", "-e", script],
        cwd=renderer_root,
        check=True,
        capture_output=True,
        text=True,
    )
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise AssertionError("Renderer current fixture root must be an object")
    return value


def beat_ids(spec: dict) -> list[str]:
    return [beat["beatId"] for scene in spec["scenes"] for beat in scene["visualBeats"]]


def identity_candidate(beat: dict, candidates: list[dict]) -> dict:
    keys = (
        "visualTemplate", "templateVariant", "screenState", "visualMode",
        "templateConfig", "objectIds", "assetPlacementIds",
    )
    matches = [candidate for candidate in candidates if all(candidate.get(key) == beat.get(key) for key in keys)]
    if not matches:
        raise AssertionError(f"current vNext catalog lacks identity Candidate: {beat['beatId']}")
    return matches[0]


def requirement_rows(spec: dict) -> tuple[list[dict], list[dict]]:
    intents = []
    requirements = []
    for beat in [item for scene in spec["scenes"] for item in scene["visualBeats"]]:
        beat_id = beat["beatId"]
        intents.append({
            "visualBeatId": beat_id,
            "purpose": "synthetic machine acceptance",
            "audienceBeliefBefore": "synthetic before",
            "audienceBeliefAfter": "synthetic after",
            "visualInformationGain": "synthetic machine-contract check",
            "preferredEvidenceModes": list(SUPPORTED_CAPABILITIES),
            "realityAnchorPreference": "neutral",
            "editorialReason": "fixture-only requirement; not a production editorial judgment",
        })
        requirements.append({
            "visualBeatId": beat_id,
            "requiredModes": list(SUPPORTED_CAPABILITIES),
            "imageRequirement": "not-required",
            "reason": "synthetic fixture accepts the pinned Renderer capability enum; no editorial ranking is encoded",
        })
    return intents, requirements


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(renderer_root: Path) -> dict:
    renderer_root = renderer_root.resolve()
    spec = generate_current_fixture(renderer_root)
    date = spec["episode"]["targetDate"]
    expected_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=renderer_root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()

    with tempfile.TemporaryDirectory(prefix="nasdaq-visual-intelligence-v12-") as temp:
        root = Path(temp)
        (root / "contracts").mkdir(parents=True)
        shutil.copyfile(ROOT / "contracts/renderer_binding.json", root / "contracts/renderer_binding.json")
        principles = root / "skills/nasdaq-cafe-visual-intelligence/references/VISUAL_EDITORIAL_INTELLIGENCE.md"
        principles.parent.mkdir(parents=True)
        shutil.copyfile(
            ROOT / "skills/nasdaq-cafe-visual-intelligence/references/VISUAL_EDITORIAL_INTELLIGENCE.md",
            principles,
        )
        working = root / "working" / date
        working.mkdir(parents=True)
        write_json(
            working / "visual_source_intents.json",
            {"contractVersion": "1.0.0", "episodeDate": date, "intents": []},
        )
        vi = working / "visual-intelligence"
        vi.mkdir(parents=True)

        editorial_snapshot = base_bridge.build_editorial_snapshot(spec)
        base_bridge.write_json(vi / "editorial_snapshot.json", editorial_snapshot)
        snapshot_sha = base_bridge.sha256_file(vi / "editorial_snapshot.json")
        pre_intents, pre_requirements = requirement_rows(spec)
        requirements_doc = {
            "contractVersion": "1.0.0",
            "bridgeContractVersion": base_bridge.BRIDGE_CONTRACT_VERSION,
            "episodeDate": date,
            "editorialSnapshotSha256": snapshot_sha,
            "intent": {"beats": pre_intents},
            "provisionalDirection": {"requirements": pre_requirements},
        }
        requirements_path = vi / "visual_requirements.json"
        write_json(requirements_path, requirements_doc)
        requirements_sha = base_bridge.sha256_file(requirements_path)

        # Stage 1: Machine produces Candidates and must stop before any Director choice.
        try:
            staged_bridge.prepare_and_compile(
                render=spec, output_root=root, date=date, renderer_root=renderer_root,
                expected_renderer_commit=expected_commit, plot_root=root,
            )
        except staged_bridge.VisualIntelligenceStageError as exc:
            if "E_VISUAL_INTELLIGENCE_DECISION_REQUIRED" not in str(exc):
                raise
        else:
            raise AssertionError("machine bridge must pause before AI-B Director decision")

        for name in (
            "editorial_snapshot.json", "financial_candidate_provider.json",
            "visual_candidate_input.json", "visual_capability_inventory.json",
            "visual_capability_hints.json", "visual_candidate_catalog.json",
            "recent_visual_pattern_context.json",
        ):
            if not (vi / name).is_file():
                raise AssertionError(f"pre-decision bridge artifact missing: {name}")

        catalog = json.loads((vi / "visual_candidate_catalog.json").read_text(encoding="utf-8"))
        catalog_sha = base_bridge.canonical_sha(catalog)
        by_beat: dict[str, list[dict]] = {}
        for candidate in catalog["candidates"]:
            by_beat.setdefault(candidate["visualBeatId"], []).append(candidate)
        selections = []
        spec_beats = [beat for scene in spec["scenes"] for beat in scene["visualBeats"]]
        for beat in spec_beats:
            beat_id = beat["beatId"]
            legal = by_beat[beat_id]
            selected = identity_candidate(beat, legal)
            alternative = next((item for item in legal if item["candidateId"] != selected["candidateId"]), None)
            selections.append({
                "visualBeatId": beat_id,
                "selectedCandidateId": selected["candidateId"],
                "strongestAlternativeCandidateId": alternative["candidateId"] if alternative else None,
                "whySelected": "identity-preserving synthetic acceptance",
                "whyNotAlternative": "fixture validates machinery, not editorial preference" if alternative else "",
            })

        # A legal Candidate ID from the wrong Catalog must be treated as stale, not reused.
        stale_decision = {
            "contractVersion": "1.0.0",
            "bridgeContractVersion": base_bridge.BRIDGE_CONTRACT_VERSION,
            "episodeDate": date,
            "editorialSnapshotSha256": snapshot_sha,
            "visualRequirementsSha256": requirements_sha,
            "director": {
                "candidateCatalogSha256": "0" * 64,
                "selections": selections,
            },
        }
        write_json(vi / "visual_intelligence_decision.json", stale_decision)
        try:
            staged_bridge.prepare_and_compile(
                render=spec, output_root=root, date=date, renderer_root=renderer_root,
                expected_renderer_commit=expected_commit, plot_root=root,
            )
        except staged_bridge.VisualIntelligenceStageError as exc:
            if "E_VISUAL_DECISION_STALE: Candidate Catalog SHA mismatch" not in str(exc):
                raise
        else:
            raise AssertionError("stale Candidate Catalog decision must be rejected")

        # Stage 2: Director-only decision is legal, but Critic must not be pre-baked.
        director_decision = {
            "contractVersion": "1.0.0",
            "bridgeContractVersion": base_bridge.BRIDGE_CONTRACT_VERSION,
            "episodeDate": date,
            "editorialSnapshotSha256": snapshot_sha,
            "visualRequirementsSha256": requirements_sha,
            "director": {
                "candidateCatalogSha256": catalog_sha,
                "selections": selections,
            },
        }
        write_json(vi / "visual_intelligence_decision.json", director_decision)
        try:
            staged_bridge.prepare_and_compile(
                render=spec, output_root=root, date=date, renderer_root=renderer_root,
                expected_renderer_commit=expected_commit, plot_root=root,
            )
        except staged_bridge.VisualIntelligenceStageError as exc:
            if "E_VISUAL_INTELLIGENCE_REVIEW_REQUIRED" not in str(exc):
                raise
        else:
            raise AssertionError("Director-only decision must stop for post-compile AI-B Critic review")

        compiled_path = vi / "visual_direction_compiled_render.json"
        warning_path = vi / "visual_editorial_warning_report.json"
        compile_report_path = vi / "visual_direction_compile_report.json"
        if not compiled_path.is_file() or not warning_path.is_file() or not compile_report_path.is_file():
            raise AssertionError("REVIEW_REQUIRED must be emitted only after compile/warning artifacts exist")
        report = json.loads(compile_report_path.read_text(encoding="utf-8"))
        if report.get("semanticDiff") != "PASS":
            raise AssertionError("Protected Semantic Diff did not PASS before Critic")
        compiled_sha = base_bridge.sha256_file(compiled_path)
        warning_sha = base_bridge.sha256_file(warning_path)

        # Stage 3: only a Critic PASS bound to these exact outputs may finalize the package.
        reviewed_decision = {
            **director_decision,
            "reviewRounds": [{
                "round": 1,
                "status": "PASS",
                "findings": [],
                "note": "synthetic fixture-only critic pass after actual compile",
                "compiledVisualSha256": compiled_sha,
                "warningReportSha256": warning_sha,
            }],
        }
        write_json(vi / "visual_intelligence_decision.json", reviewed_decision)
        compiled = staged_bridge.prepare_and_compile(
            render=spec, output_root=root, date=date, renderer_root=renderer_root,
            expected_renderer_commit=expected_commit, plot_root=root,
        )
        if compiled["render"] != spec:
            raise AssertionError("identity acceptance changed the synthetic RenderSpec")
        validation = package_validator.validate(root=root, date=date, renderer_root=renderer_root)
        if validation["status"] != "PASS":
            raise AssertionError("Visual Intelligence package validator did not PASS")
        return {
            "status": "PASS",
            "episodeDate": date,
            "rendererCommit": expected_commit,
            "candidateCount": len(catalog["candidates"]),
            "beatCount": len(beat_ids(spec)),
            "semanticDiff": report["semanticDiff"],
            "machinePausedBeforeDecision": True,
            "staleCatalogDecisionRejected": True,
            "machinePausedBeforeCritic": True,
            "criticBoundToCompiledVisual": True,
            "packageValidation": validation["status"],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renderer-root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.renderer_root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
