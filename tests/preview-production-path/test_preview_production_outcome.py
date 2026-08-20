from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import write_preview_production_outcome as outcome_writer


class PreviewProductionPathTests(unittest.TestCase):
    def _args(self, gate: Path, **overrides) -> argparse.Namespace:
        values = {
            "closure_gate": gate,
            "episode_date": "2026-08-17",
            "plot_commit": "a" * 40,
            "renderer_commit": "b" * 40,
            "handoff_upload_outcome": "skipped",
            "handoff_artifact_name": "",
            "handoff_artifact_id": "",
            "handoff_artifact_url": "",
            "handoff_artifact_digest": "",
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def _gate(self, directory: Path, value: dict) -> Path:
        path = directory / "renderer_closure_gate_v12.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_visual_decision_pause_is_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate = self._gate(
                Path(tmp),
                {"status": "PREPARED", "requiredAction": "AUTHOR_VISUAL_INTELLIGENCE_DECISION"},
            )
            outcome = outcome_writer.build_outcome(self._args(gate))
            self.assertEqual("WAITING_FOR_VISUAL_INTELLIGENCE_DECISION", outcome["state"])
            self.assertFalse(outcome["previewHandoffReady"])

    def test_reselection_pause_is_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate = self._gate(
                Path(tmp),
                {"status": "PREPARED", "requiredAction": "RESELECT_VISUAL_CANDIDATES"},
            )
            outcome = outcome_writer.build_outcome(self._args(gate))
            self.assertEqual("WAITING_FOR_VISUAL_RESELECTION", outcome["state"])

    def test_review_pause_is_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate = self._gate(Path(tmp), {"status": "REVIEW_REQUIRED"})
            outcome = outcome_writer.build_outcome(self._args(gate))
            self.assertEqual("WAITING_FOR_VISUAL_REVIEW", outcome["state"])

    def test_pass_requires_uploaded_immutable_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate = self._gate(Path(tmp), {"status": "PASS"})
            outcome = outcome_writer.build_outcome(self._args(gate))
            self.assertEqual("FAILED", outcome["state"])
            self.assertFalse(outcome["previewHandoffReady"])

    def test_pass_with_uploaded_handoff_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate = self._gate(Path(tmp), {"status": "PASS"})
            outcome = outcome_writer.build_outcome(
                self._args(
                    gate,
                    handoff_upload_outcome="success",
                    handoff_artifact_name="nasdaq-cafe-handoff-2026-08-17-123",
                    handoff_artifact_id="456",
                )
            )
            self.assertEqual("PREVIEW_HANDOFF_READY", outcome["state"])
            self.assertTrue(outcome["previewHandoffReady"])

    def test_plot_has_exactly_one_production_request_entrypoint(self) -> None:
        contract = json.loads(
            (ROOT / "contracts" / "preview_production_path.json").read_text(encoding="utf-8")
        )
        canonical = ROOT / contract["plot"]["entryWorkflow"]
        request_glob = contract["plot"]["requestGlob"]
        owners = []
        for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
            if request_glob in path.read_text(encoding="utf-8"):
                owners.append(path.resolve())
        self.assertEqual([canonical.resolve()], owners)
        self.assertEqual("PREVIEW", contract["scope"])
        self.assertFalse(contract["finalAllowed"])
        self.assertEqual(
            ".github/workflows/nasdaq-cafe-handoff-preview-request-v4.yml",
            contract["renderer"]["requestWorkflow"],
        )
        self.assertEqual(
            ".github/workflows/nasdaq-cafe-preview-handoff-v2.yml",
            contract["renderer"]["workerWorkflow"],
        )


if __name__ == "__main__":
    unittest.main()
