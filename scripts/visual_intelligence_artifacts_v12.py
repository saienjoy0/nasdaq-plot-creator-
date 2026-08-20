#!/usr/bin/env python3
"""Current Visual Intelligence semantic-payload -> canonical-artifact materializers.

Semantic payloads contain authored meaning only. Machine-derived identity is attached
here. A canonical artifact may be rematerialized by its single machine writer until
its lifecycle freeze point; after a downstream freeze guard exists, changing bytes
fails closed. This permits correction of an invalid draft without permitting sealed
evidence to be clobbered.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import renderer_binding

SEMANTIC_PAYLOAD_VERSION = "1.0.0"
CANONICAL_CONTRACT_VERSION = "1.0.0"

REQUIREMENTS_SEMANTIC = "visual_requirements.semantic.json"
REQUIREMENTS_CANONICAL = "visual_requirements.json"
DIRECTOR_SEMANTIC = "visual_director_decision.semantic.json"
DIRECTOR_CANONICAL = "visual_director_decision.json"
CRITIC_SEMANTIC = "visual_critic_review.semantic.json"
CRITIC_CANONICAL = "visual_critic_review.json"

CRITIC_STATUSES = {"PASS", "REVISE", "RETURN_TO_STORY", "BLOCKED"}
FORBIDDEN_SEMANTIC_KEYS = {
    "editorialSnapshotSha256",
    "visualRequirementsSha256",
    "candidateCatalogSha256",
    "directorDecisionSha256",
    "compiledVisualSha256",
    "warningReportSha256",
    "registrySnapshotSha256",
    "semanticFreezeSha256",
}


class VisualIntelligenceArtifactError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualIntelligenceArtifactError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualIntelligenceArtifactError(f"{label} must be an object")
    return value


def _semantic_guard(value: Any, *, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_SEMANTIC_KEYS or key.endswith("Sha256"):
                raise VisualIntelligenceArtifactError(
                    f"semantic payload must not author machine-derived SHA: {path}.{key}"
                )
            _semantic_guard(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _semantic_guard(item, path=f"{path}[{index}]")


def _require_semantic_header(value: dict[str, Any], *, date: str, label: str) -> None:
    if value.get("semanticPayloadVersion") != SEMANTIC_PAYLOAD_VERSION:
        raise VisualIntelligenceArtifactError(
            f"{label} semanticPayloadVersion must be {SEMANTIC_PAYLOAD_VERSION}"
        )
    if value.get("episodeDate") != date:
        raise VisualIntelligenceArtifactError(f"{label} episodeDate mismatch")
    _semantic_guard(value)


def write_once(path: Path, value: dict[str, Any], *, label: str) -> Path:
    payload = canonical_bytes(value)
    if path.is_file():
        if path.read_bytes() != payload:
            raise VisualIntelligenceArtifactError(
                f"E_VISUAL_IMMUTABLE_CLOBBER:{label}:{path.name}"
            )
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _write_until_frozen(
    path: Path,
    value: dict[str, Any],
    *,
    label: str,
    freeze_guards: tuple[Path, ...],
) -> Path:
    payload = canonical_bytes(value)
    if path.is_file() and path.read_bytes() == payload:
        return path
    if path.is_file() and any(guard.exists() for guard in freeze_guards):
        raise VisualIntelligenceArtifactError(
            f"E_VISUAL_IMMUTABLE_CLOBBER:{label}:{path.name}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def materialize_requirements(*, vi_dir: Path, date: str) -> Path:
    semantic_path = vi_dir / REQUIREMENTS_SEMANTIC
    snapshot_path = vi_dir / "editorial_snapshot.json"
    if not semantic_path.is_file():
        raise VisualIntelligenceArtifactError(
            f"E_VISUAL_REQUIREMENTS_SEMANTIC_MISSING:{semantic_path.name}"
        )
    if not snapshot_path.is_file():
        raise VisualIntelligenceArtifactError("E_VISUAL_EDITORIAL_SNAPSHOT_MISSING")
    semantic = load(semantic_path, "Visual Requirements semantic payload")
    _require_semantic_header(semantic, date=date, label="Visual Requirements")
    intent = semantic.get("intent")
    provisional = semantic.get("provisionalDirection")
    if not isinstance(intent, dict) or not isinstance(intent.get("beats"), list):
        raise VisualIntelligenceArtifactError("Visual Requirements semantic intent.beats missing")
    if not isinstance(provisional, dict) or not isinstance(
        provisional.get("requirements"), list
    ):
        raise VisualIntelligenceArtifactError(
            "Visual Requirements semantic provisionalDirection.requirements missing"
        )
    canonical = {
        "contractVersion": CANONICAL_CONTRACT_VERSION,
        "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
        "episodeDate": date,
        "editorialSnapshotSha256": sha256_file(snapshot_path),
        "intent": intent,
        "provisionalDirection": provisional,
    }
    return _write_until_frozen(
        vi_dir / REQUIREMENTS_CANONICAL,
        canonical,
        label="Visual Requirements canonical",
        freeze_guards=(vi_dir / "visual_candidate_catalog.json",),
    )


def materialize_director(*, vi_dir: Path, date: str) -> Path:
    semantic_path = vi_dir / DIRECTOR_SEMANTIC
    requirements_path = vi_dir / REQUIREMENTS_CANONICAL
    snapshot_path = vi_dir / "editorial_snapshot.json"
    catalog_path = vi_dir / "visual_candidate_catalog.json"
    for path, label in (
        (semantic_path, "Visual Director semantic payload"),
        (requirements_path, "Visual Requirements canonical"),
        (snapshot_path, "Editorial Snapshot"),
        (catalog_path, "Visual Candidate Catalog"),
    ):
        if not path.is_file():
            raise VisualIntelligenceArtifactError(f"{label} missing: {path.name}")
    semantic = load(semantic_path, "Visual Director semantic payload")
    _require_semantic_header(semantic, date=date, label="Visual Director")
    selections = semantic.get("selections")
    if not isinstance(selections, list):
        raise VisualIntelligenceArtifactError("Visual Director selections missing")
    canonical = {
        "contractVersion": CANONICAL_CONTRACT_VERSION,
        "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
        "episodeDate": date,
        "editorialSnapshotSha256": sha256_file(snapshot_path),
        "visualRequirementsSha256": sha256_file(requirements_path),
        "candidateCatalogSha256": sha256_file(catalog_path),
        "selections": selections,
    }
    return _write_until_frozen(
        vi_dir / DIRECTOR_CANONICAL,
        canonical,
        label="Visual Director Decision canonical",
        freeze_guards=(vi_dir / "visual_direction_compiled_render.json",),
    )


def materialize_critic(*, vi_dir: Path, date: str) -> Path:
    semantic_path = vi_dir / CRITIC_SEMANTIC
    director_path = vi_dir / DIRECTOR_CANONICAL
    compiled_path = vi_dir / "visual_direction_compiled_render.json"
    warning_path = vi_dir / "visual_editorial_warning_report.json"
    for path, label in (
        (semantic_path, "Visual Critic semantic payload"),
        (director_path, "Visual Director Decision canonical"),
        (compiled_path, "Compiled Visual"),
        (warning_path, "Visual Editorial Warning Report"),
    ):
        if not path.is_file():
            raise VisualIntelligenceArtifactError(f"{label} missing: {path.name}")
    semantic = load(semantic_path, "Visual Critic semantic payload")
    _require_semantic_header(semantic, date=date, label="Visual Critic")
    rounds = semantic.get("reviewRounds")
    if not isinstance(rounds, list) or not rounds or len(rounds) > 2:
        raise VisualIntelligenceArtifactError(
            "Visual Critic semantic reviewRounds must contain one or two rounds"
        )
    for index, item in enumerate(rounds, start=1):
        if not isinstance(item, dict):
            raise VisualIntelligenceArtifactError("Visual Critic round must be an object")
        if item.get("status") not in CRITIC_STATUSES:
            raise VisualIntelligenceArtifactError("Visual Critic status invalid")
        if item.get("round") not in (None, index):
            raise VisualIntelligenceArtifactError("Visual Critic round numbering invalid")
    canonical = {
        "contractVersion": CANONICAL_CONTRACT_VERSION,
        "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
        "episodeDate": date,
        "directorDecisionSha256": sha256_file(director_path),
        "compiledVisualSha256": sha256_file(compiled_path),
        "warningReportSha256": sha256_file(warning_path),
        "reviewRounds": rounds,
    }
    return _write_until_frozen(
        vi_dir / CRITIC_CANONICAL,
        canonical,
        label="Visual Critic Review canonical",
        freeze_guards=(vi_dir / "visual_intelligence_package.json",),
    )


def semantic_payload_paths(vi_dir: Path) -> tuple[Path, Path, Path]:
    return (
        vi_dir / REQUIREMENTS_SEMANTIC,
        vi_dir / DIRECTOR_SEMANTIC,
        vi_dir / CRITIC_SEMANTIC,
    )
