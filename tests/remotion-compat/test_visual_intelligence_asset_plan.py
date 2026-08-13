#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import visual_intelligence_asset_plan as asset_plan  # noqa: E402


def main() -> int:
    date = "2099-06-06"
    requirements = {
        "episodeDate": date,
        "provisionalDirection": {"requirements": [
            {"visualBeatId": "vb-01-01", "imageRequirement": "required"},
            {"visualBeatId": "vb-01-02", "imageRequirement": "possible"},
        ]},
    }
    planned = {
        "episodeDate": date,
        "intents": [{
            "intentId": "vi-001",
            "target": {"sceneId": "scene-01", "visualBeatId": "vb-01-01"},
        }],
    }
    result = asset_plan.validate(
        requirements=requirements,
        visual_sources=planned,
        episode_date=date,
    )
    if result["status"] != "PASS" or result["requiredImageBeatCount"] != 1:
        raise AssertionError(result)
    try:
        asset_plan.validate(
            requirements=requirements,
            visual_sources={"episodeDate": date, "intents": []},
            episode_date=date,
        )
    except asset_plan.VisualIntelligenceAssetPlanError as exc:
        if "lack Primary/Approved Fallback planning" not in str(exc):
            raise
    else:
        raise AssertionError("image-required Beat without Primary/Fallback plan must fail")
    print("visual intelligence asset plan tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
