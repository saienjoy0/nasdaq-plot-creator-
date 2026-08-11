from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_TEST = ROOT / "tests/story-plan/test_story_plan.py"

spec = importlib.util.spec_from_file_location("story_plan_base_20260810", BASE_TEST)
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
assert spec.loader is not None
spec.loader.exec_module(base)

PROVISIONAL = "弱い雇用で利上げ観測が後退し、テックに追い風が入った。"
FINAL_REFRAME = "同じNASDAQ・半導体高でも、マクロ反応と企業固有材料という複数エンジンが同じ指数方向へ重なった。"


def dossier_2026_08_10() -> dict:
    return {
        "episode_date": "2026-08-10",
        "evidence": [
            {"evidence_id": "E-001", "description": "July payroll Actual -23k versus Expected +80k; Gap -103k."},
            {"evidence_id": "E-002", "description": "Rate-hike odds moved from about 67% a week earlier to 55% prior session to about 44%."},
            {"evidence_id": "E-003", "description": "At 8:30 ET QQQ 719.16 -> 720.23, SOXX 541.06 -> 542.40, NVDA 219.95 -> 220.31."},
            {"evidence_id": "E-004", "description": "At the same 8:30 ET minute MCHP 79.58 -> 79.56, unlike the macro-sensitive series."},
            {"evidence_id": "E-005", "description": "Microchip had a separate earnings/guidance catalyst and finished +13.89%."},
            {"evidence_id": "E-006", "description": "AMD -1.21% and Alphabet -0.96% limited any blanket-tech-rally explanation."},
            {"evidence_id": "E-007", "description": "One-minute alignment is chronology evidence, not causal proof."},
        ],
        "contradictions": [
            {
                "id": "CON-01",
                "statement": "July payrolls missed badly, yet NASDAQ rose 1.30% and SOXX rose 2.02%.",
            }
        ],
        "editorial_handoff": {
            "headline_beyond_discovery": "The same semiconductor-up session contained different causal engines.",
            "confidence": "medium",
        },
        "causal_edges": [
            {"scope": "company_direct", "confidence": "high"},
            {"scope": "sector_support", "confidence": "medium"},
            {"scope": "nasdaq_wide", "confidence": "medium"},
        ],
        "contrary_evidence": [
            {"effect_on_confidence": "material", "evidence_ids": ["E-004"]},
            {"effect_on_confidence": "minor", "evidence_ids": ["E-006"]},
        ],
    }


