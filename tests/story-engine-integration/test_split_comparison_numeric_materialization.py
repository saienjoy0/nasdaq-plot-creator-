from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import remotion_template_data  # noqa: E402
import visual_intelligence_renderer_projection as vi_projection  # noqa: E402


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


def test_vi_projection_materializes_split_comparison_from_approved_card():
    source_card = "scene-03-card-001"
    scene = {
        "sceneId": "scene-03",
        "cards": [
            {
                "cardId": source_card,
                "title": "半導体の分裂",
                "role": None,
                "lines": [
                    {"label": "1", "tone": "negative", "value": "AMAT -5.12%"},
                    {"label": "2", "tone": "negative", "value": "AVGO -5.94%"},
                    {"label": "3", "tone": "positive", "value": "AMD +6.50%"},
                ],
            }
        ],
        "numbers": [],
        "nodes": [],
        "arrows": [],
        "visualEvents": [
            {
                "eventId": "event-001",
                "atChunkId": "scene-03-chunk-001",
                "timing": "chunk-start",
                "action": "show",
                "targetId": source_card,
                "offsetMs": 0,
                "expression": None,
                "motionPreset": "rise-soft",
                "durationMs": 420,
                "easingPreset": "smooth-out",
            }
        ],
        "visualBeats": [
            {
                "beatId": "scene-03-beat-001",
                "visualTemplate": "split-comparison",
                "visualMode": "number-comparison",
                "contentType": "split-comparison",
                "visualGrammarId": "comparison",
                "viewerTexts": ["AMAT -5.12%", "AVGO -5.94%", "AMD +6.50%"],
                "objectIds": [source_card],
                "templateConfig": {
                    "variant": "two-lane",
                    "comparisonBasis": "2026-08-14 US regular session close",
                    "dataBasis": "2026-08-14 US regular session close",
                    "nodeOrder": [],
                    "laneLabels": [],
                    "outcomeNodeId": None,
                },
            }
        ],
    }

    projected = vi_projection._materialize_vnext_object_inventory({"scenes": [scene]})
    projected_scene = projected["scenes"][0]
    projected_beat = projected_scene["visualBeats"][0]
    number_map = {item["numberId"]: item for item in projected_scene["numbers"]}
    selected = [number_map[item] for item in projected_beat["objectIds"]]

    assert [item["numericValue"] for item in selected] == [-5.12, -5.94, 6.5]
    assert {item["unit"] for item in selected} == {"%"}
    assert {item["comparison"] for item in selected} == {"2026-08-14 US regular session close"}
    assert [event["targetId"] for event in projected_scene["visualEvents"]] == projected_beat["objectIds"]
    assert projected_beat["viewerTexts"] == ["AMAT -5.12%", "AVGO -5.94%", "AMD +6.50%"]
