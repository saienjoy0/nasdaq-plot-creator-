#!/usr/bin/env python3
"""Restore the immutable 2026-08-10 research intake files that live outside the base payload.

TEST ONLY. The historical acceptance payload intentionally contains the authored
Research/Story/Visual workspace, while the frozen Research Input Manifest and the
files it binds remain normal repository files. H4 checks out the pinned acceptance
commit separately; this helper copies only those immutable intake files into the
regression workspace and verifies every declared SHA before production continues.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DATE = "2026-08-10"
EXPECTED_MANIFEST_SHA256 = "76fd1cbfeb90597e5d26121b9769a5730c46faca0ae74335ecf7404f2d6ecf14"
MANIFEST_REL = Path(f"research/{DATE}/research_input_manifest.json")


class IntakeRestoreError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntakeRestoreError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise IntakeRestoreError(f"JSON root must be an object: {path}")
    return value


def safe_repo_path(root: Path, relative: str | Path, label: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute():
        raise IntakeRestoreError(f"{label}: absolute paths are forbidden")
    resolved_root = root.resolve()
    resolved = (resolved_root / rel).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise IntakeRestoreError(f"{label}: path escapes repository root: {rel}")
    return resolved


def copy_exact(source_root: Path, target_root: Path, relative: str | Path) -> Path:
    source = safe_repo_path(source_root, relative, "source")
    target = safe_repo_path(target_root, relative, "target")
    if not source.is_file():
        raise IntakeRestoreError(f"immutable intake source missing: {relative}")
    payload = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(f".{target.name}.h4-intake.tmp")
    temp.write_bytes(payload)
    temp.replace(target)
    if target.read_bytes() != payload:
        raise IntakeRestoreError(f"byte-exact intake restore failed: {relative}")
    return target


def restore(*, repo_root: Path, acceptance_source: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    acceptance_source = acceptance_source.resolve()

    manifest_source = safe_repo_path(acceptance_source, MANIFEST_REL, "manifest source")
    if not manifest_source.is_file():
        raise IntakeRestoreError(f"pinned manifest missing: {MANIFEST_REL}")
    manifest_sha = sha256_file(manifest_source)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        raise IntakeRestoreError(
            f"pinned research manifest SHA drift: actual={manifest_sha} expected={EXPECTED_MANIFEST_SHA256}"
        )
    manifest = load_json(manifest_source)
    if manifest.get("episode_date") != DATE:
        raise IntakeRestoreError("research manifest episode_date drift")

    declared_inputs = manifest.get("inputs")
    if not isinstance(declared_inputs, dict) or not declared_inputs:
        raise IntakeRestoreError("research manifest inputs must be a non-empty object")

    restored: list[dict[str, str]] = []
    # Restore declared inputs first, then the manifest that binds them.
    for input_name, ref in declared_inputs.items():
        if not isinstance(ref, dict):
            raise IntakeRestoreError(f"manifest input {input_name} must be an object")
        relative = ref.get("path")
        expected_sha = ref.get("sha256")
        if not isinstance(relative, str) or not relative:
            raise IntakeRestoreError(f"manifest input {input_name} path missing")
        if not isinstance(expected_sha, str) or len(expected_sha) != 64:
            raise IntakeRestoreError(f"manifest input {input_name} sha256 missing")

        source = safe_repo_path(acceptance_source, relative, f"{input_name} source")
        if not source.is_file():
            raise IntakeRestoreError(f"manifest input source missing: {relative}")
        source_sha = sha256_file(source)
        if source_sha != expected_sha:
            raise IntakeRestoreError(
                f"manifest input SHA drift before copy: {input_name} actual={source_sha} expected={expected_sha}"
            )
        target = copy_exact(acceptance_source, repo_root, relative)
        target_sha = sha256_file(target)
        if target_sha != expected_sha:
            raise IntakeRestoreError(
                f"manifest input SHA drift after copy: {input_name} actual={target_sha} expected={expected_sha}"
            )
        restored.append({"name": input_name, "path": relative, "sha256": target_sha})

    manifest_target = copy_exact(acceptance_source, repo_root, MANIFEST_REL)
    if sha256_file(manifest_target) != EXPECTED_MANIFEST_SHA256:
        raise IntakeRestoreError("restored research manifest SHA mismatch")

    return {
        "status": "pass",
        "episode_date": DATE,
        "manifest": {
            "path": MANIFEST_REL.as_posix(),
            "sha256": EXPECTED_MANIFEST_SHA256,
        },
        "restored_inputs": restored,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--acceptance-source", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = restore(
            repo_root=args.repo_root.resolve(),
            acceptance_source=args.acceptance_source.resolve(),
        )
    except IntakeRestoreError as exc:
        print(json.dumps({"status": "fail", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2

    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output
        if not output.is_absolute():
            output = args.repo_root.resolve() / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
