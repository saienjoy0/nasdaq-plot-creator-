from __future__ import annotations

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
                {"code": "VG_DOMINANT_SURFACE_OVERWEIGHT"},
                {"code": "VG_CARD_BOARD_OVERWEIGHT"},
                {"code": "VG_NON_ANALYSIS_DURATION_TOO_LOW"},
            ],
        }

    def test_quality_thresholds_are_warning_only(self):
        recompute.validate_timing_report_metrics(self.report())

    def test_missing_quality_warning_is_detected(self):
        report = self.report()
        report["warnings"] = report["warnings"][:-1]
        with self.assertRaisesRegex(
            recompute.VisualGrammarReportRecomputeError,
            "timing quality warning codes mismatch",
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
