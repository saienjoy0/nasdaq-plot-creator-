from __future__ import annotations

import importlib.util
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_adapter():
    path = ROOT / "critic-adapters/openai/main.py"
    spec = importlib.util.spec_from_file_location("interest_openai_critic_adapter", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def request() -> dict:
    return {
        "episode_date": "2026-08-10",
        "required_review": {
            "round": 1,
            "minimum_total_score": 25,
        },
    }


def valid_review() -> dict:
    checks = []
    for index in range(1, 8):
        checks.append(
            {
                "scene_id": f"scene-{index:02d}",
                "mode": "continue",
                "payoff_delivered": True,
                "belief_changed": True,
                "continuation_reason_natural": True,
                "closure_effective": None,
                "opening_promise_recovered": None,
                "procedural_language_dominant": False,
            }
        )
    checks.append(
        {
            "scene_id": "scene-08",
            "mode": "close",
            "payoff_delivered": True,
            "belief_changed": True,
            "continuation_reason_natural": None,
            "closure_effective": True,
            "opening_promise_recovered": True,
            "procedural_language_dominant": False,
        }
    )
    return {
        "contract_version": "1.1.0",
        "episode_date": "2026-08-10",
        "reviewer": "independent_critic",
        "round": 1,
        "scores": {
            "opening": 5,
            "progression": 4,
            "discovery": 5,
            "clarity": 4,
            "fox_voice": 4,
            "late_payoff": 5,
        },
        "total_score": 27,
        "scene_checks": checks,
        "immediate_failures": [],
        "findings": [],
        "verdict": "pass",
    }


def finding(issue_type: str, severity: str, scene_ids: list[str]) -> dict:
    return {
        "finding_id": "finding-01",
        "severity": severity,
        "issue_type": issue_type,
        "scene_ids": scene_ids,
        "problem": "理解更新に対して説明上の重みが大きい。",
        "viewer_impact": "中盤の進展が弱く感じられる。",
        "minimal_fix": "既存Evidenceと因果を保ったまま重複説明を圧縮する。",
    }


def test_minor_fact_stacking_can_keep_external_critic_pass():
    adapter = load_adapter()
    review = valid_review()
    review["findings"] = [finding("FACT_STACKING", "minor", ["scene-05"])]
    adapter.validate_review(review, request())


def test_major_payoff_drought_cannot_hide_behind_external_critic_pass():
    adapter = load_adapter()
    review = deepcopy(valid_review())
    review["findings"] = [
        finding("PAYOFF_DROUGHT", "major", ["scene-02", "scene-03", "scene-04"])
    ]
    with pytest.raises(adapter.AdapterError, match="PASS review cannot contain critical or major findings"):
        adapter.validate_review(review, request())


def test_major_interest_finding_is_not_promoted_to_hard_narrative_vocabulary():
    adapter = load_adapter()
    assert "PAYOFF_DROUGHT" in adapter.ISSUE_TYPES
    assert "PAYOFF_DROUGHT" not in adapter.HARD_NARRATIVE_FINDINGS
