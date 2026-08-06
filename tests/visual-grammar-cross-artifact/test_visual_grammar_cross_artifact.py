from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import visual_grammar_cross_artifact as cross  # noqa: E402


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class VisualGrammarCrossArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.contracts = self.repo / "contracts"
        self.contracts.mkdir(parents=True)
        for name in (
            "visual_grammar_semantics.json",
            "visual_grammar_structural_report.schema.json",
            "visual_grammar_timing_report.schema.json",
            "visual_grammar_renderer_compatibility.json",
            "visual_grammar_handoff.schema.json",
        ):
            shutil.copy2(ROOT / "contracts" / name, self.contracts / name)

        self.date = "2026-08-06"
        self.final_path = self.repo / "final_episode_contract.json"
        self.render_path = self.repo / "render_spec.json"
        self.structural_path = self.repo / "visual_grammar_structural_report.json"
        self.timing_path = self.repo / "visual_grammar_timing_report.json"
        self.output_path = self.repo / "visual_grammar_handoff.json"
        self.preflight_path = self.repo / "official_execution_preflight.json"
        write_json(self.final_path, {
            "contractVersion": "1.1.0",
            "episodeDate": self.date,
            "approvedForProduction": True,
        })
        write_json(self.preflight_path, {
            "contract_version": "1.0.0",
            "episode_date": self.date,
            "status": "pass",
            "preview_authorized": False,
            "final_authorized": False,
            "unresolved_states": 0,
        })
        self.make_valid_artifacts()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def compatibility(self) -> dict[str, dict]:
        value = json.loads(
            (self.contracts / "visual_grammar_renderer_compatibility.json").read_text(
                encoding="utf-8"
            )
        )
        return {entry["visualTemplateId"]: entry for entry in value["templates"]}

    def template_rows(self) -> list[tuple[str, str, str, str]]:
        return [
            ("opening-contradiction", "default", "contradiction", "continuation"),
            ("entity-card-full", "default", "entity", "major-shift"),
            ("news-media", "default", "evidence", "continuation"),
            ("earnings-surprise", "default", "gap", "continuation"),
            ("causal-lane", "left-to-right", "causal", "major-shift"),
            ("event-reaction-timeline", "close-only", "reaction", "continuation"),
            ("split-comparison", "default", "comparison", "continuation"),
            ("verification-matrix", "strengthen-vs-weaken", "verification", "continuation"),
            ("closing-recap", "default", "assembly", "closing"),
        ]

    def appearance(self, template: str, variant: str) -> tuple[str, str, str]:
        entry = self.compatibility()[template]
        for override in entry.get("variantOverrides", []):
            if override["variant"] == variant:
                return (
                    override["appearanceClass"],
                    override["dominantSurface"],
                    override["stageShell"],
                )
        return entry["appearanceClass"], entry["dominantSurface"], entry["stageShell"]

    def make_render(self) -> dict:
        scenes = []
        for number, (template, variant, grammar, transition) in enumerate(
            self.template_rows(), start=1
        ):
            beat_id = f"vb-{number:02d}-01"
            beat = {
                "beatId": beat_id,
                "visualTemplate": template,
                "templateConfig": {"variant": variant},
                "visualGrammarId": grammar,
                "transitionRole": transition,
            }
            if number == 3:
                beat["financialVisualTrace"] = {
                    "selectedPath": "fallback",
                    "selectedPlanId": "fvp-source-fallback",
                }
            scenes.append({
                "sceneId": f"scene-{number:02d}",
                "sceneNumber": number,
                "visualBeats": [beat],
            })
        return {
            "schemaVersion": "2.4.0",
            "episode": {"id": self.date, "durationMode": "standard"},
            "visualGrammarContract": {
                "contractVersion": "1.0.0",
                "semanticsSha256": sha(self.contracts / "visual_grammar_semantics.json"),
                "rendererCompatibilitySha256": sha(
                    self.contracts / "visual_grammar_renderer_compatibility.json"
                ),
                "finalEpisodeContractSha256": sha(self.final_path),
                "beatCount": 9,
            },
            "scenes": scenes,
        }

    def make_structural(self) -> dict:
        return {
            "reportVersion": "1.0.0",
            "visualGrammarContractVersion": "1.0.0",
            "status": "PASS",
            "episodeDate": self.date,
            "beatCount": 9,
            "scene1To8BeatCount": 8,
            "semanticGrammarCount": 8,
            "frontHalfGrammarCount": 4,
            "backHalfGrammarCount": 4,
            "majorShiftCount": 2,
            "frontHalfMajorShiftCount": 1,
            "backHalfMajorShiftCount": 1,
            "bridgeTextBeatCount": 0,
            "violations": [],
        }

    def make_timing(self, render_sha: str) -> dict:
        beats = []
        appearance_duration: dict[str, int] = {}
        surface_duration: dict[str, int] = {}
        for number, (template, variant, grammar, transition) in enumerate(
            self.template_rows()[:8], start=1
        ):
            appearance, surface, stage = self.appearance(template, variant)
            appearance_duration[appearance] = appearance_duration.get(appearance, 0) + 7000
            surface_duration[surface] = surface_duration.get(surface, 0) + 7000
            beats.append({
                "sceneId": f"scene-{number:02d}",
                "sceneNumber": number,
                "beatId": f"vb-{number:02d}-01",
                "startMs": (number - 1) * 7000,
                "endMs": number * 7000,
                "durationMs": 7000,
                "visualGrammarId": grammar,
                "transitionRole": transition,
                "appearanceClass": appearance,
                "dominantSurface": surface,
                "stageShell": stage,
                "selectedPath": "fallback" if number == 3 else "not-applicable",
            })
        return {
            "contractVersion": "1.0.0",
            "status": "PASS",
            "timingBasis": "post-tts-production-data",
            "episodeId": self.date,
            "durationMode": "standard",
            "inputRenderSpecSha256": render_sha,
            "semanticsSha256": sha(self.contracts / "visual_grammar_semantics.json"),
            "rendererCompatibilitySha256": sha(
                self.contracts / "visual_grammar_renderer_compatibility.json"
            ),
            "finalEpisodeContractSha256": sha(self.final_path),
            "sceneRange": "scene-01..scene-08",
            "fallbackDiversityRecheck": "completed",
            "selectedFallbackBeatIds": ["vb-03-01"],
            "unresolvedStateCount": 0,
            "thresholds": {
                "sameAppearanceRunMaxMs": 28000,
                "dominantSurfaceMaxRatio": 0.45,
                "cardBoardMaxRatio": 0.55,
                "nonAnalysisMinMs": 10000,
                "bridgeTextMaxRatio": 0.12,
                "bridgeTextMaxMs": 18000,
                "majorShiftStageMinMs": 4000,
            },
            "metrics": {
                "measuredBeatCount": 8,
                "totalMeasuredMs": 56000,
                "appearanceClassCount": 8,
                "dominantSurfaceCount": 7,
                "majorShiftCount": 2,
                "longestSameAppearanceRunMs": 7000,
                "longestSameAppearanceRunBeatIds": ["vb-01-01"],
                "dominantSurfaceMaxRatio": 0.25,
                "dominantSurfaceMaxId": "plot",
                "cardBoardRatio": 0.0,
                "nonAnalysisDurationMs": 14000,
                "bridgeTextDurationMs": 0,
                "bridgeTextRatio": 0.0,
                "appearanceDurationMs": appearance_duration,
                "dominantSurfaceDurationMs": surface_duration,
            },
            "beats": beats,
            "failures": [],
            "warnings": [],
        }

    def make_valid_artifacts(self) -> None:
        write_json(self.render_path, self.make_render())
        write_json(self.structural_path, self.make_structural())
        write_json(self.timing_path, self.make_timing(sha(self.render_path)))

    def rewrite_render_and_sync_timing(self, render: dict) -> None:
        write_json(self.render_path, render)
        timing = json.loads(self.timing_path.read_text(encoding="utf-8"))
        timing["inputRenderSpecSha256"] = sha(self.render_path)
        write_json(self.timing_path, timing)

    def authorize(self) -> dict:
        return cross.authorize_visual_grammar_handoff(
            render_spec_path=self.render_path,
            final_episode_contract_path=self.final_path,
            structural_report_path=self.structural_path,
            timing_report_path=self.timing_path,
            semantics_registry_path=self.contracts / "visual_grammar_semantics.json",
            renderer_compatibility_path=self.contracts
            / "visual_grammar_renderer_compatibility.json",
            structural_schema_path=self.contracts
            / "visual_grammar_structural_report.schema.json",
            timing_schema_path=self.contracts / "visual_grammar_timing_report.schema.json",
            handoff_schema_path=self.contracts / "visual_grammar_handoff.schema.json",
            output_path=self.output_path,
            official_preflight_path=self.preflight_path,
        )

    def test_01_valid_handoff_passes_and_updates_preflight(self) -> None:
        result = self.authorize()
        self.assertEqual("PASS", result["status"])
        self.assertTrue(result["handoffAuthorized"])
        self.assertEqual(["vb-03-01"], result["selectedFallbackBeatIds"])
        preflight = json.loads(self.preflight_path.read_text(encoding="utf-8"))
        self.assertEqual("PASS", preflight["visualGrammarGate"]["status"])
        self.assertEqual(sha(self.output_path), preflight["visualGrammarGate"]["handoffSha256"])
        self.assertFalse(preflight["final_authorized"])

    def test_02_timing_fail_is_rejected(self) -> None:
        timing = json.loads(self.timing_path.read_text(encoding="utf-8"))
        timing["status"] = "FAIL"
        write_json(self.timing_path, timing)
        with self.assertRaisesRegex(cross.VisualGrammarCrossArtifactError, "timing report must be PASS"):
            self.authorize()

    def test_03_structural_fail_is_rejected(self) -> None:
        structural = json.loads(self.structural_path.read_text(encoding="utf-8"))
        structural["status"] = "FAIL"
        write_json(self.structural_path, structural)
        with self.assertRaisesRegex(cross.VisualGrammarCrossArtifactError, "structural report must be PASS"):
            self.authorize()

    def test_04_render_spec_sha_mismatch_is_rejected(self) -> None:
        timing = json.loads(self.timing_path.read_text(encoding="utf-8"))
        timing["inputRenderSpecSha256"] = "0" * 64
        write_json(self.timing_path, timing)
        with self.assertRaisesRegex(cross.VisualGrammarCrossArtifactError, "input render spec SHA mismatch"):
            self.authorize()

    def test_05_contract_sha_mismatch_is_rejected(self) -> None:
        render = json.loads(self.render_path.read_text(encoding="utf-8"))
        render["visualGrammarContract"]["semanticsSha256"] = "0" * 64
        self.rewrite_render_and_sync_timing(render)
        with self.assertRaisesRegex(cross.VisualGrammarCrossArtifactError, "root semanticsSha256 mismatch"):
            self.authorize()

    def test_06_timing_appearance_mismatch_is_rejected(self) -> None:
        timing = json.loads(self.timing_path.read_text(encoding="utf-8"))
        timing["beats"][0]["appearanceClass"] = "metric-board"
        write_json(self.timing_path, timing)
        with self.assertRaisesRegex(cross.VisualGrammarCrossArtifactError, "appearanceClass mismatch"):
            self.authorize()

    def test_07_fallback_beat_mismatch_is_rejected(self) -> None:
        timing = json.loads(self.timing_path.read_text(encoding="utf-8"))
        timing["selectedFallbackBeatIds"] = []
        write_json(self.timing_path, timing)
        with self.assertRaisesRegex(cross.VisualGrammarCrossArtifactError, "fallback Beat mismatch"):
            self.authorize()

    def test_08_non_selected_candidate_state_is_rejected(self) -> None:
        render = json.loads(self.render_path.read_text(encoding="utf-8"))
        render["scenes"][0]["visualBeats"][0]["candidatePlans"] = []
        self.rewrite_render_and_sync_timing(render)
        with self.assertRaisesRegex(cross.VisualGrammarCrossArtifactError, "candidate state is forbidden"):
            self.authorize()

    def test_09_unresolved_state_is_rejected(self) -> None:
        render = json.loads(self.render_path.read_text(encoding="utf-8"))
        render["scenes"][0]["visualBeats"][0]["selectionStatus"] = "not-run"
        self.rewrite_render_and_sync_timing(render)
        with self.assertRaisesRegex(cross.VisualGrammarCrossArtifactError, "unresolved state"):
            self.authorize()

    def test_10_old_render_spec_is_rejected(self) -> None:
        render = json.loads(self.render_path.read_text(encoding="utf-8"))
        render["schemaVersion"] = "2.3.0"
        self.rewrite_render_and_sync_timing(render)
        with self.assertRaisesRegex(cross.VisualGrammarCrossArtifactError, "requires render_spec 2.4.0"):
            self.authorize()

    def test_11_structural_count_falsification_is_rejected(self) -> None:
        structural = json.loads(self.structural_path.read_text(encoding="utf-8"))
        structural["semanticGrammarCount"] = 7
        write_json(self.structural_path, structural)
        with self.assertRaisesRegex(Exception, "semanticGrammarCount mismatch"):
            self.authorize()

    def test_12_timing_metric_falsification_is_rejected(self) -> None:
        timing = json.loads(self.timing_path.read_text(encoding="utf-8"))
        timing["metrics"]["totalMeasuredMs"] = 55000
        write_json(self.timing_path, timing)
        with self.assertRaisesRegex(Exception, "totalMeasuredMs mismatch"):
            self.authorize()


if __name__ == "__main__":
    unittest.main()
