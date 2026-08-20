from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import current_compatibility_adapter_v12 as adapter  # noqa: E402


def test_current_v2_review_projects_pass_into_legacy_approval_flag() -> None:
    review = {
        "verdict": "pass",
        "scores": {"hook": 5},
        "total_score": 5,
        "findings": [],
    }
    projected = adapter.project_creative_review(review)
    assert projected["approvedForCodex"] is True
    assert projected["verdict"] == "approved"


def test_current_materializer_delegates_compatibility_projection() -> None:
    source = (SCRIPTS / "materialize_chatgpt_daily_authoring.py").read_text(encoding="utf-8")
    assert "current_compatibility_adapter_v12.project_creative_review(review)" in source
    # The Current v2 materializer must not independently derive the legacy boolean.
    assert '"approvedForCodex": review["verdict"] == "pass"' not in source
