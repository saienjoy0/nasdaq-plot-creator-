#!/usr/bin/env python3
"""Validate and normalize registered Remotion 2.4 template variants.

Pre-Visual-Intelligence authoring may defer a semantic multi-variant choice to the
Visual Director. Final Renderer normalization remains strict and never infers that
choice from content.
"""

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


def validate_authored_variant(template: Any, variant: Any, *, path: str) -> None:
    """Strict final validation: semantic multi-variant choices must be resolved."""
    required_variant = SINGLE_VARIANT_BY_TEMPLATE.get(template)
    if required_variant is not None:
        if variant is not None and variant != required_variant:
            raise TemplateVariantError(
                f"{path}: {template} accepts only deterministic variant {required_variant!r}"
            )
        return

    allowed_variants = EXPLICIT_VARIANTS_BY_TEMPLATE.get(template)
    if allowed_variants is None:
        return
    if variant not in allowed_variants:
        raise TemplateVariantError(
            f"{path}: {template} requires explicit variant from {sorted(allowed_variants)}"
        )


def validate_pre_visual_intelligence_variant(
    template: Any,
    variant: Any,
    *,
    path: str,
) -> None:
    """Validate pre-VI authoring without stealing the Visual Director's choice.

    Single-variant templates remain deterministic. Multi-variant templates may be
    unresolved (missing or the materializer placeholder ``default``) until Candidate
    Catalog + Director selection. An explicitly authored value must still be registered.
    """
    required_variant = SINGLE_VARIANT_BY_TEMPLATE.get(template)
    if required_variant is not None:
        if variant is not None and variant != required_variant:
            raise TemplateVariantError(
                f"{path}: {template} accepts only deterministic variant {required_variant!r}"
            )
        return

    allowed_variants = EXPLICIT_VARIANTS_BY_TEMPLATE.get(template)
    if allowed_variants is None:
        return
    if variant is None or variant == "default":
        return
    if variant not in allowed_variants:
        raise TemplateVariantError(
            f"{path}: {template} accepts unresolved pre-VI variant or one of {sorted(allowed_variants)}"
        )


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
            validate_authored_variant(
                template,
                config_variant,
                path=f"{scene.get('sceneId')}/{beat.get('beatId')}",
            )
            if beat_variant is not None and beat_variant != config_variant:
                raise TemplateVariantError(
                    f"{scene.get('sceneId')}/{beat.get('beatId')}: templateVariant must match templateConfig.variant"
                )
            beat["templateVariant"] = config_variant
