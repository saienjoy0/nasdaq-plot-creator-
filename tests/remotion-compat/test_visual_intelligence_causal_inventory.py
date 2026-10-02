#!/usr/bin/env python3
"""Current production accepts authored causal graphs without rewriting them."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import visual_intelligence_causal_inventory as inventory  # noqa: E402


def graph_render() -> dict:
    return {"scenes": [{
        "sceneId": "scene-05",
        "nodes": [
            {"nodeId": "company-news", "label": "company expectations"},
            {"nodeId": "company-price", "label": "company price"},
            {"nodeId": "oil", "label": "oil"},
            {"nodeId": "retail", "label": "retail"},
        ],
        "arrows": [
            {"arrowId": "company-edge", "fromNodeId": "company-news", "toNodeId": "company-price", "label": ""},
            {"arrowId": "macro-edge", "fromNodeId": "oil", "toNodeId": "retail", "label": ""},
        ],
        "visualBeats": [{
            "beatId": "scene-05-beat-001",
            "visualTemplate": "causal-lane",
            "visualMode": "causal-diagram",
            "objectIds": ["company-news", "company-price", "company-edge", "oil", "retail", "macro-edge"],
            "templateConfig": {
                "variant": "branches",
                "nodeOrder": ["company-news", "company-price", "oil", "retail"],
                "outcomeNodeId": None,
            },
        }],
        "visualEvents": [],
    }]}


def expect_error(render: dict, path: str) -> None:
    original = copy.deepcopy(render)
    try:
        inventory.materialize_causal_inventory(render)
    except inventory.VisualIntelligenceCausalInventoryError as exc:
        message = str(exc)
        assert path in message, message
        assert "RETURN_TO_STORY:" in message, message
    else:
        raise AssertionError("invalid Current causal graph passed")
    assert render == original, "validation mutated its input"


def test_explicit_chain_preserved() -> None:
    render = graph_render()
    scene = render["scenes"][0]
    scene["nodes"] = scene["nodes"][:2]
    scene["arrows"] = scene["arrows"][:1]
    beat = scene["visualBeats"][0]
    beat["objectIds"] = ["company-news", "company-price", "company-edge"]
    beat["templateConfig"]["nodeOrder"] = ["company-news", "company-price"]
    beat["templateConfig"]["outcomeNodeId"] = "company-price"
    result = inventory.materialize_causal_inventory(render)
    assert result == render
    assert result is not render and result["scenes"][0] is not scene


def test_disconnected_authored_branches_preserved() -> None:
    render = graph_render()
    result = inventory.materialize_causal_inventory(render)
    assert result == render
    assert {edge["arrowId"] for edge in result["scenes"][0]["arrows"]} == {"company-edge", "macro-edge"}


def test_card_only_and_misleading_company_macro_card_rejected() -> None:
    render = graph_render()
    scene = render["scenes"][0]
    scene["cards"] = [{"cardId": "mixed-card", "lines": [
        {"value": "AMAT expectations"}, {"value": "oil / retail"}, {"value": "NASDAQ"},
    ]}]
    scene["nodes"] = []
    scene["arrows"] = []
    scene["visualBeats"][0]["objectIds"] = ["mixed-card"]
    scene["visualBeats"][0]["templateConfig"]["nodeOrder"] = []
    expect_error(render, "$.scenes[0].visualBeats[0].objectIds")


def test_causal_shot_cannot_bypass_graph_authority_using_another_template() -> None:
    for template in ("text-focus", "analogy-steps", "tailwind-headwind"):
        render = graph_render()
        scene = render["scenes"][0]
        scene["cards"] = [{"cardId": "mixed-card", "lines": [
            {"value": "company expectations"}, {"value": "oil / retail"}, {"value": "NASDAQ"},
        ]}]
        scene["nodes"] = []
        scene["arrows"] = []
        beat = scene["visualBeats"][0]
        beat["visualTemplate"] = template
        beat["visualMode"] = "text-focus"
        beat["objectIds"] = ["mixed-card"]
        beat["templateConfig"]["nodeOrder"] = []
        beat["shots"] = [{"shotRecipe": "causal-build"}]
        expect_error(render, "$.scenes[0].visualBeats[0].objectIds")


def test_missing_and_dangling_endpoints_rejected() -> None:
    missing = graph_render()
    del missing["scenes"][0]["arrows"][0]["fromNodeId"]
    expect_error(missing, "$.scenes[0].arrows[0].fromNodeId")
    dangling = graph_render()
    dangling["scenes"][0]["arrows"][0]["toNodeId"] = "absent"
    expect_error(dangling, "$.scenes[0].arrows[0].toNodeId")


def test_duplicate_ids_and_config_mismatch_rejected() -> None:
    duplicate = graph_render()
    duplicate["scenes"][0]["nodes"][1]["nodeId"] = "company-news"
    expect_error(duplicate, "$.scenes[0].nodes[1].nodeId")
    duplicate_order = graph_render()
    duplicate_order["scenes"][0]["visualBeats"][0]["templateConfig"]["nodeOrder"][1] = "company-news"
    expect_error(duplicate_order, "$.scenes[0].visualBeats[0].templateConfig.nodeOrder")
    collision = graph_render()
    collision["scenes"][0]["arrows"][0]["arrowId"] = "company-news"
    expect_error(collision, "$.scenes[0].arrows[0].arrowId")
    mismatch = graph_render()
    mismatch["scenes"][0]["visualBeats"][0]["templateConfig"]["nodeOrder"].pop()
    expect_error(mismatch, "$.scenes[0].visualBeats[0].templateConfig.nodeOrder")
    bad_outcome = graph_render()
    bad_outcome["scenes"][0]["visualBeats"][0]["templateConfig"]["outcomeNodeId"] = "absent"
    expect_error(bad_outcome, "$.scenes[0].visualBeats[0].templateConfig.outcomeNodeId")


def test_non_causal_beat_unchanged() -> None:
    render = {"scenes": [{"sceneId": "scene-01", "visualBeats": [{
        "beatId": "beat-1", "visualTemplate": "text-focus", "objectIds": ["card-1"]
    }], "cards": [{"cardId": "card-1"}]}]}
    assert inventory.materialize_causal_inventory(render) == render


def main() -> int:
    test_explicit_chain_preserved()
    test_disconnected_authored_branches_preserved()
    test_card_only_and_misleading_company_macro_card_rejected()
    test_causal_shot_cannot_bypass_graph_authority_using_another_template()
    test_missing_and_dangling_endpoints_rejected()
    test_duplicate_ids_and_config_mismatch_rejected()
    test_non_causal_beat_unchanged()
    print("Current visual intelligence causal inventory tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
