#!/usr/bin/env python3
"""Create the pre-Director Renderer 2.4 input without making editorial selections.

This reuses only the existing structural projection and reaction-data materialization.
It deliberately does NOT run Financial selected-path integration, terminal assembly,
shot materialization, or any legacy Visual Director selection before vNext.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import finalize_renderer_package
import remotion_240_projection

PRODUCER_VISUAL_MODE_ALIASES = {
    "verification": "verification-points",
    "closing-recap": "conclusion-card",
    "causal-chain": "causal-diagram",
    "intraday-comparison": "stock-comparison",
}


def _normalize_producer_modes(render: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(render)
    for scene in value.get("scenes", []):
        if not isinstance(scene, dict):
            continue
        mode = scene.get("visualMode")
        if mode in PRODUCER_VISUAL_MODE_ALIASES:
            scene["visualMode"] = PRODUCER_VISUAL_MODE_ALIASES[mode]
        for beat in scene.get("visualBeats", []):
            if not isinstance(beat, dict):
                continue
            mode = beat.get("visualMode")
            if mode in PRODUCER_VISUAL_MODE_ALIASES:
                beat["visualMode"] = PRODUCER_VISUAL_MODE_ALIASES[mode]
    return value


def canonicalize_for_visual_director(
    *,
    render: dict[str, Any],
    output_root: Path,
    date: str,
) -> dict[str, Any]:
    output_root = output_root.resolve()
    producer = _normalize_producer_modes(render)
    strict = finalize_renderer_package._strict_renderer_projection(
        producer,
        renderer_contract_version="2.4.0",
        final_episode_contract_path=output_root / "working" / date / "final_episode_contract.json",
        semantics_path=output_root / "contracts" / "visual_grammar_semantics.json",
        renderer_compatibility_path=output_root / "contracts" / "visual_grammar_renderer_compatibility.json",
    )
    remotion_240_projection.canonicalize_render_spec(
        strict,
        episode_date=date,
        reaction_bindings_path=output_root / "working" / date / "reaction_timeline_bindings.json",
    )
    return strict
