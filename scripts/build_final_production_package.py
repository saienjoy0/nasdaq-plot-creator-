#!/usr/bin/env python3
"""Build and validate final production artifacts from the final episode package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

BEGIN = "<!--BEGIN_FINAL_PRODUCTION_SOURCE-->"
END = "<!--END_FINAL_PRODUCTION_SOURCE-->"
JSON_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
MEMREF_RE = re.compile(r"<!--MEMREF:MR-[0-9]{3}:U-[0-9]{3}-->")
SCENE_IDS = [f"scene-{i:02d}" for i in range(1, 10)]


class ProductionPackageError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_schema(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductionPackageError(f"cannot load schema {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProductionPackageError("schema must be an object")
    return value


def parse_source_annex(markdown: str) -> tuple[dict[str, Any], str]:
    begin_count = markdown.count(BEGIN)
    end_count = markdown.count(END)
    if begin_count != 1 or end_count != 1:
        raise ProductionPackageError(
            f"final production source markers must appear exactly once: begin={begin_count} end={end_count}"
        )
    start = markdown.index(BEGIN)
    end_marker = markdown.index(END)
    if end_marker <= start:
        raise ProductionPackageError("final production source end marker appears before begin")
    block_end = end_marker + len(END)
    block = markdown[start:block_end]
    fences = list(JSON_FENCE_RE.finditer(block))
    if len(fences) != 1:
        raise ProductionPackageError(
            f"final production source must contain exactly one JSON fence: found={len(fences)}"
        )
    try:
        annex = json.loads(fences[0].group(1))
    except json.JSONDecodeError as exc:
        raise ProductionPackageError(f"invalid final production source JSON: {exc}") from exc
    if not isinstance(annex, dict):
        raise ProductionPackageError("final production source JSON must be an object")
    public = markdown[:start] + markdown[block_end:]
    mem_begin = "<!--BEGIN_EPISODE_MEMORY_ANNEX-->"
    mem_end = "<!--END_EPISODE_MEMORY_ANNEX-->"
    if mem_begin in public or mem_end in public:
        if public.count(mem_begin) != 1 or public.count(mem_end) != 1:
            raise ProductionPackageError("episode memory annex markers must appear exactly once when present")
        m_start = public.index(mem_begin)
        m_end = public.index(mem_end)
        if m_end <= m_start:
            raise ProductionPackageError("episode memory annex end appears before begin")
        public = public[:m_start] + public[m_end + len(mem_end):]
    return annex, public


def schema_validation_errors(annex: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"source.{'.'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
        for err in sorted(validator.iter_errors(annex), key=lambda e: list(e.absolute_path))
    ]


def collect_public_strings(render_spec: dict[str, Any]) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    publishing = render_spec.get("publishing", {})
    for key in ("recommendedTitle", "recommendedThumbnailText", "description"):
        value = publishing.get(key)
        if isinstance(value, str) and value.strip():
            values.append((f"publishing.{key}", value))
    for s_index, scene in enumerate(render_spec.get("scenes", [])):
        if not isinstance(scene, dict):
            continue
        scene_id = scene.get("sceneId", f"scenes[{s_index}]")
        value = scene.get("headline")
        if isinstance(value, str) and value.strip():
            values.append((f"{scene_id}.headline", value))
        for i, value in enumerate(scene.get("supportingTexts", [])):
            if isinstance(value, str) and value.strip():
                values.append((f"{scene_id}.supportingTexts[{i}]", value))
        for c_index, chunk in enumerate(scene.get("narrationChunks", [])):
            if not isinstance(chunk, dict):
                continue
            value = chunk.get("speechText")
            if isinstance(value, str) and value.strip():
                values.append((f"{scene_id}.narrationChunks[{c_index}].speechText", value))
        for b_index, beat in enumerate(scene.get("visualBeats", [])):
            if not isinstance(beat, dict):
                continue
            for key in ("narrationStartCue", "narrationEndCue", "screenQuestion", "primaryElement", "changeCue"):
                value = beat.get(key)
                if isinstance(value, str) and value.strip():
                    values.append((f"{scene_id}.visualBeats[{b_index}].{key}", value))
            for i, value in enumerate(beat.get("viewerTexts", [])):
                if isinstance(value, str) and value.strip():
                    values.append((f"{scene_id}.visualBeats[{b_index}].viewerTexts[{i}]", value))
    return values


def validate_source(annex: dict[str, Any], public_markdown: str, schema: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors = schema_validation_errors(annex, schema)
    warnings: list[str] = []
    if errors:
        return errors, warnings

    date = annex["episode_date"]
    render_spec = annex["render_spec"]
    if render_spec.get("episode", {}).get("targetDate") != date:
        errors.append("render_spec.episode.targetDate must match episode_date")
    if render_spec.get("schemaVersion") != annex["renderer_contract"]["schema_version"]:
        errors.append("renderer contract schema_version must match render_spec.schemaVersion")
    review = render_spec.get("review", {})
    if review.get("verdict") not in {"approved", "conditional-pass", "conditional_pass"}:
        errors.append("render_spec.review.verdict must be approved or conditional-pass")
    if review.get("approvedForCodex") is not True:
        errors.append("render_spec.review.approvedForCodex must be true")

    scenes = render_spec.get("scenes", [])
    scene_ids = [scene.get("sceneId") for scene in scenes if isinstance(scene, dict)]
    if scene_ids != SCENE_IDS:
        errors.append(f"render_spec.scenes must be exactly {SCENE_IDS}")
    chunk_ids: set[str] = set()
    beat_ids: set[str] = set()
    placement_asset_ids: set[str] = set()
    for scene in scenes:
        if not isinstance(scene, dict):
            errors.append("each render_spec scene must be an object")
            continue
        scene_id = str(scene.get("sceneId"))
        chunks = scene.get("narrationChunks", [])
        if not chunks:
            errors.append(f"{scene_id} must contain narrationChunks")
        local_chunk_ids: set[str] = set()
        for c_index, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                errors.append(f"{scene_id}.narrationChunks[{c_index}] must be an object")
                continue
            chunk_id = chunk.get("chunkId")
            if not isinstance(chunk_id, str) or not chunk_id:
                errors.append(f"{scene_id}.narrationChunks[{c_index}].chunkId is required")
                continue
            if chunk_id in chunk_ids:
                errors.append(f"duplicate chunkId: {chunk_id}")
            chunk_ids.add(chunk_id)
            local_chunk_ids.add(chunk_id)
            for key in ("speechText", "captionText"):
                text = chunk.get(key)
                if not isinstance(text, str) or not text.strip():
                    errors.append(f"{scene_id}.{chunk_id}.{key} is required")
                elif MEMREF_RE.search(text):
                    errors.append(f"MEMREF marker leaked into {scene_id}.{chunk_id}.{key}")
            pause = chunk.get("pauseAfterMs")
            if not isinstance(pause, int) or pause < 0:
                errors.append(f"{scene_id}.{chunk_id}.pauseAfterMs must be a non-negative integer")
        for b_index, beat in enumerate(scene.get("visualBeats", [])):
            if not isinstance(beat, dict):
                errors.append(f"{scene_id}.visualBeats[{b_index}] must be an object")
                continue
            beat_id = beat.get("beatId")
            if not isinstance(beat_id, str) or not beat_id:
                errors.append(f"{scene_id}.visualBeats[{b_index}].beatId is required")
                continue
            if beat_id in beat_ids:
                errors.append(f"duplicate beatId: {beat_id}")
            beat_ids.add(beat_id)
            for key in ("startChunkId", "endChunkId"):
                if beat.get(key) not in local_chunk_ids:
                    errors.append(f"{scene_id}.{beat_id}.{key} must reference a chunk in the same scene")
            for key in ("narrationStartCue", "narrationEndCue"):
                cue = beat.get(key)
                if not isinstance(cue, str) or not cue.strip():
                    errors.append(f"{scene_id}.{beat_id}.{key} is required")
                elif MEMREF_RE.search(cue):
                    errors.append(f"MEMREF marker leaked into {scene_id}.{beat_id}.{key}")
            if beat.get("assetState") not in {"resolved", "not-required", "ready"}:
                errors.append(f"{scene_id}.{beat_id}.assetState is unresolved")
        for placement in scene.get("assetPlacements", []):
            if isinstance(placement, dict) and isinstance(placement.get("assetId"), str):
                placement_asset_ids.add(placement["assetId"])

    catalog = annex["asset_catalog"]
    catalog_ids = [item["asset_id"] for item in catalog]
    if len(catalog_ids) != len(set(catalog_ids)):
        errors.append("asset_catalog contains duplicate asset_id")
    missing_assets = sorted(placement_asset_ids - set(catalog_ids))
    if missing_assets:
        errors.append(f"asset_catalog omits placement assets: {missing_assets}")
    for item in catalog:
        path = Path(item["path"])
        if path.is_absolute() or ".." in path.parts:
            errors.append(f"asset path must be safe and relative: {item['path']}")
        if item["status"] == "ready" and not item["path"].strip():
            errors.append(f"ready asset has empty path: {item['asset_id']}")

    routes = annex["image_resolution"]["routes"]
    route_beat_ids: set[str] = set()
    catalog_set = set(catalog_ids)
    for route in routes:
        beat_id = route["beat_id"]
        if beat_id in route_beat_ids:
            errors.append(f"duplicate image route beat_id: {beat_id}")
        route_beat_ids.add(beat_id)
        selected = route["selected_path"]
        selected_asset = route["selected_asset_id"]
        if selected == "primary" and selected_asset != route["primary_asset_id"]:
            errors.append(f"{beat_id}: primary selected path must select primary_asset_id")
        if selected == "fallback" and selected_asset != route["fallback_asset_id"]:
            errors.append(f"{beat_id}: fallback selected path must select fallback_asset_id")
        if selected == "not-required" and selected_asset is not None:
            errors.append(f"{beat_id}: not-required route must not select an asset")
        if selected_asset is not None and selected_asset not in catalog_set:
            errors.append(f"{beat_id}: selected image asset is absent from asset_catalog")

    for label, value in collect_public_strings(render_spec):
        if MEMREF_RE.search(value):
            errors.append(f"MEMREF marker leaked into public render text at {label}")
        if value not in public_markdown:
            errors.append(f"episode package public text does not contain exact {label}: {value!r}")
    if MEMREF_RE.search(canonical_json(render_spec)):
        errors.append("MEMREF marker leaked into render_spec")
    return errors, warnings


def build_ir(annex: dict[str, Any], episode_package_sha: str) -> dict[str, Any]:
    render_spec = annex["render_spec"]
    return {
        "contract_version": "1.0.0",
        "episode_date": annex["episode_date"],
        "episode_package_sha256": episode_package_sha,
        "post_inquisition": annex["post_inquisition"],
        "image_resolution": annex["image_resolution"],
        "renderer_contract": annex["renderer_contract"],
        "asset_catalog": annex["asset_catalog"],
        "publishing": render_spec.get("publishing", {}),
        "editorial": render_spec.get("editorial", {}),
        "sources": render_spec.get("sources", []),
        "review": render_spec.get("review", {}),
        "scenes": render_spec["scenes"],
    }


def build_spoken_script(ir: dict[str, Any]) -> str:
    lines = [f"# 朝のNASDAQカフェ｜音声専用台本 {ir['episode_date']}", ""]
    for scene in ir["scenes"]:
        lines.append(f"## {scene['sceneId']}")
        for chunk in scene["narrationChunks"]:
            lines.append(chunk["speechText"])
            if chunk.get("pauseAfterMs", 0):
                lines.append(f"<!--PAUSE_MS:{chunk['pauseAfterMs']}-->")
        lines.append("")
    text = "\n".join(lines).rstrip() + "\n"
    if MEMREF_RE.search(text):
        raise ProductionPackageError("MEMREF marker leaked into spoken script")
    return text


def build_asset_manifest(ir: dict[str, Any]) -> dict[str, Any]:
    used: dict[str, list[str]] = {}
    for scene in ir["scenes"]:
        for placement in scene.get("assetPlacements", []):
            asset_id = placement.get("assetId")
            if isinstance(asset_id, str):
                used.setdefault(asset_id, []).append(f"{scene['sceneId']}:{placement.get('placementId', '')}")
    catalog = {item["asset_id"]: item for item in ir["asset_catalog"]}
    assets = []
    for asset_id in sorted(catalog):
        item = dict(catalog[asset_id])
        item["used_by"] = sorted(used.get(asset_id, []))
        assets.append(item)
    return {
        "contract_version": "1.0.0",
        "episode_date": ir["episode_date"],
        "selected_path": ir["image_resolution"]["selected_path"],
        "assets": assets,
    }


def consistency_report(ir: dict[str, Any], spoken: str, asset_manifest: dict[str, Any], render_spec: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    expected_speech = [chunk["speechText"] for scene in ir["scenes"] for chunk in scene["narrationChunks"]]
    for speech in expected_speech:
        if spoken.count(speech) != 1:
            errors.append(f"spoken script must contain speech exactly once: {speech!r}")
    if render_spec.get("episode", {}).get("targetDate") != ir["episode_date"]:
        errors.append("IR/render spec episode date mismatch")
    if [s.get("sceneId") for s in render_spec.get("scenes", [])] != [s.get("sceneId") for s in ir["scenes"]]:
        errors.append("IR/render spec scene order mismatch")
    manifest_ids = {a["asset_id"] for a in asset_manifest["assets"]}
    required_ids = {
        p["assetId"]
        for s in ir["scenes"]
        for p in s.get("assetPlacements", [])
        if isinstance(p, dict) and isinstance(p.get("assetId"), str)
    }
    missing = sorted(required_ids - manifest_ids)
    if missing:
        errors.append(f"asset manifest misses required assets: {missing}")
    if MEMREF_RE.search(spoken) or MEMREF_RE.search(canonical_json(asset_manifest)) or MEMREF_RE.search(canonical_json(render_spec)):
        errors.append("MEMREF production metadata leaked into public artifacts")
    return {
        "contract_version": "1.0.0",
        "episode_date": ir["episode_date"],
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "unresolved_states": 0 if not errors else len(errors),
    }


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(content)
    tmp.replace(path)


def build(package_path: Path, output_root: Path, schema_path: Path) -> dict[str, Any]:
    package_path = package_path.resolve()
    output_root = output_root.resolve()
    markdown = package_path.read_text(encoding="utf-8")
    annex, public = parse_source_annex(markdown)
    schema = load_schema(schema_path)
    errors, warnings = validate_source(annex, public, schema)
    if errors:
        raise ProductionPackageError("\n".join(errors))

    package_sha = sha256_file(package_path)
    ir = build_ir(annex, package_sha)
    spoken = build_spoken_script(ir)
    asset_manifest = build_asset_manifest(ir)
    render_spec = annex["render_spec"]
    report = consistency_report(ir, spoken, asset_manifest, render_spec)
    if report["status"] != "pass":
        raise ProductionPackageError("\n".join(report["errors"]))

    date = annex["episode_date"]
    paths = {
        "ir": output_root / "working" / date / "episode_package_ir.json",
        "spoken_script": output_root / "episodes" / date / f"spoken_script_{date}.md",
        "asset_manifest": output_root / "episodes" / date / "asset_manifest.json",
        "render_spec": output_root / "render-specs" / date / "render_spec.json",
        "consistency_report": output_root / "verification" / date / "production_consistency_report.json",
        "preflight": output_root / "verification" / date / "official_execution_preflight.json",
    }
    write_atomic(paths["ir"], canonical_json(ir).encode())
    write_atomic(paths["spoken_script"], spoken.encode())
    write_atomic(paths["asset_manifest"], canonical_json(asset_manifest).encode())
    write_atomic(paths["render_spec"], canonical_json(render_spec).encode())
    write_atomic(paths["consistency_report"], canonical_json(report).encode())
    artifact_hashes = {key: sha256_file(path) for key, path in paths.items() if key != "preflight"}
    preflight = {
        "contract_version": "1.0.0",
        "episode_date": date,
        "status": "pass",
        "episode_package": {"path": str(package_path), "sha256": package_sha},
        "artifacts": artifact_hashes,
        "post_inquisition": annex["post_inquisition"],
        "image_resolution": annex["image_resolution"],
        "unresolved_states": 0,
        "preview_authorized": True,
        "final_authorized": False,
        "warnings": warnings,
    }
    write_atomic(paths["preflight"], canonical_json(preflight).encode())
    return {"status": "pass", "paths": {k: str(v) for k, v in paths.items()}, "hashes": artifact_hashes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-package", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument(
        "--schema", type=Path,
        default=Path(__file__).resolve().parents[1] / "skills/nasdaq-cafe-final-production/contracts/final_production_source_annex.schema.json",
    )
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = build(args.episode_package, args.output_root, args.schema)
        code = 0
    except (OSError, ProductionPackageError, json.JSONDecodeError) as exc:
        result = {"status": "fail", "errors": [str(exc)]}
        code = 1
    text = canonical_json(result)
    if args.report:
        write_atomic(args.report, text.encode())
    else:
        sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
