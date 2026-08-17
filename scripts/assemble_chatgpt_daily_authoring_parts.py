#!/usr/bin/env python3
"""Assemble split ChatGPT authoring fragments into canonical daily authoring.

Current-v2 is a deterministic compiler only: merge explicit fragments, apply explicit
presentation patches, bind the already-validated Research Dossier + receipt, bind the
machine-owned Story file references, validate the v2 schema, and write the canonical
file. It performs no semantic readiness checks, review synthesis, visual-mode aliases,
or market/editorial inference.

Legacy authoring keeps the historical assembly path for backward compatibility.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

import materialize_causal_research
import validate_chatgpt_daily_authoring_closure as authoring_closure

RENDERER_240_FINANCIAL_TEMPLATES = {
    "market-pulse-grid",
    "earnings-surprise",
    "dual-asset-split",
    "macro-pressure",
    "source-receipt",
}


def merge(left: Any, right: Any, path: str = "$") -> Any:
    if isinstance(left, dict) and isinstance(right, dict):
        out = dict(left)
        for key, value in right.items():
            out[key] = merge(out[key], value, f"{path}.{key}") if key in out else value
        return out
    if isinstance(left, list) and isinstance(right, list):
        return [*left, *right]
    if left == right:
        return left
    raise ValueError(f"conflicting scalar at {path}: {left!r} != {right!r}")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def projected_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def projected_sha(value: Any) -> str:
    return hashlib.sha256(projected_bytes(value)).hexdigest()


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _schema_resource(path: Path) -> tuple[str, Resource[Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    schema_id = value.get("$id")
    if not isinstance(schema_id, str) or not schema_id:
        raise SystemExit(f"schema has no $id: {path}")
    return schema_id, Resource.from_contents(value)


def _v2_registry(root: Path) -> Registry[Any]:
    registry: Registry[Any] = Registry()
    for path in (
        root / "skills/nasdaq-cafe-story-plan/contracts/story_plan.schema.json",
        root / "skills/nasdaq-cafe-story-authoring/contracts/story_script.schema.json",
        root / "skills/nasdaq-cafe-entertainment-critic/contracts/creative_review.schema.json",
    ):
        uri, resource = _schema_resource(path)
        registry = registry.with_resource(uri, resource)
    return registry


def validate_v2_schema(root: Path, value: dict[str, Any]) -> None:
    schema_path = root / "contracts/chatgpt_daily_authoring_v2.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(
        schema,
        registry=_v2_registry(root),
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    if errors:
        lines = [
            f"{'.'.join(map(str, item.absolute_path)) or '<root>'}: {item.message}"
            for item in errors
        ]
        raise SystemExit("Daily Authoring v2 schema failed:\n" + "\n".join(lines))


def _apply_patches_to_scenes(value: dict[str, Any], *, patch_key: str, beat: bool) -> int:
    patches = value.pop(patch_key, [])
    if not isinstance(patches, list):
        raise SystemExit(f"{patch_key} must be an array")
    production = value.get("production")
    scenes = production.get("scenes") if isinstance(production, dict) else None
    if not isinstance(scenes, list):
        raise SystemExit("production.scenes must be an array before applying patches")
    applied = 0
    seen: set[tuple[int, int | None]] = set()
    for row in patches:
        if not isinstance(row, dict):
            raise SystemExit(f"{patch_key} entries must be objects")
        scene_number = row.get("sceneNumber")
        fields = row.get("set")
        if not isinstance(scene_number, int) or not 1 <= scene_number <= len(scenes):
            raise SystemExit(f"{patch_key} sceneNumber invalid: {scene_number}")
        if not isinstance(fields, dict) or not fields:
            raise SystemExit(f"{patch_key} set must be a non-empty object")
        target: Any = scenes[scene_number - 1]
        beat_number: int | None = None
        if beat:
            beat_number = row.get("beatNumber")
            beats = target.get("beats") if isinstance(target, dict) else None
            if not isinstance(beats, list) or not isinstance(beat_number, int) or not 1 <= beat_number <= len(beats):
                raise SystemExit(f"beat patch beatNumber invalid: scene={scene_number} beat={beat_number}")
            target = beats[beat_number - 1]
        key = (scene_number, beat_number)
        if key in seen:
            raise SystemExit(f"duplicate {patch_key} target: {key}")
        seen.add(key)
        if not isinstance(target, dict):
            raise SystemExit(f"{patch_key} target is not an object: {key}")
        target.update(copy.deepcopy(fields))
        applied += 1
    return applied


def _strip_authoring_only_research_fields(value: dict[str, Any]) -> None:
    value.pop("researchAuthoring", None)
    value.pop("memoryQueryPlan", None)
    value.pop("causalDossierDraft", None)
    # A historical root causalDossier body is an authoring input, not v2 authority.
    current = value.get("causalDossier")
    if isinstance(current, dict) and "contract_version" in current:
        value.pop("causalDossier")


def bind_v2_lineage(value: dict[str, Any], root: Path, date: str) -> tuple[str, str]:
    dossier_rel = f"research/{date}/causal_research_dossier_{date}.json"
    receipt_rel = f"research/{date}/causal_dossier_validation.json"
    dossier_path = root / dossier_rel
    receipt_path = root / receipt_rel
    if not dossier_path.is_file() or not receipt_path.is_file():
        raise SystemExit("validated Research Dossier + receipt must exist before Daily Authoring v2 assembly")
    try:
        materialize_causal_research.verify_validation_receipt(root, date, receipt_path)
    except materialize_causal_research.ResearchMaterializationError as exc:
        raise SystemExit(f"Causal Dossier validation receipt is stale: {exc}") from exc
    dossier_ref = {"path": dossier_rel, "sha256": sha256_file(dossier_path)}
    value["causalDossier"] = {
        **dossier_ref,
        "validation": {"path": receipt_rel, "sha256": sha256_file(receipt_path)},
    }

    plan = value.get("storyPlan")
    script = value.get("storyScript")
    if not isinstance(plan, dict) or not isinstance(script, dict):
        raise SystemExit("storyPlan and storyScript must be explicitly authored before assembly")
    plan["causal_dossier"] = copy.deepcopy(dossier_ref)
    expected_plan_ref = {
        "path": f"working/{date}/story-engine/story_plan.json",
        "sha256": projected_sha(plan),
    }
    script["story_plan"] = expected_plan_ref
    script["causal_dossier"] = copy.deepcopy(dossier_ref)
    return dossier_ref["sha256"], expected_plan_ref["sha256"]


def assemble_v2(value: dict[str, Any], root: Path, date: str, part_count: int) -> int:
    if value.get("episodeDate") != date:
        raise SystemExit("assembled Daily Authoring v2 episodeDate mismatch")
    _strip_authoring_only_research_fields(value)
    scene_patches = _apply_patches_to_scenes(value, patch_key="scenePatches", beat=False)
    beat_patches = _apply_patches_to_scenes(value, patch_key="beatPatches", beat=True)
    dossier_sha, plan_sha = bind_v2_lineage(value, root, date)
    validate_v2_schema(root, value)
    output = root / "daily-authoring" / f"{date}.json"
    atomic_write_json(output, value)
    print(
        f"ASSEMBLED current-v2 {part_count} parts -> {output}; "
        f"dossier_sha256={dossier_sha}; projected_story_plan_sha256={plan_sha}; "
        f"scene_patches={scene_patches}; beat_patches={beat_patches}; semantic_inference=0"
    )
    return 0


# ---- Legacy helpers below are intentionally preserved. ----

def bind_daily_source_lineage(value: dict[str, Any], root: Path, date: str) -> str:
    daily_rel = f"daily-inputs/{date}/daily_source_package_{date}.md"
    daily_path = root / daily_rel
    if not daily_path.is_file():
        raise SystemExit(f"daily source package missing: {daily_path}")
    daily_sha = hashlib.sha256(daily_path.read_bytes()).hexdigest()
    dossier = value.get("causalDossier")
    if not isinstance(dossier, dict):
        raise SystemExit("causalDossier is required")
    provenance = dossier.get("input_provenance")
    if not isinstance(provenance, list):
        raise SystemExit("causalDossier.input_provenance is required")
    matches = [
        item for item in provenance
        if isinstance(item, dict)
        and item.get("role") == "daily_input"
        and item.get("path_or_reference") == daily_rel
    ]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one daily_input provenance row for {daily_rel}; found={len(matches)}")
    matches[0]["version_or_hash"] = daily_sha
    return daily_sha


def assert_renderer_240_financial_scope(root: Path) -> None:
    path = root / "scripts" / "materialize_renderer_sources.py"
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise SystemExit(f"cannot inspect Renderer 2.4 financial template scope: {exc}") from exc
    found: set[str] | None = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value_node = node.targets, node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value_node = [node.target], node.value
        else:
            continue
        if not any(isinstance(target, ast.Name) and target.id == "FINANCIAL_TEMPLATES" for target in targets):
            continue
        if value_node is None:
            break
        literal = ast.literal_eval(value_node)
        if not isinstance(literal, set) or not all(isinstance(item, str) for item in literal):
            raise SystemExit("FINANCIAL_TEMPLATES must be a literal set of strings")
        found = set(literal)
        break
    if found != RENDERER_240_FINANCIAL_TEMPLATES:
        actual = "missing" if found is None else sorted(found)
        raise SystemExit(
            "Renderer 2.4 financial template scope mismatch: "
            f"expected={sorted(RENDERER_240_FINANCIAL_TEMPLATES)} actual={actual}"
        )


def apply_explicit_scene_patches(value: dict[str, Any]) -> int:
    patches = value.pop("scenePatches", [])
    if not isinstance(patches, list):
        raise SystemExit("scenePatches must be an array")
    scenes = value.get("scenes")
    if not isinstance(scenes, list):
        raise SystemExit("assembled authoring scenes must be an array")
    applied = 0
    seen: set[int] = set()
    for row in patches:
        if not isinstance(row, dict):
            raise SystemExit("scenePatches entries must be objects")
        scene_number, fields = row.get("sceneNumber"), row.get("set")
        if not isinstance(scene_number, int) or not 1 <= scene_number <= len(scenes):
            raise SystemExit(f"scene patch sceneNumber invalid: {scene_number}")
        if not isinstance(fields, dict) or not fields:
            raise SystemExit("scene patch set must be a non-empty object")
        if scene_number in seen:
            raise SystemExit(f"duplicate scene patch target: scene={scene_number}")
        seen.add(scene_number)
        target = scenes[scene_number - 1]
        if not isinstance(target, dict):
            raise SystemExit(f"scene patch target is not an object: scene={scene_number}")
        target.update(fields)
        applied += 1
    return applied


def apply_explicit_beat_patches(value: dict[str, Any]) -> int:
    patches = value.pop("beatPatches", [])
    if not isinstance(patches, list):
        raise SystemExit("beatPatches must be an array")
    scenes = value.get("scenes")
    if not isinstance(scenes, list):
        raise SystemExit("assembled authoring scenes must be an array")
    applied = 0
    seen: set[tuple[int, int]] = set()
    for row in patches:
        if not isinstance(row, dict):
            raise SystemExit("beatPatches entries must be objects")
        scene_number, beat_number, fields = row.get("sceneNumber"), row.get("beatNumber"), row.get("set")
        if not isinstance(scene_number, int) or not 1 <= scene_number <= len(scenes):
            raise SystemExit(f"beat patch sceneNumber invalid: {scene_number}")
        scene = scenes[scene_number - 1]
        beats = scene.get("beats") if isinstance(scene, dict) else None
        if not isinstance(beats, list) or not isinstance(beat_number, int) or not 1 <= beat_number <= len(beats):
            raise SystemExit(f"beat patch beatNumber invalid: scene={scene_number} beat={beat_number}")
        if not isinstance(fields, dict) or not fields:
            raise SystemExit("beat patch set must be a non-empty object")
        key = (scene_number, beat_number)
        if key in seen:
            raise SystemExit(f"duplicate beat patch target: scene={scene_number} beat={beat_number}")
        seen.add(key)
        target = beats[beat_number - 1]
        if not isinstance(target, dict):
            raise SystemExit(f"beat patch target is not an object: scene={scene_number} beat={beat_number}")
        target.update(fields)
        applied += 1
    return applied


def normalize_renderer_visual_modes(value: dict[str, Any]) -> int:
    changed = 0
    scenes = value.get("scenes")
    if not isinstance(scenes, list):
        raise SystemExit("assembled authoring scenes must be an array")
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        beats = scene.get("beats")
        if not isinstance(beats, list):
            continue
        for beat in beats:
            if isinstance(beat, dict) and beat.get("visualTemplate") == "source-receipt" and beat.get("visualMode") != "text-focus":
                beat["visualMode"] = "text-focus"
                changed += 1
        if beats and isinstance(beats[0], dict) and beats[0].get("visualTemplate") == "source-receipt":
            scene["visualMode"] = "text-focus"
    return changed


def assemble_legacy(value: dict[str, Any], root: Path, date: str, part_count: int) -> int:
    if value.get("episodeDate") != date:
        raise SystemExit("assembled authoring episodeDate mismatch")
    scene_patch_count = apply_explicit_scene_patches(value)
    beat_patch_count = apply_explicit_beat_patches(value)
    review = value.get("review")
    if isinstance(review, dict) and "scores" not in review:
        story_scores = review.get("storyScores")
        if not isinstance(story_scores, dict):
            raise SystemExit("review.storyScores is required")
        review["scores"] = dict(story_scores)
    daily_sha = bind_daily_source_lineage(value, root, date)
    assert_renderer_240_financial_scope(root)
    mode_aliases = normalize_renderer_visual_modes(value)
    registry = authoring_closure.load_json(root / "contracts/financial_recipe_registry.json", "financial recipe registry")
    try:
        authoring_closure.validate_or_raise(value, registry)
    except authoring_closure.AuthoringClosureError as exc:
        raise SystemExit(f"daily authoring renderer closure failed:\n{exc}") from exc
    output = root / "daily-authoring" / f"{date}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"ASSEMBLED legacy {part_count} authoring parts -> {output}; daily_sha256={daily_sha}; "
        f"scene_patches={scene_patch_count}; beat_patches={beat_patch_count}; "
        f"source_receipt_mode_aliases={mode_aliases}; authoring_closure=PASS"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.repo_root.resolve()
    parts_dir = root / "daily-authoring-parts" / args.date
    parts = sorted(parts_dir.glob("*.json"))
    if not parts:
        raise SystemExit(f"no authoring parts: {parts_dir}")
    value: dict[str, Any] = {}
    for part in parts:
        piece = json.loads(part.read_text(encoding="utf-8"))
        if not isinstance(piece, dict):
            raise SystemExit(f"authoring part root must be object: {part}")
        value = merge(value, piece)
    if value.get("contractVersion") == "2.0.0":
        return assemble_v2(value, root, args.date, len(parts))
    return assemble_legacy(value, root, args.date, len(parts))


if __name__ == "__main__":
    raise SystemExit(main())
