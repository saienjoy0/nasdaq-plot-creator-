from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts/story-engine/validate_story_engine_bundle.py"
SCHEMA = ROOT / "skills/nasdaq-cafe-entertainment-critic/contracts/creative_review.schema.json"

spec = importlib.util.spec_from_file_location("bundle_validator", VALIDATOR)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader is not None
spec.loader.exec_module(module)


def valid_review() -> dict:
    checks = []
    for i in range(1, 8):
        checks.append({
            "scene_id": f"scene-{i:02d}",
            "mode": "continue",
            "payoff_delivered": True,
            "belief_changed": True,
            "continuation_reason_natural": True,
            "closure_effective": None,
            "opening_promise_recovered": None,
            "procedural_language_dominant": False,
        })
    checks.append({
        "scene_id": "scene-08",
        "mode": "close",
        "payoff_delivered": True,
        "belief_changed": True,
        "continuation_reason_natural": None,
        "closure_effective": True,
        "opening_promise_recovered": True,
        "procedural_language_dominant": False,
    })
    return {
        "contract_version": "1.1.0",
        "episode_date": "2026-08-06",
        "reviewer": "independent_critic",
        "round": 1,
        "scores": {"opening": 4, "progression": 5, "discovery": 5, "clarity": 4, "fox_voice": 4, "late_payoff": 5},
        "total_score": 27,
        "scene_checks": checks,
        "immediate_failures": [],
        "findings": [],
        "verdict": "pass",
    }


def finding(issue_type: str, scene_ids: list[str], *, severity: str = "major") -> dict:
    return {
        "finding_id": "finding-01",
        "severity": severity,
        "issue_type": issue_type,
        "scene_ids": scene_ids,
        "problem": "Narrative value is insufficient.",
        "viewer_impact": "The later section does not materially deepen understanding.",
        "minimal_fix": "Create a real evidence-backed understanding upgrade without changing causality.",
    }


def test_valid_review_contract_passes():
    review = valid_review()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(review)) == []
    errors: list[str] = []
    module.validate_review(review, errors)
    assert errors == []


def test_scene_08_is_closure_not_continuation():
    review = valid_review()
    assert review["scene_checks"][7]["continuation_reason_natural"] is None
    errors: list[str] = []
    module.validate_review(review, errors)
    assert not any("scene-08: continuation_reason_natural" in error for error in errors)


def test_unnatural_continuation_requires_finding():
    review = valid_review()
    review["scene_checks"][3]["continuation_reason_natural"] = False
    errors: list[str] = []
    module.validate_review(review, errors)
    assert any("scene-04: unnatural continuation requires" in error for error in errors)


def test_fake_open_loop_finding_satisfies_continuation_failure_but_blocks_pass_when_major():
    review = valid_review()
    review["scene_checks"][3]["continuation_reason_natural"] = False
    review["findings"] = [{
        "finding_id": "finding-01",
        "severity": "major",
        "issue_type": "FAKE_OPEN_LOOP",
        "scene_ids": ["scene-04"],
        "problem": "Answer is artificially withheld.",
        "viewer_impact": "The continuation feels manipulative.",
        "minimal_fix": "Deliver the current payoff and continue with a real test.",
    }]
    review["verdict"] = "conditional"
    errors: list[str] = []
    module.validate_review(review, errors)
    assert errors == []


def test_scene_08_failed_closure_cannot_pass():
    review = valid_review()
    review["scene_checks"][7]["closure_effective"] = False
    errors: list[str] = []
    module.validate_review(review, errors)
    assert any("ineffective closure cannot PASS" in error for error in errors)


def test_procedural_dominance_requires_finding():
    review = valid_review()
    review["scene_checks"][2]["procedural_language_dominant"] = True
    errors: list[str] = []
    module.validate_review(review, errors)
    assert any("PROCEDURAL_NARRATION finding" in error for error in errors)


def test_pass_cannot_hide_missing_late_payoff_behind_high_score():
    review = valid_review()
    review["scores"] = {"opening": 5, "progression": 5, "discovery": 5, "clarity": 5, "fox_voice": 4, "late_payoff": 5}
    review["total_score"] = 29
    review["scene_checks"][5]["payoff_delivered"] = False
    review["findings"] = [finding("NO_LATE_PAYOFF", ["scene-06", "scene-07", "scene-08"])]
    review["verdict"] = "pass"
    errors: list[str] = []
    module.validate_review(review, errors)
    assert any("scene-06: PASS requires payoff_delivered=true" in error for error in errors)
    assert any("review verdict must be conditional" in error for error in errors)


def test_pass_requires_belief_change_in_late_scene_even_with_matching_finding():
    review = valid_review()
    review["scene_checks"][6]["belief_changed"] = False
    review["findings"] = [finding("NO_BELIEF_CHANGE", ["scene-07"])]
    review["verdict"] = "pass"
    errors: list[str] = []
    module.validate_review(review, errors)
    assert any("scene-07: PASS requires belief_changed=true" in error for error in errors)
    assert any("review verdict must be conditional" in error for error in errors)


def test_hard_narrative_finding_cannot_be_minor():
    review = valid_review()
    review["findings"] = [finding("NO_UNDERSTANDING_UPGRADE", ["scene-05"], severity="minor")]
    errors: list[str] = []
    module.validate_review(review, errors)
    assert any("NO_UNDERSTANDING_UPGRADE must be major or critical" in error for error in errors)


def test_major_no_late_payoff_is_valid_conditional_review():
    review = valid_review()
    review["findings"] = [finding("NO_LATE_PAYOFF", ["scene-06", "scene-07", "scene-08"])]
    review["verdict"] = "conditional"
    errors: list[str] = []
    module.validate_review(review, errors)
    assert errors == []
