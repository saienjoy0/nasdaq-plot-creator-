#!/usr/bin/env python3
"""Safe two-phase promotion for approved NASDAQ Cafe episode memory.

This module is intentionally deterministic and does not call an LLM.  Planning
builds a complete staged tree without touching ``editorial-memory``.  Applying
revalidates every source and destination precondition, then performs a
rollback-capable transaction and (by default) one Git commit.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

CONTRACT_VERSION = "2.0.0"
APPROVED_STATUSES = {"approved_preview", "published"}
CLAIM_TRANSITIONS: dict[str, set[str]] = {
    "unknown": {"active", "invalidated"},
    "active": {"strengthened", "weakened", "resolved", "invalidated"},
    "strengthened": {"strengthened", "weakened", "resolved", "invalidated"},
    "weakened": {"strengthened", "weakened", "resolved", "invalidated"},
    "resolved": {"resolved"},
    "invalidated": {"invalidated"},
}
CONFIDENCE_ORDER = {"unknown": 0, "low": 1, "medium": 2, "high": 3}
REVISION_RE = re.compile(r"^v(?!000)([0-9]{3})$")
PASS_VALUES = {"pass", "passed", "success", "succeeded", "ok", "valid"}


class PromotionError(RuntimeError):
    """Base class for safe-promotion failures."""


class PreflightError(PromotionError):
    """Raised when source materials are not eligible for promotion."""


class ConflictError(PromotionError):
    """Raised when a blocking memory conflict exists."""


class StalePlanError(PromotionError):
    """Raised when a plan no longer matches source or memory state."""


@dataclass(frozen=True)
class ArtifactDigest:
    path: str
    sha256: str
    bytes: int

    def to_json(self) -> dict[str, Any]:
        return {"path": self.path, "sha256": self.sha256, "bytes": self.bytes}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest_file(path: Path, repo_root: Path) -> ArtifactDigest:
    stat = path.stat()
    if not path.is_file() or stat.st_size <= 0:
        raise PreflightError(f"source artifact must be a non-empty file: {path}")
    return ArtifactDigest(
        path=repo_relative(path, repo_root),
        sha256=sha256_file(path),
        bytes=stat.st_size,
    )


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise PreflightError(f"path is outside repository: {path}") from exc


def resolve_repo_path(raw: str, repo_root: Path, *, must_exist: bool = True) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise PreflightError(f"path traversal or repository-external path rejected: {raw}") from exc
    if must_exist and not resolved.exists():
        raise PreflightError(f"required source artifact does not exist: {raw}")
    return resolved


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreflightError(f"invalid JSON file: {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(value), encoding="utf-8")


def validate_json_schema(instance: Any, schema_path: Path) -> None:
    try:
        import jsonschema  # type: ignore
    except ImportError as exc:
        raise PreflightError("jsonschema is required for memory promotion") from exc
    schema = read_json(schema_path)
    try:
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(instance)
    except jsonschema.ValidationError as exc:  # type: ignore[attr-defined]
        location = "/".join(str(item) for item in exc.absolute_path) or "<root>"
        raise PreflightError(f"schema validation failed at {location}: {exc.message}") from exc


def validator_passes(report: Any) -> bool:
    if not isinstance(report, Mapping):
        return False
    for key in ("status", "result", "conclusion", "overall_status", "validator_status"):
        value = report.get(key)
        if isinstance(value, str) and value.strip().lower() in PASS_VALUES:
            return True
    for key in ("valid", "passed", "success", "all_passed"):
        if report.get(key) is True:
            return True
    summary = report.get("summary")
    if isinstance(summary, Mapping):
        return validator_passes(summary)
    return False


def extract_episode_date_from_render_spec(spec: Any) -> str | None:
    if not isinstance(spec, Mapping):
        return None
    for key in ("episode_date", "date", "production_date"):
        value = spec.get(key)
        if isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            return value
    metadata = spec.get("metadata")
    if isinstance(metadata, Mapping):
        return extract_episode_date_from_render_spec(metadata)
    return None


def ensure_episode_package_matches_date(text: str, episode_date: str) -> None:
    if episode_date not in text:
        raise PreflightError(
            f"episode package does not contain target episode date {episode_date}; "
            "date consistency cannot be confirmed"
        )


def _record_expected_hash(record: Mapping[str, Any], key: str) -> str | None:
    hashes = record.get("source_hashes")
    if not isinstance(hashes, Mapping):
        return None
    raw = hashes.get(key)
    if isinstance(raw, str):
        return raw
    if isinstance(raw, Mapping) and isinstance(raw.get("sha256"), str):
        return str(raw["sha256"])
    return None


def file_sha_or_none(path: Path) -> str | None:
    return sha256_file(path) if path.is_file() else None


def next_revision(
    record: Mapping[str, Any],
    memory_root: Path,
    source_fingerprint: str,
) -> tuple[str, str | None, bool, dict[str, Any] | None]:
    episode_date = str(record["episode_date"])
    episode_root = memory_root / "episodes" / episode_date
    index_path = episode_root / "index.json"
    requested = record.get("revision")
    requested_revision = requested if isinstance(requested, str) else None
    index = read_json(index_path) if index_path.exists() else None

    if index is None:
        if requested_revision not in (None, "v001"):
            raise ConflictError("first archive revision must be v001")
        return "v001", None, False, None

    if not isinstance(index, Mapping):
        raise ConflictError(f"invalid episode index: {index_path}")
    current = index.get("current_revision")
    if not isinstance(current, str) or not REVISION_RE.fullmatch(current):
        raise ConflictError(f"invalid current_revision in {index_path}")

    current_provenance_path = episode_root / "revisions" / current / "provenance.json"
    current_provenance = read_json(current_provenance_path) if current_provenance_path.exists() else None
    if isinstance(current_provenance, Mapping) and current_provenance.get("source_fingerprint") == source_fingerprint:
        return current, current, True, dict(index)

    expected_number = int(REVISION_RE.fullmatch(current).group(1)) + 1  # type: ignore[union-attr]
    expected_revision = f"v{expected_number:03d}"
    correction_reason = record.get("correction_reason")
    supersedes = record.get("supersedes_revision")
    if requested_revision is None:
        raise ConflictError(
            "same episode date has different content; explicit revision, correction_reason, "
            "and supersedes_revision are required"
        )
    if requested_revision != expected_revision:
        raise ConflictError(f"next revision must be {expected_revision}, got {requested_revision}")
    if not isinstance(correction_reason, str) or not correction_reason.strip():
        raise ConflictError("correction_reason is required for a new revision")
    if supersedes != current:
        raise ConflictError(f"supersedes_revision must be current revision {current}")
    return requested_revision, current, False, dict(index)


def bullets(items: Iterable[str]) -> str:
    materialized = [str(item) for item in items]
    return "\n".join(f"- {item}" for item in materialized) if materialized else "- なし"


def episode_summary_markdown(record: Mapping[str, Any], revision: str) -> str:
    hypothesis = record["central_hypothesis"]
    return f"""# {record['episode_date']} {revision}｜{record['title']}

