#!/usr/bin/env python3
"""Bind lineage-verified intraday evidence to Visual Intelligence Beat config.

The source registry decides *which* local market-data evidence a Beat cites. The
Research Evidence Supplement Manifest decides *which exact bytes* are approved.
This module only exposes already-approved verified 1-minute evidence to Renderer
Candidate Builder; it never invents prices, fills unavailable symbols, or changes
narration/viewer text.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import zlib
from pathlib import Path
from typing import Any


class IntradayEvidenceBindingError(ValueError):
    pass


def _load_json_object_bytes(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntradayEvidenceBindingError(f"{label}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise IntradayEvidenceBindingError(f"{label}: JSON root must be object")
    return value


def _approved_evidence_sha(repo_root: Path, date: str) -> dict[str, str]:
    manifest_path = repo_root / "research" / date / "research_evidence_supplement_manifest.json"
    if not manifest_path.is_file():
        return {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntradayEvidenceBindingError(f"supplement manifest invalid: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("episodeDate") != date:
        raise IntradayEvidenceBindingError("supplement manifest episodeDate mismatch")
    approved: dict[str, str] = {}
    for wave in manifest.get("waves", []):
        if not isinstance(wave, dict):
            continue
        for item in wave.get("evidenceFiles", []):
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            sha = item.get("sha256")
            if isinstance(path, str) and isinstance(sha, str):
                approved[path] = sha
    return approved


def _read_evidence_bytes(repo_root: Path, reference: str, expected_sha: str) -> bytes:
    relative = Path(reference)
    if relative.is_absolute() or ".." in relative.parts:
        raise IntradayEvidenceBindingError(f"unsafe evidence reference: {reference}")
    raw_path = repo_root / relative
    if raw_path.is_file():
        raw = raw_path.read_bytes()
    else:
        packed_path = Path(str(raw_path) + ".zlib.b64")
        if not packed_path.is_file():
            raise IntradayEvidenceBindingError(f"approved evidence bytes missing: {reference}")
        try:
            raw = zlib.decompress(
                base64.b64decode(packed_path.read_text(encoding="ascii").strip(), validate=True)
            )
        except (OSError, ValueError, zlib.error) as exc:
            raise IntradayEvidenceBindingError(f"packed evidence invalid: {reference}: {exc}") from exc
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != expected_sha:
        raise IntradayEvidenceBindingError(
            f"evidence SHA mismatch: {reference}: expected {expected_sha}, got {actual_sha}"
        )
    return raw


def _validate_intraday_series(value: dict[str, Any], *, reference: str) -> None:
    required = {
        "source", "kind", "symbol", "marketDate", "timezone", "session", "resolution",
        "precision", "providerSurface", "priceBasis", "points",
    }
    missing = sorted(required - set(value))
    if missing:
        raise IntradayEvidenceBindingError(f"{reference}: intraday evidence missing {missing}")
    if value.get("kind") != "intraday" or value.get("resolution") != "1m":
        raise IntradayEvidenceBindingError(f"{reference}: only 1m intraday evidence is supported")
    if value.get("precision") != "verified-intraday-series":
        raise IntradayEvidenceBindingError(f"{reference}: evidence is not verified-intraday-series")
    points = value.get("points")
    if not isinstance(points, list) or not 2 <= len(points) <= 2000:
        raise IntradayEvidenceBindingError(f"{reference}: intraday points must contain 2..2000 rows")
    previous = None
    for index, point in enumerate(points):
        if not isinstance(point, dict):
            raise IntradayEvidenceBindingError(f"{reference}: point {index} must be object")
        timestamp = point.get("timestamp")
        price = point.get("price")
        if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
            raise IntradayEvidenceBindingError(f"{reference}: point {index} timestamp must be UTC Z")
        if not isinstance(price, (int, float)):
            raise IntradayEvidenceBindingError(f"{reference}: point {index} price missing")
        if previous is not None and timestamp <= previous:
            raise IntradayEvidenceBindingError(f"{reference}: timestamps must be strictly increasing")
        previous = timestamp


def bind_verified_intraday_evidence(
    render_spec: dict[str, Any], *, repo_root: Path, date: str
) -> dict[str, Any]:
    """Return a copy with verified intraday reactionTimeline configs where cited."""
    projected = copy.deepcopy(render_spec)
    approved = _approved_evidence_sha(repo_root, date)
    if not approved:
        return projected
    sources = {
        item.get("sourceId"): item
        for item in projected.get("sources", [])
        if isinstance(item, dict) and isinstance(item.get("sourceId"), str)
    }
    cache: dict[str, dict[str, Any]] = {}
    for scene in projected.get("scenes", []):
        if not isinstance(scene, dict):
            continue
        for beat in scene.get("visualBeats", []):
            if not isinstance(beat, dict):
                continue
            config = beat.get("templateConfig")
            if not isinstance(config, dict) or config.get("reactionTimeline") is not None:
                continue
            selected = beat.get("objectIds")
            if not isinstance(selected, list) or not selected:
                continue
            series = None
            reference = None
            for source_id in beat.get("evidenceSourceIds", []):
                source = sources.get(source_id)
                if not isinstance(source, dict) or source.get("sourceType") != "market-data":
                    continue
                candidate_reference = source.get("reference")
                if not isinstance(candidate_reference, str):
                    continue
                expected_sha = approved.get(candidate_reference)
                if expected_sha is None:
                    continue
                if candidate_reference not in cache:
                    raw = _read_evidence_bytes(repo_root, candidate_reference, expected_sha)
                    value = _load_json_object_bytes(raw, candidate_reference)
                    _validate_intraday_series(value, reference=candidate_reference)
                    cache[candidate_reference] = value
                series = cache[candidate_reference]
                reference = candidate_reference
                break
            if series is None:
                continue
            config["reactionTimeline"] = {
                "precision": "verified-intraday-series",
                "eventOrderIds": list(selected),
                "seriesObjectIds": [],
                "intradaySeries": copy.deepcopy(series),
                "displayTimezone": "America/New_York",
            }
            # Keep the authored template/variant untouched. Candidate Builder will use
            # this verified config only when it constructs a time-series candidate.
            beat.setdefault("financialVisualTrace", {})
            trace = beat.get("financialVisualTrace")
            if isinstance(trace, dict):
                trace.setdefault("intradayEvidenceReference", reference)
    return projected
