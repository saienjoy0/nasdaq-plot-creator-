#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import visual_intelligence_bridge_staged as staged_bridge  # noqa: E402
import visual_intelligence_requirements as requirements  # noqa: E402


def main() -> int:
    date = "2099-05-05"
    snapshot_sha = "a" * 64
    requirements_sha = "c" * 64
    beat_id = "vb-01-01"
    render = {
        "episode": {"targetDate": date},
        "scenes": [{"visualBeats": [{"beatId": beat_id}]}],
    }
    value = {
        "contractVersion": "1.0.0",
        "bridgeContractVersion": "visual-intelligence-bridge/1.2.0",
        "episodeDate": date,
        "editorialSnapshotSha256": snapshot_sha,
        "intent": {"beats": [{
            "visualBeatId": beat_id,
            "purpose": "test",
            "audienceBeliefBefore": "before",
            "audienceBeliefAfter": "after",
            "visualInformationGain": "gain",
            "preferredEvidenceModes": ["text-only"],
            "realityAnchorPreference": "neutral",
            "editorialReason": "test",
        }]},
        "provisionalDirection": {"requirements": [{
            "visualBeatId": beat_id,
            "requiredModes": ["text-only"],
            "imageRequirement": "not-required",
            "reason": "test",
        }]},
    }
    result = requirements.validate(
        value,
        render,
        date,
        editorial_snapshot_sha256=snapshot_sha,
    )
    if result["status"] != "PASS" or result["editorialSnapshotSha256"] != snapshot_sha:
        raise AssertionError(result)
    stale = dict(value)
    stale["editorialSnapshotSha256"] = "b" * 64
    try:
        requirements.validate(
            stale,
            render,
            date,
            editorial_snapshot_sha256=snapshot_sha,
        )
    except requirements.VisualRequirementsError as exc:
        if "editorialSnapshotSha256 mismatch" not in str(exc):
            raise
    else:
        raise AssertionError("stale Visual Requirements must be rejected")

    # requiredModes remain a pre-selection coverage invariant: the catalog must
    # contain at least one Candidate satisfying the provisional direction.
    catalog = {
        "candidates": [
            {
                "candidateId": "vc-required",
                "visualBeatId": beat_id,
                "capability": "text-only",
                "realityAnchor": False,
            },
            {
                "candidateId": "vc-appearance-alternative",
                "visualBeatId": beat_id,
                "capability": "source-document",
                "realityAnchor": True,
            },
        ]
    }
    staged_bridge._validate_catalog_coverage(requirements=value, catalog=catalog)

    # After the Renderer-owned Candidate Builder has admitted both Candidates,
    # AI-B may select the legal alternative to change Appearance without rewriting
    # frozen Requirements solely to make that Candidate's capability a requiredMode.
    decision = {
        "contractVersion": "1.0.0",
        "bridgeContractVersion": "visual-intelligence-bridge/1.2.0",
        "episodeDate": date,
        "editorialSnapshotSha256": snapshot_sha,
        "visualRequirementsSha256": requirements_sha,
        "director": {"selections": [{
            "visualBeatId": beat_id,
            "selectedCandidateId": "vc-appearance-alternative",
            "strongestAlternativeCandidateId": "vc-required",
            "whySelected": "legal appearance-only alternative",
            "whyNotAlternative": "required-mode candidate keeps the measured appearance run",
        }]},
    }
    staged_bridge._validate_director(
        decision=decision,
        requirements=value,
        requirements_sha=requirements_sha,
        date=date,
        snapshot_sha=snapshot_sha,
        beat_ids=[beat_id],
        catalog=catalog,
    )

    invalid_decision = {
        **decision,
        "director": {"selections": [{
            "visualBeatId": beat_id,
            "selectedCandidateId": "vc-not-in-catalog",
            "strongestAlternativeCandidateId": "vc-required",
            "whySelected": "invalid",
            "whyNotAlternative": "invalid",
        }]},
    }
    try:
        staged_bridge._validate_director(
            decision=invalid_decision,
            requirements=value,
            requirements_sha=requirements_sha,
            date=date,
            snapshot_sha=snapshot_sha,
            beat_ids=[beat_id],
            catalog=catalog,
        )
    except staged_bridge.VisualIntelligenceStageError as exc:
        if "selectedCandidateId is not a legal Candidate" not in str(exc):
            raise
    else:
        raise AssertionError("Director must not select a Candidate outside the catalog")

    uncovered_catalog = {
        "candidates": [{
            "candidateId": "vc-only-unrequired-mode",
            "visualBeatId": beat_id,
            "capability": "source-document",
            "realityAnchor": True,
        }]
    }
    try:
        staged_bridge._validate_catalog_coverage(requirements=value, catalog=uncovered_catalog)
    except staged_bridge.VisualIntelligenceStageError as exc:
        if "E_VISUAL_REQUIRED_MODE_UNAVAILABLE" not in str(exc):
            raise
    else:
        raise AssertionError("requiredModes must still be satisfiable by the Candidate Catalog")

    print("visual intelligence requirements and Candidate authority tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
