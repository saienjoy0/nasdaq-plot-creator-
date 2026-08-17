from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import visual_grammar_report_recompute as recompute  # noqa: E402


class TimingWarningBoundaryTests(unittest.TestCase):
    def report(self) -> dict:
        return {
            "contractVersion": "1.1.0",
            "status": "PASS",
            "durationMode": "standard",
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
                "measuredBeatCount": 1,
                "totalMeasuredMs": 7000.0,
                "appearanceClassCount": 1,
                "dominantSurfaceCount": 1,
                "majorShiftCount": 0,
                "longestSameAppearanceRunMs": 7000.0,
                "longestSameAppearanceRunBeatIds": ["vb-01-01"],
                "dominantSurfaceMaxRatio": 1.0,
                "dominantSurfaceMaxId": "card-board",
                "cardBoardRatio": 1.0,
                "nonAnalysisDurationMs": 0.0,
                "bridgeTextDurationMs": 0.0,
                "bridgeTextRatio": 0.0,
                "appearanceDurationMs": {"metric-board": 7000.0},
                "dominantSurfaceDurationMs": {"card-board": 7000.0},
            },
            "staticState": {
                "mode": "report-only",
                "warningThresholdMs": 8000,
                "failureCandidateThresholdMs": 16000,
                "longestStaticStateMs": 7000,
                "longestStaticStateSceneId": "scene-01",
                "longestStaticStateBeatId": "vb-01-01",
                "warningCount": 0,
                "failureCandidateCount": 0,
                "warnings": [],
                "failureCandidates": [],
            },
            "beats": [
                {
                    "sceneId": "scene-01",
                    "sceneNumber": 1,
                    "beatId": "vb-01-01",
                    "startMs": 0,
                    "endMs": 7000,
                    "durationMs": 7000,
                    "visualGrammarId": "evidence",
                    "transitionRole": "continuation",
                    "appearanceClass": "metric-board",
                    "dominantSurface": "card-board",
                    "stageShell": "metric-stage",
                    "selectedPath": "not-applicable",
                }
            ],
            "failures": [],
            "warnings": [
                {
                    "code": "VG_DOMINANT_SURFACE_OVERWEIGHT",
                    "path": "$.metrics.dominantSurfaceDurationMs.card-board",
                    "beatId": None,
                    "actual": 1.0,
                    "limit": 0.45,
                    "unit": "ratio",
                },
                {
                    "code": "VG_CARD_BOARD_OVERWEIGHT",
                    "path": "$.metrics.dominantSurfaceDurationMs.card-board",
                    "beatId": None,
                    "actual": 1.0,
                    "limit": 0.55,
                    "unit": "ratio",
                },
                {
                    "code": "VG_NON_ANALYSIS_DURATION_TOO_LOW",
                    "path": "$.metrics.nonAnalysisDurationMs",
                    "beatId": None,
                    "actual": 0.0,
                    "limit": 10000,
                    "unit": "ms",
                },
            ],
        }

    def test_quality_thresholds_are_warning_only(self):
        recompute.validate_timing_report_metrics(self.report())

    def test_missing_quality_warning_is_detected(self):
        report = self.report()
        report["warnings"] = report["warnings"][:-1]
        with self.assertRaisesRegex(
            recompute.VisualGrammarReportRecomputeError,
            "timing quality warning payloads mismatch",
        ):
            recompute.validate_timing_report_metrics(report)

    def test_corrupted_warning_actual_is_detected(self):
        report = self.report()
        report["warnings"][0]["actual"] = 7000
        with self.assertRaisesRegex(
            recompute.VisualGrammarReportRecomputeError,
            "timing quality warning payloads mismatch",
        ):
            recompute.validate_timing_report_metrics(report)

    def test_corrupted_warning_unit_is_detected(self):
        report = self.report()
        report["warnings"][0]["unit"] = "ms"
        with self.assertRaisesRegex(
            recompute.VisualGrammarReportRecomputeError,
            "timing quality warning payloads mismatch",
        ):
            recompute.validate_timing_report_metrics(report)

    def test_bridge_ratio_warning_uses_ratio_actual_and_limit(self):
        report = copy.deepcopy(self.report())
        report["beats"][0].update(
            {
                "visualGrammarId": "bridge-text",
                "appearanceClass": "text-bridge",
                "dominantSurface": "text",
                "stageShell": "text-stage",
            }
        )
        report["metrics"].update(
            {
                "dominantSurfaceMaxId": "text",
                "cardBoardRatio": 0.0,
                "bridgeTextDurationMs": 7000.0,
                "bridgeTextRatio": 1.0,
                "appearanceDurationMs": {"text-bridge": 7000.0},
                "dominantSurfaceDurationMs": {"text": 7000.0},
            }
        )
        report["warnings"] = [
            {
                "code": "VG_DOMINANT_SURFACE_OVERWEIGHT",
                "path": "$.metrics.dominantSurfaceDurationMs.text",
                "beatId": None,
                "actual": 1.0,
                "limit": 0.45,
                "unit": "ratio",
            },
            {
                "code": "VG_NON_ANALYSIS_DURATION_TOO_LOW",
                "path": "$.metrics.nonAnalysisDurationMs",
                "beatId": None,
                "actual": 0.0,
                "limit": 10000,
                "unit": "ms",
            },
            {
                "code": "VG_BRIDGE_TEXT_OVERUSED",
                "path": "$.metrics.bridgeTextDurationMs",
                "beatId": None,
                "actual": 1.0,
                "limit": 0.12,
                "unit": "ratio",
            },
        ]
        recompute.validate_timing_report_metrics(report)
        report["warnings"][-1]["actual"] = 7000
        with self.assertRaisesRegex(
            recompute.VisualGrammarReportRecomputeError,
            "timing quality warning payloads mismatch",
        ):
            recompute.validate_timing_report_metrics(report)

    def test_quality_code_in_failures_is_rejected(self):
        report = self.report()
        report["failures"] = [
            {"code": "VG_DOMINANT_SURFACE_OVERWEIGHT"}
        ]
        with self.assertRaisesRegex(
            recompute.VisualGrammarReportRecomputeError,
            "timing PASS report must contain zero failures",
        ):
            recompute.validate_timing_report_metrics(report)


if __name__ == "__main__":
    unittest.main()
