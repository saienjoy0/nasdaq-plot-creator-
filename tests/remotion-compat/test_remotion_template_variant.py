from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import remotion_template_variant as variants  # noqa: E402


def spec_for(template: str, *, beat_variant=None, config_variant=None):
    beat = {
        "beatId": "scene-08-beat-001",
        "visualTemplate": template,
        "templateConfig": {},
    }
    if beat_variant is not None:
        beat["templateVariant"] = beat_variant
    if config_variant is not None:
        beat["templateConfig"]["variant"] = config_variant
    return {"scenes": [{"sceneId": "scene-08", "visualBeats": [beat]}]}


@pytest.mark.parametrize("variant", ["strengthen-vs-weaken", "reported-sequence"])
def test_verification_matrix_requires_and_preserves_explicit_variant(variant: str) -> None:
    value = spec_for("verification-matrix", beat_variant=variant, config_variant=variant)
    variants.normalize_single_variant_templates(value)
    beat = value["scenes"][0]["visualBeats"][0]
    assert beat["templateVariant"] == variant
    assert beat["templateConfig"]["variant"] == variant


@pytest.mark.parametrize(
    ("beat_variant", "config_variant"),
    [
        (None, None),
        ("reported-sequence", None),
        (None, "reported-sequence"),
        ("reported-sequence", "strengthen-vs-weaken"),
        ("default", "default"),
    ],
)
def test_verification_matrix_never_infers_variant_from_content(beat_variant, config_variant) -> None:
    value = spec_for("verification-matrix", beat_variant=beat_variant, config_variant=config_variant)
    with pytest.raises(variants.TemplateVariantError):
        variants.normalize_single_variant_templates(value)


def test_single_variant_templates_still_normalize_deterministically() -> None:
    value = spec_for("verification-checklist")
    variants.normalize_single_variant_templates(value)
    beat = value["scenes"][0]["visualBeats"][0]
    assert beat["templateVariant"] == "default"
    assert beat["templateConfig"]["variant"] == "default"
