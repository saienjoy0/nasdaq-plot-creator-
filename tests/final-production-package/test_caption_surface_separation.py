from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "scripts/build_final_production_package.py"
spec = importlib.util.spec_from_file_location("builder_caption_surface", SCRIPT)
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_public_narration_requires_speech_not_display_caption() -> None:
    render = {
        "publishing": {},
        "scenes": [{
            "sceneId": "scene-01",
            "headline": "",
            "supportingTexts": [],
            "narrationChunks": [{
                "speechText": "SOXXは二・〇二パーセント高でした。",
                "captionText": "SOXXは2.02%高でした。",
            }],
            "visualBeats": [],
        }],
    }
    values = builder.collect_public_strings(render)
    assert ("scene-01.narrationChunks[0].speechText", "SOXXは二・〇二パーセント高でした。") in values
    assert not any(label.endswith(".captionText") for label, _ in values)
    assert "SOXXは2.02%高でした。" not in [value for _, value in values]


def test_change_cue_is_machine_only_but_visible_beat_copy_remains_public() -> None:
    render = {
        "publishing": {},
        "scenes": [{
            "sceneId": "scene-06",
            "headline": "",
            "supportingTexts": [],
            "narrationChunks": [],
            "visualBeats": [{
                "narrationStartCue": "半導体では、その増幅が特にはっきり見えます。",
                "narrationEndCue": "会社は需要改善や在庫正常化も説明しています。",
                "screenQuestion": "Microchipは何を発表した？",
                "primaryElement": "Microchip Q1 FY27 公式IR",
                "changeCue": "Microchip Q1 FY27公式IR",
                "viewerTexts": ["売上 14.85億ドル / 非GAAP EPS 0.76ドル"],
            }],
        }],
    }
    values = builder.collect_public_strings(render)
    labels = {label for label, _ in values}
    assert "scene-06.visualBeats[0].changeCue" not in labels
    assert "scene-06.visualBeats[0].screenQuestion" in labels
    assert "scene-06.visualBeats[0].primaryElement" in labels
    assert "scene-06.visualBeats[0].viewerTexts[0]" in labels
