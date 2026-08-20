#!/usr/bin/env python3
"""Mechanical Renderer-owned compatibility contract sync for current production."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


class RendererContractSyncError(RuntimeError):
    pass


def sync_renderer_owned_contracts(root: Path, renderer_root: Path) -> None:
    source = renderer_root / "contracts" / "visual_grammar_renderer_compatibility.json"
    target = root / "contracts" / "visual_grammar_renderer_compatibility.json"
    if not source.is_file():
        raise RendererContractSyncError(
            f"pinned Renderer compatibility registry missing: {source}"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = source.read_bytes()
    if target.is_file() and target.read_bytes() == payload:
        source_sha = hashlib.sha256(payload).hexdigest()
        print(
            f"BOUND_RENDERER_VISUAL_GRAMMAR_REGISTRY sha256={source_sha}",
            flush=True,
        )
        return
    shutil.copyfile(source, target)
    source_sha = hashlib.sha256(payload).hexdigest()
    target_sha = hashlib.sha256(target.read_bytes()).hexdigest()
    if source_sha != target_sha:
        raise RendererContractSyncError(
            "Renderer compatibility registry sync mismatch: "
            f"source={source_sha} target={target_sha}"
        )
    print(f"BOUND_RENDERER_VISUAL_GRAMMAR_REGISTRY sha256={source_sha}", flush=True)
