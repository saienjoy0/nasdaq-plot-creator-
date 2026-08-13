#!/usr/bin/env python3
"""Normalize renderer-only terminal Scene metadata before Visual Intelligence review.

Renderer 2.4 defines Scene 9 as terminal: it cannot transition to a following Scene,
so its transition must be `none` with zero duration. The legacy Renderer canonicalizer
already enforces this rule. Visual Intelligence v1.2 intentionally bypasses that
legacy post-Director canonicalization, therefore the same deterministic terminal rule
must be applied *before* Candidate compilation/Critic review.

This module changes no Story meaning, Beat, Candidate, viewer text, evidence, object,
asset, or earlier Scene transition. It never mutates the producer input.
"""
from __future__ import annotations

import copy
from typing import Any


class VisualIntelligenceTerminalProjectionError(ValueError):
    pass


TERMINAL_TRANSITION = {"type": "none", "durationMs": 0}


def normalize_terminal_transition(render_spec: dict[str, Any]) -> dict[str, Any]:
    projected = copy.deepcopy(render_spec)
    scenes = projected.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 9:
        raise VisualIntelligenceTerminalProjectionError(
            "E_VISUAL_TERMINAL_PROJECTION_SCENE_COUNT: exactly nine Scenes required"
        )
    if not all(isinstance(scene, dict) for scene in scenes):
        raise VisualIntelligenceTerminalProjectionError(
            "E_VISUAL_TERMINAL_PROJECTION_INVALID: every Scene must be an object"
        )

    scenes[-1]["transition"] = dict(TERMINAL_TRANSITION)
    return projected
