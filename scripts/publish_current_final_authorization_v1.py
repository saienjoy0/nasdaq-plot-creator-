#!/usr/bin/env python3
"""Publish Current Final authorization evidence and a Renderer Final request candidate.

The input is an append-only user-approval request containing the exact approved
Preview SHA and exact preview_identity.json bytes (base64). This script creates
only control-plane artifacts; it never invokes Renderer Final.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import build_current_final_authorization_bundle_v1 as bundle_builder
import build_current_final_request_v2 as final_builder

SHA256_RE = re.compile(r"[0-9a-f]{64}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


class FinalAuthorizationPublicationError(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FinalAuthorizationPublicationError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise FinalAuthorizationPublicationError(f"{label} must be an object")
    return value


def validate_request(value: dict[str, Any]) -> None:
    required = {
        "contractVersion", "episodeDate", "previewRunId", "approvedPreviewSha256",
        "previewIdentitySha256", "previewIdentityBase64", "confirmation",
    }
    if set(value) != required:
        raise FinalAuthorizationPublicationError(f"Final authorization request fields mismatch: {sorted(value)}")
    if value.get("contractVersion") != "1.0.0" or value.get("confirmation") != "FINAL_AUTHORIZATION":
        raise FinalAuthorizationPublicationError("Final authorization request contract/confirmation mismatch")
    if not isinstance(value.get("episodeDate"), str) or not DATE_RE.fullmatch(value["episodeDate"]):
        raise FinalAuthorizationPublicationError("bad episodeDate")
    if not isinstance(value.get("previewRunId"), int) or isinstance(value["previewRunId"], bool) or value["previewRunId"] <= 0:
        raise FinalAuthorizationPublicationError("bad previewRunId")
    if not isinstance(value.get("approvedPreviewSha256"), str) or not SHA256_RE.fullmatch(value["approvedPreviewSha256"]):
        raise FinalAuthorizationPublicationError("approvedPreviewSha256 must be SHA-256")
    if not isinstance(value.get("previewIdentitySha256"), str) or not SHA256_RE.fullmatch(value["previewIdentitySha256"]):
        raise FinalAuthorizationPublicationError("previewIdentitySha256 must be SHA-256")
    if not isinstance(value.get("previewIdentityBase64"), str) or not value["previewIdentityBase64"]:
        raise FinalAuthorizationPublicationError("previewIdentityBase64 is required")


def publish(*, request: Path, plot_authorization_run_id: int, output_root: Path) -> dict[str, str]:
    if plot_authorization_run_id <= 0:
        raise FinalAuthorizationPublicationError("plot authorization run ID must be positive")
    request = request.resolve()
    value = load(request, "Final authorization request")
    validate_request(value)
    try:
        identity_bytes = base64.b64decode(value["previewIdentityBase64"], validate=True)
    except Exception as exc:
        raise FinalAuthorizationPublicationError(f"previewIdentityBase64 invalid: {exc}") from exc
    if hashlib.sha256(identity_bytes).hexdigest() != value["previewIdentitySha256"]:
        raise FinalAuthorizationPublicationError("previewIdentityBase64 SHA mismatch")

    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    identity_path = output_root / "preview_identity.json"
    identity_path.write_bytes(identity_bytes)
    identity = load(identity_path, "decoded Preview identity")
    if identity.get("episodeDate") != value["episodeDate"] or identity.get("contractVersion") != "1.0.0":
        raise FinalAuthorizationPublicationError("decoded Preview identity contract/date mismatch")

    bundle_root = output_root / "authorization-bundle"
    bundle = bundle_builder.build(
        date=value["episodeDate"],
        preview_run_id=value["previewRunId"],
        approved_preview_sha256=value["approvedPreviewSha256"],
        preview_identity=identity_path,
        explicit_user_approval=True,
        output_root=bundle_root,
    )
    artifact_name = f"nasdaq-cafe-final-authorization-{value['episodeDate']}-{plot_authorization_run_id}"
    final_request_path = output_root / "current_final_request_v2.json"
    final_request = final_builder.build(
        date=value["episodeDate"],
        preview_run_id=value["previewRunId"],
        approved_preview_sha256=value["approvedPreviewSha256"],
        preview_identity=identity_path,
        human_review=Path(bundle["human_review_path"]),
        final_authorization=Path(bundle["final_authorization_path"]),
        authorization_manifest=Path(bundle["manifest_path"]),
        plot_authorization_run_id=plot_authorization_run_id,
        plot_authorization_artifact_name=artifact_name,
        explicit_final=True,
    )
    final_request_path.write_text(
        json.dumps(final_request, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    target_path = (
        f"final-render-requests-v2/{value['episodeDate']}-plot-auth-"
        f"{plot_authorization_run_id}-{final_request['finalFingerprint'][:12]}.json"
    )
    receipt_path = output_root / "current_final_authorization_publication.json"
    receipt = {
        "contractVersion": "1.0.0",
        "state": "FINAL_REQUEST_PUBLICATION_READY",
        "episodeDate": value["episodeDate"],
        "previewRunId": value["previewRunId"],
        "plotAuthorizationRunId": plot_authorization_run_id,
        "artifactName": artifact_name,
        "request": {
            "path": final_request_path.name,
            "sha256": sha256(final_request_path),
            "finalFingerprint": final_request["finalFingerprint"],
        },
        "renderer": {"targetPath": target_path},
    }
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "bundle_root": str(bundle_root),
        "artifact_name": artifact_name,
        "final_request_path": str(final_request_path),
        "final_request_sha256": sha256(final_request_path),
        "publication_receipt_path": str(receipt_path),
        "renderer_target_path": target_path,
        "manifest_sha256": bundle["manifest_sha256"],
        "human_review_sha256": bundle["human_review_sha256"],
        "final_authorization_sha256": bundle["final_authorization_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--plot-authorization-run-id", required=True, type=int)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = publish(
            request=args.request,
            plot_authorization_run_id=args.plot_authorization_run_id,
            output_root=args.output_root,
        )
    except (OSError, FinalAuthorizationPublicationError, bundle_builder.FinalAuthorizationBundleError, final_builder.FinalRequestError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "PASS", **result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
