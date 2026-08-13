#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import visual_intelligence_renderer_input as renderer_input  # noqa: E402


def main() -> int:
    source = {
        "scenes": [
            {"sceneId": "scene-05", "visualMode": "causal-chain", "visualBeats": [
                {"beatId": "scene-05-beat-001", "visualMode": "causal-chain"},
                {"beatId": "scene-05-beat-002", "visualMode": "verification"},
            ]},
            {"sceneId": "scene-06", "visualMode": "intraday-comparison", "visualBeats": [
                {"beatId": "scene-06-beat-001", "visualMode": "intraday-comparison"},
            ]},
            {"sceneId": "scene-09", "visualMode": "closing-recap", "visualBeats": [
                {"beatId": "scene-09-beat-001", "visualMode": "closing-recap"},
                {"beatId": "scene-09-beat-002", "visualMode": "closing-recap"},
            ]},
        ]
    }
    normalized = renderer_input._normalize_producer_modes(source)
    if source["scenes"][0]["visualMode"] != "causal-chain":
        raise AssertionError("normalization mutated producer IR")
    if [len(scene["visualBeats"]) for scene in normalized["scenes"]] != [2, 1, 2]:
        raise AssertionError("pre-Director normalization changed Beat structure")
    modes = [
        (scene["visualMode"], [beat["visualMode"] for beat in scene["visualBeats"]])
        for scene in normalized["scenes"]
    ]
    expected = [
        ("causal-diagram", ["causal-diagram", "verification-points"]),
        ("stock-comparison", ["stock-comparison"]),
        ("conclusion-card", ["conclusion-card", "conclusion-card"]),
    ]
    if modes != expected:
        raise AssertionError(f"producer visual mode normalization drift: {modes}")
    print("visual intelligence renderer input normalization tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
