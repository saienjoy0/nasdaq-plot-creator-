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
