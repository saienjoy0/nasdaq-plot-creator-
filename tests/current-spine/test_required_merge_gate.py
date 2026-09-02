from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from required_merge_gate import (
    classify_changes,
    evaluate_latest_runs,
    load_policy,
    poll_expected_workflows,
    select_latest_runs,
)


POLICY = {
    "contractVersion": "1.0.0",
    "protectedBranch": "main",
    "statusContext": "Nasdaq Cafe Required Merge Gate",
    "docsOnlyPatterns": ["docs/**", "README.md", "CHANGELOG.md"],
    "requestOnlyGroups": [
        {
            "name": "final-authorization",
            "patterns": ["final-authorization-requests-v1/*.json"],
            "workflows": ["ChatGPT Daily Final Authorization"],
        }
    ],
    "workflowGroups": [
        {
            "name": "baseline",
            "patterns": ["scripts/**", "tests/**", "contracts/**", ".github/workflows/**", "skills/**", "AGENTS.md"],
            "workflows": ["Validate Daily Production Package"],
        },
        {
            "name": "daily-production",
            "patterns": ["daily-production-requests/**", "daily-authoring-parts/**", "daily-authoring/**", "daily-inputs/**", "working/**", "research/**", "episodes/**", "render-specs/**", "daily-assets/**"],
            "workflows": ["Validate Daily Production Package"],
        },
        {
            "name": "renderer-binding",
            "patterns": ["contracts/renderer_binding.json"],
            "workflows": [
                "Current Spine Exact Cross-Repo E2E",
                "Current Renderer Runtime Qualification Handoff",
                "Visual Intelligence v1.2",
            ],
        },
        {
            "name": "final-builders",
            "patterns": ["scripts/build_current_preview_request_v4.py", "scripts/build_current_final_request_v2.py"],
            "workflows": ["Current Preview Final Request Builders CI", "Current Renderer Runtime Qualification Handoff"],
        },
        {
            "name": "visual-intelligence",
            "patterns": ["scripts/visual_intelligence_v12.py", "scripts/visual-intelligence/**", "tests/visual-intelligence/**"],
            "workflows": ["Visual Intelligence v1.2"],
        },
    ],
    "unclassifiedNonDocs": "FAIL",
}


