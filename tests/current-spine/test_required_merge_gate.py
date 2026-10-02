from __future__ import annotations

import json
import fnmatch
import re
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

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_POLICY_PATH = REPO_ROOT / "contracts/required_merge_gate_policy.json"


def pull_request_paths(workflow_path: Path) -> list[str]:
    """Read the simple pull_request.paths list without adding a YAML dependency."""
    lines = workflow_path.read_text(encoding="utf-8").splitlines()
    in_pull_request = False
    in_paths = False
    paths: list[str] = []
    for line in lines:
        if line == "  pull_request:":
            in_pull_request = True
            continue
        if in_pull_request and re.match(r"^  [a-zA-Z_]", line):
            break
        if in_pull_request and line == "    paths:":
            in_paths = True
            continue
        if in_paths:
            match = re.match(r'^      - ["\'](.+)["\']$', line)
            if match:
                paths.append(match.group(1))
            elif line.strip():
                break
    return paths


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


class RealRequiredMergeGatePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy(REAL_POLICY_PATH)
        cls.workflow_paths = {
            "Verify editorial canon": pull_request_paths(
                REPO_ROOT / ".github/workflows/verify-source-materialization.yml"
            ),
            "Validate Daily Production Package": pull_request_paths(
                REPO_ROOT / ".github/workflows/validate-daily-production-package.yml"
            ),
        }

    def assertRequired(self, path: str, expected: set[str]) -> None:
        result = classify_changes(self.policy, [{"filename": path, "status": "modified"}])
        self.assertEqual(result["state"], "WORKFLOWS_REQUIRED", path)
        self.assertEqual(set(result["expectedWorkflows"]), expected, path)

    def test_canon_sources_and_materialized_files_require_both_workflows(self) -> None:
        expected = {"Verify editorial canon", "Validate Daily Production Package"}
        for path in (
            "source-of-truth/02_editorial_bible.md",
            "source-of-truth/canon_manifest.json",
            "source-of-truth/packed/03_episode_production_spec/part-00.b64",
            "source-of-truth/packed/04_entertainment_inquisitor/part-00.b64",
            "source-of-truth/03_episode_production_spec.md",
            "source-of-truth/04_entertainment_inquisitor.md",
            "source-of-truth/future_canon_input.md",
        ):
            with self.subTest(path=path):
                self.assertRequired(path, expected)

    def test_designs_require_daily_baseline(self) -> None:
        self.assertRequired(
            "designs/STORY_ENGINE_OVERHAUL_MASTER_DESIGN.md",
            {"Validate Daily Production Package"},
        )

    def test_every_editorial_canon_owner_has_a_matching_pr_trigger(self) -> None:
        representatives = (
            "source-of-truth/02_editorial_bible.md",
            "source-of-truth/packed/03_episode_production_spec/part-00.b64",
            "source-of-truth/packed/04_entertainment_inquisitor/part-00.b64",
            "contracts/canon_manifest.schema.json",
            "scripts/canon_manifest.py",
            "scripts/materialize_sources.py",
            "scripts/chatgpt_semantic_freeze.py",
            "tests/canon-manifest/test_canon_manifest.py",
            ".github/workflows/verify-source-materialization.yml",
        )
        for path in representatives:
            self.assertRequired(path, {"Verify editorial canon", "Validate Daily Production Package"})
            result = classify_changes(self.policy, [{"filename": path, "status": "modified"}])
            for workflow in result["expectedWorkflows"]:
                if workflow in self.workflow_paths:
                    with self.subTest(path=path, workflow=workflow):
                        self.assertTrue(
                            any(fnmatch.fnmatchcase(path, pattern) for pattern in self.workflow_paths[workflow]),
                            f"{workflow} does not trigger for {path}",
                        )

    def test_design_baseline_owner_has_a_matching_pr_trigger(self) -> None:
        path = "designs/STORY_ENGINE_OVERHAUL_MASTER_DESIGN.md"
        self.assertTrue(
            any(fnmatch.fnmatchcase(path, pattern) for pattern in self.workflow_paths["Validate Daily Production Package"])
        )

    def test_policy_file_remains_classified_by_existing_baseline(self) -> None:
        self.assertRequired(
            "contracts/required_merge_gate_policy.json",
            {"Validate Daily Production Package"},
        )

    def test_unknown_external_root_fails_closed(self) -> None:
        result = classify_changes(self.policy, [{"filename": "unregistered/control.txt", "status": "added"}])
        self.assertEqual(result["state"], "UNCLASSIFIED_CHANGE")

    def test_request_plus_canon_is_rejected(self) -> None:
        result = classify_changes(
            self.policy,
            [
                {"filename": "final-authorization-requests-v1/2026-09-02.json", "status": "added"},
                {"filename": "source-of-truth/02_editorial_bible.md", "status": "modified"},
            ],
        )
        self.assertEqual(result["state"], "MIXED_REQUEST_PR")


if __name__ == "__main__":
    unittest.main()
