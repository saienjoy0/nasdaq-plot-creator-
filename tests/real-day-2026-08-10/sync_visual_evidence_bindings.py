#!/usr/bin/env python3
"""Synchronize the 2026-08-10 evidence-first Visual Beat into Story bindings.

Acceptance-only helper. It changes no narration or causal meaning. The purpose is to
make Pre-TTS validation and the public episode package see the same explicitly authored
Scene 8 visual that is present in render_spec.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DATE = "2026-08-10"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def apply(root: Path) -> dict[str, Any]:
    render_path = root / f"render-specs/{DATE}/render_spec.json"
    bindings_path = root / f"working/{DATE}/story-engine/story_production_bindings.json"
    render = load(render_path)
    bindings = load(bindings_path)
    scene8 = next(
        scene for scene in render.get("scenes", []) if scene.get("sceneNumber") == 8
    )
    beat = scene8["visualBeats"][0]
    beat_id = beat.get("beatId")
    if not isinstance(beat_id, str) or not beat_id:
        raise SystemExit("Scene 8 beatId missing")
    overrides = bindings.setdefault("beat_overrides", {})
    override = overrides.setdefault(beat_id, {})
    override.update(
        {
            "screenQuestion": beat["screenQuestion"],
            "primaryElement": beat["primaryElement"],
            "viewerTexts": beat["viewerTexts"],
            "changeCue": beat["changeCue"],
            "contentType": "event-reaction-timeline",
            "visualTemplate": "event-reaction-timeline",
            "visualMode": "timeline",
            "screenState": "Chart",
            "templateVariant": "verified-series",
            "visualGrammarId": "reaction",
            "transitionRole": "major-shift",
        }
    )
    write(bindings_path, bindings)
    return {
        "status": "pass",
        "episodeDate": DATE,
        "beatId": beat_id,
        "visualTemplate": "event-reaction-timeline",
        "templateVariant": "verified-series",
        "visualGrammarId": "reaction",
        "narrationChanged": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = apply(args.repo_root.resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
