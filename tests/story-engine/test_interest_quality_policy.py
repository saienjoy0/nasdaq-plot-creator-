from __future__ import annotations

import ast
import json
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
