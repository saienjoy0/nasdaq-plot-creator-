#!/usr/bin/env python3
"""Freeze an explicit Final authorization for the exact human-approved Preview.

This is a control-plane artifact only. It does not render Final. It proves that:
- the user explicitly requested Final;
- the actual Preview SHA approved by the human review matches the Preview delivery manifest;
- that Preview was rendered from the exact current render_spec SHA;
- Visual Intelligence v1.2 remained PASS for that production package.

The resulting JSON intentionally keeps the legacy approval fields
`episode_date`, `status`, and `final_requested` so the existing forward-only
request-final state transition can use it as its approval evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import jsonschema


class FinalAuthorizationError(ValueError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FinalAuthorizationError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise FinalAuthorizationError(f"{label} root must be an object")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_file(path: Path, label: str) -> Path:
    path = path.resolve()
    if not path.is_file():
        raise FinalAuthorizationError(f"{label} missing: {path}")
    return path


def _delivery_episode(value: dict[str, Any]) -> str | None:
    episode = value.get("episodeId")
    if isinstance(episode, str):
        return episode
    episode = value.get("episodeDate")
    return episode if isinstance(episode, str) else None


def build_authorization(
    *,
    root: Path,
    date: str,
    preview_run_id: str,
    preview_delivery_manifest: Path,
    human_preview_review: Path,
    explicit_final: bool,
) -> dict[str, Any]:
    if not explicit_final:
        raise FinalAuthorizationError("Final authorization requires --explicit-final")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise FinalAuthorizationError("date must be YYYY-MM-DD")
    if not re.fullmatch(r"[0-9]+", preview_run_id):
        raise FinalAuthorizationError("preview run ID must be numeric")

    root = root.resolve()
    spec = require_file(root / "render-specs" / date / "render_spec.json", "render_spec")
    state_path = require_file(root / "working" / date / "production_state.json", "production state")
    package = require_file(
        root / "working" / date / "visual-intelligence" / "visual_intelligence_package.json",
        "Visual Intelligence package",
    )
    vi_validation = require_file(
        root / "verification" / date / "visual_intelligence_validation.json",
        "Visual Intelligence validation",
    )
    review_path = require_file(human_preview_review, "human Preview review")
    delivery_path = require_file(preview_delivery_manifest, "Preview delivery manifest")

    state = load_json(state_path, "production state")
    if state.get("episode_date") != date or state.get("current_state") != "user_preview_approved":
        raise FinalAuthorizationError(
            "Final authorization requires the forward-only state user_preview_approved"
        )

    review = load_json(review_path, "human Preview review")
    if review.get("contractVersion") != "1.0.0":
        raise FinalAuthorizationError("human Preview review contractVersion mismatch")
    if review.get("episodeDate") != date or review.get("status") != "approved":
        raise FinalAuthorizationError("human Preview review must approve the same episode")
    preview_sha = review.get("previewSha256")
    if not isinstance(preview_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", preview_sha):
        raise FinalAuthorizationError("human Preview review previewSha256 is invalid")

    delivery = load_json(delivery_path, "Preview delivery manifest")
    if delivery.get("status") not in {"preview-delivery-ready", "handoff-preview-delivery-ready"}:
        raise FinalAuthorizationError("Preview delivery manifest is not delivery-ready")
    if _delivery_episode(delivery) != date:
        raise FinalAuthorizationError("Preview delivery manifest episode mismatch")
    if str(delivery.get("runId")) != preview_run_id:
        raise FinalAuthorizationError("Preview delivery manifest runId mismatch")
    if delivery.get("previewSha256") != preview_sha:
        raise FinalAuthorizationError("human approval does not match the actual Preview SHA")

    spec_sha = sha256_file(spec)
    if delivery.get("specSha256") != spec_sha:
        raise FinalAuthorizationError(
            "approved Preview was not rendered from the current render_spec SHA"
        )

    vi = load_json(vi_validation, "Visual Intelligence validation")
    if vi.get("status") != "PASS" or vi.get("episodeDate") != date:
        raise FinalAuthorizationError("Visual Intelligence validation must PASS for the same episode")
    if vi.get("packageSha256") != sha256_file(package):
        raise FinalAuthorizationError("Visual Intelligence validation/package SHA mismatch")

    review_rel = review_path.relative_to(root).as_posix()
    expected_review_path = f"verification/{date}/human_preview_review.json"
    if review_rel != expected_review_path:
        raise FinalAuthorizationError(
            f"human Preview review must use canonical path {expected_review_path}"
        )

    authorization = {
        "contractVersion": "1.0.0",
        "episode_date": date,
        "status": "approved",
        "final_requested": True,
        "renderSpecSha256": spec_sha,
        "previewRunId": preview_run_id,
        "previewSha256": preview_sha,
        "previewDeliveryManifestSha256": sha256_file(delivery_path),
        "humanPreviewReviewPath": review_rel,
        "humanPreviewReviewSha256": sha256_file(review_path),
        "visualIntelligencePackageSha256": sha256_file(package),
        "visualIntelligenceValidationSha256": sha256_file(vi_validation),
    }

    schema = load_json(
        require_file(root / "contracts/final_render_authorization.schema.json", "Final authorization schema"),
        "Final authorization schema",
    )
    try:
        jsonschema.Draft202012Validator(schema).validate(authorization)
    except jsonschema.ValidationError as exc:
        raise FinalAuthorizationError(f"Final authorization schema failure: {exc.message}") from exc
    return authorization


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--date", required=True)
    parser.add_argument("--preview-run-id", required=True)
    parser.add_argument("--preview-delivery-manifest", required=True, type=Path)
    parser.add_argument("--human-preview-review", type=Path)
    parser.add_argument("--explicit-final", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    review = args.human_preview_review or (
        root / "verification" / args.date / "human_preview_review.json"
    )
    output = args.output or (
        root / "verification" / args.date / "final_render_authorization.json"
    )
    try:
        result = build_authorization(
            root=root,
            date=args.date,
            preview_run_id=args.preview_run_id,
            preview_delivery_manifest=args.preview_delivery_manifest,
            human_preview_review=review,
            explicit_final=args.explicit_final,
        )
    except FinalAuthorizationError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "output": str(output), **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
