#!/usr/bin/env python3
"""Authorize a Visual Grammar handoff only when all final artifacts agree.

This gate reads already finalized artifacts. It never chooses a Visual Template,
changes narration, repairs a fallback, or infers editorial meaning. It verifies
byte SHA values, structural/timing PASS reports, final selected paths, and the
absence of unresolved candidate state before writing an immutable handoff.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from visual_grammar_report_recompute import (
    VisualGrammarReportRecomputeError,
    validate_structural_report_against_render,
    validate_timing_report_metrics,
)


class VisualGrammarCrossArtifactError(ValueError):
    pass


FORBIDDEN_PRODUCTION_KEYS = {
    "candidatePlans",
    "preferredPlan",
    "fallbackPlan",
    "unselectedPlan",
    "selectionState",
    "compilerSelection",
    "preferredPlanId",
    "fallbackPlanId",
    "financialVisualIntent",
}
FORBIDDEN_STATE_VALUES = {"not-run", "pending", "unresolved", "proposed"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VisualGrammarCrossArtifactError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise VisualGrammarCrossArtifactError(
            f"{label} invalid JSON at {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise VisualGrammarCrossArtifactError(f"{label} root must be an object")
    return value


def validate_schema(payload: dict[str, Any], schema: dict[str, Any], label: str) -> None:
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda item: list(item.path))
    if not errors:
        return
    messages: list[str] = []
    for error in errors:
        location = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path
        )
        messages.append(f"{label}{location}: {error.message}")
    raise VisualGrammarCrossArtifactError("\n".join(messages))


def write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(canonical_json(value), encoding="utf-8")
    temporary.replace(path)


def _walk_for_unresolved(value: Any, path: str = "$") -> list[str]:
    violations: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_PRODUCTION_KEYS:
                violations.append(f"{child_path}: non-selected candidate state is forbidden")
            if isinstance(child, str) and child in FORBIDDEN_STATE_VALUES:
                violations.append(f"{child_path}: unresolved state {child!r} is forbidden")
            violations.extend(_walk_for_unresolved(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            violations.extend(_walk_for_unresolved(child, f"{path}[{index}]"))
    return violations


def _compatibility_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if registry.get("contractVersion") != "1.0.0":
        raise VisualGrammarCrossArtifactError("renderer compatibility contractVersion must be 1.0.0")
    templates = registry.get("templates")
    if not isinstance(templates, list) or not templates:
        raise VisualGrammarCrossArtifactError("renderer compatibility templates must be a non-empty array")
    result = {entry["visualTemplateId"]: entry for entry in templates}
    if len(result) != len(templates):
        raise VisualGrammarCrossArtifactError("renderer compatibility Visual Template IDs must be unique")
    return result


def _appearance(entry: dict[str, Any], variant: str) -> tuple[str, str, str]:
    for override in entry.get("variantOverrides", []):
        if override.get("variant") == variant:
            return (
                override["appearanceClass"],
                override["dominantSurface"],
                override["stageShell"],
            )
    return entry["appearanceClass"], entry["dominantSurface"], entry["stageShell"]


def _render_beats(render_spec: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_beats: list[dict[str, Any]] = []
    scene_1_to_8: list[dict[str, Any]] = []
    for scene in render_spec.get("scenes", []):
        scene_id = scene.get("sceneId")
        scene_number = scene.get("sceneNumber")
        for beat in scene.get("visualBeats", []):
            row = {"sceneId": scene_id, "sceneNumber": scene_number, **beat}
            all_beats.append(row)
            if isinstance(scene_number, int) and scene_number <= 8:
                scene_1_to_8.append(row)
    return all_beats, scene_1_to_8


def _validate_timing_rows(
    timing_report: dict[str, Any],
    render_beats: list[dict[str, Any]],
    compatibility: dict[str, dict[str, Any]],
) -> None:
    render_map = {(beat["sceneId"], beat["beatId"]): beat for beat in render_beats}
    timing_rows = timing_report["beats"]
    timing_map = {(beat["sceneId"], beat["beatId"]): beat for beat in timing_rows}
    if set(render_map) != set(timing_map):
        raise VisualGrammarCrossArtifactError(
            f"timing report Beat set mismatch: missing={sorted(set(render_map)-set(timing_map))} "
            f"extra={sorted(set(timing_map)-set(render_map))}"
        )
    for key, render_beat in render_map.items():
        timing_beat = timing_map[key]
        for field in ("visualGrammarId", "transitionRole"):
            if timing_beat[field] != render_beat.get(field):
                raise VisualGrammarCrossArtifactError(
                    f"timing report {field} mismatch for {key}: "
                    f"{timing_beat[field]!r} != {render_beat.get(field)!r}"
                )
        template = render_beat.get("visualTemplate")
        entry = compatibility.get(template)
        if entry is None:
            raise VisualGrammarCrossArtifactError(f"unregistered Visual Template in render spec: {template}")
        variant = render_beat.get("templateConfig", {}).get("variant")
        appearance, surface, stage = _appearance(entry, variant)
        expected = {
            "appearanceClass": appearance,
            "dominantSurface": surface,
            "stageShell": stage,
        }
        for field, value in expected.items():
            if timing_beat[field] != value:
                raise VisualGrammarCrossArtifactError(
                    f"timing report {field} mismatch for {key}: {timing_beat[field]!r} != {value!r}"
                )


def _fallback_beat_ids(render_beats: list[dict[str, Any]]) -> list[str]:
    result = [
        beat["beatId"]
        for beat in render_beats
        if beat.get("financialVisualTrace", {}).get("selectedPath") == "fallback"
    ]
    return sorted(result)


def authorize_visual_grammar_handoff(
    *,
    render_spec_path: Path,
    final_episode_contract_path: Path,
    structural_report_path: Path,
    timing_report_path: Path,
    semantics_registry_path: Path,
    renderer_compatibility_path: Path,
    structural_schema_path: Path,
    timing_schema_path: Path,
    handoff_schema_path: Path,
    output_path: Path,
    official_preflight_path: Path | None = None,
) -> dict[str, Any]:
    render_spec = load_json(render_spec_path, "render spec")
    final_episode_contract = load_json(final_episode_contract_path, "Final Episode Contract")
    structural_report = load_json(structural_report_path, "Visual Grammar structural report")
    timing_report = load_json(timing_report_path, "Visual Grammar timing report")
    semantics_registry = load_json(semantics_registry_path, "Visual Grammar semantics registry")
    renderer_compatibility = load_json(
        renderer_compatibility_path, "Visual Grammar renderer compatibility registry"
    )
    structural_schema = load_json(structural_schema_path, "structural report schema")
    timing_schema = load_json(timing_schema_path, "timing report schema")
    handoff_schema = load_json(handoff_schema_path, "handoff schema")

    validate_schema(structural_report, structural_schema, "structural report")
    validate_schema(timing_report, timing_schema, "timing report")
    if structural_report["status"] != "PASS":
        raise VisualGrammarCrossArtifactError("structural report must be PASS")
    if timing_report["status"] != "PASS":
        raise VisualGrammarCrossArtifactError("timing report must be PASS")
    if timing_report["fallbackDiversityRecheck"] != "completed":
        raise VisualGrammarCrossArtifactError("fallback diversity recheck is incomplete")
    if timing_report["unresolvedStateCount"] != 0:
        raise VisualGrammarCrossArtifactError("timing report contains unresolved state")

    if render_spec.get("schemaVersion") != "2.4.0":
        raise VisualGrammarCrossArtifactError("Visual Grammar handoff requires render_spec 2.4.0")
    root = render_spec.get("visualGrammarContract")
    if not isinstance(root, dict) or root.get("contractVersion") != "1.0.0":
        raise VisualGrammarCrossArtifactError("render spec Visual Grammar root contract is missing")

    episode_date = render_spec.get("episode", {}).get("id")
    if structural_report["episodeDate"] != episode_date:
        raise VisualGrammarCrossArtifactError("structural report episode date mismatch")
    if timing_report["episodeId"] != episode_date:
        raise VisualGrammarCrossArtifactError("timing report episode date mismatch")

    shas = {
        "renderSpecSha256": sha256_file(render_spec_path),
        "finalEpisodeContractSha256": sha256_file(final_episode_contract_path),
        "semanticsSha256": sha256_file(semantics_registry_path),
        "rendererCompatibilitySha256": sha256_file(renderer_compatibility_path),
        "structuralReportSha256": sha256_file(structural_report_path),
        "timingReportSha256": sha256_file(timing_report_path),
    }
    if timing_report["inputRenderSpecSha256"] != shas["renderSpecSha256"]:
        raise VisualGrammarCrossArtifactError("timing report input render spec SHA mismatch")
    for field in (
        "semanticsSha256",
        "rendererCompatibilitySha256",
        "finalEpisodeContractSha256",
    ):
        if root.get(field) != shas[field]:
            raise VisualGrammarCrossArtifactError(f"render spec root {field} mismatch")
        if timing_report.get(field) != shas[field]:
            raise VisualGrammarCrossArtifactError(f"timing report {field} mismatch")

    unresolved = _walk_for_unresolved(render_spec)
    if unresolved:
        raise VisualGrammarCrossArtifactError("\n".join(unresolved))

    all_beats, measured_render_beats = _render_beats(render_spec)
    if root.get("beatCount") != len(all_beats):
        raise VisualGrammarCrossArtifactError("render spec root beatCount mismatch")
    if structural_report["beatCount"] != len(all_beats):
        raise VisualGrammarCrossArtifactError("structural report beatCount mismatch")
    if structural_report["scene1To8BeatCount"] != len(measured_render_beats):
        raise VisualGrammarCrossArtifactError("structural report Scene 1–8 Beat count mismatch")
    if timing_report["metrics"]["measuredBeatCount"] != len(measured_render_beats):
        raise VisualGrammarCrossArtifactError("timing report measured Beat count mismatch")

    compatibility = _compatibility_map(renderer_compatibility)
    _validate_timing_rows(timing_report, measured_render_beats, compatibility)
    try:
        validate_structural_report_against_render(
            render_spec, structural_report, semantics_registry
        )
        validate_timing_report_metrics(timing_report)
    except VisualGrammarReportRecomputeError as exc:
        raise VisualGrammarCrossArtifactError(str(exc)) from exc
    actual_fallback_ids = _fallback_beat_ids(measured_render_beats)
    reported_fallback_ids = sorted(timing_report["selectedFallbackBeatIds"])
    if actual_fallback_ids != reported_fallback_ids:
        raise VisualGrammarCrossArtifactError(
            f"fallback Beat mismatch: render={actual_fallback_ids} timing={reported_fallback_ids}"
        )

    handoff = {
        "contractVersion": "1.0.0",
        "status": "PASS",
        "episodeDate": episode_date,
        "handoffAuthorized": True,
        "renderSpecVersion": "2.4.0",
        "visualGrammarContractVersion": "1.0.0",
        "timingBasis": "post-tts-production-data",
        "fallbackDiversityRecheck": "completed",
        "selectedFallbackBeatIds": reported_fallback_ids,
        "unresolvedStateCount": 0,
        **shas,
        "artifacts": {
            "renderSpec": render_spec_path.as_posix(),
            "finalEpisodeContract": final_episode_contract_path.as_posix(),
            "semanticsRegistry": semantics_registry_path.as_posix(),
            "rendererCompatibilityRegistry": renderer_compatibility_path.as_posix(),
            "structuralReport": structural_report_path.as_posix(),
            "timingReport": timing_report_path.as_posix(),
        },
    }
    validate_schema(handoff, handoff_schema, "handoff")
    write_atomic(output_path, handoff)

    if official_preflight_path is not None:
        preflight = load_json(official_preflight_path, "official preflight")
        preflight["visualGrammarGate"] = {
            "status": "PASS",
            "contractVersion": "1.0.0",
            "handoffSha256": sha256_file(output_path),
            "semanticsSha256": shas["semanticsSha256"],
            "rendererCompatibilitySha256": shas["rendererCompatibilitySha256"],
            "structuralReportSha256": shas["structuralReportSha256"],
            "timingReportSha256": shas["timingReportSha256"],
            "unresolvedStateCount": 0,
        }
        write_atomic(official_preflight_path, preflight)

    return handoff


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-spec", type=Path, required=True)
    parser.add_argument("--final-episode-contract", type=Path, required=True)
    parser.add_argument("--structural-report", type=Path, required=True)
    parser.add_argument("--timing-report", type=Path, required=True)
    parser.add_argument(
        "--semantics-registry", type=Path,
        default=Path("contracts/visual_grammar_semantics.json"),
    )
    parser.add_argument(
        "--renderer-compatibility", type=Path,
        default=Path("contracts/visual_grammar_renderer_compatibility.json"),
    )
    parser.add_argument(
        "--structural-schema", type=Path,
        default=Path("contracts/visual_grammar_structural_report.schema.json"),
    )
    parser.add_argument(
        "--timing-schema", type=Path,
        default=Path("contracts/visual_grammar_timing_report.schema.json"),
    )
    parser.add_argument(
        "--handoff-schema", type=Path,
        default=Path("contracts/visual_grammar_handoff.schema.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--official-preflight", type=Path)
    args = parser.parse_args(argv)
    try:
        result = authorize_visual_grammar_handoff(
            render_spec_path=args.render_spec,
            final_episode_contract_path=args.final_episode_contract,
            structural_report_path=args.structural_report,
            timing_report_path=args.timing_report,
            semantics_registry_path=args.semantics_registry,
            renderer_compatibility_path=args.renderer_compatibility,
            structural_schema_path=args.structural_schema,
            timing_schema_path=args.timing_schema,
            handoff_schema_path=args.handoff_schema,
            output_path=args.output,
            official_preflight_path=args.official_preflight,
        )
    except VisualGrammarCrossArtifactError as exc:
        print(json.dumps({"status": "FAIL", "errors": str(exc).splitlines()}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
