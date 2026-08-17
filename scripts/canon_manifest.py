#!/usr/bin/env python3
"""Verify and materialize the single NASDAQ Cafe 01-04 semantic canon manifest."""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "1.0.0"
AUTHORITY = "nasdaq-cafe-semantic-canon"
DEFAULT_MANIFEST = Path("source-of-truth/canon_manifest.json")
SHA_RE = re.compile(r"[0-9a-f]{64}")
EXPECTED_PATHS = {
    "01": "source-of-truth/01_fox_character_bible.md",
    "02": "source-of-truth/02_editorial_bible.md",
    "03": "source-of-truth/03_episode_production_spec.md",
    "04": "source-of-truth/04_entertainment_inquisitor.md",
}
ALLOWED_MODES = {"direct", "gzip+base64-concatenated"}


class CanonManifestError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _safe_path(root: Path, relative: str, label: str, *, must_exist: bool = True) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise CanonManifestError(f"{label} must be a non-empty repo-relative path: {relative!r}")
    if ".." in Path(relative).parts:
        raise CanonManifestError(f"{label} cannot contain '..': {relative}")
    root = root.resolve()
    path = root / relative
    resolved = path.resolve(strict=False)
    if root != resolved and root not in resolved.parents:
        raise CanonManifestError(f"{label} escapes repository root: {relative}")
    if must_exist and not path.is_file():
        raise CanonManifestError(f"missing {label}: {relative}")
    if must_exist and path.is_symlink():
        raise CanonManifestError(f"{label} must not be a symlink: {relative}")
    return path


def load_manifest(root: Path, manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CanonManifestError(f"canon manifest invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise CanonManifestError("canon manifest root must be an object")
    validate_shape(value)
    return value


def validate_shape(manifest: dict[str, Any]) -> None:
    if manifest.get("contractVersion") != CONTRACT_VERSION:
        raise CanonManifestError("canon contractVersion mismatch")
    if manifest.get("authority") != AUTHORITY:
        raise CanonManifestError("canon authority mismatch")
    docs = manifest.get("documents")
    if not isinstance(docs, list) or len(docs) != 4:
        raise CanonManifestError("canon documents must contain exactly 4 entries")
    ids = [str(item.get("id", "")) for item in docs if isinstance(item, dict)]
    if ids != ["01", "02", "03", "04"]:
        raise CanonManifestError("canon document ids must be exactly 01,02,03,04 in order")
    for item in docs:
        if not isinstance(item, dict):
            raise CanonManifestError("canon document entry must be an object")
        doc_id = str(item.get("id"))
        if item.get("logicalPath") != EXPECTED_PATHS[doc_id]:
            raise CanonManifestError(f"canon logicalPath mismatch for {doc_id}")
        if not SHA_RE.fullmatch(str(item.get("sha256", ""))):
            raise CanonManifestError(f"canon sha256 invalid for {doc_id}")
        if not isinstance(item.get("rawBytes"), int) or item["rawBytes"] <= 0:
            raise CanonManifestError(f"canon rawBytes invalid for {doc_id}")
        storage = item.get("storage")
        if not isinstance(storage, dict) or storage.get("mode") not in ALLOWED_MODES:
            raise CanonManifestError(f"canon storage mode invalid for {doc_id}")
        parts = storage.get("parts")
        if not isinstance(parts, list) or not parts or not all(isinstance(p, str) and p for p in parts):
            raise CanonManifestError(f"canon storage parts invalid for {doc_id}")
        if storage["mode"] == "direct" and parts != [item["logicalPath"]]:
            raise CanonManifestError(f"direct canon {doc_id} must point only to its logicalPath")
        if doc_id in {"03", "04"} and storage["mode"] == "direct":
            raise CanonManifestError(f"packed canon {doc_id} cannot use direct storage")


def document_bytes(root: Path, item: dict[str, Any]) -> bytes:
    storage = item["storage"]
    parts = [_safe_path(root, rel, f"canon part {item['id']}") for rel in storage["parts"]]
    if storage["mode"] == "direct":
        return parts[0].read_bytes()
    try:
        encoded = "".join(path.read_text(encoding="ascii").strip() for path in parts)
        return gzip.decompress(base64.b64decode(encoded, validate=True))
    except Exception as exc:
        raise CanonManifestError(f"cannot decode canon {item['id']}: {exc}") from exc


def verify(root: Path, manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    root = root.resolve()
    manifest = load_manifest(root, manifest_path)
    results = []
    for item in manifest["documents"]:
        data = document_bytes(root, item)
        actual = sha256_bytes(data)
        if actual != item["sha256"]:
            raise CanonManifestError(
                f"E_CANON_SHA_MISMATCH: {item['id']} expected {item['sha256']} got {actual}"
            )
        if len(data) != item["rawBytes"]:
            raise CanonManifestError(
                f"E_CANON_SIZE_MISMATCH: {item['id']} expected {item['rawBytes']} got {len(data)}"
            )
        results.append({"id": item["id"], "logicalPath": item["logicalPath"], "sha256": actual})
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    return {
        "status": "PASS",
        "manifestPath": path.relative_to(root).as_posix(),
        "manifestSha256": sha256_file(path),
        "documents": results,
    }


def materialize(root: Path, manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    root = root.resolve()
    manifest = load_manifest(root, manifest_path)
    written = []
    for item in manifest["documents"]:
        data = document_bytes(root, item)
        if sha256_bytes(data) != item["sha256"] or len(data) != item["rawBytes"]:
            raise CanonManifestError(f"canon source verification failed before materialization: {item['id']}")
        if item["storage"]["mode"] == "direct":
            continue
        output = _safe_path(root, item["logicalPath"], f"canon output {item['id']}", must_exist=False)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        written.append(item["logicalPath"])
    result = verify(root, manifest_path)
    result["materialized"] = written
    return result


def manifest_binding(root: Path, manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, str]:
    root = root.resolve()
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    verify(root, manifest_path)
    return {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["verify", "materialize"])
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    try:
        result = verify(args.repo_root, args.manifest) if args.command == "verify" else materialize(args.repo_root, args.manifest)
        code = 0
    except (OSError, CanonManifestError) as exc:
        result = {"status": "FAIL", "error": str(exc)}
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
