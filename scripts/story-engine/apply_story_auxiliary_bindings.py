#!/usr/bin/env python3
"""Apply explicit Story Engine auxiliary bindings after Story visual projection.

The base renderer bindings remain Story-independent so legacy compatibility tests can
canonicalize the pre-Story render spec. Story-only bindings are injected immediately
before renderer canonicalization, from the same ChatGPT-authored Story binding file
that changes the corresponding visual beat.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return value


def dump(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def beat_aliases(value: str) -> set[str]:
    aliases = {value}
    match = re.fullmatch(r"scene-(0[1-9])-beat-([0-9]{3})", value)
    if match:
        aliases.add(f"vb-{match.group(1)}-{int(match.group(2)):02d}")
    match = re.fullmatch(r"vb-(0[1-9])-([0-9]{2})", value)
    if match:
        aliases.add(f"scene-{match.group(1)}-beat-{int(match.group(2)):03d}")
    return aliases


def apply_story_reaction_bindings(
    story_bindings_path: Path,
    reaction_bindings_path: Path,
) -> dict[str, Any]:
    story = load(story_bindings_path)
    reaction = load(reaction_bindings_path)
    story_date = story.get("episode_date")
    reaction_date = reaction.get("episodeDate")
    if story_date != reaction_date:
        raise ValueError(
            f"episode date mismatch: story={story_date!r} reaction={reaction_date!r}"
        )

    rows = reaction.get("bindings")
    if not isinstance(rows, list):
        raise ValueError("reaction timeline bindings must contain bindings array")

    # If Story explicitly replaces an event-reaction-timeline Beat with another
    # template, its old base reaction binding is stale and must not survive into
    # renderer canonicalization. Remove only that exact Beat (including the
    # historical vb-XX-YY alias), never unrelated reaction bindings.
    replaced_aliases: set[str] = set()
    for source_beat_id, override in story.get("beat_overrides", {}).items():
        if not isinstance(source_beat_id, str) or not isinstance(override, dict):
            continue
        template = override.get("visualTemplate")
        if isinstance(template, str) and template != "event-reaction-timeline":
            replaced_aliases.update(beat_aliases(source_beat_id))
    removed = [
        row.get("visualBeatId")
        for row in rows
        if isinstance(row, dict) and row.get("visualBeatId") in replaced_aliases
    ]
    if removed:
        rows[:] = [
            row
            for row in rows
            if not (
                isinstance(row, dict)
                and row.get("visualBeatId") in replaced_aliases
            )
        ]

    by_id = {
        row.get("visualBeatId"): row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("visualBeatId"), str)
    }

    inserted: list[str] = []
    for source_beat_id, override in story.get("beat_overrides", {}).items():
        if not isinstance(override, dict):
            continue
        binding = override.get("reactionTimelineBinding")
        if binding is None:
            continue
        if not isinstance(binding, dict):
            raise ValueError(f"{source_beat_id}: reactionTimelineBinding must be an object")
        required = {
            "visualBeatId",
            "visualTemplate",
            "templateVariant",
            "precision",
            "eventOrderIds",
            "seriesObjectIds",
            "evidenceBasis",
        }
        missing = sorted(required - set(binding))
        if missing:
            raise ValueError(
                f"{source_beat_id}: reactionTimelineBinding missing {missing}"
            )
        if override.get("visualTemplate") != "event-reaction-timeline":
            raise ValueError(
                f"{source_beat_id}: reaction binding requires event-reaction-timeline override"
            )
        if binding["visualTemplate"] != override.get("visualTemplate"):
            raise ValueError(f"{source_beat_id}: reaction binding template mismatch")
        if binding["templateVariant"] != override.get("templateVariant"):
            raise ValueError(f"{source_beat_id}: reaction binding variant mismatch")
        beat_id = binding["visualBeatId"]
        if not isinstance(beat_id, str) or not beat_id:
            raise ValueError(f"{source_beat_id}: reaction visualBeatId is invalid")
        existing = by_id.get(beat_id)
        if existing is not None:
            if existing != binding:
                raise ValueError(
                    f"{source_beat_id}: conflicting reaction binding already exists for {beat_id}"
                )
            continue
        rows.append(binding)
        by_id[beat_id] = binding
        inserted.append(beat_id)

    dump(reaction_bindings_path, reaction)
    return {
        "status": "pass",
        "episode_date": story_date,
        "removed_reaction_bindings": removed,
        "inserted_reaction_bindings": inserted,
        "binding_count": len(rows),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--story-bindings", type=Path, required=True)
    ap.add_argument("--reaction-timeline-bindings", type=Path, required=True)
    args = ap.parse_args()
    result = apply_story_reaction_bindings(
        args.story_bindings,
        args.reaction_timeline_bindings,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