## 主役

{record['main_story']}

## ストーリーの背骨

{record['story_spine']}

## 中心仮説

- 仮説：{hypothesis['text']}
- 確信度：{hypothesis['confidence']}

## 重要な反対材料

{bullets(record.get('contrary_evidence', []))}

## 次に見る点

{bullets(record.get('watch_next', []))}
"""


def daily_markdown(record: Mapping[str, Any], revision: str, provenance_path: str) -> str:
    return episode_summary_markdown(record, revision) + f"""
## 記憶参照

- Episode revision: `{record['episode_date']}/{revision}`
- Provenance: `{provenance_path}`
- Approval: `{record['approval']['status']}` at `{record['approval']['approved_at']}`
"""


def load_json_or(path: Path, default: Any) -> Any:
    return read_json(path) if path.exists() else copy.deepcopy(default)


def build_source_fingerprint(record_digest: ArtifactDigest, artifacts: Mapping[str, Any]) -> str:
    payload = {
        "publication_record": record_digest.sha256,
        "source_artifacts": {key: value["sha256"] for key, value in artifacts.items()},
    }
    return sha256_bytes(canonical_json_bytes(payload))


def staged_operation(
    repo_root: Path,
    relative_path: str,
    data: bytes,
    action_hint: str,
    target_type: str,
    target_id: str,
    provenance_paths: list[str],
) -> dict[str, Any]:
    target = repo_root / relative_path
    before = file_sha_or_none(target)
    after = sha256_bytes(data)
    if before == after:
        action = "noop"
    elif before is None:
        action = "create"
    else:
        action = action_hint
    return {
        "operation_id": "op-" + hashlib.sha256(relative_path.encode("utf-8")).hexdigest()[:16],
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "path": relative_path,
        "before_sha256": before,
        "after_sha256": after,
        "bytes": len(data),
        "reason": "safe approved-memory promotion",
        "provenance_paths": provenance_paths,
    }


def plan_digest(plan: Mapping[str, Any]) -> str:
    payload = {key: copy.deepcopy(value) for key, value in plan.items() if key not in {"plan_digest", "generated_at"}}
    # Avoid a circular dependency: provenance stores the plan digest, while the
    # provenance file hash is itself an operation after-hash. Staged integrity
    # is checked independently at apply time, so the digest commits to paths,
    # actions and before-state but deliberately excludes staged byte hashes.
    operations = payload.get("operations")
    if isinstance(operations, list):
        for operation in operations:
            if isinstance(operation, dict):
                operation.pop("after_sha256", None)
                operation.pop("bytes", None)
    return sha256_bytes(canonical_json_bytes(payload))


