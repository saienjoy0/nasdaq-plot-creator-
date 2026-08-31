#!/usr/bin/env python3
"""PR-only readiness helpers for Current Preview semantic closure."""
from pathlib import Path


def choose_phase(root: Path, date: str) -> str:
    director = (
        root / "working" / date / "visual-intelligence" /
        "visual_director_decision.semantic.json"
    )
    return "compile" if director.is_file() else "prepare"


def classify_facade_outcome(outcome: dict) -> tuple[str, str | None]:
    status = outcome.get("status")
    if status == "PASS":
        return "PASS", None
    if status == "PREPARED":
        return "NOT_READY", outcome.get("requiredAction") or "AUTHOR_VISUAL_INTELLIGENCE_DECISION"
    if status == "REVIEW_REQUIRED":
        return "NOT_READY", "AUTHOR_VISUAL_CRITIC_REVIEW"
    return "FAIL", None
