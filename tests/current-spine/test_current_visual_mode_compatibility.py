#!/usr/bin/env python3
"""Regression: reviewed authoring visual-mode aliases stay compatible with Current Renderer."""
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import renderer_strict_projection  # noqa: E402
import visual_intelligence_renderer_projection  # noqa: E402


def _nine_scene_spec(*, first_mode="text-focus", first_template="text-focus"):
    scenes = []
    for index in range(1, 10):
        mode = first_mode if index == 1 else "text-focus"
        template = first_template if index == 1 else "text-focus"
        scenes.append(
            {
                "sceneId": f"scene-{index:02d}",
                "visualMode": mode,
                "visualBeats": [
                    {
                        "beatId": f"scene-{index:02d}-beat-001",
                        "visualMode": mode,
                        "visualTemplate": template,
                        "visualGrammarId": "bridge-text",
                        "transitionRole": "continuation",
                        "templateConfig": {"variant": "default"},
                    }
                ],
            }
        )
    return {"schemaVersion": "2.4.0", "scenes": scenes}


def _contract_paths(tmp_path):
    paths = [tmp_path / "final.json", tmp_path / "semantics.json", tmp_path / "compatibility.json"]
    for path in paths:
        path.write_text("{}\n", encoding="utf-8")
    return paths


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
    # Visual Intelligence may admit the legacy producer vocabulary at its coarse
    # vocabulary check, but the strict projection below owns the template-specific
    # canonicalization and still fails closed when the template is not reviewed.
    visual_intelligence_renderer_projection._require_known_mode(
        "comparison", path="$.scenes[5].visualMode"
    )


def test_comparison_without_reviewed_template_remains_fail_closed(tmp_path):
    final_contract, semantics, compatibility = _contract_paths(tmp_path)
    render_spec = _nine_scene_spec(
        first_mode="comparison", first_template="future-unreviewed-template"
    )
    with pytest.raises(
        renderer_strict_projection.StrictRendererProjectionError,
        match="comparison visualMode requires reviewed visualTemplate",
    ):
        renderer_strict_projection.strict_renderer_projection(
            render_spec,
            final_contract_path=final_contract,
            semantics_path=semantics,
            renderer_compatibility_path=compatibility,
        )


def test_strict_projection_contract_shape_stays_unchanged(tmp_path):
    render_spec = _nine_scene_spec()
    final_contract, semantics, compatibility = _contract_paths(tmp_path)

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

    broken = _nine_scene_spec()
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
