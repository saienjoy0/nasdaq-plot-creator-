from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StoryEngineDailyStateTests(unittest.TestCase):
    def test_hardened_daily_inserts_story_states_in_order(self):
        hardened = load_module("daily_hardened_integration", ROOT / "scripts/run_daily_production_hardened.py")
        daily = hardened.load_hardened_daily_module()
        states = daily.STATES
        chain = [
            "causal_dossier_valid",
            "story_plan_valid",
            "script_draft_ready",
            "creative_review_passed",
            "episode_package_final",
        ]
        positions = [states.index(value) for value in chain]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(positions, list(range(positions[0], positions[0] + len(chain))))

    def test_story_transition_requires_hash_bound_acceptance(self):
        hardened = load_module("daily_hardened_acceptance", ROOT / "scripts/run_daily_production_hardened.py")
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
            daily.add_transition(workspace=root, date=date, new_state="research_inputs_bound", evidence_paths=[evidence])
            daily.add_transition(workspace=root, date=date, new_state="causal_dossier_valid", evidence_paths=[evidence])

            story_dir = root / "working" / date / "story-engine"
            story_dir.mkdir(parents=True, exist_ok=True)
            plan = story_dir / "story_plan.json"
            plan.write_text("{}", encoding="utf-8")
            acceptance = story_dir / "story_engine_acceptance.json"
            acceptance.write_text(json.dumps({
                "episode_date": date,
                "status": "pass",
                "artifacts": {"story_plan": {"path": plan.relative_to(root).as_posix(), "sha256": sha(plan)}},
                "critic": {"verdict": "pass", "score": 27},
            }), encoding="utf-8")

            with self.assertRaises(daily.DailyProductionError):
                daily.add_transition(workspace=root, date=date, new_state="story_plan_valid", evidence_paths=[plan])
            result = daily.add_transition(
                workspace=root,
                date=date,
                new_state="story_plan_valid",
                evidence_paths=[plan, acceptance],
            )
            self.assertEqual("story_plan_valid", result["current_state"])


class ProjectionTests(unittest.TestCase):
    def test_sentence_segmentation_preserves_exact_text(self):
        projection = load_module("story_projection", ROOT / "scripts/story-engine/project_story_script_to_production.py")
        text = "一文目です。二文目です。三文目です。"
        parts = projection.segment(text, 2)
        self.assertEqual(text, "".join(parts))
        self.assertEqual(2, len(parts))

    def test_explicit_visual_override_updates_only_declared_fields(self):
        projection = load_module("story_projection_override", ROOT / "scripts/story-engine/project_story_script_to_production.py")
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


if __name__ == "__main__":
    unittest.main()
