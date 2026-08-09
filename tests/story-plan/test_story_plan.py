from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "skills/nasdaq-cafe-story-plan/validators/validate_story_plan.py"
SCHEMA_PATH = ROOT / "skills/nasdaq-cafe-story-plan/contracts/story_plan.schema.json"

spec = importlib.util.spec_from_file_location("story_plan_validator", VALIDATOR_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader is not None
spec.loader.exec_module(module)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def dossier() -> dict:
    return {
        "episode_date": "2026-08-06",
        "evidence": [{"evidence_id": f"E-{i:03d}"} for i in range(1, 6)],
        "contradictions": [{"id": "CON-01", "statement": "Good numbers, bad stock."}],
        "editorial_handoff": {
            "headline_beyond_discovery": "Evidence of demand mattered more than demand itself.",
            "confidence": "medium",
        },
        "causal_edges": [
            {"scope": "company_direct", "confidence": "high"},
            {"scope": "sector_support", "confidence": "medium"},
            {"scope": "nasdaq_wide", "confidence": "medium"},
        ],
        "contrary_evidence": [
            {"effect_on_confidence": "material", "evidence_ids": ["E-004"]},
            {"effect_on_confidence": "minor", "evidence_ids": ["E-005"]},
        ],
    }


def valid_plan(dossier_path: Path) -> dict:
    sha = hashlib.sha256(dossier_path.read_bytes()).hexdigest()
    formal_roles = [
        "direction_and_conclusion", "contradiction", "confirmed_facts",
        "expected_actual_gap", "global_context", "market_reaction",
        "entity_divergence", "validation_points", "fixed_closing",
    ]
    story_roles = [
        "hook", "question", "setup", "explanation", "context",
        "test", "comparison", "verification", "closing",
    ]
    connectors = [
        "opening", "but", "therefore", "therefore", "therefore",
        "but", "contrast", "callback", "closing",
    ]
    scenes = []
    for index in range(1, 10):
        scenes.append({
            "scene_id": f"scene-{index:02d}",
            "formal_role": formal_roles[index - 1],
            "story_role": story_roles[index - 1],
            "viewer_belief_before": "before" if index < 9 else "story complete",
            "new_evidence_ids": [] if index == 9 else [f"E-{min(index, 5):03d}"],
            "new_meaning": "" if index == 9 else f"meaning {index}",
            "viewer_belief_after": "done" if index == 9 else f"after {index}",
            "continuation_reason": "next value" if index <= 7 else "",
            "connector": connectors[index - 1],
        })

    selected = {
        "id": "angle-01",
        "angle_type": "contradiction",
        "central_question": "Why did good numbers fail to support the stock?",
        "story_spine": "Good numbers were not enough because proof of the next demand winner mattered more.",
        "opening_promise": "The index fell, AMD fell harder, yet the headline numbers were good. Why?",
        "midpoint_turn_claim": "The comparison shows the issue was not AI demand disappearing, but who had stronger proof of winning it.",
        "closing_reframe": "The night was less about whether AI demand exists and more about whose evidence of capture was strongest.",
        "causality_scope": "nasdaq_support",
        "confidence": "medium",
        "evidence_ids": ["E-001", "E-002"],
        "counterevidence_ids": ["E-004"],
        "risk": "Do not promote the company story to a NASDAQ-wide primary cause.",
        "why_distinct": "Starts from the good-results/bad-stock contradiction.",
    }
    angles = [
        selected,
        {
            **deepcopy(selected),
            "id": "angle-02", "angle_type": "comparison",
            "central_question": "Why did two AI suppliers move in opposite directions?",
            "story_spine": "The relative comparison exposes a proof gap between suppliers.",
            "opening_promise": "AI demand was strong, but the suppliers did not trade together.",
            "midpoint_turn_claim": "The peer split weakens a simple sector-wide risk-off explanation.",
            "closing_reframe": "The divergence was evidence of selective proof, not uniform AI pessimism.",
            "why_distinct": "Uses peer divergence as the entry point.",
            "causality_scope": "sector",
        },
        {
            **deepcopy(selected),
            "id": "angle-03", "angle_type": "causal_chain",
            "central_question": "How far can the company-specific story explain the NASDAQ decline?",
            "story_spine": "Company evidence explains part of the night, while broader tech weakness limits the scope claim.",
            "opening_promise": "A dramatic company move happened inside a broader but mixed market decline.",
            "midpoint_turn_claim": "The index evidence shows the lead is explanatory but not sufficient as the sole NASDAQ cause.",
            "closing_reframe": "The company was the clearest lens, not the only market cause.",
            "why_distinct": "Centers causal scope rather than the company surprise.",
            "causality_scope": "nasdaq_support",
        },
    ]
    return {
        "contract_version": "1.2.0",
        "episode_date": "2026-08-06",
        "created_at": "2026-08-07T12:00:00Z",
        "producer": "chatgpt",
        "causal_dossier": {"path": "research/dossier.json", "sha256": sha},
        "central_contradiction_id": "CON-01",
        "central_contradiction": "Good numbers, bad stock.",
        "central_question": selected["central_question"],
        "headline_beyond_discovery": "Evidence of demand mattered more than demand itself.",
        "naive_explanations": [{
            "id": "naive-01", "explanation": "The reported numbers were simply bad.",
            "status": "rejected", "evidence_ids": ["E-001"],
            "why": "The source evidence contradicts that simple explanation.",
        }],
        "angle_candidates": angles,
        "selected_angle_id": "angle-01",
        "story_spine": selected["story_spine"],
        "opening_promise": selected["opening_promise"],
        "midpoint_turn": {
            "scene_id": "scene-06", "claim": selected["midpoint_turn_claim"],
            "evidence_ids": ["E-002", "E-003"],
            "what_changes": "The explanation changes from bad AI demand to relative proof of winning demand.",
        },
        "closing_reframe": {"scene_id": "scene-08", "text": selected["closing_reframe"]},
        "open_loops": [{
            "id": "loop-01", "open_scene": "scene-02",
            "question": "Why did good numbers fail?", "promised_evidence_ids": ["E-002"],
            "close_scene": "scene-06", "resolution": "The price and peer comparison reveal a higher proof threshold.",
        }],
        "scenes": scenes,
    }


def validate(tmp_path: Path, plan: dict, dossier_value: dict | None = None):
    dossier_path = tmp_path / "research/dossier.json"
    write_json(dossier_path, dossier_value or dossier())
    plan = deepcopy(plan)
    plan["causal_dossier"]["sha256"] = hashlib.sha256(dossier_path.read_bytes()).hexdigest()
    story_path = tmp_path / "working/story_plan.json"
    write_json(story_path, plan)
    return module.validate_story_plan(story_path, dossier_path, repo_root=tmp_path, schema_path=SCHEMA_PATH)


def fresh(tmp_path: Path) -> dict:
    dossier_path = tmp_path / "research/dossier.json"
    write_json(dossier_path, dossier())
    return valid_plan(dossier_path)


def test_valid_plan_passes(tmp_path: Path):
    result = validate(tmp_path, fresh(tmp_path))
    assert result.ok, result.errors


def test_contract_requires_v1_2(tmp_path: Path):
    plan = fresh(tmp_path)
    plan["contract_version"] = "1.1.0"
    result = validate(tmp_path, plan)
    assert any("1.2.0" in error for error in result.errors)


def test_unknown_evidence_is_rejected(tmp_path: Path):
    plan = fresh(tmp_path)
    plan["scenes"][0]["new_evidence_ids"] = ["E-999"]
    result = validate(tmp_path, plan)
    assert any("unknown evidence id E-999" in error for error in result.errors)


def test_confidence_cannot_be_strengthened(tmp_path: Path):
    plan = fresh(tmp_path)
    plan["angle_candidates"][0]["confidence"] = "high"
    result = validate(tmp_path, plan)
    assert any("strengthens dossier confidence" in error for error in result.errors)


def test_material_counterevidence_cannot_be_removed(tmp_path: Path):
    plan = fresh(tmp_path)
    plan["angle_candidates"][0]["counterevidence_ids"] = []
    result = validate(tmp_path, plan)
    assert any("omits material counterevidence" in error for error in result.errors)


def test_scene_1_to_8_require_payoff(tmp_path: Path):
    plan = fresh(tmp_path)
    plan["scenes"][4]["new_meaning"] = ""
    result = validate(tmp_path, plan)
    assert any("scene-05: new_meaning payoff is required" in error for error in result.errors)


def test_scene_1_to_7_require_continuation_reason(tmp_path: Path):
    plan = fresh(tmp_path)
    plan["scenes"][3]["continuation_reason"] = ""
    result = validate(tmp_path, plan)
    assert any("scene-04: continuation_reason is required" in error for error in result.errors)


def test_scene_8_must_close_instead_of_continue(tmp_path: Path):
    plan = fresh(tmp_path)
    plan["scenes"][7]["continuation_reason"] = "watch the next scene"
    result = validate(tmp_path, plan)
    assert any("scene-08: continuation_reason must be empty" in error for error in result.errors)


def test_scene_09_cannot_add_evidence_meaning_or_continuation(tmp_path: Path):
    plan = fresh(tmp_path)
    plan["scenes"][8]["new_evidence_ids"] = ["E-001"]
    plan["scenes"][8]["new_meaning"] = "new argument"
    plan["scenes"][8]["continuation_reason"] = "more later"
    result = validate(tmp_path, plan)
    assert any("cannot add new evidence" in error for error in result.errors)
    assert any("cannot add new narrative meaning" in error for error in result.errors)
    assert any("cannot leave a continuation reason" in error for error in result.errors)


def test_open_loop_must_close_after_it_opens(tmp_path: Path):
    plan = fresh(tmp_path)
    plan["open_loops"][0]["open_scene"] = "scene-06"
    plan["open_loops"][0]["close_scene"] = "scene-04"
    result = validate(tmp_path, plan)
    assert any("close_scene must come after open_scene" in error for error in result.errors)


def test_scene_order_and_roles_are_fixed(tmp_path: Path):
    plan = fresh(tmp_path)
    plan["scenes"][4], plan["scenes"][5] = plan["scenes"][5], plan["scenes"][4]
    result = validate(tmp_path, plan)
    assert any("scenes must be exactly ordered" in error for error in result.errors)
    assert any("formal roles do not match" in error for error in result.errors)
