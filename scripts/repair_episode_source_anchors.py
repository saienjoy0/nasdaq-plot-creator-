#!/usr/bin/env python3
"""Ensure each Scene has its own narration-source anchor for legacy projection.

This is a mechanical Markdown compatibility repair. It copies the already-authored
`sourceLabel` into the matching Scene block only and makes no editorial changes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = ap.parse_args()
    root = args.repo_root.resolve()
    date = args.date
    authoring = json.loads((root / "daily-authoring" / f"{date}.json").read_text(encoding="utf-8"))
    package = root / "episodes" / date / f"episode_package_public_{date}.md"
    text = package.read_text(encoding="utf-8")
    scenes = authoring.get("scenes", [])
    if len(scenes) != 9:
        raise SystemExit(f"authoring scene count must be 9; found={len(scenes)}")

    for index, scene in enumerate(scenes, 1):
        heading = f"## Scene {index}｜"
        start = text.find(heading)
        if start < 0:
            raise SystemExit(f"Scene heading missing: {heading}")
        if index < 9:
            next_heading = f"## Scene {index + 1}｜"
            end = text.find(next_heading, start + len(heading))
            if end < 0:
                raise SystemExit(f"next Scene heading missing: {next_heading}")
        else:
            end = len(text)
        block = text[start:end]
        source_line = f"- ナレーションで示す出典主体・媒体：{scene.get('sourceLabel', '')}"
        if source_line in block:
            continue
        anchor = f"- 根拠と不確実性：{scene.get('uncertainty', '')}"
        if anchor not in block:
            raise SystemExit(f"Scene {index} uncertainty anchor missing")
        block = block.replace(anchor, source_line + "\n" + anchor, 1)
        text = text[:start] + block + text[end:]

    package.write_text(text, encoding="utf-8")
    print(f"REPAIRED scene-scoped narration source anchors: {package}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
