from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "validate_chatgpt_daily_authoring_closure.py"
CURRENT_FIXTURE_PATH = ROOT / "tests/current-spine/current_authoring_runtime_fixture.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


closure = _load_module("daily_authoring_closure", MODULE_PATH)
current_fixture = _load_module("daily_authoring_current_runtime_fixture", CURRENT_FIXTURE_PATH)


def registry():
    return {
        "recipes": {
            "market-pulse-grid": {
                "path": "preferred",
                "allowedVisualTemplateIds": ["market-pulse-grid"],
            },
            "opening-contradiction": {
                "path": "fallback",
                "allowedVisualTemplateIds": ["opening-contradiction"],
            },
            "source-receipt": {
                "path": "preferred",
                "allowedVisualTemplateIds": ["source-receipt"],
            },
            "news-media": {
                "path": "fallback",
                "allowedVisualTemplateIds": ["news-media"],
            },
        }
    }


def current_authoring(tmp_path: Path, template: str = "opening-contradiction"):
    _, _, authoring = current_fixture.build_workspace(tmp_path)
    authoring["production"]["scenes"][0]["beats"][0]["visualTemplate"] = template
    return authoring


def test_unbound_financial_only_template_is_reported_but_dual_use_receipt_is_not(tmp_path: Path):
    authoring = current_authoring(tmp_path, "source-receipt")
    authoring["production"]["scenes"][1]["beats"][0]["visualTemplate"] = "market-pulse-grid"
    errors = closure.validate_authoring(authoring, registry())
    assert not any("scene-01-beat-001" in error and "source-receipt" in error for error in errors)
    assert any("scene-02-beat-001" in error and "market-pulse-grid" in error for error in errors)


def test_generic_source_receipt_does_not_require_financial_binding(tmp_path: Path):
    authoring = current_authoring(tmp_path, "source-receipt")
    assert closure.validate_authoring(authoring, registry()) == []


def test_explicit_financial_source_receipt_binding_remains_valid(tmp_path: Path):
    authoring = current_authoring(tmp_path, "source-receipt")
    authoring["production"]["financialBindings"] = [
        {
            "bindingId": "binding-1",
            "intentId": "intent-1",
            "sceneId": "scene-01",
            "sourceBeatId": "scene-01-beat-001",
            "selectedVisualTemplateId": "source-receipt",
        }
    ]
    assert closure.validate_authoring(authoring, registry()) == []


def test_non_financial_fallback_does_not_require_binding(tmp_path: Path):
    authoring = current_authoring(tmp_path, "news-media")
    assert closure.validate_authoring(authoring, registry()) == []


def test_binding_mismatch_is_rejected(tmp_path: Path):
    authoring = current_authoring(tmp_path, "source-receipt")
    authoring["production"]["financialBindings"] = [
        {
            "bindingId": "binding-1",
            "intentId": "intent-1",
            "sceneId": "scene-02",
            "sourceBeatId": "scene-01-beat-001",
            "selectedVisualTemplateId": "market-pulse-grid",
        }
    ]
    errors = closure.validate_authoring(authoring, registry())
    assert any("sceneId" in error and "scene-01" in error for error in errors)
    assert any("selectedVisualTemplateId" in error and "source-receipt" in error for error in errors)


def test_pre_vi_multi_variant_template_may_defer_variant_to_visual_director(tmp_path: Path):
    authoring = current_authoring(tmp_path, "verification-matrix")
    beat = authoring["production"]["scenes"][0]["beats"][0]
    beat.pop("variant", None)
    errors = closure.validate_authoring(authoring, registry())
    assert not any(
        "scene-01-beat-001" in error
        and "verification-matrix" in error
        and "variant" in error
        for error in errors
    )


def test_pre_vi_default_placeholder_may_defer_variant_to_visual_director(tmp_path: Path):
    authoring = current_authoring(tmp_path, "verification-matrix")
    authoring["production"]["scenes"][0]["beats"][0]["variant"] = "default"
    errors = closure.validate_authoring(authoring, registry())
    assert not any(
        "scene-01-beat-001" in error
        and "verification-matrix" in error
        and "variant" in error
        for error in errors
    )


def test_pre_vi_multi_variant_template_accepts_explicit_registered_variant(tmp_path: Path):
    authoring = current_authoring(tmp_path, "verification-matrix")
    authoring["production"]["scenes"][0]["beats"][0]["variant"] = "strengthen-vs-weaken"
    errors = closure.validate_authoring(authoring, registry())
    assert not any(
        "scene-01-beat-001" in error
        and "verification-matrix" in error
        and "variant" in error
        for error in errors
    )


def test_pre_vi_multi_variant_template_rejects_unknown_explicit_variant(tmp_path: Path):
    authoring = current_authoring(tmp_path, "verification-matrix")
    authoring["production"]["scenes"][0]["beats"][0]["variant"] = "made-up-variant"
    errors = closure.validate_authoring(authoring, registry())
    assert any(
        "scene-01-beat-001" in error
        and "verification-matrix" in error
        and "variant" in error
        for error in errors
    )
