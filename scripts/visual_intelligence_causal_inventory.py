#!/usr/bin/env python3
"""Validate explicitly authored causal graphs for Current production.

Current Visual Intelligence must receive nodes, arrows, and ``templateConfig``
from Story. It never derives causality from cards, text, or object order. The
legacy card materializer in :mod:`remotion_template_data` remains available to
legacy compatibility callers, but this Current adapter deliberately bypasses it.
"""
from __future__ import annotations

import copy
from typing import Any

import remotion_template_data


class VisualIntelligenceCausalInventoryError(ValueError):
    pass


def _fail(path: str, problem: str, action: str) -> None:
    raise VisualIntelligenceCausalInventoryError(
        f"E_VISUAL_CAUSAL_INVENTORY_INVALID:{path}: {problem}; RETURN_TO_STORY: {action}"
    )


def _object_map(items: Any, id_key: str, path: str) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        _fail(path, "must be an array", f"author graph objects with unique {id_key} values")
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            _fail(item_path, "must be an object", f"author a graph object with a non-empty {id_key}")
        value = item.get(id_key)
        if not isinstance(value, str) or not value:
            _fail(f"{item_path}.{id_key}", "must be a non-empty string", f"author a unique {id_key}")
        if value in result:
            _fail(f"{item_path}.{id_key}", f"duplicates {value!r}", f"give every {id_key} a unique value")
        result[value] = item
    return result


def _validate_causal_beat(scene: dict[str, Any], beat: dict[str, Any], scene_path: str, beat_path: str) -> None:
    nodes = _object_map(scene.get("nodes"), "nodeId", f"{scene_path}.nodes")
    arrows = _object_map(scene.get("arrows"), "arrowId", f"{scene_path}.arrows")
    collisions = set(nodes) & set(arrows)
    if collisions:
        collision = next(item for item in scene["arrows"] if item.get("arrowId") in collisions)
        index = next(index for index, item in enumerate(scene["arrows"]) if item is collision)
        _fail(f"{scene_path}.arrows[{index}].arrowId", f"duplicates graph object ID {collision['arrowId']!r}", "use unique IDs across nodes and arrows")
    object_ids = beat.get("objectIds")
    if not isinstance(object_ids, list) or not all(isinstance(item, str) and item for item in object_ids):
        _fail(f"{beat_path}.objectIds", "must be an array of non-empty graph object IDs", "reference explicitly authored nodeId and arrowId values")
    if len(object_ids) != len(set(object_ids)):
        _fail(f"{beat_path}.objectIds", "contains duplicate IDs", "reference each graph object exactly once")

    selected_nodes = [item for item in object_ids if item in nodes]
    selected_arrows = [item for item in object_ids if item in arrows]
    unknown = [item for item in object_ids if item not in nodes and item not in arrows]
    if unknown:
        _fail(f"{beat_path}.objectIds", f"references non-graph or missing objects {unknown!r}", "author nodes/arrows and reference only their IDs; cards cannot be converted into causal edges")
    if not selected_nodes:
        _fail(f"{beat_path}.objectIds", "contains no explicitly authored nodes", "replace the causal card with authored nodes, authored arrows, and matching templateConfig")

    selected_node_set = set(selected_nodes)
    arrow_indexes = {id(item): index for index, item in enumerate(scene["arrows"])}
    for arrow_id in selected_arrows:
        arrow = arrows[arrow_id]
        arrow_path = f"{scene_path}.arrows[{arrow_indexes[id(arrow)]}]"
        for key in ("fromNodeId", "toNodeId"):
            endpoint = arrow.get(key)
            if not isinstance(endpoint, str) or not endpoint:
                _fail(f"{arrow_path}.{key}", "must be a non-empty nodeId", "author both endpoints for every referenced arrow")
            if endpoint not in nodes:
                _fail(f"{arrow_path}.{key}", f"references missing node {endpoint!r}", "reference an authored scene node")
            if endpoint not in selected_node_set:
                _fail(f"{arrow_path}.{key}", f"references unselected node {endpoint!r}", "include both arrow endpoints in this beat's objectIds and nodeOrder")

    config = beat.get("templateConfig")
    if not isinstance(config, dict):
        _fail(f"{beat_path}.templateConfig", "must be an authored object", "author nodeOrder and optional outcomeNodeId")
    node_order = config.get("nodeOrder")
    if not isinstance(node_order, list) or not all(isinstance(item, str) and item for item in node_order):
        _fail(f"{beat_path}.templateConfig.nodeOrder", "must be an array of non-empty node IDs", "list every selected node exactly once")
    if len(node_order) != len(set(node_order)):
        _fail(f"{beat_path}.templateConfig.nodeOrder", "contains duplicate node IDs", "list every selected node exactly once")
    if set(node_order) != selected_node_set or len(node_order) != len(selected_nodes):
        _fail(f"{beat_path}.templateConfig.nodeOrder", f"must cover exactly the selected nodes {selected_nodes!r}", "remove missing or extra IDs while preserving the authored display order")
    outcome = config.get("outcomeNodeId")
    if outcome is not None and (not isinstance(outcome, str) or outcome not in selected_node_set):
        _fail(f"{beat_path}.templateConfig.outcomeNodeId", f"must be null or one of the selected nodes, got {outcome!r}", "choose an explicitly authored selected node or null")


def materialize_causal_inventory(render: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy after validating Current causal graph authority."""
    result = copy.deepcopy(render)
    scenes = result.get("scenes", [])
    if not isinstance(scenes, list):
        _fail("$.scenes", "must be an array", "author the Current render scene list")
    for scene_index, scene in enumerate(scenes):
        scene_path = f"$.scenes[{scene_index}]"
        if not isinstance(scene, dict):
            _fail(scene_path, "must be an object", "author a scene object")
        beats = scene.get("visualBeats", [])
        if not isinstance(beats, list):
            _fail(f"{scene_path}.visualBeats", "must be an array", "author the scene visual beats")
        for beat_index, beat in enumerate(beats):
            beat_path = f"{scene_path}.visualBeats[{beat_index}]"
            if not isinstance(beat, dict):
                _fail(beat_path, "must be an object", "author a visual beat object")
            if beat.get("visualTemplate") in remotion_template_data.CAUSAL_TEMPLATE_IDS:
                _validate_causal_beat(scene, beat, scene_path, beat_path)
    return result
