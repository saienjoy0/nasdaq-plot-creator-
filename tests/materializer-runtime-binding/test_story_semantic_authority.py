from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "story-engine" / "project_story_script_to_production.py"
MATERIALIZER_PATH = REPO_ROOT / "scripts" / "materialize_daily_episode.py"

spec = importlib.util.spec_from_file_location("story_projection_identity", MODULE_PATH)
assert spec and spec.loader
story_projection = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = story_projection
spec.loader.exec_module(story_projection)


class StorySemanticAuthorityTests(unittest.TestCase):
    date = "2026-01-02"

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.story_dir = self.root / "working" / self.date / "story-engine"
        self.render_path = self.root / "render-specs" / self.date / "render_spec.json"
        self.public_path = self.root / "episodes" / self.date / f"episode_package_public_{self.date}.md"
        self.authoring_path = self.root / "daily-authoring" / f"{self.date}.json"
        self.script_path = self.story_dir / "story_script.json"
        self.plan_path = self.story_dir / "story_plan.json"
        self.review_path = self.story_dir / "creative_review.json"
        self.bindings_path = self.story_dir / "story_production_bindings.json"
        self.report_path = self.story_dir / "story_projection_report.json"
        for path in (
            self.story_dir,
            self.render_path.parent,
            self.public_path.parent,
            self.authoring_path.parent,
        ):
            path.mkdir(parents=True, exist_ok=True)
        self._write_fixture()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_json(self, path: Path, value: object) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _write_fixture(self) -> None:
        scenes = []
        plan_scenes = []
        script_scenes = []
        render_scenes = []
        md_blocks = []
        for index in range(1, 10):
            scene_id = f"scene-{index:02d}"
            connector = "closing" if index == 9 else "therefore"
            narration = f"僕のscene{index}。"
            scenes.append(
                {
                    "connector": connector,
                    "newEvidenceIds": [],
                    "newMeaning": f"meaning-{index}",
                    "continuationReason": "" if index == 9 else f"continue-{index}",
                    "causalClaims": [],
                    "chunks": [{"text": narration}],
                }
            )
            plan_scenes.append(
                {
                    "scene_id": scene_id,
                    "new_evidence_ids": [],
                    "new_meaning": f"meaning-{index}",
                    "continuation_reason": "" if index == 9 else f"continue-{index}",
                    "connector": connector,
                }
            )
            script_scenes.append(
                {
                    "scene_id": scene_id,
                    "narration": narration,
                    "connection_to_previous": connector,
                    "evidence_ids": [],
                    "causal_claims": [],
                }
            )
            chunk_id = f"{scene_id}-chunk-001"
            render_scenes.append(
                {
                    "sceneId": scene_id,
                    "narrationChunks": [{"chunkId": chunk_id, "speechText": narration}],
                    "visualBeats": [
                        {
                            "beatId": f"{scene_id}-beat-001",
                            "startChunkId": chunk_id,
                            "endChunkId": chunk_id,
                            "narrationStartCue": narration,
                            "narrationEndCue": narration,
                        }
                    ],
                }
            )
            md_blocks.append(
                f"## Scene {index}｜fixture\n\n"
                "### 完成ナレーション\n"
                f"{narration}\n"
                "- ナレーションで示す出典主体・媒体：fixture\n"
                "- 根拠と不確実性：fixture\n"
            )

        authoring = {
            "episodeDate": self.date,
            "centralContradiction": "contradiction",
            "headlineBeyondDiscovery": "discovery",
            "selectedAngleId": "angle-1",
            "centralQuestion": "question",
            "openingPromise": {"text": "promise"},
            "midpointTurn": {"scene": 5, "claim": "turn"},
            "closingReframe": {"text": "close"},
            "editorial": {"storySpine": "spine"},
            "retainedCounterevidenceIds": [],
            "unresolvedPoints": [],
            "scenes": scenes,
        }
        plan = {
            "episode_date": self.date,
            "central_contradiction": "contradiction",
            "headline_beyond_discovery": "discovery",
            "selected_angle_id": "angle-1",
            "central_question": "question",
            "story_spine": "spine",
            "opening_promise": {"text": "promise"},
            "midpoint_turn": {"scene": 5, "claim": "turn"},
            "closing_reframe": {"text": "close"},
            "scenes": plan_scenes,
        }
        script = {
            "episode_date": self.date,
            "scenes": script_scenes,
            "retained_counterevidence_ids": [],
            "unresolved_points": [],
        }
        render = {"episode": {"targetDate": self.date}, "scenes": render_scenes}
        review = {"episode_date": self.date, "verdict": "pass"}
        bindings = {
            "contract_version": "1.0.0",
            "episode_date": self.date,
            "scene_overrides": {},
            "beat_overrides": {},
        }
        self._write_json(self.authoring_path, authoring)
        self._write_json(self.plan_path, plan)
        self._write_json(self.script_path, script)
        self._write_json(self.render_path, render)
        self._write_json(self.review_path, review)
        self._write_json(self.bindings_path, bindings)
        self.public_path.write_text("\n".join(md_blocks), encoding="utf-8")

    def _validate(self) -> dict:
        return story_projection.validate_read_only(
            story_script_path=self.script_path,
            creative_review_path=self.review_path,
            render_spec_path=self.render_path,
            episode_package_public_path=self.public_path,
            bindings_path=self.bindings_path,
        )

    def test_read_only_identity_gate_preserves_production_inputs(self) -> None:
        render_before = self.render_path.read_bytes()
        public_before = self.public_path.read_bytes()
        result = self._validate()
        self.assertEqual("pass", result["status"])
        self.assertEqual("read-only-semantic-identity", result["mode"])
        self.assertEqual("chatgpt-daily-authoring", result["authority"])
        self.assertEqual("validation-only", result["story_engine_role"])
        self.assertFalse(result["semantic_writer"])
        self.assertEqual(render_before, self.render_path.read_bytes())
        self.assertEqual(public_before, self.public_path.read_bytes())
        self.assertEqual(result["before"], result["after"])

    def test_story_narration_drift_fails_closed(self) -> None:
        script = json.loads(self.script_path.read_text(encoding="utf-8"))
        script["scenes"][3]["narration"] = "僕ではなく別の意味。"
        self._write_json(self.script_path, script)
        with self.assertRaisesRegex(
            story_projection.StoryProjectionIdentityError,
            "E_STORY_SEMANTIC_DRIFT",
        ):
            self._validate()

    def test_story_plan_drift_fails_closed(self) -> None:
        plan = json.loads(self.plan_path.read_text(encoding="utf-8"))
        plan["story_spine"] = "machine changed spine"
        self._write_json(self.plan_path, plan)
        with self.assertRaisesRegex(
            story_projection.StoryProjectionIdentityError,
            "E_STORY_SEMANTIC_DRIFT",
        ):
            self._validate()

    def test_post_freeze_story_overrides_are_forbidden(self) -> None:
        bindings = json.loads(self.bindings_path.read_text(encoding="utf-8"))
        bindings["beat_overrides"] = {
            "scene-01-beat-001": {"viewerTexts": ["machine rewrite"]}
        }
        self._write_json(self.bindings_path, bindings)
        with self.assertRaisesRegex(
            story_projection.StoryProjectionIdentityError,
            "E_STORY_SEMANTIC_WRITER_FORBIDDEN",
        ):
            self._validate()

    def test_production_entry_has_no_story_writeback(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("apply_story_reaction_bindings", source)
        self.assertNotIn("args.render_spec.write_text", source)
        self.assertNotIn("args.episode_package_public.write_text", source)
        materializer = MATERIALIZER_PATH.read_text(encoding="utf-8")
        self.assertIn("scripts/story-engine/project_story_script_to_production.py", materializer)
        self.assertIn("story_projection_report.json", materializer)


if __name__ == "__main__":
    unittest.main()
