#!/usr/bin/env python3
"""Build Current Final Request V2.1 from the exact approved Preview lineage.

This builder never renders. It is fail-closed and requires --explicit-final, a
three-file Plot Final authorization bundle, the exact Renderer Preview identity,
and the immutable Plot authorization Artifact identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"[0-9a-f]{64}")
COMMIT_RE = re.compile(r"[0-9a-f]{40}")
SAFE_NAME_RE = re.compile(r"[A-Za-z0-9._-]+")


class FinalRequestError(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FinalRequestError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise FinalRequestError(f"{label} must be an object")
    return value


def require_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise FinalRequestError(f"{label} must be SHA-256")
    return value


def same(value: dict[str, Any], key: str, expected: Any, label: str) -> None:
    if value.get(key) != expected:
        raise FinalRequestError(f"{label} {key} mismatch")


def final_fingerprint(*, preview_identity_sha: str, preview_sha: str, authorization_sha: str, renderer_commit: str) -> str:
    payload = "\n".join((preview_identity_sha, preview_sha, authorization_sha, renderer_commit)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_authorization_bundle(
    *,
    date: str,
    preview_run_id: int,
    approved_preview_sha256: str,
    preview_identity_sha: str,
    human_review: Path,
    final_authorization: Path,
    authorization_manifest: Path,
) -> tuple[str, str, str]:
    review = load(human_review, "Human Preview review")
    authorization = load(final_authorization, "Final authorization")
    manifest = load(authorization_manifest, "Final authorization manifest")
    review_required = {
        "contractVersion", "status", "episodeDate", "previewRunId",
        "approvedPreviewSha256", "previewIdentitySha256",
    }
    authorization_required = {
        "contractVersion", "status", "episodeDate", "previewRunId",
        "approvedPreviewSha256", "previewIdentitySha256", "humanPreviewReviewSha256",
        "finalAuthorized",
    }
    manifest_required = {
        "contractVersion", "episodeDate", "previewRunId", "approvedPreviewSha256",
        "previewIdentitySha256", "humanPreviewReviewSha256", "plotFinalAuthorizationSha256",
    }
    if set(review) != review_required:
        raise FinalRequestError(f"Human Preview review fields mismatch: {sorted(review)}")
    if set(authorization) != authorization_required:
        raise FinalRequestError(f"Final authorization fields mismatch: {sorted(authorization)}")
    if set(manifest) != manifest_required:
        raise FinalRequestError(f"Final authorization manifest fields mismatch: {sorted(manifest)}")
    if review.get("contractVersion") != "1.0.0" or review.get("status") != "approved":
        raise FinalRequestError("Human Preview review is not approved")
    if authorization.get("contractVersion") != "1.0.0" or authorization.get("status") != "approved" or authorization.get("finalAuthorized") is not True:
        raise FinalRequestError("Plot Final authorization is not approved")
    if manifest.get("contractVersion") != "1.0.0":
        raise FinalRequestError("Final authorization manifest contractVersion mismatch")
    expected = {
        "episodeDate": date,
        "previewRunId": preview_run_id,
        "approvedPreviewSha256": approved_preview_sha256,
        "previewIdentitySha256": preview_identity_sha,
    }
    for key, value in expected.items():
        same(review, key, value, "Human review")
        same(authorization, key, value, "Final authorization")
        same(manifest, key, value, "Authorization manifest")
    review_sha = sha256(human_review)
    authorization_sha = sha256(final_authorization)
    manifest_sha = sha256(authorization_manifest)
    same(authorization, "humanPreviewReviewSha256", review_sha, "Final authorization")
    same(manifest, "humanPreviewReviewSha256", review_sha, "Authorization manifest")
    same(manifest, "plotFinalAuthorizationSha256", authorization_sha, "Authorization manifest")
    return review_sha, authorization_sha, manifest_sha


def build(
    *,
    date: str,
    preview_run_id: int,
    approved_preview_sha256: str,
    preview_identity: Path,
    human_review: Path,
    final_authorization: Path,
    authorization_manifest: Path,
    plot_authorization_run_id: int,
    plot_authorization_artifact_name: str,
    explicit_final: bool,
) -> dict[str, Any]:
    if not explicit_final:
        raise FinalRequestError("--explicit-final is required")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise FinalRequestError("episode date must be YYYY-MM-DD")
    if preview_run_id <= 0 or plot_authorization_run_id <= 0:
        raise FinalRequestError("Preview/authorization run IDs must be positive")
    require_sha(approved_preview_sha256, "approved Preview SHA")
    if not isinstance(plot_authorization_artifact_name, str) or not SAFE_NAME_RE.fullmatch(plot_authorization_artifact_name):
        raise FinalRequestError("Plot authorization Artifact name is unsafe")

    identity = load(preview_identity, "Preview identity")
    if identity.get("contractVersion") != "1.0.0" or identity.get("episodeDate") != date:
        raise FinalRequestError("Preview identity contract/date mismatch")
    preview_identity_sha = sha256(preview_identity)
    review_sha, authorization_sha, manifest_sha = validate_authorization_bundle(
        date=date,
        preview_run_id=preview_run_id,
        approved_preview_sha256=approved_preview_sha256,
        preview_identity_sha=preview_identity_sha,
        human_review=human_review,
        final_authorization=final_authorization,
        authorization_manifest=authorization_manifest,
    )

    audio = identity.get("ttsBlockAudioSha256")
    if not isinstance(audio, dict) or set(audio) != {"scenes-01-04", "scenes-05-09"}:
        raise FinalRequestError("Preview identity TTS audio map invalid")
    for key in ("registrySnapshotSha256", "inputSpecSha256", "ttsInputSha256"):
        require_sha(identity.get(key), f"Preview identity {key}")
    for block, digest in audio.items():
        require_sha(digest, f"Preview audio SHA {block}")
    renderer_commit = identity.get("rendererCommit")
    renderer_contract = identity.get("rendererContractVersion")
    if not isinstance(renderer_commit, str) or not COMMIT_RE.fullmatch(renderer_commit):
        raise FinalRequestError("Preview Renderer commit invalid")
    if not isinstance(renderer_contract, str) or not renderer_contract:
        raise FinalRequestError("Preview Renderer contract invalid")

    return {
        "requestVersion": "2.1.0",
        "episodeDate": date,
        "previewRunId": preview_run_id,
        "approvedPreviewSha256": approved_preview_sha256,
        "previewIdentitySha256": preview_identity_sha,
        "rendererCommit": renderer_commit,
        "rendererContractVersion": renderer_contract,
        "registrySnapshotSha256": identity["registrySnapshotSha256"],
        "renderSpecSha256": identity["inputSpecSha256"],
        "ttsInputSha256": identity["ttsInputSha256"],
        "ttsBlockAudioSha256": audio,
        "plotAuthorizationRunId": plot_authorization_run_id,
        "plotAuthorizationArtifactName": plot_authorization_artifact_name,
        "plotAuthorizationManifestSha256": manifest_sha,
        "humanPreviewReviewSha256": review_sha,
        "plotFinalAuthorizationSha256": authorization_sha,
        "finalFingerprint": final_fingerprint(
            preview_identity_sha=preview_identity_sha,
            preview_sha=approved_preview_sha256,
            authorization_sha=authorization_sha,
            renderer_commit=renderer_commit,
        ),
        "confirmation": "FINAL_RENDER",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--preview-run-id", type=int, required=True)
    parser.add_argument("--approved-preview-sha256", required=True)
    parser.add_argument("--preview-identity", type=Path, required=True)
    parser.add_argument("--human-review", type=Path, required=True)
    parser.add_argument("--final-authorization", type=Path, required=True)
    parser.add_argument("--authorization-manifest", type=Path, required=True)
    parser.add_argument("--plot-authorization-run-id", type=int, required=True)
    parser.add_argument("--plot-authorization-artifact-name", required=True)
    parser.add_argument("--explicit-final", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        value = build(
            date=args.date,
            preview_run_id=args.preview_run_id,
            approved_preview_sha256=args.approved_preview_sha256,
            preview_identity=args.preview_identity,
            human_review=args.human_review,
            final_authorization=args.final_authorization,
            authorization_manifest=args.authorization_manifest,
            plot_authorization_run_id=args.plot_authorization_run_id,
            plot_authorization_artifact_name=args.plot_authorization_artifact_name,
            explicit_final=args.explicit_final,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": "PASS", "path": str(args.output), "sha256": sha256(args.output)}, sort_keys=True))
        return 0
    except (OSError, FinalRequestError) as exc:
        print(json.dumps({"status": "FAIL", "errors": [str(exc)]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
