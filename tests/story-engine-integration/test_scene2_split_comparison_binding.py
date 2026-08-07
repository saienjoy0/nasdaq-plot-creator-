import json
from pathlib import Path


def test_scene2_earnings_price_beat_uses_numeric_split_comparison():
    root = Path(__file__).resolve().parents[2]
    binding_path = root / "working/2026-08-06/story-engine/story_production_bindings.json"
    binding = json.loads(binding_path.read_text(encoding="utf-8"))

    beat = binding["beat_overrides"]["scene-02-beat-002"]
    assert beat["visualTemplate"] == "split-comparison"
    assert beat["templateVariant"] == "two-lane"
    assert beat["contentType"] == "split-comparison"
    assert beat["visualMode"] == "number-comparison"
    assert beat["visualGrammarId"] == "comparison"
