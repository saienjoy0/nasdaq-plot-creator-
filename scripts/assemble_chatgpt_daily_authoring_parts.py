#!/usr/bin/env python3
"""Assemble split ChatGPT-authored JSON fragments into one daily authoring file.

Fragments are editorially complete inputs created by ChatGPT. This script only performs
a deterministic deep merge, applies explicit ChatGPT-authored Beat patches, binds the
exact daily-source SHA required by lineage, exposes approved review scores under legacy
field names, and activates exact Renderer 2.4 compatibility aliases. It makes no market
or creative decisions of its own.
"""
from __future__ import annotations

import argparse
import hashlib
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


def activate_renderer_240_financial_scope(root: Path) -> None:
    """Align the ephemeral daily materializer with the pinned Renderer 2.4 registry."""
    path = root / "scripts" / "materialize_renderer_sources.py"
    text = path.read_text(encoding="utf-8")
    legacy = 'FINANCIAL_TEMPLATES = {"market-pulse-grid", "dual-asset-split"}'
    renderer_240 = (
        'FINANCIAL_TEMPLATES = {"market-pulse-grid", "earnings-surprise", '
        '"dual-asset-split", "macro-pressure", "source-receipt"}'
    )
    if legacy in text:
        text = text.replace(legacy, renderer_240, 1)
        path.write_text(text, encoding="utf-8")
    elif renderer_240 not in text:
        raise SystemExit("cannot activate Renderer 2.4 financial template scope")


def apply_explicit_beat_patches(value: dict[str, Any]) -> int:
    """Apply patches authored in daily input; no inference or fallback is allowed."""
    patches = value.pop("beatPatches", [])
    if not isinstance(patches, list):
        raise SystemExit("beatPatches must be an array")
    scenes = value.get("scenes")
    if not isinstance(scenes, list):
        raise SystemExit("assembled authoring scenes must be an array")
    applied = 0
    seen: set[tuple[int, int]] = set()
    for row in patches:
        if not isinstance(row, dict):
            raise SystemExit("beatPatches entries must be objects")
        scene_number = row.get("sceneNumber")
        beat_number = row.get("beatNumber")
        fields = row.get("set")
        if not isinstance(scene_number, int) or not 1 <= scene_number <= len(scenes):
            raise SystemExit(f"beat patch sceneNumber invalid: {scene_number}")
        scene = scenes[scene_number - 1]
        beats = scene.get("beats") if isinstance(scene, dict) else None
        if not isinstance(beats, list) or not isinstance(beat_number, int) or not 1 <= beat_number <= len(beats):
            raise SystemExit(f"beat patch beatNumber invalid: scene={scene_number} beat={beat_number}")
        if not isinstance(fields, dict) or not fields:
            raise SystemExit("beat patch set must be a non-empty object")
        key = (scene_number, beat_number)
        if key in seen:
            raise SystemExit(f"duplicate beat patch target: scene={scene_number} beat={beat_number}")
        seen.add(key)
        target = beats[beat_number - 1]
        if not isinstance(target, dict):
            raise SystemExit(f"beat patch target is not an object: scene={scene_number} beat={beat_number}")
        target.update(fields)
        applied += 1
    return applied


def normalize_renderer_visual_modes(value: dict[str, Any]) -> int:
    """Apply template-implied mode aliases only where Renderer projection requires them."""
    changed = 0
    scenes = value.get("scenes")
    if not isinstance(scenes, list):
        raise SystemExit("assembled authoring scenes must be an array")
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        beats = scene.get("beats")
        if not isinstance(beats, list):
            continue
        for beat in beats:
            if not isinstance(beat, dict):
                continue
            if beat.get("visualTemplate") == "source-receipt" and beat.get("visualMode") != "news-media":
                beat["visualMode"] = "news-media"
                changed += 1
    return changed


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
    patch_count = apply_explicit_beat_patches(value)
    review = value.get("review")
    if isinstance(review, dict) and "scores" not in review:
        story_scores = review.get("storyScores")
        if not isinstance(story_scores, dict):
            raise SystemExit("review.storyScores is required")
        review["scores"] = dict(story_scores)
    daily_sha = bind_daily_source_lineage(value, root, args.date)
    activate_renderer_240_financial_scope(root)
    mode_aliases = normalize_renderer_visual_modes(value)
    output = root / "daily-authoring" / f"{args.date}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"ASSEMBLED {len(parts)} authoring parts -> {output}; daily_sha256={daily_sha}; "
        f"beat_patches={patch_count}; renderer_financial_scope=2.4; "
        f"source_receipt_mode_aliases={mode_aliases}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
