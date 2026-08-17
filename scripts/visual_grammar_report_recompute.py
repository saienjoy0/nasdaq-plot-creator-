#!/usr/bin/env python3
"""Independent recomputation for Visual Grammar structural and timing reports."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


class VisualGrammarReportRecomputeError(ValueError):
    pass


QUALITY_WARNING_CODES = {
    "VG_SAME_APPEARANCE_RUN_TOO_LONG",
    "VG_DOMINANT_SURFACE_OVERWEIGHT",
    "VG_CARD_BOARD_OVERWEIGHT",
    "VG_NON_ANALYSIS_DURATION_TOO_LOW",
    "VG_BRIDGE_TEXT_OVERUSED",
    "VG_MAJOR_SHIFT_HOLD_TOO_SHORT",
}


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise VisualGrammarReportRecomputeError(
            f"{label} mismatch: report={actual!r} recomputed={expected!r}"
        )


def _round_ratio(value: float) -> float:
    return round(value, 6)


def _ratio(value: float, total: float) -> float:
    return 0.0 if total <= 0 else value / total


def _render_beats(render_spec: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for scene_index, scene in enumerate(render_spec.get("scenes", [])):
        scene_number = scene.get("sceneNumber", scene_index + 1)
        for beat in scene.get("visualBeats", []):
            result.append({"sceneNumber": scene_number, **beat})
    return result


def validate_structural_report_against_render(
    render_spec: dict[str, Any],
    structural_report: dict[str, Any],
    semantics_registry: dict[str, Any],
) -> None:
    beats = _render_beats(render_spec)
    scene_1_8 = [beat for beat in beats if 1 <= beat["sceneNumber"] <= 8]
    front = [beat for beat in beats if 1 <= beat["sceneNumber"] <= 4]
    back = [beat for beat in beats if 5 <= beat["sceneNumber"] <= 8]
    counted_map = {
        grammar["grammarId"]: grammar["counted"]
        for grammar in semantics_registry.get("grammars", [])
    }

    def counted_grammars(rows: list[dict[str, Any]]) -> set[str]:
        return {
            beat.get("visualGrammarId")
            for beat in rows
            if counted_map.get(beat.get("visualGrammarId")) is True
        }

    expected = {
        "beatCount": len(beats),
        "scene1To8BeatCount": len(scene_1_8),
        "semanticGrammarCount": len(counted_grammars(scene_1_8)),
        "frontHalfGrammarCount": len(counted_grammars(front)),
        "backHalfGrammarCount": len(counted_grammars(back)),
        "majorShiftCount": sum(
            beat.get("transitionRole") == "major-shift" for beat in scene_1_8
        ),
        "frontHalfMajorShiftCount": sum(
            beat.get("transitionRole") == "major-shift" for beat in front
        ),
        "backHalfMajorShiftCount": sum(
            beat.get("transitionRole") == "major-shift" for beat in back
        ),
        "bridgeTextBeatCount": sum(
            beat.get("visualGrammarId") == "bridge-text" for beat in scene_1_8
        ),
    }
    for field, value in expected.items():
        _require_equal(f"structural report {field}", structural_report.get(field), value)
    if structural_report.get("violations") != []:
        raise VisualGrammarReportRecomputeError(
            "structural PASS report must contain zero violations"
        )
    # New/current reports must carry the editorial-warning channel. The JSON schema
    # keeps this optional only so historical 1.0.0 artifacts do not need rewriting.
    if "warnings" in structural_report and not isinstance(structural_report["warnings"], list):
        raise VisualGrammarReportRecomputeError(
            "structural report warnings must be an array when present"
        )


def _validate_static_state_report(timing_report: dict[str, Any]) -> None:
    _require_equal("timing contractVersion", timing_report.get("contractVersion"), "1.1.0")
    static = timing_report.get("staticState")
    if not isinstance(static, dict):
        raise VisualGrammarReportRecomputeError("timing report staticState must be an object")
    _require_equal("staticState mode", static.get("mode"), "report-only")
    _require_equal("staticState warningThresholdMs", static.get("warningThresholdMs"), 8000)
    _require_equal(
        "staticState failureCandidateThresholdMs",
        static.get("failureCandidateThresholdMs"),
        16000,
    )
    warnings = static.get("warnings")
    candidates = static.get("failureCandidates")
    if not isinstance(warnings, list) or not isinstance(candidates, list):
        raise VisualGrammarReportRecomputeError(
            "staticState warnings and failureCandidates must be arrays"
        )
    _require_equal("staticState warningCount", static.get("warningCount"), len(warnings))
    _require_equal(
        "staticState failureCandidateCount",
        static.get("failureCandidateCount"),
        len(candidates),
    )
    for index, row in enumerate(warnings):
        if row.get("durationMs", 0) <= 8000:
            raise VisualGrammarReportRecomputeError(
                f"staticState warning[{index}] does not exceed 8000ms"
            )
    for index, row in enumerate(candidates):
        if row.get("durationMs", 0) <= 16000:
            raise VisualGrammarReportRecomputeError(
                f"staticState failureCandidate[{index}] does not exceed 16000ms"
            )
    warning_keys = {
        (row.get("sceneId"), row.get("beatId"), row.get("startMs"), row.get("endMs"))
        for row in warnings
    }
    for index, row in enumerate(candidates):
        key = (row.get("sceneId"), row.get("beatId"), row.get("startMs"), row.get("endMs"))
        if key not in warning_keys:
            raise VisualGrammarReportRecomputeError(
                f"staticState failureCandidate[{index}] must also be present in warnings"
            )
    longest = float(static.get("longestStaticStateMs", 0))
    if warnings:
        _require_equal(
            "staticState longestStaticStateMs",
            longest,
            max(float(row["durationMs"]) for row in warnings),
        )
    elif longest > 8000:
        raise VisualGrammarReportRecomputeError(
            "staticState longestStaticStateMs exceeds warning threshold without warning row"
        )
    if any(str(row.get("code", "")).startswith("VG_STATIC_STATE") for row in timing_report.get("failures", [])):
        raise VisualGrammarReportRecomputeError(
            "Static State 1.1.0 is report-only and must not appear in hard failures"
        )


def _quality_signature(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(row.get("code")),
        str(row.get("path")),
        row.get("beatId"),
        row.get("actual"),
        row.get("limit"),
        str(row.get("unit")),
    )


def _sorted_quality_signatures(rows: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
    return sorted(
        (_quality_signature(row) for row in rows),
        key=lambda item: (
            item[0], item[1], "" if item[2] is None else str(item[2]),
            repr(item[3]), repr(item[4]), item[5],
        ),
    )


def validate_timing_report_metrics(timing_report: dict[str, Any]) -> None:
    if timing_report.get("failures") != []:
        raise VisualGrammarReportRecomputeError(
            "timing PASS report must contain zero failures"
        )
    _validate_static_state_report(timing_report)
    rows = timing_report.get("beats", [])
    if not rows:
        raise VisualGrammarReportRecomputeError("timing report must contain measured Beats")

    thresholds = timing_report["thresholds"]
    expected_non_analysis = 8000 if timing_report["durationMode"] == "shortened" else 10000
    _require_equal(
        "timing threshold nonAnalysisMinMs",
        thresholds["nonAnalysisMinMs"],
        expected_non_analysis,
    )

    appearance_duration: dict[str, float] = defaultdict(float)
    surface_duration: dict[str, float] = defaultdict(float)
    total_ms = 0.0
    non_analysis_ms = 0.0
    bridge_ms = 0.0
    major_shift_count = 0
    non_analysis_appearances = {
        "entity-canvas", "document-media", "picturebook-canvas"
    }
    expected_quality_warnings: list[dict[str, Any]] = []

    longest_run_ms = 0.0
    longest_run_ids: list[str] = []
    current_appearance: str | None = None
    current_run_ms = 0.0
    current_run_ids: list[str] = []

    def close_run() -> None:
        nonlocal longest_run_ms, longest_run_ids
        if current_run_ms > longest_run_ms:
            longest_run_ms = current_run_ms
            longest_run_ids = list(current_run_ids)
        if current_run_ms > thresholds["sameAppearanceRunMaxMs"]:
            first_id = current_run_ids[0] if current_run_ids else "unknown"
            expected_quality_warnings.append(
                {
                    "code": "VG_SAME_APPEARANCE_RUN_TOO_LONG",
                    "path": f"episode://{first_id}/appearance-run",
                    "beatId": first_id if current_run_ids else None,
                    "actual": current_run_ms,
                    "limit": thresholds["sameAppearanceRunMaxMs"],
                    "unit": "ms",
                }
            )

    for index, row in enumerate(rows):
        duration = row["endMs"] - row["startMs"]
        _require_equal(f"timing Beat[{index}] durationMs", row["durationMs"], duration)
        if duration < 0:
            raise VisualGrammarReportRecomputeError(
                f"timing Beat[{index}] has negative duration"
            )
        total_ms += duration
        appearance = row["appearanceClass"]
        surface = row["dominantSurface"]
        appearance_duration[appearance] += duration
        surface_duration[surface] += duration
        if appearance in non_analysis_appearances:
            non_analysis_ms += duration
        if row["visualGrammarId"] == "bridge-text":
            bridge_ms += duration
        if row["transitionRole"] == "major-shift":
            major_shift_count += 1
            if duration < thresholds["majorShiftStageMinMs"]:
                expected_quality_warnings.append(
                    {
                        "code": "VG_MAJOR_SHIFT_HOLD_TOO_SHORT",
                        "path": f"episode://{row['sceneId']}/{row['beatId']}/durationMs",
                        "beatId": row["beatId"],
                        "actual": duration,
                        "limit": thresholds["majorShiftStageMinMs"],
                        "unit": "ms",
                    }
                )

        if appearance != current_appearance:
            close_run()
            current_appearance = appearance
            current_run_ms = 0.0
            current_run_ids = []
        current_run_ms += duration
        current_run_ids.append(row["beatId"])
    close_run()

    surface_max_id: str | None = None
    surface_max_ms = 0.0
    for surface, duration in surface_duration.items():
        if duration > surface_max_ms:
            surface_max_id = surface
            surface_max_ms = duration
    surface_max_ratio = _round_ratio(_ratio(surface_max_ms, total_ms))
    card_ratio = _round_ratio(_ratio(surface_duration.get("card-board", 0.0), total_ms))
    bridge_ratio = _round_ratio(_ratio(bridge_ms, total_ms))

    if surface_max_ratio > thresholds["dominantSurfaceMaxRatio"]:
        expected_quality_warnings.append(
            {
                "code": "VG_DOMINANT_SURFACE_OVERWEIGHT",
                "path": f"$.metrics.dominantSurfaceDurationMs.{surface_max_id or 'unknown'}",
                "beatId": None,
                "actual": surface_max_ratio,
                "limit": thresholds["dominantSurfaceMaxRatio"],
                "unit": "ratio",
            }
        )
    if card_ratio > thresholds["cardBoardMaxRatio"]:
        expected_quality_warnings.append(
            {
                "code": "VG_CARD_BOARD_OVERWEIGHT",
                "path": "$.metrics.dominantSurfaceDurationMs.card-board",
                "beatId": None,
                "actual": card_ratio,
                "limit": thresholds["cardBoardMaxRatio"],
                "unit": "ratio",
            }
        )
    if non_analysis_ms < thresholds["nonAnalysisMinMs"]:
        expected_quality_warnings.append(
            {
                "code": "VG_NON_ANALYSIS_DURATION_TOO_LOW",
                "path": "$.metrics.nonAnalysisDurationMs",
                "beatId": None,
                "actual": non_analysis_ms,
                "limit": thresholds["nonAnalysisMinMs"],
                "unit": "ms",
            }
        )
    if (
        bridge_ms > thresholds["bridgeTextMaxMs"]
        or bridge_ratio > thresholds["bridgeTextMaxRatio"]
    ):
        absolute_exceeded = bridge_ms > thresholds["bridgeTextMaxMs"]
        expected_quality_warnings.append(
            {
                "code": "VG_BRIDGE_TEXT_OVERUSED",
                "path": "$.metrics.bridgeTextDurationMs",
                "beatId": None,
                "actual": bridge_ms if absolute_exceeded else bridge_ratio,
                "limit": thresholds["bridgeTextMaxMs"] if absolute_exceeded else thresholds["bridgeTextMaxRatio"],
                "unit": "ms" if absolute_exceeded else "ratio",
            }
        )

    actual_quality_warnings = [
        row
        for row in timing_report.get("warnings", [])
        if str(row.get("code")) in QUALITY_WARNING_CODES
    ]
    _require_equal(
        "timing quality warning payloads",
        _sorted_quality_signatures(actual_quality_warnings),
        _sorted_quality_signatures(expected_quality_warnings),
    )

    metrics = timing_report["metrics"]
    expected_metrics = {
        "measuredBeatCount": len(rows),
        "totalMeasuredMs": total_ms,
        "appearanceClassCount": len(appearance_duration),
        "dominantSurfaceCount": len(surface_duration),
        "majorShiftCount": major_shift_count,
        "longestSameAppearanceRunMs": longest_run_ms,
        "longestSameAppearanceRunBeatIds": longest_run_ids,
        "dominantSurfaceMaxRatio": surface_max_ratio,
        "dominantSurfaceMaxId": surface_max_id,
        "cardBoardRatio": card_ratio,
        "nonAnalysisDurationMs": non_analysis_ms,
        "bridgeTextDurationMs": bridge_ms,
        "bridgeTextRatio": bridge_ratio,
        "appearanceDurationMs": dict(appearance_duration),
        "dominantSurfaceDurationMs": dict(surface_duration),
    }
    for field, value in expected_metrics.items():
        _require_equal(f"timing metrics {field}", metrics.get(field), value)
