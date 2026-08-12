from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import fixup_chatgpt_daily_materialization as fixup  # noqa: E402
import materialize_chatgpt_daily_authoring as materializer  # noqa: E402
import validate_chatgpt_daily_authoring_closure as closure  # noqa: E402


class ProductionClosureTests(unittest.TestCase):
    def test_duration_mode_is_author_owned_and_reason_is_mode_consistent(self) -> None:
        self.assertEqual([], closure.validate_duration_ownership({
            "durationMode": "standard",
            "shortenedReason": None,
        }))
        self.assertEqual([], closure.validate_duration_ownership({
            "durationMode": "shortened",
            "shortenedReason": "Evidence set supports only a concise episode.",
        }))
        self.assertTrue(closure.validate_duration_ownership({
            "durationMode": "standard",
            "shortenedReason": "should not exist",
        }))
        self.assertTrue(closure.validate_duration_ownership({
            "durationMode": "shortened",
            "shortenedReason": None,
        }))

    def test_multi_object_visual_events_must_explicitly_cover_first_visibility(self) -> None:
        beat = {
            "visualEvents": [
                {
                    "action": "show",
                    "targetId": "number-a",
                    "offsetMs": 0,
                    "timing": "chunk-start",
                }
            ]
        }
        with self.assertRaisesRegex(SystemExit, "first visibility for every object"):
            materializer._project_authored_visual_events(
                beat,
                bid="scene-06-beat-001",
                cid="scene-06-chunk-001",
                object_ids=["number-a", "number-b"],
                event_serial=[0],
            )

    def test_explicit_multi_object_reveal_order_is_projected_without_inference(self) -> None:
        beat = {
            "visualEvents": [
                {
                    "action": "show",
                    "targetId": "number-a",
                    "offsetMs": 0,
                    "timing": "chunk-start",
                    "motionPreset": "rise-soft",
                    "durationMs": 420,
                    "easingPreset": "smooth-out",
                },
                {
                    "action": "show",
                    "targetId": "number-b",
                    "offsetMs": 5000,
                    "timing": "chunk-start",
                    "motionPreset": "rise-soft",
                    "durationMs": 420,
                    "easingPreset": "smooth-out",
                },
            ]
        }
        events = materializer._project_authored_visual_events(
            beat,
            bid="scene-07-beat-002",
            cid="scene-07-chunk-002",
            object_ids=["number-a", "number-b"],
            event_serial=[0],
        )
        self.assertEqual(["number-a", "number-b"], [row["targetId"] for row in events])
        self.assertEqual([0, 5000], [row["offsetMs"] for row in events])
        self.assertEqual(["event-001", "event-002"], [row["eventId"] for row in events])

    def test_legacy_show_completion_adds_nothing_to_fully_authored_production_beat(self) -> None:
        render = {
            "scenes": [
                {
                    "sceneId": "scene-06",
                    "narrationChunks": [
                        {"chunkId": "scene-06-chunk-001"},
                    ],
                    "visualBeats": [
                        {
                            "beatId": "scene-06-beat-001",
                            "startChunkId": "scene-06-chunk-001",
                            "endChunkId": "scene-06-chunk-001",
                            "objectIds": ["number-a", "number-b"],
                        }
                    ],
                    "visualEvents": [
                        {
                            "eventId": "event-001",
                            "atChunkId": "scene-06-chunk-001",
                            "timing": "chunk-start",
                            "action": "show",
                            "targetId": "number-a",
                            "offsetMs": 0,
                        },
                        {
                            "eventId": "event-002",
                            "atChunkId": "scene-06-chunk-001",
                            "timing": "chunk-start",
                            "action": "show",
                            "targetId": "number-b",
                            "offsetMs": 5000,
                        },
                    ],
                }
            ]
        }
        before = list(render["scenes"][0]["visualEvents"])
        self.assertEqual(0, fixup.complete_show_sequences(render))
        self.assertEqual(before, render["scenes"][0]["visualEvents"])

    def test_shots_use_existing_renderer_relative_progress_contract(self) -> None:
        shots = materializer._validate_authored_shots(
            {
                "shots": [
                    {
                        "shotId": "scene-05-beat-001-shot-001",
                        "shotRecipe": {"type": "hold"},
                        "startChunkId": "scene-05-chunk-001",
                        "startProgress": 0,
                        "startOffsetMs": 0,
                        "endChunkId": "scene-05-chunk-001",
                        "endProgress": 0.5,
                        "endOffsetMs": 0,
                        "endCue": "a",
                        "primaryTargetId": "node-a",
                        "continuityKey": None,
                        "stageLayout": {"id": "default"},
                        "cameraPreset": {"id": "static"},
                        "transitionIn": {"type": "cut"},
                        "transitionOut": {"type": "cut"},
                        "typographyTreatment": None,
                        "typographyText": None,
                        "soundCue": None,
                        "foxExpression": "分析",
                    },
                    {
                        "shotId": "scene-05-beat-001-shot-002",
                        "shotRecipe": {"type": "hold"},
                        "startChunkId": "scene-05-chunk-001",
                        "startProgress": 0.5,
                        "startOffsetMs": 0,
                        "endChunkId": "scene-05-chunk-001",
                        "endProgress": 1,
                        "endOffsetMs": 0,
                        "endCue": "b",
                        "primaryTargetId": "node-b",
                        "continuityKey": None,
                        "stageLayout": {"id": "default"},
                        "cameraPreset": {"id": "static"},
                        "transitionIn": {"type": "cut"},
                        "transitionOut": {"type": "cut"},
                        "typographyTreatment": None,
                        "typographyText": None,
                        "soundCue": None,
                        "foxExpression": "分析",
                    },
                ]
            },
            bid="scene-05-beat-001",
            cid="scene-05-chunk-001",
            object_ids=["node-a", "node-b"],
        )
        self.assertEqual(2, len(shots))
        self.assertEqual(0, shots[0]["startProgress"])
        self.assertEqual(1, shots[-1]["endProgress"])


if __name__ == "__main__":
    unittest.main()
