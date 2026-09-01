#!/usr/bin/env python3
"""Validate author-owned visual structure before Current semantic freeze/Preview readiness.

This gate is deliberately mechanical. It never selects a replacement template, invents
metrics, infers causality, or rewrites viewer text. It only checks that the visual
Template chosen by ChatGPT has the Renderer-native structure that choice requires.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class VisualFeasibilityError(ValueError):
    pass


NUMERIC_TEMPLATE_COUNTS: dict[str, tuple[int, int]] = {
    "market-pulse-grid": (3, 6),
    "dual-asset-split": (2, 2),
    "index-return-bars": (2, 6),
    "diverging-stock-bars": (2, 6),
    "split-comparison": (2, 4),
    "focus-matrix": (2, 6),
}

LANE_TEMPLATES = {"tailwind-headwind", "verification-matrix"}
REACTION_PRECISION_BY_VARIANT = {
    "verified-series": "verified-intraday-series",
    "reported-sequence": "reported-sequence",
    "official-time-plus-close": "official-time-plus-close",
    "close-only": "close-only",
}


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualFeasibilityError(f"authoring invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualFeasibilityError("authoring root must be an object")
    return value


def _object_ids(scene_index: int, beat_index: int, beat: dict[str, Any]) -> list[str]:
    sid = f"scene-{scene_index:02d}"
    metrics = beat.get("metrics", [])
    nodes = beat.get("nodes", [])
    result = [
        f"{sid}-number-{beat_index:02d}-{index:02d}"
        for index, _ in enumerate(metrics if isinstance(metrics, list) else [], 1)
    ]
    result.extend(
        f"{sid}-node-{beat_index:02d}-{index:02d}"
        for index, _ in enumerate(nodes if isinstance(nodes, list) else [], 1)
    )
    return result or [f"{sid}-card-{beat_index:03d}"]


def _financial_bound_beats(production: dict[str, Any]) -> set[str]:
    rows = production.get("financialBindings", [])
    if not isinstance(rows, list):
        return set()
    return {
        row.get("sourceBeatId")
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("sourceBeatId"), str)
    }


def _validate_numeric(
    beat: dict[str, Any], *, beat_id: str, template: str, financial_bound: bool
) -> list[str]:
    if financial_bound:
        return []
    minimum, maximum = NUMERIC_TEMPLATE_COUNTS[template]
    metrics = beat.get("metrics")
    if not isinstance(metrics, list) or not minimum <= len(metrics) <= maximum:
        return [
            f"{beat_id}: {template} requires {minimum}-{maximum} explicit authored metrics "
            "unless a financial binding owns the Renderer data"
        ]
    errors: list[str] = []
    comparisons: set[str] = set()
    units: set[str] = set()
    for index, metric in enumerate(metrics, 1):
        path = f"{beat_id}.metrics[{index - 1}]"
        if not isinstance(metric, dict):
            errors.append(f"{path}: metric must be an object")
            continue
        numeric = metric.get("numericValue")
        if not isinstance(numeric, (int, float)) or isinstance(numeric, bool):
            errors.append(f"{path}.numericValue: explicit number required for {template}")
        unit = metric.get("unit", "")
        if not isinstance(unit, str):
            errors.append(f"{path}.unit: string required")
        else:
            units.add(unit)
        comparison = metric.get("comparison")
        if not isinstance(comparison, str) or not comparison.strip():
            errors.append(f"{path}.comparison: explicit common comparison basis required")
        else:
            comparisons.add(comparison.strip())
    if len(units) > 1:
        errors.append(f"{beat_id}: {template} requires one aligned unit; found={sorted(units)}")
    if len(comparisons) > 1:
        errors.append(
            f"{beat_id}: {template} requires one aligned comparison basis; found={sorted(comparisons)}"
        )
    return errors


def _validate_lanes(beat: dict[str, Any], *, beat_id: str, template: str) -> list[str]:
    labels = beat.get("laneLabels")
    if not isinstance(labels, list) or len(labels) != 2 or not all(
        isinstance(item, str) and item.strip() for item in labels
    ):
        return [f"{beat_id}: {template} requires exactly two explicit laneLabels"]
    viewer = beat.get("viewerTexts", [])
    if not isinstance(viewer, list):
        return [f"{beat_id}: viewerTexts must be an array"]
    errors: list[str] = []
    for label in labels:
        prefix = f"{label.strip()}｜"
        if not any(isinstance(item, str) and item.startswith(prefix) for item in viewer):
            errors.append(
                f"{beat_id}: {template} requires viewer text prefixed with {prefix!r}"
            )
    return errors


def _validate_reaction_timeline(
    beat: dict[str, Any], *, scene_index: int, beat_index: int, beat_id: str
) -> list[str]:
    variant = beat.get("variant")
    expected_precision = REACTION_PRECISION_BY_VARIANT.get(variant)
    if expected_precision is None:
        return [
            f"{beat_id}: event-reaction-timeline requires explicit variant in "
            f"{sorted(REACTION_PRECISION_BY_VARIANT)}"
        ]
    reaction = beat.get("reactionTimeline")
    if not isinstance(reaction, dict):
        return [f"{beat_id}: event-reaction-timeline requires explicit reactionTimeline"]
    errors: list[str] = []
    if reaction.get("precision") != expected_precision:
        errors.append(
            f"{beat_id}: reactionTimeline.precision must be {expected_precision!r} for {variant!r}"
        )
    event_order = reaction.get("eventOrderIds")
    legal_objects = set(_object_ids(scene_index, beat_index, beat))
    if not isinstance(event_order, list) or not event_order or not all(
        isinstance(item, str) and item in legal_objects for item in event_order
    ):
        errors.append(
            f"{beat_id}: reactionTimeline.eventOrderIds must reference authored Beat objects; "
            f"legal={sorted(legal_objects)}"
        )
    series = reaction.get("seriesObjectIds")
    if not isinstance(series, list):
        errors.append(f"{beat_id}: reactionTimeline.seriesObjectIds must be an array")
    elif expected_precision != "verified-intraday-series" and series:
        errors.append(f"{beat_id}: non-series reaction variant must not declare seriesObjectIds")
    elif expected_precision == "verified-intraday-series" and not (
        len(series) >= 2 or isinstance(reaction.get("intradaySeries"), dict) or "reactionBinding" in beat
    ):
        errors.append(
            f"{beat_id}: verified-series requires verified series objects, intradaySeries, or reactionBinding"
        )
    return errors


def validate(authoring: dict[str, Any]) -> list[str]:
    if authoring.get("contractVersion") != "2.0.0":
        return []
    production = authoring.get("production")
    if not isinstance(production, dict):
        return ["$.production: object required"]
    scenes = production.get("scenes")
    if not isinstance(scenes, list):
        return ["$.production.scenes: array required"]
    bound = _financial_bound_beats(production)
    errors: list[str] = []
    for scene_index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            continue
        beats = scene.get("beats", [])
        if not isinstance(beats, list):
            continue
        for beat_index, beat in enumerate(beats, 1):
            if not isinstance(beat, dict):
                continue
            beat_id = f"scene-{scene_index:02d}-beat-{beat_index:03d}"
            template = beat.get("visualTemplate")
            if template == "expected-actual-gap-flow" and beat.get("visualMode") != "expected-actual-gap":
                errors.append(
                    f"{beat_id}: expected-actual-gap-flow requires canonical visualMode 'expected-actual-gap'"
                )
            if template in NUMERIC_TEMPLATE_COUNTS:
                errors.extend(
                    _validate_numeric(
                        beat,
                        beat_id=beat_id,
                        template=template,
                        financial_bound=beat_id in bound,
                    )
                )
            if template in LANE_TEMPLATES:
                errors.extend(_validate_lanes(beat, beat_id=beat_id, template=template))
            if template == "event-reaction-timeline":
                errors.extend(
                    _validate_reaction_timeline(
                        beat,
                        scene_index=scene_index,
                        beat_index=beat_index,
                        beat_id=beat_id,
                    )
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authoring", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    authoring = load(args.authoring)
    errors = validate(authoring)
    result = {
        "contractVersion": "1.0.0",
        "episodeDate": authoring.get("episodeDate"),
        "status": "PASS" if not errors else "FAIL",
        "errorCount": len(errors),
        "errors": errors,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
