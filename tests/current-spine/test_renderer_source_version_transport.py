from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "materialize_renderer_sources.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


renderer_sources = load_module("renderer_source_version_transport", MODULE_PATH)


def render(version: str) -> dict:
    return {
        "schemaVersion": version,
        "sources": [
            {
                "sourceId": "source-001",
                "sourceType": "official",
                "publisher": "Synthetic IR",
                "title": "Synthetic source",
            }
        ],
        "scenes": [
            {
                "sceneId": "scene-01",
                "visualMode": "text-focus",
                "evidenceSourceIds": ["source-001"],
                "visualBeats": [
                    {
                        "beatId": "scene-01-beat-001",
                        "visualBeatId": "scene-01-beat-001",
                        "visualMode": "text-focus",
                        "semanticScope": "multiple",
                        "evidenceSourceIds": ["source-001"],
                        "templateConfig": {"variant": "default"},
                        "visualGrammar": {
                            "contractVersion": "1.0.0",
                            "grammarId": "text-focus",
                            "transitionRole": "continuation",
                        },
                    }
                ],
            }
        ],
    }


def test_normalization_preserves_current_2_5_version_and_semantic_scope():
    normalized, _ = renderer_sources.normalize_render_base(render("2.5.0"))
    assert normalized["schemaVersion"] == "2.5.0"
    assert normalized["scenes"][0]["visualBeats"][0]["semanticScope"] == "multiple"


def test_normalization_preserves_legacy_2_4_version():
    normalized, _ = renderer_sources.normalize_render_base(render("2.4.0"))
    assert normalized["schemaVersion"] == "2.4.0"
