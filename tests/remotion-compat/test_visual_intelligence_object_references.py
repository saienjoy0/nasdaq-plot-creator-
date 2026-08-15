#!/usr/bin/env python3
"""Regression coverage for fail-closed Visual Intelligence object references."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import visual_intelligence_causal_inventory as causal_inventory  # noqa: E402
import visual_intelligence_object_references as refs  # noqa: E402


def beat(beat_id: str, chunk_id: str, object_ids: list[str]) -> dict:
    return {
        "beatId": beat_id,
        "startChunkId": chunk_id,
        "endChunkId": chunk_id,
        "visualMode": "text-focus",
        "visualTemplate": "text-focus",
        "objectIds": object_ids,
        "templateConfig": {
            "variant": "default",
            "comparisonBasis": None,
            "dataBasis": "synthetic",
            "nodeOrder": [],
            "laneLabels": [],
            "outcomeNodeId": None,
        },
        "shots": [],
    }


def event(event_id: str, chunk_id: str, action: str, target_id: str) -> dict:
    return {
        "eventId": event_id,
        "atChunkId": chunk_id,
        "timing": "chunk-start",
        "action": action,
        "targetId": target_id,
        "offsetMs": 0,
        "expression": None,
    }


def scene() -> dict:
    first = beat("scene-01-beat-001", "scene-01-chunk-001", ["old-object"])
    first["shots"] = [{
        "shotId": "shot-1",
        "primaryTargetId": "old-object",
        "referenceTargetId": "old-object",
        "outcomeTargetId": "old-object",
        "secondaryTargetIds": ["old-object", "other-object"],
        "cameraTargetId": "old-object",
    }]
    first["templateConfig"].update({
        "outcomeNodeId": "old-object",
        "nodeOrder": ["old-object"],
        "displayOrder": ["old-object"],
        "metricIds": ["old-object"],
        "causalStepIds": ["old-object"],
        "highlightObjectIds": ["old-object"],
        "reactionTimeline": {
            "precision": "verified-intraday-series",
            "eventOrderIds": ["event-marker-1"],
            "seriesObjectIds": ["old-object"],
        },
    })
    second = beat("scene-01-beat-002", "scene-01-chunk-002", ["other-object"])
    return {
        "sceneId": "scene-01",
        "narrationChunks": [
            {"chunkId": "scene-01-chunk-001"},
            {"chunkId": "scene-01-chunk-002"},
        ],
        "visualBeats": [first, second],
        "visualEvents": [
            event("event-001", "scene-01-chunk-001", "show", "old-object"),
            event("event-002", "scene-01-chunk-001", "hide", "old-object"),
            event("event-003", "scene-01-chunk-001", "highlight", "old-object"),
            event("event-004", "scene-01-chunk-001", "unhighlight", "old-object"),
        ],
    }


def expect_error(producer: dict, projected: dict, code: str) -> None:
    try:
        refs.reconcile_projected_object_references(producer, projected)
    except refs.ObjectReferenceReconciliationError as exc:
        if code not in str(exc):
            raise AssertionError(f"expected {code}, got {exc}") from exc
    else:
        raise AssertionError(f"expected fail-closed error {code}")


def test_one_to_one() -> None:
    producer = {"scenes": [scene()]}
    projected = copy.deepcopy(producer)
    projected["scenes"][0]["visualBeats"][0]["objectIds"] = ["new-object"]
    result = refs.reconcile_projected_object_references(producer, projected)
    first = result["scenes"][0]["visualBeats"][0]
    targets = [item["targetId"] for item in result["scenes"][0]["visualEvents"]]
    if targets != ["new-object"] * 4:
        raise AssertionError(f"Visual Events were not rebound: {targets}")
    shot = first["shots"][0]
    for key in ("primaryTargetId", "referenceTargetId", "outcomeTargetId", "cameraTargetId"):
        if shot[key] != "new-object":
            raise AssertionError(f"shot {key} was not rebound")
    if shot["secondaryTargetIds"] != ["new-object", "other-object"]:
        raise AssertionError("shot secondaryTargetIds were not rebound")
    config = first["templateConfig"]
    for key in ("outcomeNodeId",):
        if config[key] != "new-object":
            raise AssertionError(f"templateConfig {key} was not rebound")
    for key in ("nodeOrder", "displayOrder", "metricIds", "causalStepIds", "highlightObjectIds"):
        if config[key] != ["new-object"]:
            raise AssertionError(f"templateConfig {key} was not rebound")
    if config["reactionTimeline"]["seriesObjectIds"] != ["new-object"]:
        raise AssertionError("reactionTimeline.seriesObjectIds was not rebound")
    if config["reactionTimeline"]["eventOrderIds"] != ["event-marker-1"]:
        raise AssertionError("reactionTimeline.eventOrderIds must not be treated as object IDs")
    if producer["scenes"][0]["visualBeats"][0]["objectIds"] != ["old-object"]:
        raise AssertionError("reconciliation mutated producer input")


def test_outside_beat_fails() -> None:
    producer = {"scenes": [scene()]}
    producer["scenes"][0]["visualEvents"].append(
        event("event-005", "scene-01-chunk-002", "highlight", "old-object")
    )
    projected = copy.deepcopy(producer)
    projected["scenes"][0]["visualBeats"][0]["objectIds"] = ["new-object"]
    for item in projected["scenes"][0]["visualEvents"]:
        if item["targetId"] == "old-object":
            item["targetId"] = "new-object"
    expect_error(producer, projected, "E_VISUAL_OBJECT_REFERENCE_OUTSIDE_BEAT")


def test_shared_object_fails() -> None:
    producer = {"scenes": [scene()]}
    producer["scenes"][0]["visualBeats"][1]["objectIds"] = ["old-object"]
    projected = copy.deepcopy(producer)
    projected["scenes"][0]["visualBeats"][0]["objectIds"] = ["new-object"]
    expect_error(producer, projected, "E_VISUAL_OBJECT_REWRITE_SHARED")


def test_ambiguous_complex_rewrite_fails() -> None:
    producer = {"scenes": [scene()]}
    projected = copy.deepcopy(producer)
    projected["scenes"][0]["visualBeats"][0]["objectIds"] = ["new-a", "new-b"]
    expect_error(producer, projected, "E_VISUAL_OBJECT_REWRITE_AMBIGUOUS")


def test_expected_actual_gap_specialized_rewrite() -> None:
    source_scene = scene()
    source_scene["visualEvents"] = [
        event("event-001", "scene-01-chunk-001", "show", "old-object")
    ]
    producer = {"scenes": [source_scene]}
    projected = copy.deepcopy(producer)
    first = projected["scenes"][0]["visualBeats"][0]
    first["objectIds"] = ["expected-card", "actual-card", "gap-card"]
    first["visualTemplate"] = "expected-actual-gap-flow"
    first["visualMode"] = "expected-actual-gap"
    first["shots"] = []
    first["templateConfig"] = {
        "variant": "default",
        "comparisonBasis": None,
        "dataBasis": "synthetic",
        "nodeOrder": [],
        "laneLabels": [],
        "outcomeNodeId": None,
    }
    projected["scenes"][0]["visualEvents"] = [
        event("event-101", "scene-01-chunk-001", "show", "expected-card"),
        event("event-102", "scene-01-chunk-001", "show", "actual-card"),
        event("event-103", "scene-01-chunk-001", "show", "gap-card"),
    ]
    result = refs.reconcile_projected_object_references(producer, projected)
    observed = [item["targetId"] for item in result["scenes"][0]["visualEvents"]]
    if observed != ["expected-card", "actual-card", "gap-card"]:
        raise AssertionError(f"specialized E/A/G references drifted: {observed}")


def test_causal_card_specialized_rewrite() -> None:
    source_scene = scene()
    source_scene["cards"] = [{
        "cardId": "old-object",
        "role": None,
        "title": "承認済み因果",
        "lines": [
            {"label": "1", "value": "A", "tone": "neutral"},
            {"label": "2", "value": "B", "tone": "neutral"},
            {"label": "3", "value": "C", "tone": "neutral"},
            {"label": "4", "value": "D", "tone": "neutral"},
        ],
    }]
    source_scene["nodes"] = []
    source_scene["arrows"] = []
    source_scene["visualEvents"] = [
        event("event-001", "scene-01-chunk-001", "show", "old-object")
    ]
    source_scene["visualBeats"][0]["shots"] = []
    producer = {"scenes": [source_scene]}
    projected = copy.deepcopy(producer)
    first = projected["scenes"][0]["visualBeats"][0]
    first["visualTemplate"] = "causal-lane"
    first["visualMode"] = "causal-diagram"
    first["templateConfig"] = {
        "variant": "left-to-right",
        "comparisonBasis": None,
        "dataBasis": "synthetic",
        "nodeOrder": [],
        "laneLabels": [],
        "outcomeNodeId": None,
    }

    materialized = causal_inventory.materialize_causal_inventory(projected)
    causal_scene = materialized["scenes"][0]
    causal_beat = causal_scene["visualBeats"][0]
    node_ids = [item["nodeId"] for item in causal_scene["nodes"]]
    if len(node_ids) != 4 or len(causal_scene["arrows"]) != 3:
        raise AssertionError("4-line causal card did not become four nodes and three arrows")
    if causal_beat["templateConfig"]["nodeOrder"] != node_ids:
        raise AssertionError("causal nodeOrder drifted from generated approved nodes")
    if causal_beat["templateConfig"]["outcomeNodeId"] != node_ids[-1]:
        raise AssertionError("causal outcomeNodeId must be the authored final line")
    if len(causal_beat["objectIds"]) != 7:
        raise AssertionError("causal Beat must expose the complete node/arrow inventory")

    result = refs.reconcile_projected_object_references(producer, materialized)
    targets = [item["targetId"] for item in result["scenes"][0]["visualEvents"]]
    if len(targets) != 7 or set(targets) != set(causal_beat["objectIds"]):
        raise AssertionError(f"causal display events did not fan out to generated objects: {targets}")
    if "old-object" in targets:
        raise AssertionError("old causal source card remained in viewer events")
    if producer["scenes"][0]["visualBeats"][0]["objectIds"] != ["old-object"]:
        raise AssertionError("causal canonicalization mutated producer input")


def test_noop_is_byte_equivalent() -> None:
    producer = {"scenes": [scene()]}
    projected = copy.deepcopy(producer)
    result = refs.reconcile_projected_object_references(producer, projected)
    if result != projected:
        raise AssertionError("unchanged object inventory must be a no-op")


def main() -> int:
    test_one_to_one()
    test_outside_beat_fails()
    test_shared_object_fails()
    test_ambiguous_complex_rewrite_fails()
    test_expected_actual_gap_specialized_rewrite()
    test_causal_card_specialized_rewrite()
    test_noop_is_byte_equivalent()
    print("visual intelligence object reference reconciliation tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
