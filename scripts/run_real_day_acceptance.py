#!/usr/bin/env python3
"""Validate one new real-day Nasdaq Cafe preview path without running final."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


class AcceptanceError(ValueError):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_file(root: Path, value: str | Path, label: str) -> Path:
    path = Path(value)
    resolved = path.resolve() if path.is_absolute() else (root.resolve() / path).resolve()
    root = root.resolve()
    if resolved != root and root not in resolved.parents:
        raise AcceptanceError(f"{label}: path escapes root: {value}")
    if not resolved.is_file():
        raise AcceptanceError(f"{label}: file does not exist: {value}")
    return resolved


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AcceptanceError(f"{label}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise AcceptanceError(f"{label}: top-level JSON must be an object")
    return value


def verify_handoff(bundle_root: Path, manifest_path: Path, date: str) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest = load_json(manifest_path, "handoff manifest")
    if manifest.get("episode_date") != date:
        raise AcceptanceError("handoff episode_date mismatch")
    if date == "2026-07-31":
        raise AcceptanceError("real-day acceptance may not reuse the 2026-07-31 seed")
    if manifest.get("mode") != "preview":
        raise AcceptanceError("real-day acceptance requires a preview handoff")
    if manifest.get("final_authorized") is not False:
        raise AcceptanceError("preview handoff must have final_authorized=false")
    if manifest.get("validation", {}).get("production_package") != "pass":
        raise AcceptanceError("handoff production package must pass")
    if manifest.get("validation", {}).get("unresolved_states") != 0:
        raise AcceptanceError("handoff unresolved states must be zero")
    bundle_id = manifest.get("bundle_id")
    if not isinstance(bundle_id, str) or len(bundle_id) != 64:
        raise AcceptanceError("handoff bundle_id is invalid")
    file_index: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(manifest.get("files", [])):
        if not isinstance(item, dict):
            raise AcceptanceError(f"handoff files[{index}] must be an object")
        destination = item.get("destination_path")
        if not isinstance(destination, str):
            raise AcceptanceError(f"handoff files[{index}].destination_path is required")
        path = safe_file(bundle_root, destination, f"bundle file {destination}")
        if sha256_file(path) != item.get("sha256"):
            raise AcceptanceError(f"bundle file SHA mismatch: {destination}")
        if path.stat().st_size != item.get("size"):
            raise AcceptanceError(f"bundle file size mismatch: {destination}")
        role = item.get("role")
        if isinstance(role, str):
            if role in file_index and role != "asset":
                raise AcceptanceError(f"duplicate non-asset handoff role: {role}")
            if role != "asset":
                file_index[role] = item
    for role in ("render_spec", "preflight", "consistency_report", "episode_package"):
        if role not in file_index:
            raise AcceptanceError(f"handoff lacks required acceptance role: {role}")
    return manifest, file_index


def validate_user_review(
    record: dict[str, Any] | None,
    date: str,
    bundle_id: str,
    preview_sha256: str,
) -> dict[str, Any]:
    """Normalize Preview review while giving approval one canonical authority.

    Historical bundle-scoped pending/rejected review records remain readable for
    diagnostics. An approval, however, must use the canonical Human Preview Review
    contract produced from the exact MP4 bytes by write_human_preview_review.py.
    This prevents a bundle-only review from advancing production state without
    proving which Preview the user actually approved.
    """
    if record is None:
        return {"status": "pending", "reviewed_at": None, "notes": ""}

    if "contractVersion" in record or "previewSha256" in record:
        required = {"contractVersion", "episodeDate", "previewSha256", "status", "reviewedAt"}
        if set(record) != required:
            raise AcceptanceError("canonical human Preview review fields mismatch")
        if record.get("contractVersion") != "1.0.0":
            raise AcceptanceError("canonical human Preview review contractVersion mismatch")
        if record.get("episodeDate") != date:
            raise AcceptanceError("canonical human Preview review episodeDate mismatch")
        if record.get("status") != "approved":
            raise AcceptanceError("canonical human Preview review status must be approved")
        if record.get("previewSha256") != preview_sha256:
            raise AcceptanceError("canonical human Preview review does not match actual Preview SHA")
        if not isinstance(record.get("reviewedAt"), str) or not record["reviewedAt"].strip():
            raise AcceptanceError("canonical human Preview review reviewedAt is required")
        return {
            "status": "approved",
            "reviewed_at": record["reviewedAt"],
            "notes": "",
            "preview_sha256": preview_sha256,
            "authority": "human-preview-review/1.0.0",
        }

    if record.get("episode_date") != date:
        raise AcceptanceError("user review episode_date mismatch")
    if record.get("bundle_id") != bundle_id:
        raise AcceptanceError("user review bundle_id mismatch")
    status = record.get("status")
    if status not in {"pending", "approved", "rejected"}:
        raise AcceptanceError("user review status must be pending, approved, or rejected")
    if status == "approved":
        raise AcceptanceError(
            "approved Preview review must use canonical human_preview_review.json bound to the actual MP4 SHA"
        )
    if status == "rejected" and not record.get("reviewed_at"):
        raise AcceptanceError("completed user review requires reviewed_at")
    return {"status": status, "reviewed_at": record.get("reviewed_at"), "notes": str(record.get("notes", ""))}


def validate_acceptance(*, episode_date: str, daily_source_root: Path, daily_source_path: Path, bundle_root: Path, handoff_manifest_path: Path, renderer_artifact_root: Path, technical_report_path: Path, user_review_path: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if episode_date == "2026-07-31":
        raise AcceptanceError("real-day acceptance may not reuse the 2026-07-31 seed")
    daily_source = safe_file(daily_source_root, daily_source_path, "daily source package")
    if episode_date not in daily_source.name:
        raise AcceptanceError("daily source filename must include episode_date")
    if daily_source.stat().st_size == 0:
        raise AcceptanceError("daily source package must be non-empty")

    manifest_path = safe_file(bundle_root, handoff_manifest_path, "handoff manifest")
    bundle_directory = manifest_path.parent
    manifest, file_index = verify_handoff(bundle_directory, manifest_path, episode_date)

    technical_path = safe_file(renderer_artifact_root, technical_report_path, "renderer technical report")
    technical = load_json(technical_path, "renderer technical report")
    if technical.get("status") != "pass":
        raise AcceptanceError("renderer technical report status must be pass")
    if technical.get("episode_date") != episode_date:
        raise AcceptanceError("renderer technical report episode_date mismatch")
    expected_renderer = manifest.get("renderer", {}).get("expected_base_commit")
    if technical.get("renderer_commit") != expected_renderer:
        raise AcceptanceError("renderer commit mismatch")
    if technical.get("final_render_executed") is not False:
        raise AcceptanceError("real-day preview acceptance forbids final rendering")

    render_item = file_index["render_spec"]
    if technical.get("render_spec_sha256") != render_item.get("sha256"):
        raise AcceptanceError("renderer technical report render_spec SHA mismatch")
    if technical.get("technical_checks") != "pass":
        raise AcceptanceError("renderer technical checks must pass")

    preview_ref = technical.get("preview_artifact")
    if not isinstance(preview_ref, str) or not preview_ref:
        raise AcceptanceError("renderer technical report must identify preview_artifact")
    preview = safe_file(renderer_artifact_root, preview_ref, "preview artifact")
    if preview.stat().st_size <= 0:
        raise AcceptanceError("preview artifact must be non-empty")
    preview_sha = sha256_file(preview)
    declared_preview_sha = technical.get("preview_sha256")
    if declared_preview_sha is not None and declared_preview_sha != preview_sha:
        raise AcceptanceError("preview artifact SHA mismatch")

    review_record = load_json(safe_file(renderer_artifact_root, user_review_path, "user review"), "user review") if user_review_path else None
    user_review = validate_user_review(
        review_record,
        episode_date,
        manifest["bundle_id"],
        preview_sha,
    )
    if user_review["status"] == "approved":
        mvp_status = "passed"
    elif user_review["status"] == "rejected":
        mvp_status = "failed"
        warnings.append("preview was technically valid but rejected by user visual review")
    else:
        mvp_status = "preview_ready_user_review_pending"

    return {
        "contract_version": "1.0.0",
        "episode_date": episode_date,
        "daily_source": {"path": daily_source.relative_to(daily_source_root.resolve()).as_posix(), "sha256": sha256_file(daily_source)},
        "handoff": {"bundle_id": manifest["bundle_id"], "manifest_path": manifest_path.relative_to(bundle_root.resolve()).as_posix(), "manifest_sha256": sha256_file(manifest_path)},
        "renderer": {"expected_commit": expected_renderer, "observed_commit": technical["renderer_commit"], "technical_report_sha256": sha256_file(technical_path)},
        "preview": {"artifact_path": preview.relative_to(renderer_artifact_root.resolve()).as_posix(), "sha256": preview_sha, "size": preview.stat().st_size},
        "user_review": user_review,
        "validation": {"status": "pass" if not errors else "fail", "errors": errors, "warnings": warnings},
        "final_render_executed": False,
        "mvp_status": mvp_status,
    }


def write_report(report: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "acceptance_report.json"
    md_path = output_dir / "acceptance_report.md"
    json_path.write_bytes(canonical_json(report))
    md_path.write_text(
        f"# Real-Day Acceptance {report['episode_date']}\n\n"
        f"- MVP status: `{report['mvp_status']}`\n"
        f"- Technical validation: `{report['validation']['status']}`\n"
        f"- User review: `{report['user_review']['status']}`\n"
        f"- Final render executed: `false`\n"
        f"- Bundle ID: `{report['handoff']['bundle_id']}`\n"
        f"- Preview SHA-256: `{report['preview']['sha256']}`\n",
        encoding="utf-8",
    )
    return {"json": str(json_path), "markdown": str(md_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-date", required=True)
    parser.add_argument("--daily-source-root", required=True, type=Path)
    parser.add_argument("--daily-source-package", required=True, type=Path)
    parser.add_argument("--bundle-root", required=True, type=Path)
    parser.add_argument("--handoff-manifest", required=True, type=Path)
    parser.add_argument("--renderer-artifact-root", required=True, type=Path)
    parser.add_argument("--technical-report", required=True, type=Path)
    parser.add_argument("--user-review", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = validate_acceptance(
            episode_date=args.episode_date, daily_source_root=args.daily_source_root,
            daily_source_path=args.daily_source_package, bundle_root=args.bundle_root,
            handoff_manifest_path=args.handoff_manifest, renderer_artifact_root=args.renderer_artifact_root,
            technical_report_path=args.technical_report, user_review_path=args.user_review,
        )
        paths = write_report(report, args.output_dir)
        result = {"status": "pass", "mvp_status": report["mvp_status"], "paths": paths}
        code = 0
    except (AcceptanceError, OSError, json.JSONDecodeError) as exc:
        result = {"status": "fail", "errors": [str(exc)]}
        code = 1
    sys.stdout.buffer.write(canonical_json(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
