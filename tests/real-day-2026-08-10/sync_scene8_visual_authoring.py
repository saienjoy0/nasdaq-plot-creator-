#!/usr/bin/env python3
"""Finalize the corrected Scene 8 Visual authoring for the H4 frozen fixture.

TEST ONLY. This runs before Story->Production projection and does not patch a produced
render. It binds the verified wave-2 timing facts to the two already-authored Scene 8
beats so each Beat owns exactly the card shown during its narration chunk.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DATE = "2026-08-10"


class Scene8AuthoringError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Scene8AuthoringError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise Scene8AuthoringError(f"JSON root must be object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temp = path.with_name(f".{path.name}.h4-scene8.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sync(*, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    path = root / f"render-specs/{DATE}/render_spec.json"
    render = load_json(path)
    if render.get("episode", {}).get("targetDate") != DATE:
        raise Scene8AuthoringError("render targetDate drift")
    scenes = render.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 9:
        raise Scene8AuthoringError("render must contain exactly nine scenes")
    scene = scenes[7]
    if scene.get("sceneId") != "scene-08":
        raise Scene8AuthoringError("Scene 8 identity drift")

    cards = {
        item.get("cardId"): item
        for item in scene.get("cards", [])
        if isinstance(item, dict) and isinstance(item.get("cardId"), str)
    }
    card1 = cards.get("scene-08-card-001")
    card2 = cards.get("scene-08-card-002")
    if card1 is None or card2 is None:
        raise Scene8AuthoringError("Scene 8 approved cards are missing")

    card1.update(
        {
            "title": "発表時刻の初動",
            "lines": [
                {"label": "QQQ", "tone": "neutral", "value": "719.16 → 720.23"},
                {"label": "SOXX", "tone": "neutral", "value": "541.06 → 542.40"},
                {"label": "NVDA", "tone": "neutral", "value": "219.95 → 220.31"},
                {"label": "MCHP", "tone": "neutral", "value": "79.58 → 79.56"},
            ],
        }
    )
    card2.update(
        {
            "title": "言わないこと",
            "lines": [
                {"label": "1", "tone": "neutral", "value": "1分足だけで因果確定"},
                {"label": "2", "tone": "neutral", "value": "MCHPも同時反応した"},
                {"label": "3", "tone": "neutral", "value": "会社固有材料をマクロ原因にする"},
            ],
        }
    )

    beats = scene.get("visualBeats")
    if not isinstance(beats, list) or len(beats) != 2:
        raise Scene8AuthoringError("Scene 8 must contain exactly two Visual Beats")
    beat1 = next(
        (item for item in beats if isinstance(item, dict) and item.get("beatId") == "scene-08-beat-001"),
        None,
    )
    beat2 = next(
        (item for item in beats if isinstance(item, dict) and item.get("beatId") == "scene-08-beat-002"),
        None,
    )
    if beat1 is None or beat2 is None:
        raise Scene8AuthoringError("Scene 8 Beat identity drift")
    beat1["objectIds"] = ["scene-08-card-001"]
    beat2["objectIds"] = ["scene-08-card-002"]

    events = scene.get("visualEvents")
    if not isinstance(events, list):
        raise Scene8AuthoringError("Scene 8 visualEvents missing")
    expected = {
        "scene-08-card-001": "scene-08-chunk-001",
        "scene-08-card-002": "scene-08-chunk-002",
    }
    seen: dict[str, str] = {}
    for event in events:
        if not isinstance(event, dict) or event.get("action") != "show":
            continue
        target = event.get("targetId")
        if target in expected:
            at_chunk = event.get("atChunkId")
            if at_chunk != expected[target]:
                raise Scene8AuthoringError(
                    f"{target}: show event chunk drift actual={at_chunk} expected={expected[target]}"
                )
            seen[target] = at_chunk
    if set(seen) != set(expected):
        raise Scene8AuthoringError(f"Scene 8 show-event coverage drift: {seen}")

    stale = (
        "分足未取得",
        "未確認：8:30 ET直後の分足",
        "対象日のminute dataは取得できませんでした",
    )
    scene_text = json.dumps(scene, ensure_ascii=False)
    hits = [token for token in stale if token in scene_text]
    if hits:
        # All stale phrases must be removed by this authoring pass, including card data.
        scene_text = scene_text
        for token in hits:
            if token in scene_text:
                raise Scene8AuthoringError(f"stale Scene 8 authoring remains: {token}")

    digest = write_json(path, render)
    return {
        "status": "pass",
        "episode_date": DATE,
        "render_authoring_sha256": digest,
        "beat_object_ids": {
            "scene-08-beat-001": beat1["objectIds"],
            "scene-08-beat-002": beat2["objectIds"],
        },
        "show_targets": seen,
        "card_titles": [card1["title"], card2["title"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = sync(repo_root=args.repo_root.resolve())
    except Scene8AuthoringError as exc:
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
