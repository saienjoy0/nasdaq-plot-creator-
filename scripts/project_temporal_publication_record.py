#!/usr/bin/env python3
"""Deterministically add Temporal Evidence v1.1 to an authored publication record."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from temporal_evidence import (
    TemporalEvidenceError,
    project_publication_temporal,
    validate_publication_temporal,
)


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TemporalEvidenceError(f"JSON root must be an object: {path}")
    return value


def write_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.temporal.tmp")
    temp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publication-record", required=True, type=Path)
    parser.add_argument("--causal-dossier", required=True, type=Path)
    parser.add_argument("--story-plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        projected = project_publication_temporal(
            load(args.publication_record),
            dossier=load(args.causal_dossier),
            story_plan=load(args.story_plan),
        )
        validate_publication_temporal(projected, args.repo_root.resolve())
        write_atomic(args.output, projected)
    except (OSError, json.JSONDecodeError, KeyError, TemporalEvidenceError) as exc:
        print(f"FAIL: {exc}")
        return 2
    print(f"PASS: wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
