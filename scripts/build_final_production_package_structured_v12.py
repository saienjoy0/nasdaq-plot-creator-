#!/usr/bin/env python3
"""Current-v1.2 final package builder using structured machine authority.

Machine execution reads `working/<date>/current_final_production_source.json`.
`episode_package_<date>.md` is consumed only as a human projection identity target;
its embedded JSON formatting is never used to reconstruct Renderer input.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import build_final_production_package as base

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STORY_BEGIN = "<!--BEGIN_STORY_ENGINE_ANNEX-->"
STORY_END = "<!--END_STORY_ENGINE_ANNEX-->"
MEM_BEGIN = "<!--BEGIN_EPISODE_MEMORY_ANNEX-->"
MEM_END = "<!--END_EPISODE_MEMORY_ANNEX-->"
PROD_BEGIN = "<!--BEGIN_FINAL_PRODUCTION_SOURCE-->"
PROD_END = "<!--END_FINAL_PRODUCTION_SOURCE-->"
ANNEX_BLOCKS = (
    (STORY_BEGIN, STORY_END),
    (MEM_BEGIN, MEM_END),
    (PROD_BEGIN, PROD_END),
)


class StructuredFinalProductionError(ValueError):
    pass


def _date_from_package(package: Path) -> str:
    date = package.parent.name
    if not DATE_RE.fullmatch(date):
        raise StructuredFinalProductionError(
            f"cannot derive current episode date from package path: {package}"
        )
    return date


def _strip_human_annex_blocks(markdown: str) -> str:
    """Remove machine annex projections without parsing their JSON payloads."""
    public = markdown
    for begin, end in ANNEX_BLOCKS:
        start = public.find(begin)
        if start < 0:
            continue
        stop = public.find(end, start)
        if stop < 0:
            raise StructuredFinalProductionError(
                f"human projection has unterminated annex marker: {begin}"
            )
        stop += len(end)
        public = public[:start] + public[stop:]
    return public.strip()


def _load_structured_source(output_root: Path, date: str) -> tuple[Path, dict[str, Any]]:
    path = output_root / "working" / date / "current_final_production_source.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StructuredFinalProductionError(
            f"current structured production source invalid: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise StructuredFinalProductionError(
            "current structured production source must be an object"
        )
    if value.get("episode_date") != date:
        raise StructuredFinalProductionError(
            "current structured production source episode_date mismatch"
        )
    return path, value


def build(package_path: Path, output_root: Path, schema_path: Path) -> dict[str, Any]:
    package_path = package_path.resolve()
    output_root = output_root.resolve()
    date = _date_from_package(package_path)
    source_path, annex = _load_structured_source(output_root, date)
    markdown = package_path.read_text(encoding="utf-8")
    public = _strip_human_annex_blocks(markdown)
    schema = base.load_schema(schema_path)

    errors, warnings = base.validate_source(annex, public, schema)
    if errors:
        raise StructuredFinalProductionError("\n".join(errors))

    package_sha = base.sha256_file(package_path)
    source_sha = base.sha256_file(source_path)
    ir = base.build_ir(annex, package_sha)
    spoken = base.build_spoken_script(ir)
    asset_manifest = base.build_asset_manifest(ir)
    render_spec = annex["render_spec"]
    report = base.consistency_report(ir, spoken, asset_manifest, render_spec)
    if report["status"] != "pass":
        raise StructuredFinalProductionError("\n".join(report["errors"]))

    report["machine_authority"] = {
        "kind": "structured-artifact",
        "path": source_path.relative_to(output_root).as_posix(),
        "sha256": source_sha,
        "markdownRole": "human-projection-identity-only",
    }
    paths = {
        "ir": output_root / "working" / date / "episode_package_ir.json",
        "spoken_script": output_root / "episodes" / date / f"spoken_script_{date}.md",
        "asset_manifest": output_root / "episodes" / date / "asset_manifest.json",
        "render_spec": output_root / "render-specs" / date / "render_spec.json",
        "consistency_report": output_root / "verification" / date / "production_consistency_report.json",
        "preflight": output_root / "verification" / date / "official_execution_preflight.json",
    }
    base.write_atomic(paths["ir"], base.canonical_json(ir).encode())
    base.write_atomic(paths["spoken_script"], spoken.encode())
    base.write_atomic(paths["asset_manifest"], base.canonical_json(asset_manifest).encode())
    base.write_atomic(paths["render_spec"], base.canonical_json(render_spec).encode())
    base.write_atomic(paths["consistency_report"], base.canonical_json(report).encode())
    artifact_hashes = {
        key: base.sha256_file(path) for key, path in paths.items() if key != "preflight"
    }
    preflight = {
        "contract_version": "1.0.0",
        "episode_date": date,
        "status": "pass",
        "episode_package": {"path": str(package_path), "sha256": package_sha},
        "machine_authority": {
            "path": source_path.relative_to(output_root).as_posix(),
            "sha256": source_sha,
        },
        "artifacts": artifact_hashes,
        "post_inquisition": annex["post_inquisition"],
        "image_resolution": annex["image_resolution"],
        "unresolved_states": 0,
        "preview_authorized": True,
        "final_authorized": False,
        "warnings": warnings,
    }
    base.write_atomic(paths["preflight"], base.canonical_json(preflight).encode())
    return {
        "status": "pass",
        "paths": {key: str(value) for key, value in paths.items()},
        "hashes": artifact_hashes,
        "machine_authority": preflight["machine_authority"],
    }
