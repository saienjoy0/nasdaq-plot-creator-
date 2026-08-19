#!/usr/bin/env python3
"""Single-writer Visual Source checkpoint for current Daily Authoring v2."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class VisualSourceCheckpointError(RuntimeError):
    pass


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def materialize(*, work: Path, date: str, projected: dict[str, Any]) -> str:
    """Seed before Requirements; preserve byte-for-byte after Requirements seal."""
    requirements_sealed = work / "visual-intelligence" / "visual_requirements.json"
    intents_path = work / "visual_source_intents.json"
    selection_path = work / "visual_source_selection.json"
    if requirements_sealed.is_file():
        if not intents_path.is_file():
            raise VisualSourceCheckpointError(
                "sealed Visual Requirements require the existing ChatGPT Visual Source checkpoint"
            )
        return "preserved"

    _write(
        intents_path,
        {
            "contractVersion": "1.0.0",
            "episodeDate": date,
            "intents": projected.get("visualSourceIntents", []),
        },
    )
    if projected.get("visualSourceSelection") is not None:
        _write(selection_path, projected["visualSourceSelection"])
    return "seeded"
