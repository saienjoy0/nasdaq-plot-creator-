#!/usr/bin/env python3
"""Validate ChatGPT daily authoring closure before renderer production.

This gate makes no editorial or visual selection. It checks the author-owned duration
mode contract, renderer-source availability, the fixed nine-Scene/chunk-to-Beat closure,
authored presentation invariants that the deterministic materializer requires, and that
every authored financial-only Visual Template has one explicit authored financial binding
pointing to the exact Scene/Beat/template it claims to drive.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import remotion_template_variant


class AuthoringClosureError(ValueError):
    pass


DUAL_USE_VISUAL_TEMPLATE_IDS = {"source-receipt"}
RENDERABLE_SOURCE_TYPES = {
    "official", "company", "company-ir", "major-media", "analyst", "market-data", "other",
}
SOURCE_ID_RE = re.compile(r"^source-[0-9]{3}$")


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuthoringClosureError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise AuthoringClosureError(f"{label} root must be an object")
    return value


def financial_template_ids(registry: dict[str, Any]) -> set[str]:
    recipes = registry.get("recipes")
    if not isinstance(recipes, dict):
        raise AuthoringClosureError("financial recipe registry recipes must be an object")
    result: set[str] = set()
    for recipe_id, recipe in recipes.items():
        if not isinstance(recipe, dict):
            raise AuthoringClosureError(f"financial recipe {recipe_id} must be an object")
        if recipe.get("path") != "preferred":
            continue
        templates = recipe.get("allowedVisualTemplateIds")
        if not isinstance(templates, list) or not templates or not all(
            isinstance(item, str) and item for item in templates
        ):
            raise AuthoringClosureError(
                f"financial recipe {recipe_id}.allowedVisualTemplateIds must be a non-empty string array"
            )
        result.update(templates)
    result.difference_update(DUAL_USE_VISUAL_TEMPLATE_IDS)
    return result


def validate_duration_ownership(authoring: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    mode = authoring.get("durationMode")
    reason = authoring.get("shortenedReason")
    if mode not in {"standard", "shortened"}:
        errors.append("$.durationMode: must be 'standard' or 'shortened'")
        return errors
    if mode == "standard" and reason is not None:
        errors.append("$.shortenedReason: standard duration requires null")
    if mode == "shortened" and (not isinstance(reason, str) or not reason.strip()):
        errors.append("$.shortenedReason: shortened duration requires a non-empty reason")
    return errors


def validate_renderer_source_registry(surface: dict[str, Any]) -> list[str]:
    """Fail before materialization when no source can survive Renderer normalization."""
    errors: list[str] = []
    sources = surface.get("sources")
    if not isinstance(sources, list):
        return ["$.sources: must be an array"]

    renderable = 0
    seen_renderable_ids: set[str] = set()
    for index, source in enumerate(sources):
        path = f"$.sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{path}: must be an object")
            continue
        source_type = source.get("sourceType")
        source_id = source.get("sourceId")

        if source_type == "historical-memory":
            continue

        if source_type not in RENDERABLE_SOURCE_TYPES:
            errors.append(f"{path}.sourceType: unsupported renderer sourceType {source_type!r}")
            continue
        if not isinstance(source_id, str) or not SOURCE_ID_RE.fullmatch(source_id):
            errors.append(f"{path}.sourceId: must match source-NNN for Renderer delivery")
            continue
        if source_id in seen_renderable_ids:
            errors.append(f"{path}.sourceId: duplicate renderable source {source_id}")
            continue
        seen_renderable_ids.add(source_id)
        renderable += 1

        for key in ("title", "publisher", "reference", "accessedAt"):
            value = source.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{path}.{key}: non-empty string required for Renderer delivery")
        published = source.get("publishedAt")
        if published is not None and (not isinstance(published, str) or not published.strip()):
            errors.append(f"{path}.publishedAt: must be null or a non-empty string")
        used_for = source.get("usedFor")
        if not isinstance(used_for, list) or not used_for or not all(
            isinstance(item, str) and item.strip() for item in used_for
        ):
            errors.append(f"{path}.usedFor: non-empty string array required for Renderer delivery")
        attribution = source.get("narrationAttribution")
        if attribution is not None and (not isinstance(attribution, str) or not attribution.strip()):
            errors.append(f"{path}.narrationAttribution: must be omitted or a non-empty string")

    if renderable == 0:
        errors.append("$.sources: at least one renderable source-NNN is required")
    return errors


def _authored_object_ids(
    scene_index: int,
    beat_index: int,
    beat: dict[str, Any],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    sid = f"scene-{scene_index:02d}"
    metrics = beat.get("metrics", [])
    nodes = beat.get("nodes", [])
    if not isinstance(metrics, list):
        errors.append(f"{sid}-beat-{beat_index:03d}: metrics must be an array when present")
        metrics = []
    if not isinstance(nodes, list):
        errors.append(f"{sid}-beat-{beat_index:03d}: nodes must be an array when present")
        nodes = []
    object_ids = [
        f"{sid}-number-{beat_index:02d}-{metric_index:02d}"
        for metric_index, _ in enumerate(metrics, 1)
    ]
    object_ids.extend(
        f"{sid}-node-{beat_index:02d}-{node_index:02d}"
        for node_index, _ in enumerate(nodes, 1)
    )
    if not object_ids:
        object_ids.append(f"{sid}-card-{beat_index:03d}")
    return object_ids, errors


def validate_authored_presentation(
    scene_index: int,
    beat_index: int,
    beat: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    sid = f"scene-{scene_index:02d}"
    bid = f"{sid}-beat-{beat_index:03d}"
    cid = f"{sid}-chunk-{beat_index:03d}"
    object_ids, object_errors = _authored_object_ids(scene_index, beat_index, beat)
    errors.extend(object_errors)
    valid_targets = set(object_ids)

    shots_present = "shots" in beat
    shots = beat.get("shots")
    if shots_present:
        if not isinstance(shots, list) or not 1 <= len(shots) <= 4:
            errors.append(f"{bid}: authored shots must contain 1-4 existing Renderer shots")
        else:
            for shot_index, shot in enumerate(shots, 1):
                if not isinstance(shot, dict):
                    errors.append(f"{bid}: shot {shot_index} must be an object")
                    continue
                expected_id = f"{bid}-shot-{shot_index:03d}"
                if shot.get("shotId") != expected_id:
                    errors.append(f"{bid}: shot {shot_index} must use deterministic ID {expected_id}")
                if shot.get("startChunkId") != cid or shot.get("endChunkId") != cid:
                    errors.append(f"{bid}: authored shots must stay inside {cid}")
                start = shot.get("startProgress")
                end = shot.get("endProgress")
                start_ok = isinstance(start, (int, float)) and not isinstance(start, bool) and 0 <= start <= 1
                end_ok = isinstance(end, (int, float)) and not isinstance(end, bool) and 0 <= end <= 1
                if not start_ok:
                    errors.append(f"{bid}: shot {shot_index}.startProgress must be within 0..1")
                if not end_ok:
                    errors.append(f"{bid}: shot {shot_index}.endProgress must be within 0..1")
                if start_ok and end_ok and float(end) <= float(start):
                    errors.append(f"{bid}: shot {shot_index} must end after it starts")
                for key in (
                    "primaryTargetId", "referenceTargetId", "outcomeTargetId", "cameraTargetId",
                ):
                    target = shot.get(key)
                    if target is not None and target not in valid_targets:
                        errors.append(f"{bid}: shot {shot_index}.{key} targets unknown object {target}")
                secondary = shot.get("secondaryTargetIds", [])
                if not isinstance(secondary, list) or any(
                    target not in valid_targets for target in secondary
                ):
                    errors.append(f"{bid}: shot {shot_index}.secondaryTargetIds contains unknown objects")
            if shots and isinstance(shots[0], dict):
                start = shots[0].get("startProgress")
                if isinstance(start, (int, float)) and not isinstance(start, bool) and float(start) != 0:
                    errors.append(f"{bid}: first authored shot must start at progress 0")
            if shots and isinstance(shots[-1], dict):
                end = shots[-1].get("endProgress")
                if isinstance(end, (int, float)) and not isinstance(end, bool) and float(end) != 1:
                    errors.append(f"{bid}: final authored shot must end at progress 1")

    events_present = "visualEvents" in beat
    events = beat.get("visualEvents")
    if events_present:
        if not isinstance(events, list) or not events:
            errors.append(f"{bid}: visualEvents must be a non-empty array when present")
        else:
            visibility_targets: set[str] = set()
            for item_index, item in enumerate(events, 1):
                if not isinstance(item, dict):
                    errors.append(f"{bid}: visualEvents[{item_index}] must be an object")
                    continue
                action = item.get("action")
                if action not in {"show", "hide", "highlight", "unhighlight", "set-expression"}:
                    errors.append(f"{bid}: visualEvents[{item_index}] has invalid action {action!r}")
                    continue
                target = item.get("targetId")
                if action == "set-expression":
                    if target is not None:
                        errors.append(f"{bid}: set-expression must not target an object")
                else:
                    if target not in valid_targets:
                        errors.append(f"{bid}: visualEvents[{item_index}] targets unknown object {target!r}")
                    if action in {"show", "hide"} and target in valid_targets:
                        visibility_targets.add(str(target))
                offset = item.get("offsetMs", 0)
                if not isinstance(offset, int) or isinstance(offset, bool) or not 0 <= offset <= 10_000:
                    errors.append(f"{bid}: visualEvents[{item_index}].offsetMs must be 0..10000")
            if len(object_ids) > 1 and not set(object_ids).issubset(visibility_targets):
                missing = sorted(set(object_ids) - visibility_targets)
                errors.append(
                    f"{bid}: multi-object visualEvents must explicitly author first visibility "
                    f"for every object; missing={missing}"
                )

    if len(object_ids) > 1 and not shots_present and not events_present:
        errors.append(
            f"{bid}: multi-object Beat requires authored shots or visualEvents; "
            "automatic reveal order is not production-authoritative"
        )
    return errors


def validate_authoring(authoring: dict[str, Any], registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_duration_ownership(authoring))

    surface = authoring
    if authoring.get("contractVersion") == "2.0.0":
        production = authoring.get("production")
        if not isinstance(production, dict):
            return [*errors, "$.production: must be an object"]
        surface = dict(production)
        surface["durationMode"] = authoring.get("durationMode")
        surface["shortenedReason"] = authoring.get("shortenedReason")

    errors.extend(validate_renderer_source_registry(surface))

    scenes = surface.get("scenes")
    if not isinstance(scenes, list):
        return [*errors, "$.scenes: must be an array"]
    if len(scenes) != 9:
        errors.append(f"$.scenes: expected 9 scenes; found={len(scenes)}")

    financial_templates = financial_template_ids(registry)
    beat_map: dict[str, tuple[int, dict[str, Any]]] = {}
    total_beats = 0
    for scene_index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            errors.append(f"$.scenes[{scene_index - 1}]: must be an object")
            continue
        chunks = scene.get("chunks")
        beats = scene.get("beats")
        if not isinstance(chunks, list):
            errors.append(f"$.scenes[{scene_index - 1}].chunks: must be an array")
            chunks = []
        if not isinstance(beats, list):
            errors.append(f"$.scenes[{scene_index - 1}].beats: must be an array")
            beats = []
        total_beats += len(beats)
        if len(chunks) != len(beats):
            errors.append(
                f"scene-{scene_index:02d}: chunks/beats length mismatch "
                f"chunks={len(chunks)} beats={len(beats)}"
            )
        for beat_index, beat in enumerate(beats, 1):
            beat_id = f"scene-{scene_index:02d}-beat-{beat_index:03d}"
            if not isinstance(beat, dict):
                errors.append(f"{beat_id}: beat must be an object")
                continue
            try:
                remotion_template_variant.validate_pre_visual_intelligence_variant(
                    beat.get("visualTemplate"),
                    beat.get("variant"),
                    path=beat_id,
                )
            except remotion_template_variant.TemplateVariantError as exc:
                errors.append(str(exc))
            errors.extend(validate_authored_presentation(scene_index, beat_index, beat))
            beat_map[beat_id] = (scene_index, beat)
    if total_beats != 18:
        errors.append(f"$.scenes[*].beats: expected 18 total Visual Beats; found={total_beats}")

    bindings = surface.get("financialBindings", [])
    if not isinstance(bindings, list):
        errors.append("$.financialBindings: must be an array")
        bindings = []

    by_beat: dict[str, dict[str, Any]] = {}
    binding_ids: set[str] = set()
    intent_ids: set[str] = set()
    for index, binding in enumerate(bindings):
        path = f"$.financialBindings[{index}]"
        if not isinstance(binding, dict):
            errors.append(f"{path}: must be an object")
            continue
        binding_id = binding.get("bindingId")
        intent_id = binding.get("intentId")
        source_beat_id = binding.get("sourceBeatId")
        scene_id = binding.get("sceneId")
        selected_template = binding.get("selectedVisualTemplateId")
        if not isinstance(binding_id, str) or not binding_id:
            errors.append(f"{path}.bindingId: required")
        elif binding_id in binding_ids:
            errors.append(f"{path}.bindingId: duplicate {binding_id}")
        else:
            binding_ids.add(binding_id)
        if not isinstance(intent_id, str) or not intent_id:
            errors.append(f"{path}.intentId: required")
        elif intent_id in intent_ids:
            errors.append(f"{path}.intentId: duplicate {intent_id}")
        else:
            intent_ids.add(intent_id)
        if not isinstance(source_beat_id, str) or not source_beat_id:
            errors.append(f"{path}.sourceBeatId: required")
            continue
        if source_beat_id in by_beat:
            errors.append(f"{path}.sourceBeatId: duplicate binding target {source_beat_id}")
            continue
        by_beat[source_beat_id] = binding
        target = beat_map.get(source_beat_id)
        if target is None:
            errors.append(f"{path}.sourceBeatId: unknown authored Beat {source_beat_id}")
            continue
        scene_index, beat = target
        expected_scene_id = f"scene-{scene_index:02d}"
        if scene_id != expected_scene_id:
            errors.append(
                f"{path}.sceneId: {scene_id!r} does not match target {expected_scene_id!r}"
            )
        authored_template = beat.get("visualTemplate")
        if selected_template != authored_template:
            errors.append(
                f"{path}.selectedVisualTemplateId: {selected_template!r} does not match "
                f"authored template {authored_template!r} at {source_beat_id}"
            )

    for beat_id, (_, beat) in beat_map.items():
        template = beat.get("visualTemplate")
        if template in financial_templates and beat_id not in by_beat:
            errors.append(
                f"{beat_id}: Financial-only Visual Template {template!r} requires an explicit "
                "financialBindings entry; author a binding or explicitly choose its approved non-financial fallback"
            )

    return errors


def validate_or_raise(authoring: dict[str, Any], registry: dict[str, Any]) -> None:
    errors = validate_authoring(authoring, registry)
    if errors:
        raise AuthoringClosureError("\n".join(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authoring", type=Path, required=True)
    parser.add_argument(
        "--registry", type=Path, default=Path("contracts/financial_recipe_registry.json")
    )
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)
    try:
        authoring = load_json(args.authoring, "daily authoring")
        registry = load_json(args.registry, "financial recipe registry")
        errors = validate_authoring(authoring, registry)
        report = {
            "contractVersion": "1.1.0",
            "status": "PASS" if not errors else "FAIL",
            "errorCount": len(errors),
            "errors": errors,
        }
        code = 0 if not errors else 2
    except AuthoringClosureError as exc:
        report = {
            "contractVersion": "1.1.0",
            "status": "FAIL",
            "errorCount": 1,
            "errors": [str(exc)],
        }
        code = 2
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
