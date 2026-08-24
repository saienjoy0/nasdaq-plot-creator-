#!/usr/bin/env python3
"""Lock v1.2 reuse of the canonical Expected/Actual/Gap object projection."""
from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import visual_intelligence_renderer_projection as projection  # noqa: E402
from test_visual_intelligence_renderer_projection import scene, write  # noqa: E402


def main() -> int:
    date = "2099-05-06"
    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-gap-") as temp:
        root = Path(temp)
        write(root / "working" / date / "final_episode_contract.json", {"contractVersion": "1.1.0"})
        write(root / "contracts" / "visual_grammar_semantics.json", {"contractVersion": "1.0.0"})
        write(root / "contracts" / "visual_grammar_renderer_compatibility.json", {"contractVersion": "1.0.0"})

        scenes = [scene(number, "verification", ["verification", "verification"]) for number in range(1, 10)]
        s4 = scenes[3]
        first = s4["visualBeats"][0]
        second = s4["visualBeats"][1]
        first.update({
            "visualMode": "expectation-gap",
            "visualTemplate": "expected-actual-gap-flow",
            "visualGrammar": {
                "contractVersion": "1.0.0",
                "grammarId": "gap",
                "transitionRole": "major-shift",
            },
            "templateConfig": {
                "variant": "left-to-right",
                "comparisonBasis": None,
                "dataBasis": "synthetic",
                "nodeOrder": [],
                "laneLabels": [],
                "outcomeNodeId": None,
            },
            "screenQuestion": "何が外れた？",
            "primaryElement": "予想 / 実際 / 差分",
            "viewerTexts": [
                "予想：緊張緩和・再開",
                "実際：閉鎖条件・Brent +1.4%",
                "差分：安心材料が来ない",
            ],
            "objectIds": ["scene-04-card-001"],
        })
        second["objectIds"] = ["scene-04-card-002"]
        s4["cards"] = [
            {
                "cardId": "scene-04-card-001",
                "role": None,
                "title": "予想 / 実際 / 差分",
                "lines": [
                    {"label": "1", "value": "予想：緊張緩和・再開", "tone": "neutral"},
                    {"label": "2", "value": "実際：閉鎖条件・Brent +1.4%", "tone": "neutral"},
                    {"label": "3", "value": "差分：安心材料が来ない", "tone": "neutral"},
                ],
            },
            {
                "cardId": "scene-04-card-002",
                "role": None,
                "title": "根拠",
                "lines": [{"label": "1", "value": "主要報道に基づく期待", "tone": "neutral"}],
            },
        ]
        s4["visualEvents"] = [
            {
                "eventId": "event-007",
                "atChunkId": "scene-04-chunk-001",
                "action": "show",
                "targetId": "scene-04-card-001",
                "timing": "chunk-start",
                "offsetMs": 0,
                "durationMs": 420,
                "motionPreset": "rise-soft",
                "easingPreset": "smooth-out",
                "expression": None,
            },
            {
                "eventId": "event-008",
                "atChunkId": "scene-04-chunk-001",
                "action": "show",
                "targetId": "scene-04-card-002",
                "timing": "chunk-start",
                "offsetMs": 0,
                "durationMs": 420,
                "motionPreset": "rise-soft",
                "easingPreset": "smooth-out",
                "expression": None,
            },
        ]
        render = {
            "schemaVersion": "2.4.0",
            "episode": {"targetDate": date},
            "scenes": scenes,
        }
        before = copy.deepcopy(render)
        strict = projection.project_visual_intelligence_renderer_input(render, repo_root=root, date=date)
        if render != before:
            raise AssertionError("producer render mutated")
        projected_scene = strict["scenes"][3]
        projected_first = projected_scene["visualBeats"][0]
        roles = [card.get("role") for card in projected_scene["cards"][:3]]
        if roles != ["expected", "actual", "gap"]:
            raise AssertionError(f"gap roles not materialized from authored expectation-gap alias: {roles}")
        if projected_first["objectIds"] != [
            "scene-04-card-expected", "scene-04-card-actual", "scene-04-card-gap"
        ]:
            raise AssertionError(projected_first["objectIds"])
        if projected_scene["visualBeats"][1]["objectIds"] != ["scene-04-card-002"]:
            raise AssertionError("later Beat source card was not preserved")
        if projected_first["viewerTexts"] != first["viewerTexts"]:
            raise AssertionError("Expected/Actual/Gap viewer text changed")
        targets = [event["targetId"] for event in projected_scene["visualEvents"]]
        for target in ("scene-04-card-expected", "scene-04-card-actual", "scene-04-card-gap", "scene-04-card-002"):
            if target not in targets:
                raise AssertionError(f"missing rewritten show event target: {target}")

    print("visual intelligence Expected/Actual/Gap projection test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