def real_day_plan(tmp_path: Path, *, revised: bool) -> dict:
    plan = base.fresh(tmp_path)
    plan["episode_date"] = "2026-08-10"
    plan["created_at"] = "2026-08-11T01:00:00Z"
    plan["central_contradiction"] = dossier_2026_08_10()["contradictions"][0]["statement"]
    plan["headline_beyond_discovery"] = dossier_2026_08_10()["editorial_handoff"]["headline_beyond_discovery"]

    selected = next(item for item in plan["angle_candidates"] if item["id"] == plan["selected_angle_id"])
    selected.update(
        {
            "central_question": "Why did NASDAQ and semiconductors rise after such a large payroll miss?",
            "story_spine": "The payroll miss first worked through Fed expectations, but the semiconductor move cannot be treated as one uniform macro trade.",
            "opening_promise": "悪い雇用なのにNASDAQと半導体は上昇した。鍵は金利だが、それだけでは一つ数字が合わない。",
            "midpoint_turn_claim": (
                "MCHPの8:30無反応が、半導体高を一つのマクロ要因だけで説明する見方を崩す。"
                if revised
                else "金利観測の低下に原油安も重なり、テックへの支援材料が増えた。"
            ),
            "closing_reframe": FINAL_REFRAME if revised else "弱い雇用で利上げ観測が後退し、テックに追い風が入った夜だった。",
            "causality_scope": "nasdaq_support",
            "confidence": "medium",
            "evidence_ids": ["E-001", "E-002", "E-003", "E-004", "E-005", "E-006", "E-007"],
            "counterevidence_ids": ["E-004", "E-006"],
            "risk": "Do not turn company-specific Microchip earnings into the NASDAQ-wide primary cause.",
            "why_distinct": "Separates immediate macro reaction from a company-specific semiconductor engine.",
        }
    )

    plan["central_question"] = selected["central_question"]
    plan["story_spine"] = selected["story_spine"]
    plan["opening_promise"] = selected["opening_promise"]
    plan["closing_reframe"] = {"scene_id": "scene-08", "text": selected["closing_reframe"]}

    scenes = plan["scenes"]
    after_values = [
        "悪い雇用でもNASDAQとSOXXは上昇した。",
        "雇用はExpected +8万人に対してActual -2.3万人だった。",
        "Gapは-10.3万人で、見出しより大きな下振れだった。",
        PROVISIONAL,
        "金利観測の低下に加え、他の支援材料も同じ方向へ働いた。",
        (
            "QQQ・SOXX・NVDAは8:30に上向いたが、MCHPは79.58から79.56でほぼ反応せず、マクロだけでは半導体高を一括説明できない。"
            if revised
            else "Microchipの決算も半導体高を支え、弱い雇用からのテック追い風という説明を補強した。"
        ),
        (
            "MCHPには決算という別エンジンがあり、AMDとAlphabetの下落はテック全面高という一般化も制限する。"
            if revised
            else "AMDとAlphabetは下落しており、全面高ではないという留保が必要だ。"
        ),
        FINAL_REFRAME if revised else PROVISIONAL,
    ]
    evidence_by_scene = [
        ["E-001"], ["E-001"], ["E-001"], ["E-001", "E-002"],
        ["E-002"], ["E-003", "E-004"] if revised else ["E-005"],
        ["E-005", "E-006"] if revised else ["E-006"], ["E-003", "E-004", "E-007"],
    ]
    previous = "雇用悪化なら普通はリスク資産に逆風だと考えている。"
    for index, scene in enumerate(scenes[:8]):
        scene["viewer_belief_before"] = previous
        scene["viewer_belief_after"] = after_values[index]
        scene["new_meaning"] = f"2026-08-10 understanding step {index + 1}"
        scene["new_evidence_ids"] = evidence_by_scene[index]
        scene["continuation_reason"] = "次のEvidenceで説明範囲を確認する" if index < 7 else ""
        previous = after_values[index]

    if revised:
        plan["midpoint_turn"] = {
            "scene_id": "scene-06",
            "claim": selected["midpoint_turn_claim"],
            "evidence_ids": ["E-003", "E-004"],
            "what_changes": "半導体高を一つの金利マクロ取引として見る暫定解から、マクロ反応と企業固有材料を分ける説明へ更新する。",
        }
    else:
        plan["midpoint_turn"] = {
            "scene_id": "scene-05",
            "claim": selected["midpoint_turn_claim"],
            "evidence_ids": ["E-002"],
            "what_changes": "金利要因に別の支援材料を追加する。",
        }

    plan["open_loops"] = [
        {
            "id": "loop-01",
            "open_scene": "scene-02",
            "question": "Why did tech rise after the payroll miss?",
            "promised_evidence_ids": ["E-002", "E-003", "E-004"],
            "close_scene": "scene-08",
            "resolution": "The immediate macro reaction and the MCHP non-reaction separate the causal engines.",
        }
    ]
    return plan


def test_2026_08_10_front_loaded_structure_is_rejected(tmp_path: Path):
    plan = real_day_plan(tmp_path, revised=False)
    result = base.validate(tmp_path, plan, dossier_2026_08_10())
    assert not result.ok
    assert any(
        "scene-08 understanding must be structurally deeper/different than scene-04 understanding" in error
        for error in result.errors
    )


def test_2026_08_10_revised_branch_structure_passes(tmp_path: Path):
    plan = real_day_plan(tmp_path, revised=True)
    result = base.validate(tmp_path, plan, dossier_2026_08_10())
    assert result.ok, result.errors
