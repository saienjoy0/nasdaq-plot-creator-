#!/usr/bin/env python3
"""Independent recomputation for Visual Grammar structural and timing reports."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


class VisualGrammarReportRecomputeError(ValueError):
    pass


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


def validate_timing_report_metrics(timing_report: dict[str, Any]) -> None:
    if timing_report.get("failures") != []:
        raise VisualGrammarReportRecomputeError(
            "timing PASS report must contain zero failures"
        )
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
            raise VisualGrammarReportRecomputeError(
                f"same Appearance run exceeds threshold: {current_run_ms}"
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
                raise VisualGrammarReportRecomputeError(
                    f"major-shift Beat {row['beatId']} is shorter than threshold"
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
        raise VisualGrammarReportRecomputeError(
            f"Dominant Surface ratio exceeds threshold: {surface_max_ratio}"
        )
    if card_ratio > thresholds["cardBoardMaxRatio"]:
        raise VisualGrammarReportRecomputeError(
            f"card-board ratio exceeds threshold: {card_ratio}"
        )
    if non_analysis_ms < thresholds["nonAnalysisMinMs"]:
        raise VisualGrammarReportRecomputeError(
            f"non-analysis duration is below threshold: {non_analysis_ms}"
        )
    if (
        bridge_ms > thresholds["bridgeTextMaxMs"]
        or bridge_ratio > thresholds["bridgeTextMaxRatio"]
    ):
        raise VisualGrammarReportRecomputeError(
            f"bridge-text exceeds threshold: {bridge_ms}ms / {bridge_ratio}"
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
