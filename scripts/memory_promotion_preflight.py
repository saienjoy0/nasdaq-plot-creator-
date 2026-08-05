#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

from memory_promotion_common import (
    CONTRACT_VERSION, APPROVED_STATUSES, ArtifactDigest, PreflightError, digest_file,
    read_json, resolve_repo_path, validate_json_schema, validator_passes,
    extract_episode_date_from_render_spec, ensure_episode_package_matches_date,
    utc_now, _record_expected_hash,
)


def _normalize_validator_report(report: Any) -> Any:
    """Accept the renderer's production-ready camelCase status fields.

    The normalized object is used only for eligibility checks. The original
    validator artifact is still hashed and archived byte-for-byte.
    """
    if not isinstance(report, Mapping):
        return report
    normalized = dict(report)
    aliases = {
        "validatorStatus": "validator_status",
        "overallStatus": "overall_status",
        "allPassed": "all_passed",
    }
    for source_key, target_key in aliases.items():
        if target_key not in normalized and source_key in normalized:
            normalized[target_key] = normalized[source_key]
    return normalized


def _extract_renderer_episode_date(spec: Any) -> str | None:
    """Read the date from both memory-native and renderer-native layouts."""
    direct = extract_episode_date_from_render_spec(spec)
    if direct is not None:
        return direct
    if not isinstance(spec, Mapping):
        return None
    episode = spec.get("episode")
    if isinstance(episode, Mapping):
        for key in ("targetDate", "episodeDate", "productionDate"):
            value = episode.get(key)
            if isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
                return value
    for key in ("targetDate", "episodeDate", "productionDate"):
        value = spec.get(key)
        if isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            return value
    return None


def source_preflight(
    record_path: Path,
    repo_root: Path,
    contracts_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Path]]:
    repo_root = repo_root.resolve()
    record_path = resolve_repo_path(str(record_path), repo_root)
    record = read_json(record_path)
    validate_json_schema(record, contracts_dir / "publication_record.schema.json")

    approval = record.get("approval", {})
    status = approval.get("status") if isinstance(approval, Mapping) else None
    if status not in APPROVED_STATUSES:
        raise PreflightError("publication record must be approved_preview or published")

    source_paths = record.get("source_paths")
    if not isinstance(source_paths, Mapping):
        raise PreflightError("publication record source_paths must be an object")

    resolved: dict[str, Path] = {}
    digests: dict[str, ArtifactDigest] = {}
    for key in ("episode_package", "render_spec", "validator_report"):
        raw = source_paths.get(key)
        if not isinstance(raw, str) or not raw:
            raise PreflightError(f"missing source path: {key}")
        path = resolve_repo_path(raw, repo_root)
        resolved[key] = path
        digests[key] = digest_file(path, repo_root)
        expected = _record_expected_hash(record, key)
        if expected is not None and expected != digests[key].sha256:
            raise PreflightError(
                f"source SHA-256 mismatch for {key}: expected {expected}, got {digests[key].sha256}"
            )

    validator_report = _normalize_validator_report(read_json(resolved["validator_report"]))
    if not validator_passes(validator_report):
        raise PreflightError("validator report does not contain a formal PASS result")

    render_spec = read_json(resolved["render_spec"])
    render_date = _extract_renderer_episode_date(render_spec)
    if render_date is not None and render_date != record["episode_date"]:
        raise PreflightError(
            f"render spec date {render_date} does not match publication date {record['episode_date']}"
        )
    ensure_episode_package_matches_date(
        resolved["episode_package"].read_text(encoding="utf-8"), record["episode_date"]
    )

    record_digest = digest_file(record_path, repo_root)
    report = {
        "contract_version": CONTRACT_VERSION,
        "status": "pass",
        "episode_date": record["episode_date"],
        "approval_status": status,
        "publication_record": record_digest.to_json(),
        "source_artifacts": {key: value.to_json() for key, value in digests.items()},
        "checks": {
            "publication_schema": "pass",
            "approval": "pass",
            "paths_within_repository": "pass",
            "artifacts_present": "pass",
            "declared_hashes": "pass",
            "validator_report": "pass",
            "episode_date_consistency": "pass",
        },
        "generated_at": utc_now(),
    }
    return record, report, resolved
