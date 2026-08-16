from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github/workflows/chatgpt-daily-preview-production.yml"
CANARY = ROOT / ".github/workflows/visual-intelligence-real-day-canary.yml"


class PreviewProductionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.canary = CANARY.read_text(encoding="utf-8")

    def test_exactly_one_request_is_required(self) -> None:
        self.assertIn("Exactly one daily production request JSON must change per production commit", self.text)
        self.assertIn('if [[ "${#CHANGED[@]}" -ne 1 ]]', self.text)
        self.assertNotIn("tail -n 1", self.text)

    def test_visual_source_runtime_dependencies_are_installed(self) -> None:
        self.assertIn("poppler-utils", self.text)
        self.assertIn("playwright==1.61.0", self.text)
        self.assertIn("python -m playwright install --with-deps chromium", self.text)

    def test_semantic_pause_does_not_build_handoff(self) -> None:
        self.assertIn("renderer_closure_gate_v12.json", self.text)
        self.assertIn("status in {'PREPARED', 'REVIEW_REQUIRED'}", self.text)
        self.assertGreaterEqual(
            self.text.count("if: steps.closure.outputs.continue == 'true'"),
            3,
        )

    def test_only_pass_may_continue(self) -> None:
        self.assertIn("if status == 'PASS':", self.text)
        self.assertIn("print('continue=true')", self.text)
        self.assertIn("unexpected renderer closure status", self.text)

    def test_existing_canary_has_real_source_probe_with_fallback_semantics(self) -> None:
        self.assertIn("- source-probe", self.canary)
        self.assertIn("resolve_visual_sources.resolve_all", self.canary)
        self.assertIn("real_source_e2e_report.json", self.canary)
        self.assertIn("rightsBoundaryPreserved", self.canary)
        self.assertIn("selected_path not in {'primary', 'fallback'}", self.canary)
        self.assertIn("resolution_class = 'fallback-resolved'", self.canary)
        self.assertIn("Approved Fallback resolution failed", self.canary)
        self.assertIn("Primary is the selected production path but is unavailable", self.canary)
        self.assertIn("primaryUnavailable", self.canary)
        self.assertIn("playwright==1.61.0", self.canary)
        self.assertIn("poppler-utils", self.canary)


if __name__ == "__main__":
    unittest.main()
