import json
from pathlib import Path


def test_scene2_earnings_price_beat_authors_two_tailwind_lanes():
    root = Path(__file__).resolve().parents[2]
    binding_path = root / "working/2026-08-06/story-engine/story_production_bindings.json"
    binding = json.loads(binding_path.read_text(encoding="utf-8"))

    beat = binding["beat_overrides"]["scene-02-beat-002"]
    assert beat["screenQuestion"] == "業績と株価は同じ方向だったか"
    assert beat["primaryElement"] == "好決算と株価下落"
    assert beat["viewerTexts"] == [
        "追い風｜Q2売上 115.4億ドル",
        "向かい風｜AMD -7.04%",
    ]
    assert "visualTemplate" not in beat
    assert "visualMode" not in beat
