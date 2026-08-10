#!/usr/bin/env python3
"""Dry-run the approved Story visual overrides against the existing Visual Grammar contract.

This is the Pre-TTS structural gate described by the Visual Grammar master design.
It composes the already-authored Story production bindings with the current render
shell in memory, validates Semantic Grammar plus the mirrored Renderer compatibility
registry, and writes only a validation report. It never selects or repairs a Template,
changes narration, or mutates the input render spec.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import visual_grammar_contract


class PreTTSVisualGateError(ValueError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreTTSVisualGateError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise PreTTSVisualGateError(f"{label} must be an object")
    return value


def _load_story_projection_module():
    path = ROOT / "scripts/story-engine/project_story_script_to_production.py"
    spec = importlib.util.spec_from_file_location("pre_tts_story_projection", path)
    if not spec or not spec.loader:
        raise PreTTSVisualGateError(f"cannot import Story projection module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _schema_errors(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda item: list(item.path))
    result: list[str] = []
    for error in errors:
        location = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path
        )
        result.append(f"{label}{location}: {error.message}")
    return result


def _compatibility_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if registry.get("contractVersion") != "1.0.0":
        raise PreTTSVisualGateError("renderer compatibility contractVersion must be 1.0.0")
    templates = registry.get("templates")
    if not isinstance(templates, list) or not templates:
        raise PreTTSVisualGateError("renderer compatibility templates must be a non-empty array")
    result: dict[str, dict[str, Any]] = {}
    for item in templates:
        if not isinstance(item, dict) or not isinstance(item.get("visualTemplateId"), str):
            raise PreTTSVisualGateError("renderer compatibility template entry is invalid")
        template_id = item["visualTemplateId"]
        if template_id in result:
            raise PreTTSVisualGateError(f"duplicate Visual Template ID: {template_id}")
        result[template_id] = item
    return result


def _appearance(entry: dict[str, Any], variant: str | None) -> tuple[str, str]:
    for override in entry.get("variantOverrides", []):
        if isinstance(override, dict) and override.get("variant") == variant:
            return str(override["appearanceClass"]), str(override["dominantSurface"])
    return str(entry["appearanceClass"]), str(entry["dominantSurface"])


def _sidecar_from_render(render: dict[str, Any], episode_date: str) -> dict[str, Any]:
    expected_confirmed = render.get("expectedConfirmed")
    if not isinstance(expected_confirmed, bool):
        raise PreTTSVisualGateError("render shell expectedConfirmed must be explicit boolean")
    scenes: list[dict[str, Any]] = []
    for scene_index, scene in enumerate(render.get("scenes", []), start=1):
        beats: list[dict[str, Any]] = []
        for beat_index, beat in enumerate(scene.get("visualBeats", []), start=1):
            visual_beat_id = beat.get("visualBeatId") or beat.get("beatId")
            grammar = beat.get("visualGrammar")
            if not isinstance(visual_beat_id, str) or not visual_beat_id:
                raise PreTTSVisualGateError(
                    f"scene-{scene_index:02d} beat {beat_index}: visualBeatId/beatId missing"
                )
            if not isinstance(grammar, dict):
                raise PreTTSVisualGateError(
                    f"scene-{scene_index:02d}/{visual_beat_id}: visualGrammar missing"
                )
            beats.append({"visualBeatId": visual_beat_id, "visualGrammar": copy.deepcopy(grammar)})
        scenes.append({"sceneId": scene.get("sceneId"), "visualBeats": beats})
    return {
        "episodeDate": episode_date,
        "visualGrammarContractVersion": "1.0.0",
        "expectedConfirmed": expected_confirmed,
        "scene5CausalExceptionReason": render.get("scene5CausalExceptionReason"),
        "scenes": scenes,
    }


def _append_violation(report: dict[str, Any], code: str, path: str, message: str) -> None:
    report["violations"].append({"code": code, "path": path, "message": message})
    report["status"] = "FAIL"


def _validate_renderer_compatibility(
    render: dict[str, Any],
    report: dict[str, Any],
    compatibility: dict[str, dict[str, Any]],
) -> None:
    measured: list[tuple[int, int, str, str, str, str]] = []
    for scene_index, scene in enumerate(render.get("scenes", [])):
        for beat_index, beat in enumerate(scene.get("visualBeats", [])):
            path = f"$.scenes[{scene_index}].visualBeats[{beat_index}]"
            template = beat.get("visualTemplate")
            grammar_obj = beat.get("visualGrammar")
            grammar = grammar_obj.get("grammarId") if isinstance(grammar_obj, dict) else None
            entry = compatibility.get(template) if isinstance(template, str) else None
            if entry is None:
                _append_violation(
                    report,
                    "VG_GRAMMAR_TEMPLATE_MISMATCH",
                    f"{path}.visualTemplate",
                    f"unregistered Visual Template: {template!r}",
                )
                continue
            allowed = entry.get("allowedGrammarIds", [])
            if grammar not in allowed:
                _append_violation(
                    report,
                    "VG_GRAMMAR_TEMPLATE_MISMATCH",
                    path,
                    f"grammar {grammar!r} is not allowed for Visual Template {template!r}; allowed={allowed}",
                )
            config = beat.get("templateConfig")
            variant = config.get("variant") if isinstance(config, dict) else beat.get("templateVariant")
            appearance, surface = _appearance(entry, variant if isinstance(variant, str) else None)
            measured.append((scene_index, beat_index, str(grammar), appearance, surface, str(beat.get("visualGrammar", {}).get("transitionRole"))))

    scene_1_8 = [row for row in measured if row[0] <= 7]
    front = [row for row in scene_1_8 if row[0] <= 3]
    back = [row for row in scene_1_8 if 4 <= row[0] <= 7]
    appearances = {row[3] for row in scene_1_8}
    surfaces = {row[4] for row in scene_1_8}
    if len(appearances) < 6:
        _append_violation(
            report,
            "VG_APPEARANCE_COUNT_TOO_LOW",
            "$.scenes[0:8]",
            f"requires at least 6 Appearance Classes; found={len(appearances)}",
        )
    if len(surfaces) < 5:
        _append_violation(
            report,
            "VG_DOMINANT_SURFACE_COUNT_TOO_LOW",
            "$.scenes[0:8]",
            f"requires at least 5 Dominant Surfaces; found={len(surfaces)}",
        )
    if len({row[3] for row in front}) < 3:
        _append_violation(
            report,
            "VG_FRONT_HALF_APPEARANCE_COUNT_TOO_LOW",
            "$.scenes[0:4]",
            f"requires at least 3 Appearance Classes; found={len({row[3] for row in front})}",
        )
    if len({row[3] for row in back}) < 3:
        _append_violation(
            report,
            "VG_BACK_HALF_APPEARANCE_COUNT_TOO_LOW",
            "$.scenes[4:8]",
            f"requires at least 3 Appearance Classes; found={len({row[3] for row in back})}",
        )

    ordered = sorted(measured, key=lambda row: (row[0], row[1]))
    appearance_run = 1
    surface_run = 1
    previous: tuple[int, int, str, str, str, str] | None = None
    for row in ordered:
        scene_index, beat_index, _, appearance, surface, transition = row
        path = f"$.scenes[{scene_index}].visualBeats[{beat_index}]"
        if previous is not None:
            appearance_run = appearance_run + 1 if previous[3] == appearance else 1
            surface_run = surface_run + 1 if previous[4] == surface else 1
            if appearance_run >= 3:
                _append_violation(
                    report,
                    "VG_SAME_APPEARANCE_RUN_TOO_LONG",
                    path,
                    f"same Appearance Class {appearance!r} may not run for 3 consecutive Beats",
                )
            if surface_run >= 4:
                _append_violation(
                    report,
                    "VG_SAME_DOMINANT_SURFACE_RUN_TOO_LONG",
                    path,
                    f"same Dominant Surface {surface!r} may not run for 4 consecutive Beats",
                )
            if transition == "major-shift" and previous[3] == appearance and previous[4] == surface:
                _append_violation(
                    report,
                    "VG_MAJOR_SHIFT_NOT_PHYSICAL",
                    path,
                    "major-shift requires a physical Appearance Class or Dominant Surface change",
                )
        previous = row


def validate_pre_tts(
    *,
    render: dict[str, Any],
    story_bindings: dict[str, Any],
    semantics: dict[str, Any],
    semantics_schema: dict[str, Any],
    compatibility_registry: dict[str, Any],
    compatibility_schema: dict[str, Any],
    report_schema: dict[str, Any],
) -> dict[str, Any]:
    episode_date = story_bindings.get("episode_date")
    if not isinstance(episode_date, str) or not episode_date:
        raise PreTTSVisualGateError("Story production bindings episode_date is required")
    if story_bindings.get("contract_version") != "1.0.0":
        raise PreTTSVisualGateError("Story production bindings contract_version must be 1.0.0")
    render_date = render.get("episode", {}).get("id")
    if render_date != episode_date:
        raise PreTTSVisualGateError(
            f"Story/render episode date mismatch: story={episode_date!r} render={render_date!r}"
        )

    semantics_errors = _schema_errors(semantics, semantics_schema, "semantics")
    compatibility_errors = _schema_errors(
        compatibility_registry, compatibility_schema, "renderer compatibility"
    )
    if semantics_errors or compatibility_errors:
        raise PreTTSVisualGateError("\n".join(semantics_errors + compatibility_errors))
    visual_grammar_contract.validate_registry(semantics, semantics_schema)
    compatibility = _compatibility_map(compatibility_registry)

    transient = copy.deepcopy(render)
    projection = _load_story_projection_module()
    projection.apply_visual_overrides(transient, story_bindings)

    sidecar = _sidecar_from_render(transient, episode_date)
    report = visual_grammar_contract.validate_episode(sidecar, semantics)
    _validate_renderer_compatibility(transient, report, compatibility)

    report_errors = _schema_errors(report, report_schema, "Pre-TTS report")
    if report_errors:
        raise PreTTSVisualGateError("\n".join(report_errors))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-spec", type=Path, required=True)
    parser.add_argument("--story-bindings", type=Path, required=True)
    parser.add_argument(
        "--semantics", type=Path, default=Path("contracts/visual_grammar_semantics.json")
    )
    parser.add_argument(
        "--semantics-schema",
        type=Path,
        default=Path("contracts/visual_grammar_semantics.schema.json"),
    )
    parser.add_argument(
        "--renderer-compatibility",
        type=Path,
        default=Path("contracts/visual_grammar_renderer_compatibility.json"),
    )
    parser.add_argument(
        "--renderer-compatibility-schema",
        type=Path,
        default=Path("contracts/visual_grammar_renderer_compatibility.schema.json"),
    )
    parser.add_argument(
        "--report-schema",
        type=Path,
        default=Path("contracts/visual_grammar_structural_report.schema.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = validate_pre_tts(
            render=load_json(args.render_spec, "render spec"),
            story_bindings=load_json(args.story_bindings, "Story production bindings"),
            semantics=load_json(args.semantics, "Visual Grammar semantics"),
            semantics_schema=load_json(args.semantics_schema, "Visual Grammar semantics schema"),
            compatibility_registry=load_json(
                args.renderer_compatibility, "Renderer compatibility registry"
            ),
            compatibility_schema=load_json(
                args.renderer_compatibility_schema, "Renderer compatibility schema"
            ),
            report_schema=load_json(args.report_schema, "structural report schema"),
        )
    except (PreTTSVisualGateError, visual_grammar_contract.VisualGrammarError) as exc:
        print(json.dumps({"status": "FAIL", "errors": str(exc).splitlines()}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
