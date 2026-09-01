#!/usr/bin/env python3
"""Build the Plot-side Current Final authorization bundle for an exact approved Preview.

This is control-plane evidence only. It never renders and it refuses to produce
approval evidence unless the caller supplies an explicit user approval flag.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"[0-9a-f]{64}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


class FinalAuthorizationBundleError(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FinalAuthorizationBundleError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise FinalAuthorizationBundleError(f"{label} must be an object")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build(
    *,
    date: str,
    preview_run_id: int,
    approved_preview_sha256: str,
    preview_identity: Path,
    explicit_user_approval: bool,
    output_root: Path,
) -> dict[str, str]:
    if not explicit_user_approval:
        raise FinalAuthorizationBundleError("explicit user approval is required")
    if not DATE_RE.fullmatch(date):
        raise FinalAuthorizationBundleError("episode date must be YYYY-MM-DD")
    if preview_run_id <= 0:
        raise FinalAuthorizationBundleError("preview_run_id must be positive")
    if not SHA256_RE.fullmatch(approved_preview_sha256):
        raise FinalAuthorizationBundleError("approved Preview SHA must be SHA-256")
    preview_identity = preview_identity.resolve()
    if not preview_identity.is_file():
        raise FinalAuthorizationBundleError(f"Preview identity missing: {preview_identity}")
    identity = load(preview_identity, "Preview identity")
    if identity.get("contractVersion") != "1.0.0" or identity.get("episodeDate") != date:
        raise FinalAuthorizationBundleError("Preview identity contract/date mismatch")
    identity_sha = sha256(preview_identity)

    output_root = output_root.resolve()
    review_path = output_root / "human_preview_review.json"
    authorization_path = output_root / "final_render_authorization.json"
    manifest_path = output_root / "final_authorization_manifest.json"

    review = {
        "contractVersion": "1.0.0",
        "status": "approved",
        "episodeDate": date,
        "previewRunId": preview_run_id,
        "approvedPreviewSha256": approved_preview_sha256,
        "previewIdentitySha256": identity_sha,
    }
    write(review_path, review)
    review_sha = sha256(review_path)

    authorization = {
        "contractVersion": "1.0.0",
        "status": "approved",
        "episodeDate": date,
        "previewRunId": preview_run_id,
        "approvedPreviewSha256": approved_preview_sha256,
        "previewIdentitySha256": identity_sha,
        "humanPreviewReviewSha256": review_sha,
        "finalAuthorized": True,
    }
    write(authorization_path, authorization)
    authorization_sha = sha256(authorization_path)

    manifest = {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "previewRunId": preview_run_id,
        "approvedPreviewSha256": approved_preview_sha256,
        "previewIdentitySha256": identity_sha,
        "humanPreviewReviewSha256": review_sha,
        "plotFinalAuthorizationSha256": authorization_sha,
    }
    write(manifest_path, manifest)

    return {
        "human_review_path": str(review_path),
        "human_review_sha256": review_sha,
        "final_authorization_path": str(authorization_path),
        "final_authorization_sha256": authorization_sha,
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256(manifest_path),
        "preview_identity_sha256": identity_sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--preview-run-id", required=True, type=int)
    parser.add_argument("--approved-preview-sha256", required=True)
    parser.add_argument("--preview-identity", required=True, type=Path)
    parser.add_argument("--explicit-user-approval", action="store_true")
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build(
            date=args.date,
            preview_run_id=args.preview_run_id,
            approved_preview_sha256=args.approved_preview_sha256,
            preview_identity=args.preview_identity,
            explicit_user_approval=args.explicit_user_approval,
            output_root=args.output_root,
        )
    except FinalAuthorizationBundleError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "PASS", **result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
