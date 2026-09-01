from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import visual_intelligence_pipeline_v12 as pipeline  # noqa: E402


def _requirements() -> dict:
    return {
        "intent": {"beats": [{"visualBeatId": "scene-01-beat-001"}]},
        "provisionalDirection": {
            "requirements": [
                {
                    "visualBeatId": "scene-01-beat-001",
                    "requiredModes": ["comparison-set"],
                }
            ]
        },
    }


def test_renderer_requirements_satisfied_is_authoritative_even_when_capability_label_differs() -> None:
    catalog = {
        "candidates": [
            {
                "candidateId": "vc-1",
                "visualBeatId": "scene-01-beat-001",
                "capability": "text-only",
                "requirementsSatisfied": True,
            }
        ]
    }
    pipeline._validate_catalog_coverage(requirements=_requirements(), catalog=catalog)


def test_catalog_rejects_beat_when_no_renderer_candidate_satisfies_requirements() -> None:
    catalog = {
        "candidates": [
            {
                "candidateId": "vc-1",
                "visualBeatId": "scene-01-beat-001",
                "capability": "text-only",
                "requirementsSatisfied": False,
            }
        ]
    }
    with pytest.raises(pipeline.VisualIntelligenceStageError, match="E_VISUAL_REQUIRED_MODE_UNAVAILABLE"):
        pipeline._validate_catalog_coverage(requirements=_requirements(), catalog=catalog)
