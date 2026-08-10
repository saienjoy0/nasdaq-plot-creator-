from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import remotion_template_data  # noqa: E402


def test_mixed_metric_conversion_reuses_numbers_and_existing_numeric_labels():
    scene = {
        "sceneId": "scene-02",
        "cards": [
            {
                "cardId": "scene-02-card-002",
                "title": "好決算と株価下落",
                "role": None,
                "lines": [
                    {"label": "1", "tone": "neutral", "value": "Q2売上 115.4億ドル"},
                    {"label": "2", "tone": "neutral", "value": "AMD -7.04%"},
                ],
            }
        ],
        "numbers": [],
        "visualBeats": [
            {
                "beatId": "vb-02-02",
                "visualTemplate": "diverging-stock-bars",
                "visualMode": "number-comparison",
                "contentType": "diverging-stock-bars",
                "visualGrammarId": "comparison",
                "viewerTexts": ["Q2売上 115.4億ドル", "AMD -7.04%"],
                "objectIds": ["scene-02-card-002"],
                "templateConfig": {"variant": "default", "laneLabels": []},
            }
        ],
    }
    beat = scene["visualBeats"][0]
    remotion_template_data._materialize_numeric_template(scene, beat)

    numbers = {item["numberId"]: item for item in scene["numbers"]}
    selected = [numbers[item] for item in beat["objectIds"]]
    assert len(selected) == 2
    assert selected[0]["numericValue"] == 115.4
    assert selected[0]["unit"] == "億ドル"
    assert selected[1]["numericValue"] == -7.04
    assert selected[1]["unit"] == "%"
    assert beat["visualTemplate"] == "tailwind-headwind"
    assert beat["templateVariant"] == "two-lane"
    assert beat["visualGrammarId"] == "evidence"
    assert beat["templateConfig"]["laneLabels"] == ["Q2売上", "AMD"]
    assert beat["viewerTexts"] == ["Q2売上｜115.4億ドル", "AMD｜-7.04%"]


def test_explicit_two_lane_story_binding_infers_renderer_lane_labels():
    beat = {
        "beatId": "scene-01-beat-002",
        "visualTemplate": "tailwind-headwind",
        "contentType": "tailwind-headwind",
        "templateVariant": "two-lane",
        "viewerTexts": ["数字｜良かった", "株価｜AMD -7.04%"],
        "templateConfig": {"variant": "two-lane", "laneLabels": []},
    }

    remotion_template_data._normalize_tailwind_headwind_template(beat)

    assert beat["templateConfig"]["laneLabels"] == ["数字", "株価"]
    assert beat["templateConfig"]["variant"] == "two-lane"
    assert beat["templateVariant"] == "two-lane"
    assert beat["viewerTexts"] == ["数字｜良かった", "株価｜AMD -7.04%"]
