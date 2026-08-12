from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "validate_chatgpt_daily_authoring_closure.py"
SPEC = importlib.util.spec_from_file_location("daily_authoring_closure", MODULE_PATH)
assert SPEC and SPEC.loader
closure = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(closure)


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


def nine_scene_authoring(template: str = "opening-contradiction"):
    scenes = []
    for index in range(1, 10):
        scenes.append(
            {
                "chunks": [
                    {"text": f"scene {index} beat 1"},
                    {"text": f"scene {index} beat 2"},
                ],
                "beats": [
                    {
                        "visualTemplate": template if index == 1 else "opening-contradiction",
                    },
                    {
                        "visualTemplate": "opening-contradiction",
                    },
                ],
            }
        )
    return {
        "durationMode": "standard",
        "shortenedReason": None,
        "scenes": scenes,
        "financialBindings": [],
    }


def test_unbound_financial_templates_are_reported_together():
    authoring = nine_scene_authoring("source-receipt")
    authoring["scenes"][1]["beats"][0]["visualTemplate"] = "market-pulse-grid"
    errors = closure.validate_authoring(authoring, registry())
    assert any("scene-01-beat-001" in error and "source-receipt" in error for error in errors)
    assert any("scene-02-beat-001" in error and "market-pulse-grid" in error for error in errors)


def test_exact_binding_closes_financial_template():
    authoring = nine_scene_authoring("source-receipt")
    authoring["financialBindings"] = [
        {
            "bindingId": "binding-1",
            "intentId": "intent-1",
            "sceneId": "scene-01",
            "sourceBeatId": "scene-01-beat-001",
            "selectedVisualTemplateId": "source-receipt",
        }
    ]
    assert closure.validate_authoring(authoring, registry()) == []


def test_non_financial_fallback_does_not_require_binding():
    authoring = nine_scene_authoring("news-media")
    assert closure.validate_authoring(authoring, registry()) == []


def test_binding_mismatch_is_rejected():
    authoring = nine_scene_authoring("source-receipt")
    authoring["financialBindings"] = [
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
