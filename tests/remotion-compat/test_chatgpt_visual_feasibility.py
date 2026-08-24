from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "validate_chatgpt_visual_feasibility.py"


def _load():
    spec = importlib.util.spec_from_file_location("visual_feasibility", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


feasibility = _load()


def authoring(beat: dict, *, financial_bindings=None):
    return {
        "contractVersion": "2.0.0",
        "episodeDate": "2099-01-02",
        "production": {
            "financialBindings": financial_bindings or [],
            "scenes": [{"beats": [beat]}],
        },
    }


def base_beat(template: str, grammar: str = "comparison"):
    return {
        "visualTemplate": template,
        "visualMode": "number-comparison",
        "grammarId": grammar,
        "viewerTexts": ["A", "B"],
    }


def test_split_comparison_requires_explicit_aligned_metrics():
    beat = base_beat("split-comparison")
    errors = feasibility.validate(authoring(beat))
    assert any("explicit authored metrics" in error for error in errors)

    beat["metrics"] = [
        {"label": "AMAT", "value": "-5.12%", "numericValue": -5.12, "unit": "%", "comparison": "same close"},
        {"label": "AMD", "value": "+6.50%", "numericValue": 6.5, "unit": "%", "comparison": "same close"},
    ]
    assert feasibility.validate(authoring(beat)) == []


def test_numeric_template_rejects_mixed_comparison_basis():
    beat = base_beat("split-comparison")
    beat["metrics"] = [
        {"label": "A", "value": "1%", "numericValue": 1, "unit": "%", "comparison": "close A"},
        {"label": "B", "value": "2%", "numericValue": 2, "unit": "%", "comparison": "close B"},
    ]
    errors = feasibility.validate(authoring(beat))
    assert any("one aligned comparison basis" in error for error in errors)


def test_financial_binding_may_own_numeric_renderer_data():
    beat = base_beat("market-pulse-grid", grammar="evidence")
    bindings = [{"sourceBeatId": "scene-01-beat-001"}]
    assert feasibility.validate(authoring(beat, financial_bindings=bindings)) == []


def test_lane_templates_require_two_explicit_prefixed_lanes():
    beat = base_beat("tailwind-headwind", grammar="causal")
    beat["visualMode"] = "causal-chain"
    errors = feasibility.validate(authoring(beat))
    assert any("two explicit laneLabels" in error for error in errors)

    beat["laneLabels"] = ["逆風", "相殺"]
    beat["viewerTexts"] = ["逆風｜成長不安", "相殺｜利上げ観測後退"]
    assert feasibility.validate(authoring(beat)) == []


def test_nonseries_reaction_timeline_requires_explicit_variant_and_event_order():
    beat = base_beat("event-reaction-timeline", grammar="reaction")
    beat["visualMode"] = "comparison"
    beat["variant"] = "official-time-plus-close"
    beat["metrics"] = [
        {"label": "8/13 引け後", "value": "AMAT反応開始"},
        {"label": "8/14 08:30", "value": "小売発表"},
        {"label": "09:30", "value": "NASDAQ寄り付き"},
    ]
    beat["reactionTimeline"] = {
        "precision": "official-time-plus-close",
        "eventOrderIds": [
            "scene-01-number-01-01",
            "scene-01-number-01-02",
            "scene-01-number-01-03",
        ],
        "seriesObjectIds": [],
    }
    assert feasibility.validate(authoring(beat)) == []


def test_reaction_variant_precision_mismatch_fails():
    beat = base_beat("event-reaction-timeline", grammar="reaction")
    beat["variant"] = "reported-sequence"
    beat["reactionTimeline"] = {
        "precision": "official-time-plus-close",
        "eventOrderIds": ["scene-01-card-001"],
        "seriesObjectIds": [],
    }
    errors = feasibility.validate(authoring(beat))
    assert any("precision must be 'reported-sequence'" in error for error in errors)


def test_gap_flow_requires_canonical_visual_mode_before_freeze():
    beat = base_beat("expected-actual-gap-flow", grammar="gap")
    beat["visualMode"] = "expectation-gap"
    errors = feasibility.validate(authoring(beat))
    assert any("canonical visualMode 'expected-actual-gap'" in error for error in errors)
