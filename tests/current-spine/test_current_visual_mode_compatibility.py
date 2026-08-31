#!/usr/bin/env python3
"""Regression: reviewed authoring visual-mode aliases stay compatible with Current Renderer."""
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import renderer_strict_projection  # noqa: E402
import visual_intelligence_renderer_projection  # noqa: E402


def test_expectation_gap_is_reviewed_renderer_alias():
    assert renderer_strict_projection.VISUAL_MODE_MAP["expectation-gap"] == "expected-actual-gap"
    visual_intelligence_renderer_projection._require_known_mode(
        "expectation-gap", path="$.scenes[3].visualMode"
    )


def test_comparison_is_normalized_only_by_reviewed_template():
    assert renderer_strict_projection.normalize_visual_mode(
        "comparison", visual_template="event-reaction-timeline"
    ) == "timeline"
    assert renderer_strict_projection.normalize_visual_mode(
        "comparison", visual_template="verification-matrix"
    ) == "verification-points"

    visual_intelligence_renderer_projection._require_known_mode(
        "comparison",
        path="$.scenes[5].visualBeats[0].visualMode",
        visual_template="event-reaction-timeline",
    )
    visual_intelligence_renderer_projection._require_known_mode(
        "comparison",
        path="$.scenes[5].visualBeats[1].visualMode",
        visual_template="verification-matrix",
    )


def test_comparison_without_reviewed_template_remains_fail_closed():
    with pytest.raises(
        visual_intelligence_renderer_projection.VisualIntelligenceRendererProjectionError,
        match="E_VISUAL_MODE_UNMAPPED",
    ):
        visual_intelligence_renderer_projection._require_known_mode(
            "comparison", path="$.scenes[5].visualMode"
        )


def test_strict_projection_contract_shape_stays_unchanged(tmp_path):
    scenes = []
    for index in range(1, 10):
        scenes.append(
            {
                "sceneId": f"scene-{index:02d}",
                "visualMode": "text-focus",
                "visualBeats": [
                    {
                        "beatId": f"scene-{index:02d}-beat-001",
                        "visualMode": "text-focus",
                        "visualTemplate": "text-focus",
                        "visualGrammarId": "bridge-text",
                        "transitionRole": "continuation",
                        "templateConfig": {"variant": "default"},
                    }
                ],
            }
        )
    render_spec = {"schemaVersion": "2.4.0", "scenes": scenes}
    final_contract = tmp_path / "final.json"
    semantics = tmp_path / "semantics.json"
    compatibility = tmp_path / "compatibility.json"
    for path in (final_contract, semantics, compatibility):
        path.write_text("{}\n", encoding="utf-8")

    projected = renderer_strict_projection.strict_renderer_projection(
        render_spec,
        final_contract_path=final_contract,
        semantics_path=semantics,
        renderer_compatibility_path=compatibility,
    )

    assert "visualGrammarContract" in projected
    assert "rendererCompatibility" not in projected
    assert projected["visualGrammarContract"]["contractVersion"] == "1.0.0"
    assert projected["visualGrammarContract"]["beatCount"] == 9
    assert projected["scenes"][0]["visualBeats"][0]["templateVariant"] == "default"

    broken = {"schemaVersion": "2.4.0", "scenes": scenes}
    del broken["scenes"][0]["visualBeats"][0]["templateConfig"]
    with pytest.raises(renderer_strict_projection.StrictRendererProjectionError, match="templateConfig missing"):
        renderer_strict_projection.strict_renderer_projection(
            broken,
            final_contract_path=final_contract,
            semantics_path=semantics,
            renderer_compatibility_path=compatibility,
        )


def test_unknown_mode_remains_fail_closed():
    try:
        visual_intelligence_renderer_projection._require_known_mode(
            "future-unreviewed-mode", path="$.scenes[0].visualMode"
        )
    except visual_intelligence_renderer_projection.VisualIntelligenceRendererProjectionError as exc:
        assert "E_VISUAL_MODE_UNMAPPED" in str(exc)
    else:
        raise AssertionError("unknown visualMode did not fail closed")
