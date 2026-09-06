from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

CURRENT_E2E = Path(__file__).with_name("test_current_contract_e2e.py")
SPEC = importlib.util.spec_from_file_location("current_contract_e2e_for_visual_feasibility", CURRENT_E2E)
assert SPEC and SPEC.loader
current_e2e = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = current_e2e
SPEC.loader.exec_module(current_e2e)


def test_visual_feasibility_failure_cannot_publish_semantic_acceptance(tmp_path: Path):
    root, authoring = current_e2e.build_workspace(tmp_path)
    beat = authoring["production"]["scenes"][0]["beats"][0]
    beat.update(
        {
            "visualMode": "number-comparison",
            "visualTemplate": "split-comparison",
            "contentType": "comparison",
            "grammarId": current_e2e.fx.current_grammar_id("split-comparison"),
            "metrics": [
                {
                    "label": "AAA",
                    "value": "+1.00%",
                    "numericValue": 1.0,
                    "unit": "%",
                },
                {
                    "label": "BBB",
                    "value": "+2.00%",
                    "numericValue": 2.0,
                    "unit": "%",
                },
            ],
            "visualEvents": [
                {
                    "action": "show",
                    "targetId": "scene-01-number-01-01",
                    "timing": "chunk-start",
                    "offsetMs": 0,
                },
                {
                    "action": "show",
                    "targetId": "scene-01-number-01-02",
                    "timing": "chunk-start",
                    "offsetMs": 180,
                },
            ],
        }
    )

    path = root / "daily-authoring" / f"{current_e2e.fx.DATE}.json"
    current_e2e.fx.write_json(path, authoring)
    semantic = current_e2e.load_module(
        "fixture_semantic_visual_feasibility_pre_freeze",
        root / "scripts/validate_editorial_semantic_boundary.py",
    )

    with pytest.raises(Exception, match="explicit common comparison basis"):
        semantic.validate_boundary(root, current_e2e.fx.DATE, path)
