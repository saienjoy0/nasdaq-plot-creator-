#!/usr/bin/env python3
"""Create or verify the committed ChatGPT semantic-source freeze.

v1.2 freezes the accepted semantic chain: raw authoring lineage, daily source package,
canonical Daily Authoring v2, validated Causal Dossier + validation receipt, Editorial
Semantic Acceptance, and Canon Manifest. Story Plan/Script/04 authority is embedded in
canonical authoring and is bound by semantic digests inside the acceptance receipt.

Legacy v1.1 source sets remain build/verify-compatible for historical tooling and tests.
Current production is still fail-closed: whenever canonical Daily Authoring exists it
must be v2, and the Preview workflow separately requires a committed Freeze v1.2.
Production Runtime must call only ``verify``; current-v2 ``create`` belongs to
ChatGPT authoring/PR preparation.
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

from canon_manifest import DEFAULT_MANIFEST as DEFAULT_CANON_MANIFEST
from canon_manifest import CanonManifestError, manifest_binding

import validate_editorial_semantic_boundary

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
SHA_RE = re.compile(r"[0-9a-f]{64}")
CURRENT_CONTRACT_VERSION = "1.2.0"
LEGACY_CONTRACT_VERSION = "1.1.0"
AUTHORITY = "chatgpt-semantic-source"


class SemanticFreezeError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SemanticFreezeError(f"{label} invalid: {exc}") from exc


def _repo_file(root: Path, relative: str, label: str) -> Path:
    root = root.resolve()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        raise SemanticFreezeError(f"{label} escapes repository root: {relative}")
    if not path.is_file():
        raise SemanticFreezeError(f"missing {label}: {relative}")
    return path


def _json_binding(root: Path, relative: str, label: str) -> dict[str, str]:
    path = _repo_file(root, relative, label)
    value = load_json(path, label)
    if not isinstance(value, dict):
        raise SemanticFreezeError(f"{label} root must be an object: {relative}")
    return {"path": relative, "sha256": sha256_file(path), "semanticSha256": canonical_sha(value)}


def _file_binding(root: Path, relative: str, label: str) -> dict[str, str]:
    path = _repo_file(root, relative, label)
    return {"path": relative, "sha256": sha256_file(path)}


def _canon_binding(root: Path) -> dict[str, str]:
    try:
        return manifest_binding(root, DEFAULT_CANON_MANIFEST)
    except CanonManifestError as exc:
        raise SemanticFreezeError(f"E_CANON_INVALID: {exc}") from exc


def _parts(root: Path, date: str) -> list[dict[str, str]]:
    paths = sorted((root / "daily-authoring-parts" / date).glob("*.json"))
    if not paths:
        raise SemanticFreezeError(f"no ChatGPT authoring parts for {date}")
    return [_json_binding(root, p.relative_to(root).as_posix(), "ChatGPT authoring part") for p in paths]


def _require_current_chain(root: Path, date: str) -> dict[str, dict[str, str]]:
    authoring_rel = f"daily-authoring/{date}.json"
    dossier_rel = f"research/{date}/causal_research_dossier_{date}.json"
    dossier_receipt_rel = f"research/{date}/causal_dossier_validation.json"
    acceptance_rel = f"verification/{date}/editorial_semantic_acceptance.json"

    authoring = _json_binding(root, authoring_rel, "canonical daily authoring")
    dossier = _json_binding(root, dossier_rel, "Causal Dossier")
    dossier_receipt = _json_binding(root, dossier_receipt_rel, "Causal Dossier validation receipt")
    acceptance = _json_binding(root, acceptance_rel, "Editorial Semantic Acceptance")

    authoring_doc = load_json(root / authoring_rel, "canonical daily authoring")
    if authoring_doc.get("contractVersion") != "2.0.0" or authoring_doc.get("episodeDate") != date:
        raise SemanticFreezeError("new semantic freeze requires canonical Daily Authoring v2")
    dossier_binding = authoring_doc.get("causalDossier")
    if not isinstance(dossier_binding, dict):
        raise SemanticFreezeError("canonical authoring causalDossier binding missing")
    if dossier_binding.get("path") != dossier_rel or dossier_binding.get("sha256") != dossier["sha256"]:
        raise SemanticFreezeError("canonical authoring Causal Dossier binding is stale")
    validation_binding = dossier_binding.get("validation")
    if not isinstance(validation_binding, dict):
        raise SemanticFreezeError("canonical authoring Causal Dossier validation binding missing")
    if validation_binding.get("path") != dossier_receipt_rel or validation_binding.get("sha256") != dossier_receipt["sha256"]:
        raise SemanticFreezeError("canonical authoring Causal Dossier validation binding is stale")

    try:
        validate_editorial_semantic_boundary.verify_acceptance(root, date, root / acceptance_rel)
    except Exception as exc:
        raise SemanticFreezeError(f"Editorial Semantic Acceptance is stale: {exc}") from exc

    return {
        "canonicalAuthoring": authoring,
        "causalDossier": dossier,
        "causalDossierValidation": dossier_receipt,
        "editorialSemanticAcceptance": acceptance,
    }


def _build_legacy_manifest(root: Path, date: str) -> dict[str, Any]:
    parts = _parts(root, date)
    daily = _file_binding(root, f"daily-inputs/{date}/daily_source_package_{date}.md", "daily source package")
    canon = _canon_binding(root)
    digest_payload = {
        "episodeDate": date,
        "parts": [{"path": item["path"], "semanticSha256": item["semanticSha256"]} for item in parts],
        "dailySourceSha256": daily["sha256"],
        "canonManifest": canon,
    }
    return {
        "contractVersion": LEGACY_CONTRACT_VERSION,
        "authority": AUTHORITY,
        "episodeDate": date,
        "canonManifest": canon,
        "parts": parts,
        "dailySourcePackage": daily,
        "sourceSetDigestSha256": canonical_sha(digest_payload),
    }


def build_manifest(root: Path, date: str) -> dict[str, Any]:
    if not DATE_RE.fullmatch(date):
        raise SemanticFreezeError("episode date must be YYYY-MM-DD")
    root = root.resolve()

    # Historical source sets predate canonical Daily Authoring v2. Preserve their
    # deterministic v1.1 builder for compatibility, but never downgrade an existing
    # canonical authoring file: presence of that file means current-v2 rules apply and
    # any unsupported/stale version fails closed inside _require_current_chain().
    authoring_path = root / "daily-authoring" / f"{date}.json"
    if not authoring_path.is_file():
        return _build_legacy_manifest(root, date)

    parts = _parts(root, date)
    daily = _file_binding(root, f"daily-inputs/{date}/daily_source_package_{date}.md", "daily source package")
    canon = _canon_binding(root)
    chain = _require_current_chain(root, date)
    digest_payload = {
        "episodeDate": date,
        "parts": [{"path": item["path"], "semanticSha256": item["semanticSha256"]} for item in parts],
        "dailySourceSha256": daily["sha256"],
        "canonManifest": canon,
        "canonicalAuthoringSemanticSha256": chain["canonicalAuthoring"]["semanticSha256"],
        "causalDossierSemanticSha256": chain["causalDossier"]["semanticSha256"],
        "causalDossierValidationSemanticSha256": chain["causalDossierValidation"]["semanticSha256"],
        "editorialSemanticAcceptanceSemanticSha256": chain["editorialSemanticAcceptance"]["semanticSha256"],
    }
    return {
        "contractVersion": CURRENT_CONTRACT_VERSION,
        "authority": AUTHORITY,
        "episodeDate": date,
        "canonManifest": canon,
        "parts": parts,
        "dailySourcePackage": daily,
        **chain,
        "sourceSetDigestSha256": canonical_sha(digest_payload),
    }


def validate_manifest_shape(manifest: dict[str, Any], date: str) -> None:
    version = manifest.get("contractVersion")
    if version not in {CURRENT_CONTRACT_VERSION, LEGACY_CONTRACT_VERSION}:
        raise SemanticFreezeError("semantic freeze contractVersion mismatch")
    if manifest.get("authority") != AUTHORITY or manifest.get("episodeDate") != date:
        raise SemanticFreezeError("semantic freeze authority/date mismatch")
    if not SHA_RE.fullmatch(str(manifest.get("sourceSetDigestSha256", ""))):
        raise SemanticFreezeError("semantic freeze sourceSetDigestSha256 invalid")
    if not isinstance(manifest.get("parts"), list) or not manifest["parts"]:
        raise SemanticFreezeError("semantic freeze parts must be non-empty")
    if version == CURRENT_CONTRACT_VERSION:
        for key in (
            "canonicalAuthoring",
            "causalDossier",
            "causalDossierValidation",
            "editorialSemanticAcceptance",
        ):
            if not isinstance(manifest.get(key), dict):
                raise SemanticFreezeError(f"semantic freeze {key} binding missing")


def write_manifest(root: Path, date: str, output: Path) -> dict[str, Any]:
    manifest = build_manifest(root, date)
    path = output if output.is_absolute() else root.resolve() / output
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)
    return manifest


def verify_manifest(root: Path, date: str, manifest_path: Path) -> dict[str, Any]:
    root = root.resolve()
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    value = load_json(path, "semantic freeze manifest")
    if not isinstance(value, dict):
        raise SemanticFreezeError("semantic freeze manifest root must be an object")
    validate_manifest_shape(value, date)
    expected = build_manifest(root, date) if value["contractVersion"] == CURRENT_CONTRACT_VERSION else _build_legacy_manifest(root, date)
    if value != expected:
        raise SemanticFreezeError(
            "E_CHATGPT_SEMANTIC_FREEZE_STALE: committed semantic freeze no longer matches bound authority"
        )
    return value


def manifest_sha256(root: Path, manifest_path: Path) -> str:
    path = manifest_path if manifest_path.is_absolute() else root.resolve() / manifest_path
    if not path.is_file():
        raise SemanticFreezeError(f"semantic freeze manifest missing: {path}")
    return sha256_file(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--date", required=True)
    create.add_argument("--output", type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("--date", required=True)
    verify.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    try:
        if args.command == "create":
            output = args.output or Path("semantic-freezes") / f"{args.date}.json"
            manifest = write_manifest(root, args.date, output)
            path = output if output.is_absolute() else root / output
            result = {
                "status": "PASS",
                "episodeDate": args.date,
                "contractVersion": manifest["contractVersion"],
                "manifest": path.relative_to(root).as_posix(),
                "manifestSha256": sha256_file(path),
                "sourceSetDigestSha256": manifest["sourceSetDigestSha256"],
            }
        else:
            manifest = verify_manifest(root, args.date, args.manifest)
            result = {
                "status": "PASS",
                "episodeDate": args.date,
                "contractVersion": manifest["contractVersion"],
                "manifestSha256": manifest_sha256(root, args.manifest),
                "sourceSetDigestSha256": manifest["sourceSetDigestSha256"],
            }
        code = 0
    except (OSError, SemanticFreezeError) as exc:
        result = {"status": "FAIL", "error": str(exc)}
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
