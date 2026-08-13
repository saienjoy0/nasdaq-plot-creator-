#!/usr/bin/env python3
"""Synthetic cross-repo acceptance for visual-intelligence-bridge/1.2.0.

This test never makes an editorial recommendation. It uses the Renderer's current
synthetic fixture and an identity-preserving test selection solely to prove the
machine contract: AI-B requirements exist before Candidate generation, candidate
generation pauses for AI-B, frozen artifacts are emitted, a legal authored decision
compiles, Protected Semantic Diff passes, and the final package validator accepts the
exact Renderer/Registry lineage.
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
import visual_intelligence_bridge as bridge  # noqa: E402


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


def requirement_rows(spec: dict, *, mode_for_beat=None) -> tuple[list[dict], list[dict]]:
    intents = []
    requirements = []
    for beat in [item for scene in spec["scenes"] for item in scene["visualBeats"]]:
        beat_id = beat["beatId"]
        mode = mode_for_beat(beat) if mode_for_beat else "text-only"
        intents.append({
            "visualBeatId": beat_id,
            "purpose": "synthetic machine acceptance",
            "audienceBeliefBefore": "synthetic before",
            "audienceBeliefAfter": "synthetic after",
            "visualInformationGain": "synthetic machine-contract check",
            "preferredEvidenceModes": [mode],
            "realityAnchorPreference": "neutral",
            "editorialReason": "fixture-only requirement; not a production editorial judgment",
        })
        requirements.append({
            "visualBeatId": beat_id,
            "requiredModes": [mode],
            "imageRequirement": "not-required",
            "reason": "synthetic fixture requires no generated image",
        })
    return intents, requirements


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
        (working / "visual_source_intents.json").write_text(
            json.dumps({"contractVersion": "1.0.0", "episodeDate": date, "intents": []}, indent=2) + "\n",
            encoding="utf-8",
        )
        vi = working / "visual-intelligence"
        vi.mkdir(parents=True)
        pre_intents, pre_requirements = requirement_rows(spec)
        pre_doc = {
            "contractVersion": "1.0.0",
            "bridgeContractVersion": bridge.BRIDGE_CONTRACT_VERSION,
            "episodeDate": date,
            "intent": {"beats": pre_intents},
            "provisionalDirection": {"requirements": pre_requirements},
        }
        (vi / "visual_requirements.json").write_text(
            json.dumps(pre_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        try:
            bridge.prepare_and_compile(
                render=spec, output_root=root, date=date, renderer_root=renderer_root,
                expected_renderer_commit=expected_commit, plot_root=root,
            )
        except bridge.VisualIntelligenceBridgeError as exc:
            if "E_VISUAL_INTELLIGENCE_DECISION_REQUIRED" not in str(exc):
                raise
        else:
            raise AssertionError("Visual Intelligence machine bridge must pause before AI-B decision")

        for name in (
            "editorial_snapshot.json", "financial_candidate_provider.json",
            "visual_candidate_input.json", "visual_capability_inventory.json",
            "visual_capability_hints.json", "visual_candidate_catalog.json",
            "recent_visual_pattern_context.json",
        ):
            if not (vi / name).is_file():
                raise AssertionError(f"pre-decision bridge artifact missing: {name}")

        catalog = json.loads((vi / "visual_candidate_catalog.json").read_text(encoding="utf-8"))
        by_beat: dict[str, list[dict]] = {}
        for candidate in catalog["candidates"]:
            by_beat.setdefault(candidate["visualBeatId"], []).append(candidate)
        intents = []
        requirements = []
        selections = []
        spec_beats = [beat for scene in spec["scenes"] for beat in scene["visualBeats"]]
        for beat in spec_beats:
            beat_id = beat["beatId"]
            legal = by_beat[beat_id]
            selected = identity_candidate(beat, legal)
            alternative = next((item for item in legal if item["candidateId"] != selected["candidateId"]), None)
            intents.append({
                "visualBeatId": beat_id,
                "purpose": "synthetic identity acceptance",
                "audienceBeliefBefore": "synthetic before",
                "audienceBeliefAfter": "synthetic after",
                "visualInformationGain": "synthetic machine-contract check",
                "preferredEvidenceModes": [selected["capability"]],
                "realityAnchorPreference": "neutral",
                "editorialReason": "fixture-only identity selection; not a production editorial judgment",
            })
            requirements.append({
                "visualBeatId": beat_id,
                "requiredModes": [selected["capability"]],
                "imageRequirement": "not-required",
                "reason": "synthetic fixture requires no generated image",
            })
            selections.append({
                "visualBeatId": beat_id,
                "selectedCandidateId": selected["candidateId"],
                "strongestAlternativeCandidateId": alternative["candidateId"] if alternative else None,
                "whySelected": "identity-preserving synthetic acceptance",
                "whyNotAlternative": "fixture validates machinery, not editorial preference" if alternative else "",
            })

        requirements_doc = {
            "contractVersion": "1.0.0",
            "bridgeContractVersion": bridge.BRIDGE_CONTRACT_VERSION,
            "episodeDate": date,
            "intent": {"beats": intents},
            "provisionalDirection": {"requirements": requirements},
        }
        (vi / "visual_requirements.json").write_text(
            json.dumps(requirements_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        decision = {
            **requirements_doc,
            "director": {"selections": selections},
            "reviewRounds": [{
                "round": 1, "status": "PASS", "findings": [],
                "note": "synthetic fixture-only critic pass",
            }],
        }
        (vi / "visual_intelligence_decision.json").write_text(
            json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        compiled = bridge.prepare_and_compile(
            render=spec, output_root=root, date=date, renderer_root=renderer_root,
            expected_renderer_commit=expected_commit, plot_root=root,
        )
        if compiled["render"] != spec:
            raise AssertionError("identity acceptance changed the synthetic RenderSpec")
        validation = package_validator.validate(root=root, date=date, renderer_root=renderer_root)
        if validation["status"] != "PASS":
            raise AssertionError("Visual Intelligence package validator did not PASS")
        report = json.loads((vi / "visual_direction_compile_report.json").read_text(encoding="utf-8"))
        if report.get("semanticDiff") != "PASS":
            raise AssertionError("Protected Semantic Diff did not PASS")
        return {
            "status": "PASS", "episodeDate": date, "rendererCommit": expected_commit,
            "candidateCount": len(catalog["candidates"]), "beatCount": len(beat_ids(spec)),
            "semanticDiff": report["semanticDiff"], "machinePausedBeforeDecision": True,
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
