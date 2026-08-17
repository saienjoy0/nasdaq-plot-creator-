#!/usr/bin/env python3
"""Create and verify the committed ChatGPT semantic-source freeze.

WS-3 freezes only the committed semantic authority inputs: ChatGPT-authored JSON
fragments plus the exact daily evidence package they cite. It deliberately does not
freeze generated render_spec / episode-package outputs yet; WS-4 removes the remaining
secondary Story Engine semantic projection before those outputs can become immutable.

The manifest contains no timestamp, so identical inputs produce identical bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
SHA_RE = re.compile(r"[0-9a-f]{64}")
CONTRACT_VERSION = "1.0.0"
AUTHORITY = "chatgpt-semantic-source"


class SemanticFreezeError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


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
    if root != path and root not in path.parents:
        raise SemanticFreezeError(f"{label} escapes repository root: {relative}")
    if not path.is_file():
        raise SemanticFreezeError(f"missing {label}: {relative}")
    return path


def _json_binding(root: Path, relative: str, label: str) -> dict[str, str]:
    path = _repo_file(root, relative, label)
    value = load_json(path, label)
    if not isinstance(value, dict):
        raise SemanticFreezeError(f"{label} root must be an object: {relative}")
    return {
        "path": relative,
        "sha256": sha256_file(path),
        "semanticSha256": canonical_sha(value),
    }


def _file_binding(root: Path, relative: str, label: str) -> dict[str, str]:
    path = _repo_file(root, relative, label)
    return {"path": relative, "sha256": sha256_file(path)}


def build_manifest(root: Path, date: str) -> dict[str, Any]:
    if not DATE_RE.fullmatch(date):
        raise SemanticFreezeError("episode date must be YYYY-MM-DD")
    root = root.resolve()
    parts_dir = root / "daily-authoring-parts" / date
    parts = sorted(parts_dir.glob("*.json"))
    if not parts:
        raise SemanticFreezeError(f"no ChatGPT authoring parts for {date}")

    part_bindings: list[dict[str, str]] = []
    for path in parts:
        relative = path.relative_to(root).as_posix()
        part_bindings.append(_json_binding(root, relative, "ChatGPT authoring part"))

    daily_rel = f"daily-inputs/{date}/daily_source_package_{date}.md"
    daily = _file_binding(root, daily_rel, "daily source package")
    digest_payload = {
        "episodeDate": date,
        "parts": [
            {"path": item["path"], "semanticSha256": item["semanticSha256"]}
            for item in part_bindings
        ],
        "dailySourceSha256": daily["sha256"],
    }
    return {
        "contractVersion": CONTRACT_VERSION,
        "authority": AUTHORITY,
        "episodeDate": date,
        "parts": part_bindings,
        "dailySourcePackage": daily,
        "sourceSetDigestSha256": canonical_sha(digest_payload),
    }


def validate_manifest_shape(manifest: dict[str, Any], date: str) -> None:
    if manifest.get("contractVersion") != CONTRACT_VERSION:
        raise SemanticFreezeError("semantic freeze contractVersion mismatch")
    if manifest.get("authority") != AUTHORITY:
        raise SemanticFreezeError("semantic freeze authority mismatch")
    if manifest.get("episodeDate") != date:
        raise SemanticFreezeError("semantic freeze episodeDate mismatch")
    if not SHA_RE.fullmatch(str(manifest.get("sourceSetDigestSha256", ""))):
        raise SemanticFreezeError("semantic freeze sourceSetDigestSha256 invalid")
    parts = manifest.get("parts")
    if not isinstance(parts, list) or not parts:
        raise SemanticFreezeError("semantic freeze parts must be a non-empty array")


def write_manifest(root: Path, date: str, output: Path) -> dict[str, Any]:
    manifest = build_manifest(root, date)
    output = output if output.is_absolute() else root.resolve() / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_manifest(root: Path, date: str, manifest_path: Path) -> dict[str, Any]:
    root = root.resolve()
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    value = load_json(path, "semantic freeze manifest")
    if not isinstance(value, dict):
        raise SemanticFreezeError("semantic freeze manifest root must be an object")
    validate_manifest_shape(value, date)
    expected = build_manifest(root, date)
    if value != expected:
        raise SemanticFreezeError(
            "E_CHATGPT_SEMANTIC_FREEZE_STALE: committed semantic freeze no longer matches ChatGPT source"
        )
    return value


def manifest_sha256(root: Path, manifest_path: Path) -> str:
    root = root.resolve()
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
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
                "manifest": path.relative_to(root).as_posix(),
                "manifestSha256": sha256_file(path),
                "sourceSetDigestSha256": manifest["sourceSetDigestSha256"],
            }
        else:
            manifest = verify_manifest(root, args.date, args.manifest)
            result = {
                "status": "PASS",
                "episodeDate": args.date,
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
