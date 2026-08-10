from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORY_ENGINE_DIR = ROOT / "scripts/story-engine"
if str(STORY_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(STORY_ENGINE_DIR))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class StoryEngineDailyStateTests(unittest.TestCase):
    def test_hardened_daily_keeps_story_passes_internal(self):
        hardened = load_module(
            "daily_hardened_integration",
            ROOT / "scripts/run_daily_production_hardened.py",
        )
        daily = hardened.load_hardened_daily_module()
        states = daily.STATES
        for internal in ("story_plan_valid", "script_draft_ready", "creative_review_passed"):
            self.assertNotIn(internal, states)
        causal = states.index("causal_dossier_valid")
        final = states.index("episode_package_final")
        self.assertEqual(causal + 1, final)

    def test_episode_package_final_requires_story_acceptance_package_and_projection(self):
        hardened = load_module(
            "daily_hardened_acceptance",
            ROOT / "scripts/run_daily_production_hardened.py",
        )
        daily = hardened.load_hardened_daily_module()
        date = "2026-08-06"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            daily_source = root / f"daily_source_package_{date}.md"
            daily_source.write_text("source", encoding="utf-8")
            daily.init_request(
                workspace=root,
                date=date,
                daily_source=daily_source,
                requested_scope="preview",
                renderer_commit="a" * 40,
                renderer_contract_version="2.4.0",
            )
            evidence = root / "evidence.json"
            evidence.write_text("{}", encoding="utf-8")
            daily.add_transition(
                workspace=root,
                date=date,
                new_state="research_inputs_bound",
                evidence_paths=[evidence],
            )
            daily.add_transition(
                workspace=root,
                date=date,
                new_state="causal_dossier_valid",
                evidence_paths=[evidence],
            )

            package = root / "episodes" / date / f"episode_package_{date}.md"
            package.parent.mkdir(parents=True)
            package.write_text("package", encoding="utf-8")
            with self.assertRaises(daily.DailyProductionError):
                daily.add_transition(
                    workspace=root,
                    date=date,
                    new_state="episode_package_final",
                    evidence_paths=[package],
                )

            with self.assertRaises(daily.DailyProductionError):
                daily.add_transition(
                    workspace=root,
                    date=date,
                    new_state="story_plan_valid",
                    evidence_paths=[evidence],
                )


class ProjectionTests(unittest.TestCase):
    def test_sentence_segmentation_preserves_exact_text(self):
        projection = load_module(
            "story_projection",
            ROOT / "scripts/story-engine/project_story_script_to_production.py",
        )
        text = "一文目です。二文目です。三文目です。"
        parts = projection.segment(text, 2)
        self.assertEqual(text, "".join(parts))
        self.assertEqual(2, len(parts))

    def test_explicit_visual_override_updates_only_declared_fields(self):
        projection = load_module(
            "story_projection_override",
            ROOT / "scripts/story-engine/project_story_script_to_production.py",
        )
        render = {"scenes": [{
            "sceneId": "scene-01",
            "headline": "old",
            "supportingTexts": [],
            "visualBeats": [{
                "beatId": "scene-01-beat-001",
                "screenQuestion": "old",
                "primaryElement": "old",
                "viewerTexts": ["old"],
                "changeCue": "old",
                "contentType": "verification-checklist",
                "visualTemplate": "verification-checklist",
                "visualMode": "verification",
                "screenState": "Data",
                "templateConfig": {"variant": "default"},
                "visualGrammar": {
                    "contractVersion": "1.0.0",
                    "grammarId": "verification",
                    "transitionRole": "continuation",
                    "returnTargetBeatId": None,
                },
            }],
        }]}
        binding = {
            "scene_overrides": {"scene-01": {"headline": "new"}},
            "beat_overrides": {"scene-01-beat-001": {
                "screenQuestion": "question",
                "viewerTexts": ["A", "B"],
                "visualTemplate": "evidence-boundary",
                "templateVariant": "confirmed-vs-unconfirmed",
                "contentType": "evidence-boundary",
                "visualGrammarId": "evidence",
            }},
        }
        projection.apply_visual_overrides(render, binding)
        self.assertEqual("new", render["scenes"][0]["headline"])
        beat = render["scenes"][0]["visualBeats"][0]
        self.assertEqual("question", beat["screenQuestion"])
        self.assertEqual(["A", "B"], beat["viewerTexts"])
        self.assertEqual("old", beat["primaryElement"])
        self.assertEqual("evidence-boundary", beat["visualTemplate"])
        self.assertEqual("evidence-boundary", beat["contentType"])
        self.assertEqual("confirmed-vs-unconfirmed", beat["templateConfig"]["variant"])
        self.assertEqual("evidence", beat["visualGrammar"]["grammarId"])
        self.assertEqual("continuation", beat["visualGrammar"]["transitionRole"])
        self.assertEqual("verification", beat["visualMode"])

    def test_scene_07_close_only_reaction_binding_is_injected_at_story_projection(self):
        auxiliary = load_module(
            "story_auxiliary_bindings_test",
            ROOT / "scripts/story-engine/apply_story_auxiliary_bindings.py",
        )
        story_path = ROOT / "working/2026-08-06/story-engine/story_production_bindings.json"
        base_path = ROOT / "working/2026-08-06/reaction_timeline_bindings.json"
        base = json.loads(base_path.read_text(encoding="utf-8"))
        self.assertEqual(["vb-06-01"], [row["visualBeatId"] for row in base["bindings"]])

        with tempfile.TemporaryDirectory() as temp:
            reaction_path = Path(temp) / "reaction_timeline_bindings.json"
            reaction_path.write_text(
                json.dumps(base, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            result = auxiliary.apply_story_reaction_bindings(story_path, reaction_path)
            self.assertEqual("pass", result["status"])
            self.assertEqual(["vb-07-01"], result["inserted_reaction_bindings"])
            document = json.loads(reaction_path.read_text(encoding="utf-8"))
            rows = {row["visualBeatId"]: row for row in document["bindings"]}
            row = rows["vb-07-01"]
            self.assertEqual("event-reaction-timeline", row["visualTemplate"])
            self.assertEqual("close-only", row["templateVariant"])
            self.assertEqual("close-only", row["precision"])
            self.assertEqual(["scene-07-card-001"], row["eventOrderIds"])
            self.assertEqual([], row["seriesObjectIds"])
            self.assertIn("分足", row["evidenceBasis"])


if __name__ == "__main__":
    unittest.main()
