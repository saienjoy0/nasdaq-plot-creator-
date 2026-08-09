from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

OPENAI_AVAILABLE = importlib.util.find_spec("openai") is not None

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "critic-adapters/openai/main.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("openai_critic_adapter_test", ADAPTER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    status = "completed"

    def __init__(self, output_text: str):
        self.output_text = output_text


class FakeResponses:
    def __init__(self, review: dict):
        self.review = review
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse(json.dumps(self.review, ensure_ascii=False))


class FakeClient:
    def __init__(self, review: dict):
        self.responses = FakeResponses(review)


@unittest.skipUnless(
    OPENAI_AVAILABLE,
    "OpenAI Critic adapter checks run in the dedicated Story Engine v1.1 Gate CI",
)
class OpenAICriticAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter = load_adapter()

    def valid_review(self, date: str = "2026-08-06", round_no: int = 2) -> dict:
        checks = []
        for i in range(1, 8):
            checks.append({
                "scene_id": f"scene-{i:02d}",
                "mode": "continue",
                "payoff_delivered": True,
                "belief_changed": True,
                "continuation_reason_natural": True,
                "closure_effective": None,
                "opening_promise_recovered": None,
                "procedural_language_dominant": False,
            })
        checks.append({
            "scene_id": "scene-08",
            "mode": "close",
            "payoff_delivered": True,
            "belief_changed": True,
            "continuation_reason_natural": None,
            "closure_effective": True,
            "opening_promise_recovered": True,
            "procedural_language_dominant": False,
        })
        return {
            "contract_version": "1.1.0",
            "episode_date": date,
            "reviewer": "independent_critic",
            "round": round_no,
            "scores": {
                "opening": 4,
                "progression": 5,
                "discovery": 5,
                "clarity": 4,
                "fox_voice": 4,
                "late_payoff": 5,
            },
            "total_score": 27,
            "scene_checks": checks,
            "immediate_failures": [],
            "findings": [],
            "verdict": "pass",
        }

    def test_validate_review_rejects_score_mismatch(self):
        request = {"episode_date": "2026-08-06", "required_review": {"round": 2, "minimum_total_score": 25}}
        review = self.valid_review()
        review["total_score"] = 26
        with self.assertRaises(self.adapter.AdapterError):
            self.adapter.validate_review(review, request)

    def test_validate_review_rejects_scene_08_continuation_mode(self):
        request = {"episode_date": "2026-08-06", "required_review": {"round": 2, "minimum_total_score": 25}}
        review = self.valid_review()
        review["scene_checks"][7]["mode"] = "continue"
        review["scene_checks"][7]["continuation_reason_natural"] = True
        with self.assertRaises(self.adapter.AdapterError):
            self.adapter.validate_review(review, request)

    def test_validate_review_rejects_major_finding_on_pass(self):
        request = {"episode_date": "2026-08-06", "required_review": {"round": 2, "minimum_total_score": 25}}
        review = self.valid_review()
        review["findings"] = [{
            "finding_id": "finding-01",
            "severity": "major",
            "issue_type": "FAKE_OPEN_LOOP",
            "scene_ids": ["scene-04"],
            "problem": "答えを隠している。",
            "viewer_impact": "引き延ばしに見える。",
            "minimal_fix": "現在SceneでPayoffを渡す。",
        }]
        with self.assertRaises(self.adapter.AdapterError):
            self.adapter.validate_review(review, request)

    def test_render_bundle_reads_only_manifest_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "inputs").mkdir()
            (root / "logical_rules").mkdir()
            (root / "inputs/story.md").write_text("STORY", encoding="utf-8")
            (root / "logical_rules/04.md").write_text("RULE", encoding="utf-8")
            (root / "secret.txt").write_text("DO NOT READ", encoding="utf-8")
            manifest = {
                "inputs": [{"role": "draft_episode_package", "bundled_path": "inputs/story.md"}],
                "logical_rules": [{"logical_path": "source-of-truth/04_entertainment_inquisitor.md", "bundled_path": "logical_rules/04.md"}],
            }
            text = self.adapter.render_bundle(root, manifest)
            self.assertIn("STORY", text)
            self.assertIn("RULE", text)
            self.assertNotIn("DO NOT READ", text)

    def test_main_uses_structured_responses_without_tools(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_dir = root / "input"
            output_dir = root / "output"
            (input_dir / "inputs").mkdir(parents=True)
            (input_dir / "logical_rules").mkdir()
            output_dir.mkdir()
            (input_dir / "inputs/story.md").write_text("draft", encoding="utf-8")
            (input_dir / "logical_rules/04.md").write_text("critic rules", encoding="utf-8")

            request = {
                "contract_version": "1.0.0",
                "episode_date": "2026-08-06",
                "author_invocation_id": "author-1",
                "requested_critic_invocation_id": "critic-2",
                "instruction": "Review only frozen inputs.",
                "required_review": {
                    "round": 2,
                    "minimum_total_score": 25,
                    "required_verdict": "pass",
                    "critical_findings_allowed": 0,
                    "must_review_complete_episode_package": True,
                    "must_preserve_causality": True,
                },
            }
            manifest = {
                "episode_date": "2026-08-06",
                "critic_invocation_id": "critic-2",
                "inputs": [{"role": "draft_episode_package", "bundled_path": "inputs/story.md"}],
                "logical_rules": [{"logical_path": "source-of-truth/04_entertainment_inquisitor.md", "bundled_path": "logical_rules/04.md"}],
            }
            request_path = input_dir / "critic_request.json"
            manifest_path = input_dir / "bundle_manifest.json"
            review_path = output_dir / "creative_review.json"
            request_path.write_text(json.dumps(request), encoding="utf-8")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            fake = FakeClient(self.valid_review())
            original_client = self.adapter.OpenAI
            old_env = os.environ.copy()
            try:
                self.adapter.OpenAI = lambda timeout: fake
                os.environ.update({
                    "NASDAQ_CAFE_CRITIC_REQUEST": str(request_path),
                    "NASDAQ_CAFE_CRITIC_BUNDLE": str(manifest_path),
                    "NASDAQ_CAFE_CRITIC_REVIEW_OUT": str(review_path),
                    "OPENAI_API_KEY": "test-only",
                    "OPENAI_CRITIC_MODEL": "gpt-5.6",
                })
                self.assertEqual(0, self.adapter.main())
            finally:
                self.adapter.OpenAI = original_client
                os.environ.clear()
                os.environ.update(old_env)

            result = json.loads(review_path.read_text(encoding="utf-8"))
            self.assertEqual("1.1.0", result["contract_version"])
            self.assertEqual("pass", result["verdict"])
            self.assertEqual("close", result["scene_checks"][7]["mode"])
            self.assertEqual(1, len(fake.responses.calls))
            call = fake.responses.calls[0]
            self.assertEqual("gpt-5.6", call["model"])
            self.assertFalse(call["store"])
            self.assertNotIn("tools", call)
            self.assertEqual("json_schema", call["text"]["format"]["type"])
            self.assertTrue(call["text"]["format"]["strict"])


if __name__ == "__main__":
    unittest.main()
