#!/usr/bin/env python3
"""Finalize Scene 2 Visual authoring for the H4 frozen fixture.

TEST ONLY. Scene 2 Beat 2 compares a payroll revision (people) with NASDAQ return
(percent). A numeric-axis matrix would imply a shared unit and violates Renderer 2.4.
Keep the approved card and narration, but author it as an evidence boundary before H2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DATE = "2026-08-10"
BEAT_ID = "scene-02-beat-002"


class Scene2AuthoringError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Scene2AuthoringError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise Scene2AuthoringError(f"JSON root must be object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temp = path.with_name(f".{path.name}.h4-scene2.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sync(*, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    bindings_path = root / f"working/{DATE}/story-engine/story_production_bindings.json"
    render_path = root / f"render-specs/{DATE}/render_spec.json"
    bindings = load_json(bindings_path)
    render = load_json(render_path)

    overrides = bindings.get("beat_overrides")
    if not isinstance(overrides, dict):
        raise Scene2AuthoringError("story production beat_overrides must be an object")
    override = overrides.setdefault(BEAT_ID, {})
    override.update(
        {
            "contentType": "text-focus",
            "visualMode": "text-focus",
            "visualTemplate": "evidence-boundary",
            "templateVariant": "confirmed-vs-unconfirmed",
            "visualGrammarId": "evidence",
            "transitionRole": "continuation",
        }
    )

    scenes = render.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 9:
        raise Scene2AuthoringError("render must contain nine scenes")
    scene = scenes[1]
    if scene.get("sceneId") != "scene-02":
        raise Scene2AuthoringError("Scene 2 identity drift")
    beats = scene.get("visualBeats")
    if not isinstance(beats, list) or len(beats) < 2:
        raise Scene2AuthoringError("Scene 2 Beat 2 missing")
    beat = next(
        (
            item
            for item in beats
            if isinstance(item, dict)
            and item.get("beatId") in {"vb-02-02", BEAT_ID}
        ),
        None,
    )
    if beat is None:
        raise Scene2AuthoringError("Scene 2 Beat 2 identity drift")
    if beat.get("objectIds") != ["scene-02-card-002"]:
        raise Scene2AuthoringError(
            f"Scene 2 Beat 2 approved card drift: {beat.get('objectIds')}"
        )
    card = next(
        (
            item
            for item in scene.get("cards", [])
            if isinstance(item, dict) and item.get("cardId") == "scene-02-card-002"
        ),
        None,
    )
    if card is None:
        raise Scene2AuthoringError("Scene 2 Beat 2 approved card missing")
    values = [
        line.get("value")
        for line in card.get("lines", [])
        if isinstance(line, dict) and isinstance(line.get("value"), str)
    ]
    if len(values) < 2 or not any("万人" in value for value in values) or not any("%" in value for value in values):
        raise Scene2AuthoringError(
            "Scene 2 Beat 2 no longer represents the mixed-unit payroll/NASDAQ comparison"
        )

    bindings_sha = write_json(bindings_path, bindings)
    return {
        "status": "pass",
        "episode_date": DATE,
        "visual_beat_id": BEAT_ID,
        "visual_template": override["visualTemplate"],
        "template_variant": override["templateVariant"],
        "visual_grammar_id": override["visualGrammarId"],
        "object_ids": beat["objectIds"],
        "visible_values": values,
        "story_production_bindings_sha256": bindings_sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = sync(repo_root=args.repo_root.resolve())
    except Scene2AuthoringError as exc:
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
