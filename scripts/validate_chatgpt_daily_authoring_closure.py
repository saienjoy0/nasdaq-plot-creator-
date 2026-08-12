#!/usr/bin/env python3
"""Validate ChatGPT daily authoring closure before renderer production.

This gate makes no editorial or visual selection. It checks the author-owned duration
mode contract, the fixed nine-Scene/chunk-to-Beat closure, and that every authored
Financial Visual Template has one explicit authored financial binding pointing to the
exact Scene/Beat/template it claims to drive. Financial template ownership is derived
from the existing financial recipe registry, not duplicated here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class AuthoringClosureError(ValueError):
    pass


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
    if not result:
        raise AuthoringClosureError(
            "financial recipe registry exposes no preferred Financial Visual Templates"
        )
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


def validate_authoring(authoring: dict[str, Any], registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_duration_ownership(authoring))

    scenes = authoring.get("scenes")
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
            beat_map[beat_id] = (scene_index, beat)
    if total_beats != 18:
        errors.append(f"$.scenes[*].beats: expected 18 total Visual Beats; found={total_beats}")

    bindings = authoring.get("financialBindings", [])
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
                f"{beat_id}: Financial Visual Template {template!r} requires an explicit "
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
