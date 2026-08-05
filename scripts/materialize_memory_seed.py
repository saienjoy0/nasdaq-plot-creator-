#!/usr/bin/env python3
"""Materialize one pinned, approved renderer episode into editorial memory.

The manifest contains a fixed source repository, commit, paths, SHA-256 values,
and an already editorially-approved publication record. This script only
fetches, verifies, plans, and applies deterministic memory promotion. It does
not decide market causality or create new claims with an LLM.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Mapping


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def safe_repo_path(repo_root: Path, raw: str) -> Path:
    candidate = (repo_root / raw).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise SystemExit(f"REFUSE: path escapes repository: {raw}") from exc
    return candidate


def require_string(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise SystemExit(f"REFUSE: missing string field {key}")
    return value


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "nasdaq-cafe-editorial-memory-seed/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def run(command: list[str], cwd: Path) -> None:
    print("RUN", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path
    manifest_path = manifest_path.resolve()
    try:
        manifest_path.relative_to(repo_root)
    except ValueError as exc:
        raise SystemExit("REFUSE: manifest must be inside repository") from exc

    manifest = read_json(manifest_path)
    if not isinstance(manifest, Mapping):
        raise SystemExit("REFUSE: manifest must be an object")
    if manifest.get("contract_version") != "1.0.0":
        raise SystemExit("REFUSE: unsupported seed contract_version")

    seed_id = require_string(manifest, "seed_id")
    episode_date = require_string(manifest, "episode_date")
    revision = require_string(manifest, "revision")
    source_repository = require_string(manifest, "source_repository")
    source_commit = require_string(manifest, "source_commit")
    if revision != "v001":
        raise SystemExit("REFUSE: initial seed revision must be v001")

    source_files = manifest.get("source_files")
    if not isinstance(source_files, Mapping):
        raise SystemExit("REFUSE: source_files must be an object")

    resolved_sources: dict[str, dict[str, str]] = {}
    for key in ("episode_package", "render_spec", "validator_report"):
        item = source_files.get(key)
        if not isinstance(item, Mapping):
            raise SystemExit(f"REFUSE: missing source file declaration {key}")
        remote_path = require_string(item, "remote_path")
        local_path = require_string(item, "local_path")
        expected_sha = require_string(item, "sha256")
        if len(expected_sha) != 64 or any(ch not in "0123456789abcdef" for ch in expected_sha):
            raise SystemExit(f"REFUSE: invalid SHA-256 for {key}")
        destination = safe_repo_path(repo_root, local_path)
        if destination.exists():
            data = destination.read_bytes()
        else:
            url = (
                f"https://raw.githubusercontent.com/{source_repository}/"
                f"{source_commit}/{remote_path}"
            )
            data = fetch_bytes(url)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        actual_sha = sha256_bytes(data)
        if actual_sha != expected_sha:
            raise SystemExit(
                f"REFUSE: SHA-256 mismatch for {key}: expected {expected_sha}, got {actual_sha}"
            )
        if not data:
            raise SystemExit(f"REFUSE: empty source file {key}")
        resolved_sources[key] = {
            "remote_path": remote_path,
            "local_path": local_path,
            "sha256": actual_sha,
        }
        print(f"VERIFIED_SOURCE {key} {actual_sha}")

    publication = manifest.get("publication_record")
    if not isinstance(publication, Mapping):
        raise SystemExit("REFUSE: publication_record must be an object")
    publication_record = copy.deepcopy(dict(publication))
    if publication_record.get("episode_date") != episode_date:
        raise SystemExit("REFUSE: publication record date differs from seed date")
    if publication_record.get("revision") != revision:
        raise SystemExit("REFUSE: publication record revision differs from seed revision")

    declared_paths = publication_record.get("source_paths")
    declared_hashes = publication_record.get("source_hashes")
    if not isinstance(declared_paths, Mapping) or not isinstance(declared_hashes, Mapping):
        raise SystemExit("REFUSE: publication record must declare source paths and hashes")
    for key, source in resolved_sources.items():
        if declared_paths.get(key) != source["local_path"]:
            raise SystemExit(f"REFUSE: source path mismatch for {key}")
        if declared_hashes.get(key) != source["sha256"]:
            raise SystemExit(f"REFUSE: source hash mismatch for {key}")

    record_path = manifest_path.parent / "publication_record.json"
    write_json(record_path, publication_record)

    working_root = repo_root / "working" / "memory-seeds" / seed_id
    first_run = working_root / "plan"
    noop_run = working_root / "noop"
    if working_root.exists():
        shutil.rmtree(working_root)

    run(
        [
            sys.executable,
            "scripts/plan_memory_promotion.py",
            str(record_path.relative_to(repo_root)),
            "--output",
            str(first_run.relative_to(repo_root)),
        ],
        repo_root,
    )
    plan = read_json(first_run / "promotion_plan.json")
    if plan.get("safe_to_apply") is not True:
        raise SystemExit("REFUSE: promotion plan is not safe to apply")
    if plan.get("revision") != revision:
        raise SystemExit("REFUSE: planned revision differs from manifest")

    if args.apply:
        run(
            [
                sys.executable,
                "scripts/apply_memory_promotion.py",
                str((first_run / "promotion_plan.json").relative_to(repo_root)),
                "--apply",
                "--no-commit",
            ],
            repo_root,
        )
    elif plan.get("noop") is not True:
        print("PLAN_ONLY: rerun with --apply to write editorial memory")
        return 0

    run(
        [
            sys.executable,
            "scripts/plan_memory_promotion.py",
            str(record_path.relative_to(repo_root)),
            "--output",
            str(noop_run.relative_to(repo_root)),
        ],
        repo_root,
    )
    noop_plan = read_json(noop_run / "promotion_plan.json")
    if noop_plan.get("safe_to_apply") is not True or noop_plan.get("noop") is not True:
        raise SystemExit("REFUSE: repeated seed promotion is not a safe no-op")
    if noop_plan.get("operations") != []:
        raise SystemExit("REFUSE: no-op plan contains operations")

    episode_root = repo_root / "editorial-memory" / "episodes" / episode_date
    archive = episode_root / "revisions" / revision
    index = read_json(episode_root / "index.json")
    provenance = read_json(archive / "provenance.json")
    if index.get("current_revision") != revision:
        raise SystemExit("REFUSE: archive index does not point to seeded revision")

    archived_pairs = {
        "episode_package": archive / "episode_package.md",
        "render_spec": archive / "render_spec.json",
        "validator_report": archive / "validator_report.json",
    }
    for key, path in archived_pairs.items():
        actual = sha256_bytes(path.read_bytes())
        if actual != resolved_sources[key]["sha256"]:
            raise SystemExit(f"REFUSE: archived SHA-256 mismatch for {key}")

    expected_memory = manifest.get("expected_memory", {})
    if not isinstance(expected_memory, Mapping):
        raise SystemExit("REFUSE: expected_memory must be an object")
    generated = provenance.get("generated_memory_ids", {})
    if not isinstance(generated, Mapping):
        raise SystemExit("REFUSE: provenance lacks generated_memory_ids")
    checks = {
        "threads": "thread_ids",
        "claims": "claim_ids",
        "aliases": "entity_ids",
    }
    for generated_key, expected_key in checks.items():
        expected = sorted(expected_memory.get(expected_key, []))
        actual = sorted(generated.get(generated_key, []))
        if actual != expected:
            raise SystemExit(
                f"REFUSE: generated {generated_key} differ: expected {expected}, got {actual}"
            )

    report = {
        "contract_version": "1.0.0",
        "seed_id": seed_id,
        "status": "verified",
        "episode_date": episode_date,
        "revision": revision,
        "source_repository": source_repository,
        "source_commit": source_commit,
        "source_files": resolved_sources,
        "generated_memory_ids": {
            "threads": sorted(generated.get("threads", [])),
            "claims": sorted(generated.get("claims", [])),
            "aliases": sorted(generated.get("aliases", [])),
            "lessons": sorted(generated.get("lessons", [])),
        },
        "repeat_result": "noop",
    }
    write_json(manifest_path.parent / "seed_report.json", report)
    print(f"SEED_VERIFIED {episode_date}/{revision}")
    print("REPEAT_RESULT noop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
