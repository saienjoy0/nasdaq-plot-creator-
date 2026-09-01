#!/usr/bin/env python3
"""Regression: reviewed authoring compatibility stays compatible with Current Renderer."""
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
    ],
)
def test_template_aware_modes_use_reviewed_renderer_template_mapping(
    producer_mode, visual_template, renderer_mode
):
    assert renderer_strict_projection.normalize_visual_mode(
        producer_mode, visual_template=visual_template
    ) == renderer_mode
    visual_intelligence_renderer_projection._require_known_mode(
        producer_mode, path="$.scenes[5].visualMode"
    )


@pytest.mark.parametrize("producer_mode", ["comparison", "verification-matrix"])
def test_template_aware_mode_without_reviewed_template_remains_fail_closed(
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


def test_current_producer_shell_is_mechanically_projected_for_renderer_24(tmp_path):
    render_spec = _nine_scene_spec(first_mode="expectation-gap", first_template="expected-actual-gap-flow")
    render_spec.update(
        {
            "editorial": {
                "leadNews": "lead",
                "storySpine": "spine",
                "centralHypothesis": "hypothesis",
                "confidence": "medium",
                "expected": "expected",
                "actual": "actual",
                "gap": "gap",
                "expectedBasisType": "major_reporting",
                "expectedBasisDetails": "details",
                "counterEvidence": ["counter"],
            },
            "publishing": {
                "titleCandidates": ["title-1", "title-2", "title-3"],
                "thumbnailTextCandidates": ["thumb-1", "thumb-2", "thumb-3"],
                "description": "description",
            },
            "review": {
                "verdict": "approved",
                "approvedForCodex": True,
                "scores": {
                    "clarity": 5,
                    "discovery": 5,
                    "fox_voice": 4,
                    "late_payoff": 5,
                    "opening": 5,
                    "progression": 4,
                },
                "totalScore": 28,
                "largestDropoffRisk": "",
                "requiredChanges": [],
                "changesApplied": [],
            },
        }
    )
    render_spec["scenes"][0]["causalScope"] = "company_direct"
    render_spec["scenes"][0]["expectedBasisType"] = "major-reporting"
    render_spec["scenes"][0]["visualBeats"][0]["screenState"] = "Source"

    final_contract, semantics, compatibility = _contract_paths(tmp_path)
    projected = renderer_strict_projection.strict_renderer_projection(
        render_spec,
        final_contract_path=final_contract,
        semantics_path=semantics,
        renderer_compatibility_path=compatibility,
    )

    assert projected["editorial"]["leadTheme"] is None
    assert projected["editorial"]["targetIndices"] == ["Nasdaq Composite"]
    assert projected["editorial"]["directMaterial"] == []
    assert projected["editorial"]["nasdaqDrivers"] == []
    assert projected["editorial"]["amplifiers"] == []
    assert projected["editorial"]["offsettingFactors"] == []
    assert projected["editorial"]["expectedBasisType"] == "major-reporting"
    assert projected["editorial"]["expectedSourceIds"] == []
    assert projected["editorial"]["timelineBasis"] is None
    assert projected["editorial"]["verificationPoints"] == []
    assert projected["publishing"]["recommendedTitle"] == "title-1"
    assert projected["publishing"]["recommendedThumbnailText"] == "thumb-1"
    assert projected["review"]["scores"] == {
        "openingHook": 5,
        "storyProgression": 4,
        "discovery": 5,
        "clarity": 5,
        "foxCharacter": 4,
        "reasonToFinish": 5,
    }
    assert projected["review"]["largestDropoffRisk"] == "none-identified"
    assert projected["review"]["titleThumbnailConsistency"] == "consistent"
    assert projected["scenes"][0]["causalScope"] == "lead-stock"
    assert projected["scenes"][0]["visualBeats"][0]["screenState"] == "News"


def test_current_shell_projection_preserves_explicit_renderer_fields(tmp_path):
    render_spec = _nine_scene_spec()
    render_spec["editorial"] = {
        "leadNews": "lead",
        "leadTheme": "theme",
        "targetIndices": ["Nasdaq Composite", "SOXX"],
        "storySpine": "spine",
        "centralHypothesis": "hypothesis",
        "confidence": "medium",
        "directMaterial": ["direct"],
        "nasdaqDrivers": ["driver"],
        "amplifiers": ["amp"],
        "offsettingFactors": ["offset"],
        "expected": None,
        "actual": None,
        "gap": None,
        "expectedBasisType": None,
        "expectedBasisDetails": None,
        "expectedSourceIds": ["source-001"],
        "timelineBasis": "timeline",
        "counterEvidence": ["counter"],
        "verificationPoints": ["verify"],
    }
    render_spec["publishing"] = {
        "recommendedTitle": "chosen-title",
        "titleCandidates": ["chosen-title", "title-2", "title-3"],
        "recommendedThumbnailText": "chosen-thumb",
        "thumbnailTextCandidates": ["chosen-thumb", "thumb-2", "thumb-3"],
        "description": "description",
    }
    render_spec["review"] = {
        "verdict": "approved",
        "scores": {
            "openingHook": 5,
            "storyProgression": 4,
            "discovery": 5,
            "clarity": 5,
            "foxCharacter": 4,
            "reasonToFinish": 5,
        },
        "totalScore": 28,
        "largestDropoffRisk": "explicit-risk",
        "requiredChanges": [],
        "changesApplied": [],
        "titleThumbnailConsistency": "needs-revision",
        "approvedForCodex": True,
    }
    final_contract, semantics, compatibility = _contract_paths(tmp_path)
    projected = renderer_strict_projection.strict_renderer_projection(
        render_spec,
        final_contract_path=final_contract,
        semantics_path=semantics,
        renderer_compatibility_path=compatibility,
    )
    assert projected["editorial"] == render_spec["editorial"]
    assert projected["publishing"] == render_spec["publishing"]
    assert projected["review"] == render_spec["review"]


def test_unknown_mode_remains_fail_closed():
    try:
        visual_intelligence_renderer_projection._require_known_mode(
            "future-unreviewed-mode", path="$.scenes[0].visualMode"
        )
    except visual_intelligence_renderer_projection.VisualIntelligenceRendererProjectionError as exc:
        assert "E_VISUAL_MODE_UNMAPPED" in str(exc)
    else:
        raise AssertionError("unknown visualMode did not fail closed")
