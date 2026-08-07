from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import remotion_template_data  # noqa: E402


def test_split_comparison_reuses_existing_numeric_parser():
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
                "visualTemplate": "split-comparison",
                "visualMode": "number-comparison",
                "objectIds": ["scene-02-card-002"],
                "templateConfig": {"variant": "two-lane"},
            }
        ],
    }
    beat = scene["visualBeats"][0]
    remotion_template_data._materialize_numeric_template(scene, beat)

    numbers = {item["numberId"]: item for item in scene["numbers"]}
    selected = [numbers[item] for item in beat["objectIds"]]
    assert len(selected) == 2
    assert selected[0]["numericValue"] == 115.4
    assert selected[0]["precision"] == 1
    assert selected[0]["unit"] == "億ドル"
    assert selected[1]["numericValue"] == -7.04
    assert selected[1]["precision"] == 2
    assert selected[1]["unit"] == "%"
