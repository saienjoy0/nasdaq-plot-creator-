#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import visual_intelligence_requirements as requirements  # noqa: E402


def main() -> int:
    date = "2099-05-05"
    snapshot_sha = "a" * 64
    render = {
        "episode": {"targetDate": date},
        "scenes": [{"visualBeats": [{"beatId": "vb-01-01"}]}],
    }
    value = {
        "contractVersion": "1.0.0",
        "bridgeContractVersion": "visual-intelligence-bridge/1.2.0",
        "episodeDate": date,
        "editorialSnapshotSha256": snapshot_sha,
        "intent": {"beats": [{
            "visualBeatId": "vb-01-01",
            "purpose": "test",
            "audienceBeliefBefore": "before",
            "audienceBeliefAfter": "after",
            "visualInformationGain": "gain",
            "preferredEvidenceModes": ["text-only"],
            "realityAnchorPreference": "neutral",
            "editorialReason": "test",
        }]},
        "provisionalDirection": {"requirements": [{
            "visualBeatId": "vb-01-01",
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
    print("visual intelligence requirements tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
