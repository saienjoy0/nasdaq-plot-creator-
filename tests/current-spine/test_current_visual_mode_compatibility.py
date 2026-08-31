#!/usr/bin/env python3
"""Regression: reviewed producer modes project to the selected Renderer template mode."""
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


@pytest.mark.parametrize(
    ("producer_mode", "visual_template", "renderer_mode"),
    [
        ("comparison", "event-reaction-timeline", "timeline"),
        ("comparison", "verification-matrix", "verification-points"),
        ("comparison", "split-comparison", "stock-comparison"),
        ("verification-matrix", "verification-matrix", "verification-points"),
        ("verification-matrix", "split-comparison", "stock-comparison"),
        ("conclusion-card", "hero-number", "text-focus"),
        ("text-focus", "split-comparison", "stock-comparison"),
        ("number-comparison", "verification-matrix", "verification-points"),
    ],
)
def test_selected_template_is_renderer_mode_authority(
    producer_mode, visual_template, renderer_mode
):
    assert renderer_strict_projection.normalize_visual_mode(
        producer_mode, visual_template=visual_template
    ) == renderer_mode
    visual_intelligence_renderer_projection._require_known_mode(
        producer_mode, path="$.scenes[5].visualMode"
    )


def test_scene_and_beat_mode_follow_first_selected_template(tmp_path):
    final_contract, semantics, compatibility = _contract_paths(tmp_path)
    render_spec = _nine_scene_spec(
        first_mode="comparison", first_template="split-comparison"
    )
    projected = renderer_strict_projection.strict_renderer_projection(
        render_spec,
        final_contract_path=final_contract,
        semantics_path=semantics,
        renderer_compatibility_path=compatibility,
    )
    assert projected["scenes"][0]["visualMode"] == "stock-comparison"
    assert projected["scenes"][0]["visualBeats"][0]["visualMode"] == "stock-comparison"


@pytest.mark.parametrize("producer_mode", ["comparison", "verification-matrix"])
def test_template_derived_legacy_mode_without_reviewed_template_remains_fail_closed(
    tmp_path, producer_mode
):
    final_contract, semantics, compatibility = _contract_paths(tmp_path)
    render_spec = _nine_scene_spec(
        first_mode=producer_mode, first_template="future-unreviewed-template"
    )
    with pytest.raises(
        renderer_strict_projection.StrictRendererProjectionError,
        match="requires reviewed visualTemplate",
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
