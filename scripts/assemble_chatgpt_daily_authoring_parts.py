#!/usr/bin/env python3
"""Assemble split ChatGPT-authored JSON fragments into one daily authoring file.

Fragments are editorially complete inputs created by ChatGPT. This script only performs
a deterministic deep merge, binds the exact daily-source file SHA required by lineage,
validates that authored Financial Visual Templates are explicitly closed by authored
financial bindings, and exposes already-approved review scores under legacy field names.
It makes no market or creative decisions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import validate_chatgpt_daily_authoring_closure as authoring_closure


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


def bind_daily_source_lineage(value: dict[str, Any], root: Path, date: str) -> str:
    daily_rel = f"daily-inputs/{date}/daily_source_package_{date}.md"
    daily_path = root / daily_rel
    if not daily_path.is_file():
        raise SystemExit(f"daily source package missing: {daily_path}")
    daily_sha = hashlib.sha256(daily_path.read_bytes()).hexdigest()
    dossier = value.get("causalDossier")
    if not isinstance(dossier, dict):
        raise SystemExit("causalDossier is required")
    provenance = dossier.get("input_provenance")
    if not isinstance(provenance, list):
        raise SystemExit("causalDossier.input_provenance is required")
    matches = [
        item for item in provenance
        if isinstance(item, dict)
        and item.get("role") == "daily_input"
        and item.get("path_or_reference") == daily_rel
    ]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one daily_input provenance row for {daily_rel}; found={len(matches)}")
    matches[0]["version_or_hash"] = daily_sha
    return daily_sha


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
    daily_sha = bind_daily_source_lineage(value, root, args.date)
    registry = authoring_closure.load_json(
        root / "contracts" / "financial_recipe_registry.json",
        "financial recipe registry",
    )
    try:
        authoring_closure.validate_or_raise(value, registry)
    except authoring_closure.AuthoringClosureError as exc:
        raise SystemExit(f"daily authoring renderer closure failed:\n{exc}") from exc
    output = root / "daily-authoring" / f"{args.date}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"ASSEMBLED {len(parts)} authoring parts -> {output}; "
        f"daily_sha256={daily_sha}; renderer_closure=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