class RequiredMergeGateTests(unittest.TestCase):
    def test_load_policy_requires_expected_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "policy.json"
            path.write_text(json.dumps(POLICY), encoding="utf-8")
            self.assertEqual(load_policy(path)["contractVersion"], "1.0.0")

    def test_one_final_authorization_request_is_request_only(self) -> None:
        result = classify_changes(POLICY, [{"filename": "final-authorization-requests-v1/2026-09-02.json", "status": "added"}])
        self.assertEqual(result["state"], "REQUEST_ONLY")
        self.assertEqual(result["expectedWorkflows"], ["ChatGPT Daily Final Authorization"])

    def test_request_plus_second_file_fails_closed(self) -> None:
        result = classify_changes(POLICY, [
            {"filename": "final-authorization-requests-v1/2026-09-02.json", "status": "added"},
            {"filename": "README.md", "status": "modified"},
        ])
        self.assertEqual(result["state"], "MIXED_REQUEST_PR")

    def test_renderer_binding_collects_all_owners(self) -> None:
        result = classify_changes(POLICY, [{"filename": "contracts/renderer_binding.json", "status": "modified"}])
        self.assertEqual(result["state"], "WORKFLOWS_REQUIRED")
        self.assertEqual(
            set(result["expectedWorkflows"]),
            {
                "Validate Daily Production Package",
                "Current Spine Exact Cross-Repo E2E",
                "Current Renderer Runtime Qualification Handoff",
                "Visual Intelligence v1.2",
            },
        )

    def test_agents_is_not_docs_only(self) -> None:
        result = classify_changes(POLICY, [{"filename": "AGENTS.md", "status": "modified"}])
        self.assertEqual(result["state"], "WORKFLOWS_REQUIRED")
        self.assertEqual(result["expectedWorkflows"], ["Validate Daily Production Package"])

    def test_docs_only_passes_without_workflow(self) -> None:
        result = classify_changes(POLICY, [{"filename": "docs/reliability/example.md", "status": "modified"}])
        self.assertEqual(result["state"], "DOCS_ONLY")
        self.assertEqual(result["expectedWorkflows"], [])

    def test_unknown_non_doc_fails_closed(self) -> None:
        result = classify_changes(POLICY, [{"filename": "mystery/control.txt", "status": "added"}])
        self.assertEqual(result["state"], "UNCLASSIFIED_CHANGE")

    def test_wrong_head_sha_is_ignored(self) -> None:
        selected = select_latest_runs(
            {"Validate Daily Production Package"},
            [{"name": "Validate Daily Production Package", "head_sha": "wrong", "event": "pull_request", "run_number": 9, "run_attempt": 1, "id": 9, "status": "completed", "conclusion": "success"}],
            "head",
        )
        self.assertEqual(selected, {})

    def test_no_run_yet_waits_instead_of_failing(self) -> None:
        result = evaluate_latest_runs({"Validate Daily Production Package"}, {})
        self.assertEqual(result["state"], "WAITING_FOR_WORKFLOW")

    def test_newer_pending_masks_old_success(self) -> None:
        runs = [
            {"name": "Validate Daily Production Package", "head_sha": "head", "event": "pull_request", "run_number": 4, "run_attempt": 1, "id": 4, "status": "completed", "conclusion": "success"},
            {"name": "Validate Daily Production Package", "head_sha": "head", "event": "pull_request", "run_number": 5, "run_attempt": 1, "id": 5, "status": "in_progress", "conclusion": None},
        ]
        selected = select_latest_runs({"Validate Daily Production Package"}, runs, "head")
        self.assertEqual(evaluate_latest_runs({"Validate Daily Production Package"}, selected)["state"], "WAITING_FOR_COMPLETION")

    def test_newer_failure_masks_old_success(self) -> None:
        runs = [
            {"name": "Validate Daily Production Package", "head_sha": "head", "event": "pull_request", "run_number": 4, "run_attempt": 1, "id": 4, "status": "completed", "conclusion": "success"},
            {"name": "Validate Daily Production Package", "head_sha": "head", "event": "pull_request", "run_number": 5, "run_attempt": 2, "id": 6, "status": "completed", "conclusion": "failure"},
        ]
        selected = select_latest_runs({"Validate Daily Production Package"}, runs, "head")
        self.assertEqual(evaluate_latest_runs({"Validate Daily Production Package"}, selected)["state"], "EXPECTED_WORKFLOW_FAILED")

    def test_newer_success_masks_old_failure(self) -> None:
        runs = [
            {"name": "Validate Daily Production Package", "head_sha": "head", "event": "pull_request", "run_number": 4, "run_attempt": 1, "id": 4, "status": "completed", "conclusion": "failure"},
            {"name": "Validate Daily Production Package", "head_sha": "head", "event": "pull_request", "run_number": 5, "run_attempt": 1, "id": 5, "status": "completed", "conclusion": "success"},
        ]
        selected = select_latest_runs({"Validate Daily Production Package"}, runs, "head")
        self.assertEqual(evaluate_latest_runs({"Validate Daily Production Package"}, selected)["state"], "PASS")

    def test_missing_workflow_times_out_only_at_deadline(self) -> None:
        now = [0.0]

        def request_fn(_url: str):
            return {"workflow_runs": []}

        def sleep_fn(seconds: float) -> None:
            now[0] += seconds

        result = poll_expected_workflows(
            "owner/repo",
            "head",
            {"Validate Daily Production Package"},
            "token",
            request_fn=request_fn,
            sleep_fn=sleep_fn,
            monotonic_fn=lambda: now[0],
            timeout_seconds=20,
            poll_seconds=10,
        )
        self.assertEqual(result["state"], "EXPECTED_WORKFLOW_TIMEOUT")
        self.assertGreaterEqual(now[0], 20)


if __name__ == "__main__":
    unittest.main()
