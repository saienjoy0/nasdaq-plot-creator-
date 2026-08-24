#!/usr/bin/env python3
"""Regression contract for Current Preview semantic readiness.

This test is intentionally written before the readiness coordinator. It freezes the
r8 failure mode: a PREVIEW request with Visual Requirements present but no Director
semantic must stay in a non-publishing authoring checkpoint instead of reaching the
compile-only main Production lane.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import current_preview_request_readiness_v12 as readiness


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
    test_review_required_is_critic_checkpoint()
    test_pass_is_merge_ready()
    test_machine_failure_stays_failure()
    print("current Preview request readiness regression PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
