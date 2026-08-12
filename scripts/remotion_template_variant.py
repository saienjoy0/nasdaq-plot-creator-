#!/usr/bin/env python3
"""Normalize registered Remotion 2.4 template variants without inferring meaning."""

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
    "news-media": "default",
    "text-focus": "default",
}

EXPLICIT_VARIANTS_BY_TEMPLATE = {
    "verification-matrix": {"strengthen-vs-weaken", "reported-sequence"},
}


def normalize_single_variant_templates(render_spec: dict[str, Any]) -> None:
    scenes = render_spec.get("scenes")
    if not isinstance(scenes, list):
        raise TemplateVariantError("render spec scenes must be an array")
    for scene in scenes:
        for beat in scene.get("visualBeats", []):
            template = beat.get("visualTemplate")
            config = beat.get("templateConfig")
            if not isinstance(config, dict):
                raise TemplateVariantError(
                    f"{scene.get('sceneId')}/{beat.get('beatId')}: templateConfig missing"
                )

            required_variant = SINGLE_VARIANT_BY_TEMPLATE.get(template)
            if required_variant is not None:
                beat["templateVariant"] = required_variant
                config["variant"] = required_variant
                continue

            allowed_variants = EXPLICIT_VARIANTS_BY_TEMPLATE.get(template)
            if allowed_variants is None:
                continue
            config_variant = config.get("variant")
            beat_variant = beat.get("templateVariant")
            if config_variant != beat_variant or config_variant not in allowed_variants:
                raise TemplateVariantError(
                    f"{scene.get('sceneId')}/{beat.get('beatId')}: {template} requires an explicit matching variant from {sorted(allowed_variants)}"
                )
