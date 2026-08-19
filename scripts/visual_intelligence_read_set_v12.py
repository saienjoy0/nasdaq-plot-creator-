#!/usr/bin/env python3
"""Direct read-set receipts for current Visual Intelligence stages.

This is not a global dependency registry. It snapshots only the exact direct files
and pinned implementation identities consumed by each current stage and is embedded
in the existing Visual Intelligence validation receipt.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import renderer_binding


class VisualIntelligenceReadSetError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_ref(root: Path, path: Path) -> dict[str, str]:
    resolved = path.resolve()
    root = root.resolve()
    if root not in resolved.parents and resolved != root:
        raise VisualIntelligenceReadSetError(f"read-set path escapes Plot root: {path}")
    if not resolved.is_file():
        raise VisualIntelligenceReadSetError(f"read-set input missing: {path}")
    return {
        "path": resolved.relative_to(root).as_posix(),
        "sha256": sha256_file(resolved),
    }


def external_file_ref(path: Path, *, label: str) -> dict[str, str]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise VisualIntelligenceReadSetError(f"{label} missing: {resolved}")
    return {"identity": label, "sha256": sha256_file(resolved)}


def renderer_identity(root: Path, renderer_root: Path) -> list[dict[str, str]]:
    binding = renderer_binding.verify_renderer_checkout(root, renderer_root)
    registry = renderer_root / binding["renderer"]["registrySnapshotPath"]
    return [
        {"identity": "rendererCommit", "value": binding["renderer"]["commit"]},
        {"identity": "rendererContractVersion", "value": binding["renderer"]["contractVersion"]},
        external_file_ref(registry, label="rendererRegistrySnapshot"),
    ]


def _existing(root: Path, paths: list[Path]) -> list[dict[str, str]]:
    return [file_ref(root, path) for path in paths if path.is_file()]


def build(*, root: Path, date: str, renderer_root: Path) -> dict[str, Any]:
    root = root.resolve()
    vi = root / "working" / date / "visual-intelligence"
    principles = root / "skills/nasdaq-cafe-visual-intelligence/references/VISUAL_EDITORIAL_INTELLIGENCE.md"
    renderer_ids = renderer_identity(root, renderer_root)

    stages = {
        "visualRequirementsCanonical": [
            vi / "visual_requirements.semantic.json",
            vi / "editorial_snapshot.json",
        ],
        "visualCandidateCatalog": [
            vi / "visual_direction_input.json",
            vi / "visual_capability_hints.json",
        ],
        "visualDirectorDecisionCanonical": [
            vi / "visual_director_decision.semantic.json",
            vi / "visual_requirements.json",
            vi / "editorial_snapshot.json",
            vi / "visual_candidate_catalog.json",
        ],
        "visualDirectionPlan": [
            vi / "visual_director_decision.json",
            vi / "visual_candidate_catalog.json",
        ],
        "compiledVisual": [
            vi / "visual_direction_input.json",
            vi / "visual_candidate_catalog.json",
            vi / "visual_direction_plan.json",
        ],
        "visualCriticReviewCanonical": [
            vi / "visual_critic_review.semantic.json",
            vi / "visual_director_decision.json",
            vi / "visual_direction_compiled_render.json",
            vi / "visual_editorial_warning_report.json",
        ],
        "visualIntelligencePackage": [
            vi / "visual_requirements.json",
            vi / "visual_director_decision.json",
            vi / "visual_critic_review.json",
            vi / "asset_resolution_state.json",
            vi / "recent_visual_pattern_context.json",
            vi / "visual_capability_hints.json",
            vi / "visual_direction_plan.json",
            vi / "visual_direction_compiled_render.json",
            vi / "visual_editorial_warning_report.json",
            principles,
        ],
    }
    renderer_stages = {
        "visualCandidateCatalog",
        "compiledVisual",
        "visualIntelligencePackage",
    }
    result: dict[str, Any] = {}
    for stage, paths in stages.items():
        refs = _existing(root, paths)
        if refs:
            result[stage] = {
                "files": refs,
                "implementation": renderer_ids if stage in renderer_stages else [],
            }
    return result


def verify(
    root: Path,
    receipt: dict[str, Any],
    *,
    renderer_root: Path | None = None,
) -> list[str]:
    """Return stale direct inputs; unrelated files are intentionally ignored."""
    root = root.resolve()
    stale: list[str] = []
    current_implementation: dict[str, dict[str, str]] = {}
    if renderer_root is not None:
        for item in renderer_identity(root, renderer_root.resolve()):
            current_implementation[item["identity"]] = item

    for stage, value in receipt.items():
        if not isinstance(value, dict):
            stale.append(f"{stage}: invalid read-set object")
            continue
        files = value.get("files", [])
        if not isinstance(files, list):
            stale.append(f"{stage}: invalid files")
            continue
        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                stale.append(f"{stage}: invalid file ref")
                continue
            path = root / item["path"]
            if not path.is_file():
                stale.append(f"{stage}:{item['path']}:missing")
                continue
            if sha256_file(path) != item.get("sha256"):
                stale.append(f"{stage}:{item['path']}:sha-mismatch")

        implementation = value.get("implementation", [])
        if not isinstance(implementation, list):
            stale.append(f"{stage}: invalid implementation read-set")
            continue
        if implementation and renderer_root is None:
            stale.append(f"{stage}: renderer verification unavailable")
            continue
        for item in implementation:
            if not isinstance(item, dict) or not isinstance(item.get("identity"), str):
                stale.append(f"{stage}: invalid implementation ref")
                continue
            identity = item["identity"]
            current = current_implementation.get(identity)
            if current != item:
                stale.append(f"{stage}:{identity}:identity-mismatch")
    return stale
