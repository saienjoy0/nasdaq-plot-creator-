#!/usr/bin/env python3
"""Deterministic compatibility projection for current-v1.2 production.

This module is the only current owner of legacy-shaped compatibility fields. It may
copy or deterministically derive a mechanical field from already-accepted current
authority, but it must never make an editorial choice or infer missing meaning.
"""
from __future__ import annotations

from typing import Any


class CurrentCompatibilityError(ValueError):
    pass


def project_creative_review(review: dict[str, Any]) -> dict[str, Any]:
    """Project current Creative Review into the legacy review shape.

    `approvedForCodex` is a compatibility boolean only. The semantic authority is
    still the current Creative Review verdict; this adapter does not re-review it.
    """
    verdict = review.get("verdict")
    if verdict not in {"pass", "revise", "return_to_story", "blocked"}:
        raise CurrentCompatibilityError(f"unsupported current Creative Review verdict: {verdict!r}")
    findings = review.get("findings", [])
    if not isinstance(findings, list):
        raise CurrentCompatibilityError("current Creative Review findings must be a list")
    scores = review.get("scores")
    if not isinstance(scores, dict):
        raise CurrentCompatibilityError("current Creative Review scores must be an object")
    return {
        "verdict": "approved" if verdict == "pass" else verdict,
        "approvedForCodex": verdict == "pass",
        "scores": scores,
        "totalScore": review.get("total_score"),
        "largestDropoffRisk": (
            findings[0].get("viewer_impact", "")
            if findings and isinstance(findings[0], dict)
            else ""
        ),
        "requiredChanges": [
            item.get("minimal_fix", "")
            for item in findings
            if isinstance(item, dict) and item.get("severity") in {"critical", "major"}
        ],
        "changesApplied": [],
    }


def assert_compatibility_review_matches(
    *,
    current_review: dict[str, Any],
    compatibility_review: dict[str, Any],
) -> None:
    expected = project_creative_review(current_review)
    if compatibility_review != expected:
        raise CurrentCompatibilityError(
            "legacy-shaped Creative Review projection does not match current authority"
        )
