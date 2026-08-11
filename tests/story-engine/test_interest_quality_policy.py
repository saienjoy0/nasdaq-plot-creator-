from __future__ import annotations

import ast
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

INTEREST_FINDINGS = {
    "FACT_STACKING",
    "LOW_INFORMATION_GAIN",
    "PAYOFF_DROUGHT",
    "WEAK_SURPRISE",
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assigned_literal(path: str, name: str):
    tree = ast.parse(read(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"assignment not found: {name}")


def load_bundle_validator():
    path = ROOT / "scripts/story-engine/validate_story_engine_bundle.py"
    spec = importlib.util.spec_from_file_location("interest_bundle_validator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
        "reviewer": "editorial_critic",
        "round": 1,
        "scores": {
            "opening": 4,
            "progression": 5,
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


def test_interest_policy_is_wired_across_story_plan_authoring_and_critic():
    story_plan = read("skills/nasdaq-cafe-story-plan/SKILL.md")
    authoring = read("skills/nasdaq-cafe-story-authoring/SKILL.md")
    critic = read("skills/nasdaq-cafe-entertainment-critic/SKILL.md")

    assert "Information Gain" in story_plan
    assert "Information Gap boundary" in story_plan
    assert "Internal Understanding Gain classification" in story_plan
    assert "support" in story_plan and "branch" in story_plan and "verification" in story_plan

    assert "And / But / Therefore (ABT)" in authoring
    assert "Fact-stacking compression rule" in authoring

    for issue_type in INTEREST_FINDINGS:
        assert issue_type in critic


def test_creative_review_schema_accepts_interest_findings():
    schema = json.loads(
        read("skills/nasdaq-cafe-entertainment-critic/contracts/creative_review.schema.json")
    )
    allowed = set(
        schema["$defs"]["finding"]["properties"]["issue_type"]["enum"]
    )
    assert INTEREST_FINDINGS <= allowed


def test_external_critic_has_same_interest_vocabulary_and_policy():
    adapter_path = "critic-adapters/openai/main.py"
    issue_types = set(assigned_literal(adapter_path, "ISSUE_TYPES"))
    hard_findings = set(assigned_literal(adapter_path, "HARD_NARRATIVE_FINDINGS"))
    prompt_source = read(adapter_path)

    assert INTEREST_FINDINGS <= issue_types
    assert INTEREST_FINDINGS.isdisjoint(hard_findings)
    assert "interest-quality diagnostics" in prompt_source
    assert "Interestingness means Evidence-backed model update" in prompt_source


def test_interest_quality_remains_semantic_not_story_plan_schema_math():
    schema = json.loads(
        read("skills/nasdaq-cafe-story-plan/contracts/story_plan.schema.json")
    )
    scene_properties = schema["$defs"]["scene"]["properties"]
    assert "information_gain" not in scene_properties
    assert "gain_type" not in scene_properties
    assert "surprise_score" not in scene_properties


def test_minor_interest_finding_can_remain_a_pass():
    validator = load_bundle_validator()
    review = valid_review()
    review["findings"] = [
        {
            "finding_id": "finding-01",
            "severity": "minor",
            "issue_type": "FACT_STACKING",
            "scene_ids": ["scene-05"],
            "problem": "支援材料が続き、説明モデルの更新が小さい。",
            "viewer_impact": "中盤のテンポが少し落ちる。",
            "minimal_fix": "Scene 5の重複説明を圧縮する。",
        }
    ]
    errors: list[str] = []
    validator.validate_review(review, errors)
    assert errors == []


def test_major_interest_finding_blocks_pass_without_becoming_a_hard_finding():
    validator = load_bundle_validator()
    review = deepcopy(valid_review())
    review["findings"] = [
        {
            "finding_id": "finding-01",
            "severity": "major",
            "issue_type": "PAYOFF_DROUGHT",
            "scene_ids": ["scene-02", "scene-03", "scene-04"],
            "problem": "複数Sceneで事実追加が続き、理解の報酬が不足している。",
            "viewer_impact": "Scene 6の本当の発見まで講義のように感じる。",
            "minimal_fix": "既存Evidenceとformal roleを保ったまま中盤を圧縮する。",
        }
    ]
    errors: list[str] = []
    validator.validate_review(review, errors)
    assert any("review verdict must be conditional" in error for error in errors)


def test_2026_08_10_interest_benchmark_keeps_support_short_and_scene6_high_gain():
    benchmark = json.loads(
        read("tests/story-engine/fixtures/2026-08-10-interest/interest_benchmark.json")
    )
    profile = {row["scene_id"]: row for row in benchmark["scene_gain_profile"]}

    assert benchmark["episode_date"] == "2026-08-10"
    assert profile["scene-05"]["primary_gain"] == "support"
    assert profile["scene-05"]["strength"] == "low"

    assert profile["scene-06"]["primary_gain"] == "branch"
    assert "verification" in profile["scene-06"]["secondary_gains"]
    assert profile["scene-06"]["strength"] == "very_high"
    assert set(profile["scene-06"]["required_evidence_ids"]) == {
        "E-003",
        "E-004",
        "E-007",
    }

    assert "NO_LATE_PAYOFF" in benchmark["old_frontloaded_expected_findings"]
    assert set(benchmark["interest_findings"]) == INTEREST_FINDINGS
    assert "NO_LATE_PAYOFF" in benchmark["revised_expected_hard_findings_absent"]
