#!/usr/bin/env python3
"""Verify an immutable current-v1.2 Semantic Freeze without revalidating it against mutable Current contracts.

This verifier owns only sealed editorial identity. It proves that the episode inputs bound by
an already-issued Semantic Freeze have not changed and that the bound Editorial Semantic
Acceptance still points to those exact inputs. It deliberately does NOT compare historical
contractBindings or the historical Canon Manifest SHA to today's mutable repository files.

Current compatibility is a separate responsibility. Production reaches
validate_chatgpt_daily_authoring_closure.py immediately after this gate, where the frozen
Daily Authoring is checked against the current Authoring/Renderer contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import chatgpt_semantic_freeze as freeze

SHA_RE = re.compile(r"^[0-9a-f]{64}$")
CURRENT_VERSION = "1.2.0"


class SealedSemanticFreezeError(ValueError):
    pass


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SealedSemanticFreezeError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise SealedSemanticFreezeError(f"{label} root must be an object")
    return value


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve(root: Path, relative: str, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise SealedSemanticFreezeError(f"{label}.path missing")
    candidate = Path(relative)
    if candidate.is_absolute():
        raise SealedSemanticFreezeError(f"{label}.path must be repository-relative")
    root = root.resolve()
    path = (root / candidate).resolve()
    if path != root and root not in path.parents:
        raise SealedSemanticFreezeError(f"{label}.path escapes repository root")
    if not path.is_file():
        raise SealedSemanticFreezeError(f"{label} missing: {relative}")
    return path


def _verify_binding(
    root: Path,
    binding: dict[str, Any],
    label: str,
    *,
    semantic: bool,
) -> dict[str, Any] | None:
    if not isinstance(binding, dict):
        raise SealedSemanticFreezeError(f"{label} binding missing")
    path = _resolve(root, binding.get("path"), label)
    actual_sha = _sha256_file(path)
    if binding.get("sha256") != actual_sha:
        raise SealedSemanticFreezeError(
            f"{label}.sha256 mismatch: declared={binding.get('sha256')} actual={actual_sha}"
        )
    if not semantic:
        return None
    value = _load_json(path, label)
    actual_semantic = freeze.canonical_sha(value)
    if binding.get("semanticSha256") != actual_semantic:
        raise SealedSemanticFreezeError(
            f"{label}.semanticSha256 mismatch: declared={binding.get('semanticSha256')} actual={actual_semantic}"
        )
    return value


def _same_file_binding(left: dict[str, Any], right: dict[str, Any], *, semantic: bool) -> bool:
    keys = ("path", "sha256", "semanticSha256") if semantic else ("path", "sha256")
    return all(left.get(key) == right.get(key) for key in keys)


def _validate_recorded_contract_bindings(acceptance: dict[str, Any]) -> None:
    rows = acceptance.get("contractBindings")
    if not isinstance(rows, list) or not rows:
        raise SealedSemanticFreezeError("Acceptance contractBindings must be non-empty")
    seen_roles: set[str] = set()
    seen_paths: set[str] = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise SealedSemanticFreezeError(f"Acceptance contractBindings[{index}] must be an object")
        role = row.get("role")
        path = row.get("path")
        sha = row.get("sha256")
        if not isinstance(role, str) or not role:
            raise SealedSemanticFreezeError(f"Acceptance contractBindings[{index}].role missing")
        if not isinstance(path, str) or not path:
            raise SealedSemanticFreezeError(f"Acceptance contractBindings[{index}].path missing")
        if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
            raise SealedSemanticFreezeError(f"Acceptance contractBindings[{index}].sha256 invalid")
        if role in seen_roles:
            raise SealedSemanticFreezeError(f"Acceptance contractBindings duplicate role: {role}")
        if path in seen_paths:
            raise SealedSemanticFreezeError(f"Acceptance contractBindings duplicate path: {path}")
        seen_roles.add(role)
        seen_paths.add(path)


def _verify_validation_projections(root: Path, acceptance: dict[str, Any]) -> None:
    projections = acceptance.get("validationProjections")
    if not isinstance(projections, dict):
        raise SealedSemanticFreezeError("Acceptance validationProjections missing")
    for key in ("storyPlan", "storyScript", "creativeReview"):
        binding = projections.get(key)
        _verify_binding(root, binding, f"Acceptance validationProjections.{key}", semantic=False)


def _verify_acceptance_snapshot(
    root: Path,
    date: str,
    manifest: dict[str, Any],
    acceptance: dict[str, Any],
    authoring: dict[str, Any],
) -> None:
    if acceptance.get("contractVersion") != "1.0.0":
        raise SealedSemanticFreezeError("Acceptance contractVersion mismatch")
    if acceptance.get("episodeDate") != date:
        raise SealedSemanticFreezeError("Acceptance episodeDate mismatch")
    if acceptance.get("status") != "PASS" or acceptance.get("errors") != []:
        raise SealedSemanticFreezeError("Acceptance is not a sealed PASS")

    if not _same_file_binding(
        acceptance.get("authoring", {}), manifest["canonicalAuthoring"], semantic=True
    ):
        raise SealedSemanticFreezeError("Acceptance authoring binding differs from Semantic Freeze")
    if not _same_file_binding(
        acceptance.get("causalDossier", {}), manifest["causalDossier"], semantic=False
    ):
        raise SealedSemanticFreezeError("Acceptance Causal Dossier binding differs from Semantic Freeze")
    if not _same_file_binding(
        acceptance.get("causalDossierValidation", {}),
        manifest["causalDossierValidation"],
        semantic=False,
    ):
        raise SealedSemanticFreezeError(
            "Acceptance Causal Dossier validation binding differs from Semantic Freeze"
        )
    if acceptance.get("canonManifest") != manifest.get("canonManifest"):
        raise SealedSemanticFreezeError("Acceptance Canon Manifest identity differs from Semantic Freeze")

    embedded = acceptance.get("storySubdocuments")
    if not isinstance(embedded, dict):
        raise SealedSemanticFreezeError("Acceptance storySubdocuments missing")
    expected = {
        "storyPlan": ("/storyPlan", "storyPlan"),
        "storyScript": ("/storyScript", "storyScript"),
        "creativeReview": ("/creativeReview", "creativeReview"),
    }
    for key, (pointer, authoring_key) in expected.items():
        item = embedded.get(key)
        if not isinstance(item, dict) or item.get("jsonPointer") != pointer:
            raise SealedSemanticFreezeError(f"Acceptance storySubdocuments.{key} pointer mismatch")
        actual = freeze.canonical_sha(authoring.get(authoring_key))
        if item.get("semanticSha256") != actual:
            raise SealedSemanticFreezeError(
                f"Acceptance storySubdocuments.{key} semantic digest differs from frozen authoring"
            )

    _validate_recorded_contract_bindings(acceptance)
    _verify_validation_projections(root, acceptance)


def _verify_manifest_digest(manifest: dict[str, Any]) -> None:
    payload = {
        "episodeDate": manifest["episodeDate"],
        "parts": [
            {"path": item["path"], "semanticSha256": item["semanticSha256"]}
            for item in manifest["parts"]
        ],
        "dailySourceSha256": manifest["dailySourcePackage"]["sha256"],
        "canonManifest": manifest["canonManifest"],
        "canonicalAuthoringSemanticSha256": manifest["canonicalAuthoring"]["semanticSha256"],
        "causalDossierSemanticSha256": manifest["causalDossier"]["semanticSha256"],
        "causalDossierValidationSemanticSha256": manifest["causalDossierValidation"]["semanticSha256"],
        "editorialSemanticAcceptanceSemanticSha256": manifest["editorialSemanticAcceptance"]["semanticSha256"],
    }
    actual = freeze.canonical_sha(payload)
    if manifest.get("sourceSetDigestSha256") != actual:
        raise SealedSemanticFreezeError(
            "Semantic Freeze sourceSetDigestSha256 is internally inconsistent"
        )


def verify_manifest(root: Path, date: str, manifest_path: Path) -> dict[str, Any]:
    root = root.resolve()
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    manifest = _load_json(path, "Semantic Freeze")
    try:
        freeze.validate_manifest_shape(manifest, date)
    except freeze.SemanticFreezeError as exc:
        raise SealedSemanticFreezeError(str(exc)) from exc
    if manifest.get("contractVersion") != CURRENT_VERSION:
        raise SealedSemanticFreezeError(
            f"Current production requires Semantic Freeze {CURRENT_VERSION}"
        )

    for index, item in enumerate(manifest["parts"], 1):
        _verify_binding(root, item, f"Semantic Freeze part {index}", semantic=True)
    _verify_binding(root, manifest["dailySourcePackage"], "daily source package", semantic=False)
    authoring = _verify_binding(
        root, manifest["canonicalAuthoring"], "canonical Daily Authoring", semantic=True
    )
    _verify_binding(root, manifest["causalDossier"], "Causal Dossier", semantic=True)
    _verify_binding(
        root,
        manifest["causalDossierValidation"],
        "Causal Dossier validation receipt",
        semantic=True,
    )
    acceptance = _verify_binding(
        root,
        manifest["editorialSemanticAcceptance"],
        "Editorial Semantic Acceptance",
        semantic=True,
    )
    assert authoring is not None and acceptance is not None

    dossier_binding = authoring.get("causalDossier")
    if not isinstance(dossier_binding, dict):
        raise SealedSemanticFreezeError("Frozen authoring Causal Dossier binding missing")
    if not _same_file_binding(dossier_binding, manifest["causalDossier"], semantic=False):
        raise SealedSemanticFreezeError("Frozen authoring Causal Dossier binding differs from Freeze")
    validation_binding = dossier_binding.get("validation")
    if not isinstance(validation_binding, dict) or not _same_file_binding(
        validation_binding, manifest["causalDossierValidation"], semantic=False
    ):
        raise SealedSemanticFreezeError(
            "Frozen authoring Causal Dossier validation binding differs from Freeze"
        )

    _verify_acceptance_snapshot(root, date, manifest, acceptance, authoring)
    _verify_manifest_digest(manifest)
    return manifest


def manifest_sha256(root: Path, manifest_path: Path) -> str:
    path = manifest_path if manifest_path.is_absolute() else root.resolve() / manifest_path
    if not path.is_file():
        raise SealedSemanticFreezeError(f"Semantic Freeze missing: {path}")
    return _sha256_file(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--date", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    try:
        manifest = verify_manifest(root, args.date, args.manifest)
        result = {
            "status": "PASS",
            "episodeDate": args.date,
            "contractVersion": manifest["contractVersion"],
            "manifestSha256": manifest_sha256(root, args.manifest),
            "verificationMode": "sealed-editorial-identity",
        }
        code = 0
    except (OSError, SealedSemanticFreezeError) as exc:
        result = {
            "status": "FAIL",
            "episodeDate": args.date,
            "errors": [str(exc)],
            "verificationMode": "sealed-editorial-identity",
        }
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
