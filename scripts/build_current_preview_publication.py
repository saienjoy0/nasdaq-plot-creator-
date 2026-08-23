#!/usr/bin/env python3
"""Build the immutable Renderer publication identity for one Current Preview request.

This script does not write to GitHub.  It turns the already validated Plot request
into one deterministic, append-only Renderer target path so transports can retry
without creating a second logical request.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import renderer_binding


DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
COMMIT_RE = re.compile(r"[0-9a-f]{40}")
SAFE_NAME_RE = re.compile(r"[A-Za-z0-9._-]+")
RENDERER_REPOSITORY = "saienjoy0/saienjoy0-nasdaq-cafe-remotion"
RENDERER_REQUEST_DIR = "handoff-preview-requests-v4"


class PublicationError(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_request(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicationError(f"Preview request invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise PublicationError("Preview request root must be an object")
    required = {
        "contractVersion", "episodeDate", "plotRunId", "handoffArtifactName",
        "expectedBundleId", "expectedManifestSha256", "expectedRendererCommit",
        "expectedRendererContractVersion", "expectedRegistrySnapshotSha256", "confirmation",
    }
    if set(value) != required:
        raise PublicationError(f"Preview request fields mismatch: {sorted(value)}")
    if value["contractVersion"] != "2.1.0" or value["confirmation"] != "PREVIEW":
        raise PublicationError("Preview request contract/confirmation mismatch")
    if not isinstance(value["episodeDate"], str) or not DATE_RE.fullmatch(value["episodeDate"]):
        raise PublicationError("Preview request episodeDate is invalid")
    if not isinstance(value["plotRunId"], int) or isinstance(value["plotRunId"], bool) or value["plotRunId"] <= 0:
        raise PublicationError("Preview request plotRunId must be positive")
    if not isinstance(value["handoffArtifactName"], str) or not SAFE_NAME_RE.fullmatch(value["handoffArtifactName"]):
        raise PublicationError("Preview request handoffArtifactName is unsafe")
    for key in ("expectedBundleId", "expectedManifestSha256", "expectedRegistrySnapshotSha256"):
        if not isinstance(value[key], str) or not SHA256_RE.fullmatch(value[key]):
            raise PublicationError(f"Preview request {key} must be SHA-256")
    if not isinstance(value["expectedRendererCommit"], str) or not COMMIT_RE.fullmatch(value["expectedRendererCommit"]):
        raise PublicationError("Preview request expectedRendererCommit must be 40-hex")
    if not isinstance(value["expectedRendererContractVersion"], str) or not value["expectedRendererContractVersion"]:
        raise PublicationError("Preview request expectedRendererContractVersion is invalid")
    return value


def build(*, root: Path, request_path: Path) -> dict[str, Any]:
    root = root.resolve()
    request_path = request_path.resolve()
    request = load_request(request_path)
    binding = renderer_binding.load_binding(root)
    renderer = binding["renderer"]
    expected = {
        "expectedRendererCommit": renderer["commit"],
        "expectedRendererContractVersion": renderer["contractVersion"],
        "expectedRegistrySnapshotSha256": renderer["registrySnapshotSha256"],
    }
    for key, value in expected.items():
        if request[key] != value:
            raise PublicationError(f"Preview request {key} no longer matches canonical Renderer binding")

    request_sha = sha256(request_path)
    target_path = (
        f"{RENDERER_REQUEST_DIR}/{request['episodeDate']}-plot-"
        f"{request['plotRunId']}-{request_sha[:12]}.json"
    )
    return {
        "contractVersion": "1.0.0",
        "authority": "nasdaq-cafe-current-preview-publication",
        "state": "REQUEST_PUBLICATION_READY",
        "episodeDate": request["episodeDate"],
        "plotRunId": request["plotRunId"],
        "request": {
            "path": request_path.relative_to(root).as_posix(),
            "sha256": request_sha,
        },
        "renderer": {
            "repository": RENDERER_REPOSITORY,
            "targetPath": target_path,
            "commit": request["expectedRendererCommit"],
            "contractVersion": request["expectedRendererContractVersion"],
            "registrySnapshotSha256": request["expectedRegistrySnapshotSha256"],
        },
        "handoffArtifactName": request["handoffArtifactName"],
        "expectedBundleId": request["expectedBundleId"],
        "expectedManifestSha256": request["expectedManifestSha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        value = build(root=args.root, request_path=args.request)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": "PASS", "targetPath": value["renderer"]["targetPath"], "receipt": str(args.output)}, sort_keys=True))
        return 0
    except (OSError, PublicationError, renderer_binding.RendererBindingError) as exc:
        print(json.dumps({"status": "FAIL", "errors": [str(exc)]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
