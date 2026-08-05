#!/usr/bin/env python3
"""Verify the mirrored cross-repository financial render fixture."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "shared-fixtures" / "financial-visual-2.3"
RENDER_SPEC = FIXTURE_DIR / "render_spec.json"
MANIFEST = FIXTURE_DIR / "fixture_manifest.json"
MATRIX = ROOT / "contracts" / "financial_visual_compatibility.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} root must be an object")
    return value


def verify() -> dict[str, Any]:
    manifest = load_json(MANIFEST)
    spec = load_json(RENDER_SPEC)
    matrix = load_json(MATRIX)

    expected = {
        "fixtureVersion": "1.0.0",
        "fixtureId": "financial-visual-2.3-earnings-surprise",
        "compatibilityMatrixId": "financial-visual-compat-2026-08",
        "renderSpecVersion": "2.3.0",
        "financialVisualTraceVersion": "1.0.0",
        "financialTemplateRegistryVersion": "1.0.0",
        "selectedTemplate": "earnings-surprise",
        "selectedSceneId": "scene-04",
        "selectedVisualBeatId": "vb-04-02",
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"manifest {key} mismatch: {manifest.get(key)!r} != {value!r}")

    render_sha = sha256(RENDER_SPEC)
    matrix_sha = sha256(MATRIX)
    if manifest.get("renderSpecSha256") != render_sha:
        raise ValueError("render spec SHA mismatch")
    if manifest.get("compatibilityMatrixSha256") != matrix_sha:
        raise ValueError("compatibility matrix SHA mismatch")
    if matrix.get("matrixId") != manifest["compatibilityMatrixId"]:
        raise ValueError("compatibility matrix ID mismatch")
    if spec.get("schemaVersion") != manifest["renderSpecVersion"]:
        raise ValueError("render spec version mismatch")

    financial = spec.get("financialVisualContract")
    if not isinstance(financial, dict) or financial.get("selectionCount") != 1:
        raise ValueError("shared fixture must contain exactly one selected financial visual")

    scene = next(
        (item for item in spec.get("scenes", []) if item.get("sceneId") == manifest["selectedSceneId"]),
        None,
    )
    if not isinstance(scene, dict):
        raise ValueError("selected Scene missing")
    beat = next(
        (
            item
            for item in scene.get("visualBeats", [])
            if item.get("beatId") == manifest["selectedVisualBeatId"]
        ),
        None,
    )
    if not isinstance(beat, dict):
        raise ValueError("selected Visual Beat missing")
    if beat.get("visualTemplate") != manifest["selectedTemplate"]:
        raise ValueError("selected Template mismatch")
    trace = beat.get("financialVisualTrace")
    if not isinstance(trace, dict) or trace.get("selectedPath") != "preferred":
        raise ValueError("selected path must be preferred")
    if trace.get("displayOrder") != beat.get("objectIds"):
        raise ValueError("displayOrder/objectIds mismatch")
    if trace.get("metricIds") != beat.get("templateConfig", {}).get("metricIds"):
        raise ValueError("metricIds mismatch")

    return {
        "status": "pass",
        "renderSpecSha256": render_sha,
        "compatibilityMatrixSha256": matrix_sha,
        "selectedSceneId": manifest["selectedSceneId"],
        "selectedVisualBeatId": manifest["selectedVisualBeatId"],
        "selectedTemplate": manifest["selectedTemplate"],
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2, sort_keys=True))
