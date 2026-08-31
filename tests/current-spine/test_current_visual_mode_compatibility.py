#!/usr/bin/env python3
"""Regression: reviewed authoring visual-mode aliases stay compatible with Current Renderer."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import renderer_strict_projection  # noqa: E402
import visual_intelligence_renderer_projection  # noqa: E402


def test_expectation_gap_is_reviewed_renderer_alias():
    assert renderer_strict_projection.VISUAL_MODE_MAP["expectation-gap"] == "expected-actual-gap"
    visual_intelligence_renderer_projection._require_known_mode(
        "expectation-gap", path="$.scenes[3].visualMode"
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
