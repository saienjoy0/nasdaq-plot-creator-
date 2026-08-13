#!/usr/bin/env python3
"""Canonical Renderer binding for Visual Intelligence production.

The binding is repository-owned machine configuration. Daily workflows must read
this file instead of copying Renderer commit/SHA values into multiple scripts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

BRIDGE_CONTRACT_VERSION = "visual-intelligence-bridge/1.2.0"
FROZEN_INTERFACE_SHA256 = "a9c54f2115f1d5a73251be64edcd5ff3f84c0940613ff7a6d7718f755581977f"
RENDERER_REPOSITORY = "saienjoy0/saienjoy0-nasdaq-cafe-remotion"
RENDERER_CONTRACT_VERSION = "2.4.0"


class RendererBindingError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_binding(root: Path) -> dict[str, Any]:
    root = root.resolve()
    path = root / "contracts/renderer_binding.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RendererBindingError(f"renderer binding invalid: {exc}") from exc
    if value.get("contractVersion") != "1.0.0":
        raise RendererBindingError("renderer binding contractVersion must be 1.0.0")
    if value.get("bridgeContractVersion") != BRIDGE_CONTRACT_VERSION:
        raise RendererBindingError("renderer binding bridgeContractVersion mismatch")
    if value.get("frozenInterfaceSha256") != FROZEN_INTERFACE_SHA256:
        raise RendererBindingError("renderer binding Frozen Interface SHA mismatch")
    renderer = value.get("renderer")
    if not isinstance(renderer, dict):
        raise RendererBindingError("renderer binding renderer must be an object")
    if renderer.get("repository") != RENDERER_REPOSITORY:
        raise RendererBindingError("renderer repository mismatch")
    commit = renderer.get("commit")
    if not isinstance(commit, str) or len(commit) != 40:
        raise RendererBindingError("renderer commit must be a 40-character SHA")
    try:
        int(commit, 16)
    except ValueError as exc:
        raise RendererBindingError("renderer commit must be hexadecimal") from exc
    if renderer.get("contractVersion") != RENDERER_CONTRACT_VERSION:
        raise RendererBindingError("renderer contract version mismatch")
    snapshot_path = renderer.get("registrySnapshotPath")
    snapshot_sha = renderer.get("registrySnapshotSha256")
    if snapshot_path != "contracts/visual_component_registry_snapshot.json":
        raise RendererBindingError("renderer registry snapshot path mismatch")
    if not isinstance(snapshot_sha, str) or len(snapshot_sha) != 64:
        raise RendererBindingError("renderer registry snapshot SHA must be sha256")
    return value


def verify_renderer_checkout(root: Path, renderer_root: Path) -> dict[str, Any]:
    import subprocess

    binding = load_binding(root)
    renderer = binding["renderer"]
    renderer_root = renderer_root.resolve()
    actual_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=renderer_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual_commit != renderer["commit"]:
        raise RendererBindingError(
            f"renderer checkout mismatch: expected {renderer['commit']} actual {actual_commit}"
        )
    snapshot = renderer_root / renderer["registrySnapshotPath"]
    if not snapshot.is_file():
        raise RendererBindingError(f"renderer registry snapshot missing: {snapshot}")
    actual_snapshot_sha = sha256_file(snapshot)
    if actual_snapshot_sha != renderer["registrySnapshotSha256"]:
        raise RendererBindingError(
            "renderer registry snapshot SHA mismatch: "
            f"expected {renderer['registrySnapshotSha256']} actual {actual_snapshot_sha}"
        )
    return binding
