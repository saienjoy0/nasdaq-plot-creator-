from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/story-engine/apply_story_auxiliary_bindings.py"
spec = importlib.util.spec_from_file_location("reaction_binding_prune_test", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_replaced_reaction_beat_prunes_only_its_old_binding(tmp_path: Path) -> None:
    story_path = tmp_path / "story.json"
    reaction_path = tmp_path / "reaction.json"
    story_path.write_text(json.dumps({
        "episode_date": "2026-08-10",
        "beat_overrides": {
            "scene-06-beat-001": {
                "visualTemplate": "news-media",
            },
            "scene-08-beat-001": {
                "visualTemplate": "event-reaction-timeline",
                "templateVariant": "verified-series",
                "reactionTimelineBinding": {
                    "visualBeatId": "vb-08-01",
                    "visualTemplate": "event-reaction-timeline",
                    "templateVariant": "verified-series",
                    "precision": "verified-intraday-series",
                    "eventOrderIds": ["qqq-0829", "qqq-0830", "qqq-0831"],
                    "seriesObjectIds": ["qqq-0829", "qqq-0830", "qqq-0831"],
                    "evidenceBasis": "verified QQQ minute closes",
                },
            },
        },
    }), encoding="utf-8")
    reaction_path.write_text(json.dumps({
        "contractVersion": "1.0.0",
        "episodeDate": "2026-08-10",
        "bindings": [
            {
                "visualBeatId": "vb-06-01",
                "visualTemplate": "event-reaction-timeline",
                "templateVariant": "official-time-plus-close",
                "precision": "official-time-plus-close",
                "eventOrderIds": ["scene-06-card-001"],
                "seriesObjectIds": [],
                "evidenceBasis": "old Scene 6 binding",
            },
            {
                "visualBeatId": "vb-07-01",
                "visualTemplate": "event-reaction-timeline",
                "templateVariant": "close-only",
                "precision": "close-only",
                "eventOrderIds": ["scene-07-card-001"],
                "seriesObjectIds": [],
                "evidenceBasis": "unrelated binding",
            },
        ],
    }), encoding="utf-8")

    result = module.apply_story_reaction_bindings(story_path, reaction_path)
    assert result["removed_reaction_bindings"] == ["vb-06-01"]
    assert result["inserted_reaction_bindings"] == ["vb-08-01"]
    document = json.loads(reaction_path.read_text(encoding="utf-8"))
    ids = [row["visualBeatId"] for row in document["bindings"]]
    assert ids == ["vb-07-01", "vb-08-01"]
