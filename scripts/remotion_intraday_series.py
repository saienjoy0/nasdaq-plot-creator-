#!/usr/bin/env python3
"""Attach verified Collector 1-minute series after Renderer 2.4 projection.

The producer projection intentionally stays small and continues to carry the legacy
summary objects used by older renderer revisions. When a reaction binding explicitly
references a normalized Collector intraday-series file, this module copies that
verified series into the already-canonicalized render spec immediately before the
pinned renderer validator runs.

No market meaning is inferred here. The target Beat, source file, release marker and
display timezone must already be explicitly authored in reaction_timeline_bindings.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class IntradaySeriesAttachmentError(ValueError):
    pass


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntradaySeriesAttachmentError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise IntradaySeriesAttachmentError(f"{label} must be an object")
    return value


def _inside(root: Path, relative: str, label: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise IntradaySeriesAttachmentError(f"{label} must be a non-empty path")
    root = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise IntradaySeriesAttachmentError(f"{label} escapes output root: {relative}") from exc
    if not candidate.is_file():
        raise IntradaySeriesAttachmentError(f"{label} does not exist: {relative}")
    return candidate


def _validate_series(series: dict[str, Any], *, path: Path) -> None:
    if series.get("kind") != "intraday":
        raise IntradaySeriesAttachmentError(f"{path}: kind must be intraday")
    if series.get("precision") != "verified-intraday-series":
        raise IntradaySeriesAttachmentError(
            f"{path}: precision must be verified-intraday-series"
        )
    if series.get("resolution") != "1m":
        raise IntradaySeriesAttachmentError(f"{path}: resolution must be 1m")
    for key in ("source", "symbol", "marketDate", "timezone", "providerSurface", "priceBasis"):
        if not isinstance(series.get(key), str) or not series[key].strip():
            raise IntradaySeriesAttachmentError(f"{path}: {key} is required")
    if series.get("session") not in {"regular", "all"}:
        raise IntradaySeriesAttachmentError(f"{path}: session must be regular or all")
    points = series.get("points")
    if not isinstance(points, list) or len(points) < 2:
        raise IntradaySeriesAttachmentError(f"{path}: points must contain at least two rows")
    previous = ""
    for index, point in enumerate(points):
        if not isinstance(point, dict):
            raise IntradaySeriesAttachmentError(f"{path}: points[{index}] must be an object")
        timestamp = point.get("timestamp")
        price = point.get("price")
        if not isinstance(timestamp, str) or not timestamp:
            raise IntradaySeriesAttachmentError(f"{path}: points[{index}].timestamp is required")
        if previous and timestamp <= previous:
            raise IntradaySeriesAttachmentError(
                f"{path}: minute timestamps must be strictly increasing"
            )
        previous = timestamp
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise IntradaySeriesAttachmentError(f"{path}: points[{index}].price must be numeric")


def attach_bound_intraday_series(
    render: dict[str, Any],
    *,
    output_root: Path,
    episode_date: str,
    reaction_bindings_path: Path,
) -> dict[str, Any]:
    """Attach only explicitly bound verified intraday series; otherwise no-op."""
    bindings = _load_json(reaction_bindings_path, "reaction timeline bindings")
    if bindings.get("episodeDate") != episode_date:
        raise IntradaySeriesAttachmentError("reaction timeline bindings episodeDate mismatch")
    rows = bindings.get("bindings")
    if not isinstance(rows, list):
        raise IntradaySeriesAttachmentError("reaction timeline bindings.bindings must be an array")

    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise IntradaySeriesAttachmentError("reaction timeline binding must be an object")
        beat_id = row.get("visualBeatId")
        if isinstance(beat_id, str) and beat_id:
            by_id[beat_id] = row

    attached: list[dict[str, Any]] = []
    for scene in render.get("scenes", []):
        if not isinstance(scene, dict):
            continue
        for beat in scene.get("visualBeats", []):
            if not isinstance(beat, dict):
                continue
            beat_id = beat.get("beatId")
            binding = by_id.get(beat_id) if isinstance(beat_id, str) else None
            if binding is None or "intradaySeriesPath" not in binding:
                continue
            if beat.get("visualTemplate") != "event-reaction-timeline":
                raise IntradaySeriesAttachmentError(
                    f"{beat_id}: intradaySeriesPath requires event-reaction-timeline"
                )
            if binding.get("precision") != "verified-intraday-series":
                raise IntradaySeriesAttachmentError(
                    f"{beat_id}: intradaySeriesPath requires verified-intraday-series"
                )
            config = beat.get("templateConfig")
            if not isinstance(config, dict):
                raise IntradaySeriesAttachmentError(f"{beat_id}: templateConfig missing")
            reaction = config.get("reactionTimeline")
            if not isinstance(reaction, dict) or reaction.get("precision") != "verified-intraday-series":
                raise IntradaySeriesAttachmentError(
                    f"{beat_id}: canonical reactionTimeline is not verified-intraday-series"
                )

            relative_path = binding["intradaySeriesPath"]
            source_path = _inside(output_root, relative_path, f"{beat_id}.intradaySeriesPath")
            series = _load_json(source_path, f"{beat_id} intraday series")
            _validate_series(series, path=source_path)

            event_marker = binding.get("eventMarker")
            if event_marker is not None:
                if not isinstance(event_marker, dict):
                    raise IntradaySeriesAttachmentError(f"{beat_id}.eventMarker must be an object")
                if not isinstance(event_marker.get("timestamp"), str) or not event_marker["timestamp"]:
                    raise IntradaySeriesAttachmentError(f"{beat_id}.eventMarker.timestamp is required")
                if not isinstance(event_marker.get("label"), str) or not event_marker["label"].strip():
                    raise IntradaySeriesAttachmentError(f"{beat_id}.eventMarker.label is required")

            display_timezone = binding.get("displayTimezone")
            if display_timezone is not None and (
                not isinstance(display_timezone, str) or not display_timezone.strip()
            ):
                raise IntradaySeriesAttachmentError(f"{beat_id}.displayTimezone must be non-empty")

            reaction["intradaySeries"] = series
            if event_marker is not None:
                reaction["eventMarker"] = event_marker
            if display_timezone is not None:
                reaction["displayTimezone"] = display_timezone
            attached.append(
                {
                    "sceneId": scene.get("sceneId"),
                    "beatId": beat_id,
                    "symbol": series["symbol"],
                    "pointCount": len(series["points"]),
                    "sourcePath": str(relative_path),
                }
            )

    return {
        "status": "pass",
        "episodeDate": episode_date,
        "attached": attached,
        "attachmentCount": len(attached),
    }
