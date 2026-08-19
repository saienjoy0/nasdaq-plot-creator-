#!/usr/bin/env python3
"""Synthetic Cross-Repo acceptance for the separated current VI artifact order.

No editorial recommendation is encoded. The pinned Renderer's current fixture and
identity Candidate prove only machinery and lifecycle boundaries.
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
import visual_intelligence_artifacts_v12 as artifacts  # noqa: E402
import visual_intelligence_bridge as base_bridge  # noqa: E402
import visual_intelligence_pipeline_v12 as pipeline  # noqa: E402

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
        "visualTemplate",
        "templateVariant",
        "screenState",
        "visualMode",
        "templateConfig",
        "objectIds",
        "assetPlacementIds",
    )
    matches = [
        candidate
        for candidate in candidates
        if all(candidate.get(key) == beat.get(key) for key in keys)
    ]
    if not matches:
        raise AssertionError(
            f"current vNext catalog lacks identity Candidate: {beat['beatId']}"
        )
    return matches[0]


def requirement_rows(spec: dict) -> tuple[list[dict], list[dict]]:
    intents: list[dict] = []
    requirements: list[dict] = []
    for beat in [item for scene in spec["scenes"] for item in scene["visualBeats"]]:
        beat_id = beat["beatId"]
        intents.append(
            {
                "visualBeatId": beat_id,
                "purpose": "synthetic machine acceptance",
                "audienceBeliefBefore": "synthetic before",
                "audienceBeliefAfter": "synthetic after",
                "visualInformationGain": "synthetic machine-contract check",
                "preferredEvidenceModes": list(SUPPORTED_CAPABILITIES),
                "realityAnchorPreference": "neutral",
                "editorialReason": "fixture-only requirement; not production judgment",
            }
        )
        requirements.append(
            {
                "visualBeatId": beat_id,
                "requiredModes": list(SUPPORTED_CAPABILITIES),
                "imageRequirement": "not-required",
                "reason": "synthetic fixture accepts the pinned capability enum",
            }
        )
    return intents, requirements


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(renderer_root: Path) -> dict:
    renderer_root = renderer_root.resolve()
    spec = generate_current_fixture(renderer_root)
    date = spec["episode"]["targetDate"]
    expected_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=renderer_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    with tempfile.TemporaryDirectory(prefix="nasdaq-visual-intelligence-v12-") as temp:
        root = Path(temp)
        (root / "contracts").mkdir(parents=True)
        shutil.copyfile(
            ROOT / "contracts/renderer_binding.json",
            root / "contracts/renderer_binding.json",
        )
        principles = (
            root
            / "skills/nasdaq-cafe-visual-intelligence/references/VISUAL_EDITORIAL_INTELLIGENCE.md"
        )
        principles.parent.mkdir(parents=True)
        shutil.copyfile(
            ROOT
            / "skills/nasdaq-cafe-visual-intelligence/references/VISUAL_EDITORIAL_INTELLIGENCE.md",
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

        base_bridge.write_json(
            vi / "editorial_snapshot.json",
            base_bridge.build_editorial_snapshot(spec),
        )
        intents, requirements = requirement_rows(spec)
        requirements_semantic = {
            "semanticPayloadVersion": "1.0.0",
            "episodeDate": date,
            "intent": {"beats": intents},
            "provisionalDirection": {"requirements": requirements},
        }
        write_json(vi / artifacts.REQUIREMENTS_SEMANTIC, requirements_semantic)

        # Stage 1: semantic Requirements are materialized, Candidates are built once,
        # and the machine must pause before any Director choice.
        try:
            pipeline.prepare_and_compile(
                render=spec,
                output_root=root,
                date=date,
                renderer_root=renderer_root,
                expected_renderer_commit=expected_commit,
                plot_root=root,
            )
        except pipeline.VisualIntelligenceStageError as exc:
            if "E_VISUAL_INTELLIGENCE_DECISION_REQUIRED" not in str(exc):
                raise
        else:
            raise AssertionError("pipeline must pause before Director semantic payload")

        requirements_canonical = vi / artifacts.REQUIREMENTS_CANONICAL
        catalog_path = vi / "visual_candidate_catalog.json"
        if not requirements_canonical.is_file() or not catalog_path.is_file():
            raise AssertionError("Requirements canonical/Candidate Catalog missing")
        if any(key.endswith("Sha256") for key in requirements_semantic):
            raise AssertionError("semantic Requirements authored a machine SHA")

        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        by_beat: dict[str, list[dict]] = {}
        for candidate in catalog["candidates"]:
            by_beat.setdefault(candidate["visualBeatId"], []).append(candidate)
        selections: list[dict] = []
        spec_beats = [beat for scene in spec["scenes"] for beat in scene["visualBeats"]]
        for beat in spec_beats:
            beat_id = beat["beatId"]
            legal = by_beat[beat_id]
            selected = identity_candidate(beat, legal)
            alternative = next(
                (
                    item
                    for item in legal
                    if item["candidateId"] != selected["candidateId"]
                ),
                None,
            )
            selections.append(
                {
                    "visualBeatId": beat_id,
                    "selectedCandidateId": selected["candidateId"],
                    "strongestAlternativeCandidateId": (
                        alternative["candidateId"] if alternative else None
                    ),
                    "whySelected": "identity-preserving synthetic acceptance",
                    "whyNotAlternative": (
                        "fixture validates machinery, not editorial preference"
                        if alternative
                        else ""
                    ),
                }
            )

        # Invalid semantic selection is rejected before compile and remains correctable
        # because Director canonical is not yet lifecycle-frozen.
        bad = [dict(item) for item in selections]
        bad[0]["selectedCandidateId"] = "candidate-does-not-exist"
        director_semantic_path = vi / artifacts.DIRECTOR_SEMANTIC
        write_json(
            director_semantic_path,
            {
                "semanticPayloadVersion": "1.0.0",
                "episodeDate": date,
                "selections": bad,
            },
        )
        try:
            pipeline.prepare_and_compile(
                render=spec,
                output_root=root,
                date=date,
                renderer_root=renderer_root,
                expected_renderer_commit=expected_commit,
                plot_root=root,
            )
        except pipeline.VisualIntelligenceStageError as exc:
            if "selectedCandidateId is not a legal Candidate" not in str(exc):
                raise
        else:
            raise AssertionError("illegal Director selection must be rejected")

        director_semantic = {
            "semanticPayloadVersion": "1.0.0",
            "episodeDate": date,
            "selections": selections,
        }
        write_json(director_semantic_path, director_semantic)

        # Stage 2: legal Director canonical is sealed by compile; no Critic can be
        # authored before actual compiled/warning bytes exist.
        try:
            pipeline.prepare_and_compile(
                render=spec,
                output_root=root,
                date=date,
                renderer_root=renderer_root,
                expected_renderer_commit=expected_commit,
                plot_root=root,
            )
        except pipeline.VisualIntelligenceStageError as exc:
            if "E_VISUAL_INTELLIGENCE_REVIEW_REQUIRED" not in str(exc):
                raise
        else:
            raise AssertionError("Director must stop for post-compile Critic review")

        director_path = vi / artifacts.DIRECTOR_CANONICAL
        compiled_path = vi / "visual_direction_compiled_render.json"
        warning_path = vi / "visual_editorial_warning_report.json"
        compile_report_path = vi / "visual_direction_compile_report.json"
        for path in (director_path, compiled_path, warning_path, compile_report_path):
            if not path.is_file():
                raise AssertionError(f"REVIEW_REQUIRED artifact missing: {path.name}")
        report = json.loads(compile_report_path.read_text(encoding="utf-8"))
        if report.get("semanticDiff") != "PASS":
            raise AssertionError("Protected Semantic Diff did not PASS")
        director_before = director_path.read_bytes()
        compiled_before = compiled_path.read_bytes()

        changed_director = json.loads(json.dumps(director_semantic))
        changed_director["selections"][0]["whySelected"] = "attempted post-compile rewrite"
        write_json(director_semantic_path, changed_director)
        try:
            pipeline.prepare_and_compile(
                render=spec,
                output_root=root,
                date=date,
                renderer_root=renderer_root,
                expected_renderer_commit=expected_commit,
                plot_root=root,
            )
        except pipeline.VisualIntelligenceStageError as exc:
            if "E_VISUAL_IMMUTABLE_CLOBBER:Visual Director Decision canonical" not in str(exc):
                raise
        else:
            raise AssertionError("post-compile Director rewrite must fail closed")
        if director_path.read_bytes() != director_before or compiled_path.read_bytes() != compiled_before:
            raise AssertionError("sealed Director/compiled bytes changed after rejected rewrite")
        write_json(director_semantic_path, director_semantic)

        # Stage 3: Critic semantic contains no machine SHA. Materializer binds it to
        # exact Director/compiled/warning bytes and only then may the package PASS.
        critic_semantic = {
            "semanticPayloadVersion": "1.0.0",
            "episodeDate": date,
            "reviewRounds": [
                {
                    "round": 1,
                    "status": "PASS",
                    "findings": [],
                    "viewerImpact": "none in synthetic fixture",
                    "reason": "synthetic fixture-only post-compile review",
                }
            ],
        }
        write_json(vi / artifacts.CRITIC_SEMANTIC, critic_semantic)
        compiled = pipeline.prepare_and_compile(
            render=spec,
            output_root=root,
            date=date,
            renderer_root=renderer_root,
            expected_renderer_commit=expected_commit,
            plot_root=root,
        )
        if compiled["render"] != spec:
            raise AssertionError("identity acceptance changed synthetic RenderSpec")
        if compiled_path.read_bytes() != compiled_before:
            raise AssertionError("Critic pass recompiled or rewrote compiled visual")

        critic_path = vi / artifacts.CRITIC_CANONICAL
        critic = json.loads(critic_path.read_text(encoding="utf-8"))
        if critic.get("compiledVisualSha256") != base_bridge.sha256_file(compiled_path):
            raise AssertionError("canonical Critic is not bound to compiled visual")
        if critic.get("warningReportSha256") != base_bridge.sha256_file(warning_path):
            raise AssertionError("canonical Critic is not bound to warning report")
        if any(key.endswith("Sha256") for key in critic_semantic):
            raise AssertionError("semantic Critic authored a machine SHA")

        validation = package_validator.validate(
            root=root,
            date=date,
            renderer_root=renderer_root,
        )
        if validation["status"] != "PASS":
            raise AssertionError("Visual Intelligence package validator did not PASS")
        if (vi / "visual_intelligence_decision.json").exists():
            raise AssertionError("combined Director/Critic artifact reappeared in current path")
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
            "directorSealedBeforeCritic": True,
            "semanticPayloadShaFree": True,
            "combinedDecisionAuthorityAbsent": True,
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
