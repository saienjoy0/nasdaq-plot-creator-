#!/usr/bin/env python3
"""Assemble split ChatGPT-authored JSON fragments into one daily authoring file.

Fragments are editorially complete inputs created by ChatGPT. This script only performs
a deterministic deep merge: dictionaries merge recursively, lists concatenate, and
scalar duplicates must be byte-equivalent. It makes no market or creative decisions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def merge(left: Any, right: Any, path: str = "$") -> Any:
    if isinstance(left, dict) and isinstance(right, dict):
        out = dict(left)
        for key, value in right.items():
            out[key] = merge(out[key], value, f"{path}.{key}") if key in out else value
        return out
    if isinstance(left, list) and isinstance(right, list):
        return [*left, *right]
    if left == right:
        return left
    raise ValueError(f"conflicting scalar at {path}: {left!r} != {right!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = ap.parse_args()
    root = args.repo_root.resolve()
    parts_dir = root / "daily-authoring-parts" / args.date
    parts = sorted(parts_dir.glob("*.json"))
    if not parts:
        raise SystemExit(f"no authoring parts: {parts_dir}")
    value: dict[str, Any] = {}
    for part in parts:
        piece = json.loads(part.read_text(encoding="utf-8"))
        if not isinstance(piece, dict):
            raise SystemExit(f"authoring part root must be object: {part}")
        value = merge(value, piece)
    if value.get("episodeDate") != args.date:
        raise SystemExit("assembled authoring episodeDate mismatch")
    review = value.get("review")
    if isinstance(review, dict) and "scores" not in review:
        story_scores = review.get("storyScores")
        if not isinstance(story_scores, dict):
            raise SystemExit("review.storyScores is required")
        review["scores"] = dict(story_scores)
    output = root / "daily-authoring" / f"{args.date}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ASSEMBLED {len(parts)} authoring parts -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
