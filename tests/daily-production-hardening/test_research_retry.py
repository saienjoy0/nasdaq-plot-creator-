from __future__ import annotations

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


hardened = load_module(
    "daily_hardened_retry_test",
    ROOT / "scripts/run_daily_production_hardened.py",
)
retry_module = load_module(
    "research_retry_test",
    ROOT / "scripts/restart_causal_research.py",
)


class ResearchRetryTests(unittest.TestCase):
    date = "2026-08-06"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.daily = hardened.load_hardened_daily_module()
        self.source = self.workspace / f"daily_source_package_{self.date}.md"
        self.source.write_text("source", encoding="utf-8")
        self.daily.init_request(
            workspace=self.workspace,
            date=self.date,
            daily_source=self.source,
            requested_scope="preview",
            renderer_commit="a" * 40,
            renderer_contract_version="2.4.0",
        )
        evidence = self.workspace / "research.json"
        evidence.write_text("{}\n", encoding="utf-8")
        self.daily.add_transition(
            workspace=self.workspace,
            date=self.date,
            new_state="research_inputs_bound",
            evidence_paths=[evidence],
        )
        self.daily.add_transition(
            workspace=self.workspace,
            date=self.date,
            new_state="causal_dossier_valid",
            evidence_paths=[evidence],
        )

    def tearDown(self):
        self.temp.cleanup()

    def review_document(self, *, issue_type: str | None = None, factual: str | None = None):
        scene_checks = []
        for number in range(1, 9):
            scene_checks.append(
                {
                    "scene_id": f"scene-{number:02d}",
                    "mode": "close" if number == 8 else "continue",
                    "payoff_delivered": True,
                    "belief_changed": True,
                    "continuation_reason_natural": None if number == 8 else True,
                    "closure_effective": True if number == 8 else None,
                    "opening_promise_recovered": True if number == 8 else None,
                    "procedural_language_dominant": False,
                }
            )
        findings = []
        if issue_type:
            findings.append(
                {
                    "finding_id": "finding-01",
                    "severity": "critical",
                    "issue_type": issue_type,
                    "scene_ids": ["scene-05"],
                    "problem": "meaning defect",
                    "viewer_impact": "wrong conclusion",
                    "minimal_fix": "return to causal research",
                }
            )
        return {
            "contract_version": "1.1.0",
            "episode_date": self.date,
            "reviewer": "editorial_critic",
            "round": 1,
            "scores": {
                "opening": 4,
                "progression": 4,
                "discovery": 4,
                "clarity": 4,
                "fox_voice": 4,
                "late_payoff": 4,
            },
            "total_score": 24,
            "scene_checks": scene_checks,
            "immediate_failures": [factual] if factual else [],
            "findings": findings,
            "verdict": "fail",
        }

    def write_retry(self, *, reason: str, issue_type: str | None = None, factual: str | None = None):
        review_path = self.workspace / "working" / self.date / "story-engine" / "creative_review.json"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(
            json.dumps(self.review_document(issue_type=issue_type, factual=factual), ensure_ascii=False),
            encoding="utf-8",
        )
        request = {
            "contract_version": "1.0.0",
            "episode_date": self.date,
            "requested_action": "restart_causal_research",
            "reason_type": reason,
            "creative_review": {
                "path": review_path.relative_to(self.workspace).as_posix(),
                "sha256": self.daily.sha256_file(review_path),
            },
            "finding_ids": ["finding-01"] if issue_type else [],
            "immediate_failure_texts": [factual] if factual else [],
        }
        request_path = self.workspace / "working" / self.date / "research_retry_request.json"
        request_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
        return request_path

    def restart(self, request_path: Path):
        return retry_module.restart(
            daily_module=self.daily,
            workspace=self.workspace,
            date=self.date,
            retry_request_path=request_path,
            retry_schema_path=ROOT / "skills/nasdaq-cafe-daily-production/contracts/research_retry_request.schema.json",
            creative_review_schema_path=ROOT / "skills/nasdaq-cafe-entertainment-critic/contracts/creative_review.schema.json",
        )

    def test_critical_causality_finding_supersedes_without_state_regression(self):
        request = self.write_retry(
            reason="CAUSALITY_DRIFT",
            issue_type="CAUSALITY_DRIFT",
        )
        result = self.restart(request)
        self.assertEqual("restarted", result["status"])
        self.assertEqual("causal_dossier_valid", result["previous_state"])
        self.assertEqual("intake_ready", result["current_state"])

        active = self.daily.load_json(
            self.daily.state_path(self.workspace, self.date), "active state"
        )
        self.assertFalse(active["invalidated"])
        self.assertEqual("intake_ready", active["current_state"])
        receipt_refs = [
            item["path"]
            for item in active["transitions"][0]["evidence"]
            if item["path"].endswith("research_retry_receipt.json")
        ]
        self.assertEqual(1, len(receipt_refs))

        archive = self.workspace / result["archive"]
        invalidated = json.loads(
            (archive / "invalidated_production_state.json").read_text(encoding="utf-8")
        )
        self.assertTrue(invalidated["invalidated"])
        self.assertEqual("causal_dossier_valid", invalidated["current_state"])
        self.assertTrue((archive / "superseded_production_request.json").is_file())
        self.assertTrue((archive / "creative_review.json").is_file())

    def test_clarity_finding_cannot_be_relabelled_as_causality_retry(self):
        request = self.write_retry(
            reason="CAUSALITY_DRIFT",
            issue_type="CLARITY_OVERLOAD",
        )
        with self.assertRaises(retry_module.ResearchRetryError):
            self.restart(request)
        status = self.daily.status(workspace=self.workspace, date=self.date)
        self.assertEqual("pass", status["validation"]["status"])
        self.assertEqual("causal_dossier_valid", status["current_state"])

    def test_factual_error_requires_exact_immediate_failure(self):
        request = self.write_retry(
            reason="FACTUAL_ERROR",
            factual="BLS release time is wrong",
        )
        result = self.restart(request)
        self.assertEqual("FACTUAL_ERROR", result["reason_type"])
        self.assertEqual("intake_ready", result["current_state"])

    def test_retry_is_forbidden_after_public_episode_finalization(self):
        request = self.write_retry(
            reason="TIMELINE_DRIFT",
            issue_type="TIMELINE_DRIFT",
        )
        state_path = self.daily.state_path(self.workspace, self.date)
        state = self.daily.load_json(state_path, "state")
        state["current_state"] = "episode_package_final"
        self.daily.write_atomic(state_path, state)
        with self.assertRaises(retry_module.ResearchRetryError):
            self.restart(request)

    def test_failed_reinitialization_leaves_old_attempt_invalidated(self):
        request = self.write_retry(
            reason="NASDAQ_SCOPE_OVERREACH",
            issue_type="NASDAQ_SCOPE_OVERREACH",
        )
        original_init = self.daily.init_request

        def fail_init(**kwargs):
            raise RuntimeError("synthetic init failure")

        self.daily.init_request = fail_init
        try:
            with self.assertRaises(RuntimeError):
                self.restart(request)
        finally:
            self.daily.init_request = original_init
        state = self.daily.load_json(
            self.daily.state_path(self.workspace, self.date), "restored invalidated state"
        )
        self.assertTrue(state["invalidated"])
        self.assertEqual(
            "fail",
            self.daily.status(workspace=self.workspace, date=self.date)["validation"]["status"],
        )


if __name__ == "__main__":
    unittest.main()
