#!/usr/bin/env python3
"""Regression contract for Current Preview semantic readiness.

This test freezes both the r8 premature-compile failure and the later real-day
candidate-coverage failure. Semantic/human checkpoints must remain non-publishing
PREPARED states, while genuine machine failures remain failures.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import current_preview_request_readiness_v12 as readiness
import run_daily_renderer_closure_v12 as closure


def test_phase_selection() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        date = "2026-08-17"
        vi = root / "working" / date / "visual-intelligence"
        vi.mkdir(parents=True)

        assert readiness.select_phase(root, date) == "prepare"

        (vi / "visual_director_decision.semantic.json").write_text(
            '{"semanticPayloadVersion":"1.0.0"}\n', encoding="utf-8"
        )
        assert readiness.select_phase(root, date) == "compile"


def test_prepared_is_actionable_not_ready() -> None:
    result = readiness.classify_facade_outcome(
        {
            "status": "PREPARED",
            "requiredAction": "AUTHOR_VISUAL_INTELLIGENCE_DECISION",
            "reason": "Candidate Catalog ready",
        }
    )
    assert result == {
        "readiness": "NOT_READY",
        "requiredAction": "AUTHOR_VISUAL_INTELLIGENCE_DECISION",
        "reason": "Candidate Catalog ready",
        "exitCode": 3,
    }


def test_candidate_coverage_unavailable_returns_to_story() -> None:
    result = closure.classify_prepare_visual_intelligence_pause(
        {
            "status": "DECISION_REQUIRED",
            "errors": [
                "E_VISUAL_CANDIDATE_COVERAGE_UNAVAILABLE:"
                "scene-02-beat-002,scene-04-beat-001"
            ],
            "candidateCoverage": (
                "working/2026-08-17/visual-intelligence/"
                "visual_candidate_coverage.json"
            ),
        }
    )
    assert result == {
        "requiredAction": "RETURN_TO_STORY_FOR_VISUAL_FEASIBILITY",
        "includeCandidateCatalog": False,
        "candidateCoverage": (
            "working/2026-08-17/visual-intelligence/"
            "visual_candidate_coverage.json"
        ),
        "reason": (
            "E_VISUAL_CANDIDATE_COVERAGE_UNAVAILABLE:"
            "scene-02-beat-002,scene-04-beat-001"
        ),
    }


def test_normal_prepare_pause_still_requests_director() -> None:
    result = closure.classify_prepare_visual_intelligence_pause(
        {
            "status": "DECISION_REQUIRED",
            "errors": [
                "E_VISUAL_INTELLIGENCE_DECISION_REQUIRED: Candidate Catalog is ready"
            ],
        }
    )
    assert result == {
        "requiredAction": "AUTHOR_VISUAL_INTELLIGENCE_DECISION",
        "includeCandidateCatalog": True,
        "candidateCoverage": None,
        "reason": (
            "E_VISUAL_INTELLIGENCE_DECISION_REQUIRED: Candidate Catalog is ready"
        ),
    }


def test_review_required_is_critic_checkpoint() -> None:
    result = readiness.classify_facade_outcome(
        {
            "status": "REVIEW_REQUIRED",
            "requiredAction": None,
            "reason": None,
        }
    )
    assert result == {
        "readiness": "NOT_READY",
        "requiredAction": "AUTHOR_VISUAL_CRITIC_REVIEW",
        "reason": None,
        "exitCode": 3,
    }


def test_pass_is_merge_ready() -> None:
    result = readiness.classify_facade_outcome(
        {"status": "PASS", "requiredAction": None, "reason": None}
    )
    assert result == {
        "readiness": "PASS",
        "requiredAction": None,
        "reason": None,
        "exitCode": 0,
    }


def test_machine_failure_stays_failure() -> None:
    result = readiness.classify_facade_outcome(
        {"status": "FAIL", "requiredAction": None, "reason": "boom"}
    )
    assert result == {
        "readiness": "FAIL",
        "requiredAction": None,
        "reason": "boom",
        "exitCode": 2,
    }


def main() -> int:
    test_phase_selection()
    test_prepared_is_actionable_not_ready()
    test_candidate_coverage_unavailable_returns_to_story()
    test_normal_prepare_pause_still_requests_director()
    test_review_required_is_critic_checkpoint()
    test_pass_is_merge_ready()
    test_machine_failure_stays_failure()
    print("current Preview request readiness regression PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
