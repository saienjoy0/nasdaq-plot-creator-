#!/usr/bin/env python3
"""Normalize templates that have exactly one registered Remotion 2.4 variant."""

from __future__ import annotations

from typing import Any


class TemplateVariantError(ValueError):
    pass


SINGLE_VARIANT_BY_TEMPLATE = {
    "opening-contradiction": "default",
    "closing-recap": "default",
    "conclusion-card": "default",
    "metric-comparison-board": "default",
    "index-return-bars": "zero-baseline",
    "diverging-stock-bars": "center-zero",
    "causal-lane": "left-to-right",
    "tailwind-headwind": "two-lane",
    "evidence-boundary": "confirmed-vs-unconfirmed",
    "verification-checklist": "default",
    "verification-matrix": "strengthen-vs-weaken",
    "news-media": "default",
    "text-focus": "default",
}


def normalize_single_variant_templates(render_spec: dict[str, Any]) -> None:
    scenes = render_spec.get("scenes")
    if not isinstance(scenes, list):
        raise TemplateVariantError("render spec scenes must be an array")
    for scene in scenes:
        for beat in scene.get("visualBeats", []):
            template = beat.get("visualTemplate")
            required_variant = SINGLE_VARIANT_BY_TEMPLATE.get(template)
            if required_variant is None:
                continue
            config = beat.get("templateConfig")
            if not isinstance(config, dict):
                raise TemplateVariantError(
                    f"{scene.get('sceneId')}/{beat.get('beatId')}: templateConfig missing"
                )
            beat["templateVariant"] = required_variant
            config["variant"] = required_variant
