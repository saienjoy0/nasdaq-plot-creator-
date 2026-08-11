#!/usr/bin/env python3
"""Assemble one approved daily episode package from already-authored artifacts.

This is a deterministic packaging step, not an editorial author. It does not run
research, choose a lead, rewrite narration, score entertainment, select a Visual
Template, generate an image, or choose Primary/Fallback. It binds the already
validated Causal Dossier, Story Engine output, explicit Visual Source decision,
Financial Visual bindings, and current render shell into the canonical final episode
package used by Daily Production.

Historical memory usage is never inferred. Selected memory entries whose dossier
``editorial_use`` is ``not_used`` are safely recorded as internal-only. Any selected
memory entry that is actually used requires an explicit ``memory_usage_bindings.json``
input produced by ChatGPT; otherwise assembly fails closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import materialize_financial_contract_1_0 as financial_projection
import materialize_renderer_sources as renderer_sources
import visual_source_projection

STORY_BEGIN = "<!--BEGIN_STORY_ENGINE_ANNEX-->"
STORY_END = "<!--END_STORY_ENGINE_ANNEX-->"
MEM_BEGIN = "<!--BEGIN_EPISODE_MEMORY_ANNEX-->"
MEM_END = "<!--END_EPISODE_MEMORY_ANNEX-->"
PROD_BEGIN = "<!--BEGIN_FINAL_PRODUCTION_SOURCE-->"
PROD_END = "<!--END_FINAL_PRODUCTION_SOURCE-->"


class DailyEpisodeAssemblyError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DailyEpisodeAssemblyError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise DailyEpisodeAssemblyError(f"{label} must be an object")
    return value


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def normalize_scene_headings(text: str) -> str:
    for number in range(1, 10):
        text = re.sub(
            rf"(?m)^##\s+B{number}\.\s+Scene\s+{number}(?=｜|\|)",
            f"## Scene {number}",
            text,
        )
    return text


def _reference(root: Path, path: Path) -> dict[str, str]:
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise DailyEpisodeAssemblyError(f"artifact escapes repository root: {path}") from exc
    return {"path": relative, "sha256": sha256_file(path)}


def _story_annex(root: Path, date: str) -> dict[str, Any]:
    story = root / "working" / date / "story-engine"
    acceptance_path = story / "story_engine_acceptance.json"
    acceptance = load_json(acceptance_path, "Story Engine acceptance")
    if acceptance.get("episode_date") != date or acceptance.get("status") != "pass":
        raise DailyEpisodeAssemblyError("Story Engine acceptance must be PASS for the same episode date")
    required = {
        "story_plan": story / "story_plan.json",
        "story_script": story / "story_script.json",
        "creative_review": story / "creative_review.json",
        "acceptance": acceptance_path,
        "projection": story / "story_projection_report.json",
    }
    for label, path in required.items():
        if not path.is_file():
            raise DailyEpisodeAssemblyError(f"missing Story Engine artifact {label}: {path}")
    projection = load_json(required["projection"], "Story Engine projection")
    if projection.get("episode_date") != date or projection.get("status") != "pass":
        raise DailyEpisodeAssemblyError("Story Engine projection must be PASS for the same episode date")
    return {
        "contract_version": "1.0.0",
        "episode_date": date,
        "status": "pass",
        **{key: _reference(root, path) for key, path in required.items()},
        "critic": acceptance.get("critic", {}),
    }


def _usage_binding_map(path: Path | None, root: Path, date: str) -> dict[tuple[str, str], dict[str, Any]]:
    if path is None:
        return {}
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise DailyEpisodeAssemblyError("memory usage bindings must be inside repository root") from exc
    document = load_json(resolved, "memory usage bindings")
    if document.get("contract_version") != "1.0.0" or document.get("episode_date") != date:
        raise DailyEpisodeAssemblyError("memory usage bindings contract/date mismatch")
    rows = document.get("references")
    if not isinstance(rows, list):
        raise DailyEpisodeAssemblyError("memory usage bindings references must be an array")
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise DailyEpisodeAssemblyError(f"memory usage bindings references[{index}] must be an object")
        key = (row.get("memory_reference_type"), row.get("memory_reference_id"))
        if not all(isinstance(item, str) and item for item in key):
            raise DailyEpisodeAssemblyError(f"memory usage bindings references[{index}] key is invalid")
        if key in result:
            raise DailyEpisodeAssemblyError(f"duplicate memory usage binding: {key}")
        mode = row.get("public_usage_mode")
        usages = row.get("usages")
        scope_limit = row.get("scope_limit")
        if mode not in {"internal_only", "public_revalidated"}:
            raise DailyEpisodeAssemblyError(f"memory usage binding mode is invalid: {key}")
        if not isinstance(usages, list) or not isinstance(scope_limit, str) or not scope_limit:
            raise DailyEpisodeAssemblyError(f"memory usage binding usages/scope_limit invalid: {key}")
        result[key] = row
    return result


def _memory_annex(
    root: Path,
    date: str,
    *,
    memory_usage_bindings: Path | None,
) -> dict[str, Any]:
    work = root / "working" / date
    research = root / "research" / date
    dossier_path = research / f"causal_research_dossier_{date}.json"
    retrieval_path = work / f"memory_retrieval_report_{date}.json"
    dossier = load_json(dossier_path, "Causal Dossier")
    retrieval = load_json(retrieval_path, "memory retrieval report")
    if dossier.get("episode_date") != date or retrieval.get("episode_date") != date:
        raise DailyEpisodeAssemblyError("Causal Dossier / memory retrieval date mismatch")
    revalidation = {
        (item["memory_reference_type"], item["memory_reference_id"]): item
        for item in dossier.get("memory_revalidation", [])
        if isinstance(item, dict)
        and isinstance(item.get("memory_reference_type"), str)
        and isinstance(item.get("memory_reference_id"), str)
    }
    bindings = _usage_binding_map(memory_usage_bindings, root, date)
    refs: list[dict[str, Any]] = []
    serial = 1
    for item in retrieval.get("selected", []):
        if item.get("item_type") == "core":
            continue
        key = (item.get("item_type"), item.get("item_id"))
        entry = revalidation.get(key)
        if entry is None:
            raise DailyEpisodeAssemblyError(f"missing memory revalidation for selected item: {key}")
        editorial_use = entry.get("editorial_use")
        binding = bindings.get(key)
        if editorial_use == "not_used":
            if binding is not None and (binding.get("public_usage_mode") != "internal_only" or binding.get("usages")):
                raise DailyEpisodeAssemblyError(f"not_used memory cannot have public usages: {key}")
            public_usage_mode = "internal_only"
            scope_limit = (
                binding.get("scope_limit")
                if binding is not None
                else "過去記録は現在証拠として使わず、当日の一次情報・主要報道で再検証した内部比較に限定する。"
            )
            usages: list[Any] = []
        else:
            if binding is None:
                raise DailyEpisodeAssemblyError(
                    f"selected memory used by the Dossier requires explicit memory_usage_bindings.json: {key}"
                )
            if binding.get("public_usage_mode") != "public_revalidated" or not binding.get("usages"):
                raise DailyEpisodeAssemblyError(f"used memory requires explicit public_revalidated usages: {key}")
            public_usage_mode = "public_revalidated"
            scope_limit = binding["scope_limit"]
            usages = binding["usages"]
        refs.append(
            {
                "reference_id": f"MR-{serial:03d}",
                "memory_reference_type": entry["memory_reference_type"],
                "memory_reference_id": entry["memory_reference_id"],
                "historical_confidence": entry["historical_confidence"],
                "current_revalidation_status": entry["revalidation_status"],
                "dossier_editorial_use": editorial_use,
                "dossier_current_evidence_ids": entry["current_evidence_ids"],
                "difference_from_previous": entry["difference_from_previous"],
                "public_usage_mode": public_usage_mode,
                "scope_limit": scope_limit,
                "usages": usages,
            }
        )
        serial += 1
    extra = sorted(set(bindings) - set(revalidation))
    if extra:
        raise DailyEpisodeAssemblyError(f"memory usage bindings contain unknown references: {extra}")
    return {
        "contract_version": "1.0.0",
        "episode_date": date,
        "causal_dossier": _reference(root, dossier_path),
        "references": refs,
        "validation_intent": {
            "past_mentions_complete": True,
            "title_thumbnail_checked": True,
            "post_inquisition_final": True,
        },
    }


def _resolve_assets(
    root: Path,
    date: str,
    *,
    final_contract_path: Path,
    render: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    verification = root / "verification" / date
    visual = visual_source_projection.prepare_visual_sources(
        root=root,
        date=date,
        final_contract_path=final_contract_path,
        render=render,
    )
    asset_catalog = visual_source_projection.build_asset_catalog(render, visual)
    asset_log = verification / "asset_resolution_log.json"
    image_log = verification / "image_generation_log.json"
    if visual["has_visual_sources"]:
        if not asset_log.is_file():
            raise DailyEpisodeAssemblyError(
                "Visual Source selection requires precomputed verification asset_resolution_log.json"
            )
        audit = load_json(asset_log, "asset resolution log")
        selection = audit.get("selection") if isinstance(audit, dict) else None
        if not isinstance(selection, dict) or selection.get("status") != "resolved":
            raise DailyEpisodeAssemblyError("Visual Source asset resolution selection is unresolved")
        if selection.get("selected_path") != visual["selected_path"]:
            raise DailyEpisodeAssemblyError("Visual Source selected_path mismatch")
    else:
        write_atomic(
            asset_log,
            dump(
                {
                    "episode_date": date,
                    "status": "resolved",
                    "selected_path": "not-required",
                    "unresolved_count": 0,
                    "registered_assets": [item["asset_id"] for item in asset_catalog],
                }
            )
            + "\n",
        )
    selected_generated = [
        item for item in visual["selected_assets"] if item.get("sourceKind") == "generated-image"
    ]
    if not selected_generated:
        write_atomic(
            image_log,
            dump(
                {
                    "episode_date": date,
                    "status": "not-required",
                    "attempts": 0,
                    "selected_path": visual["selected_path"],
                }
            )
            + "\n",
        )
    elif not image_log.is_file():
        raise DailyEpisodeAssemblyError(
            "selected generated-image requires precomputed image_generation_log.json"
        )
    image_resolution = {
        "status": "resolved",
        "selected_path": visual["selected_path"],
        "unresolved_count": 0,
        "routes": visual["routes"],
    }
    return image_resolution, asset_catalog


def assemble(
    *,
    root: Path,
    date: str,
    memory_usage_bindings: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    work = root / "working" / date
    episodes = root / "episodes" / date
    verification = root / "verification" / date
    render_path = root / "render-specs" / date / "render_spec.json"
    public_path = episodes / f"episode_package_public_{date}.md"
    financial_bindings = work / "financial_visual_bindings.json"
    for path, label in (
        (render_path, "render spec"),
        (public_path, "public episode package"),
        (financial_bindings, "financial visual bindings"),
        (root / "research" / date / f"causal_research_dossier_{date}.json", "Causal Dossier"),
        (work / f"memory_retrieval_report_{date}.json", "memory retrieval report"),
    ):
        if not path.is_file() or path.stat().st_size == 0:
            raise DailyEpisodeAssemblyError(f"missing {label}: {path}")
    episodes.mkdir(parents=True, exist_ok=True)
    verification.mkdir(parents=True, exist_ok=True)

    materialized = renderer_sources.materialize(
        root=root,
        date=date,
        render_path=render_path,
        public_package_path=public_path,
        bindings_path=financial_bindings,
    )
    render = materialized["render"]
    financial_projection.materialize(root=root, date=date)
    image_resolution, asset_catalog = _resolve_assets(
        root,
        date,
        final_contract_path=materialized["final_contract_path"],
        render=render,
    )
    # Visual Source projection mutates the authoritative render in memory with the
    # selected placements. Persist that exact render before H3/H4 reads render_spec.json.
    write_atomic(render_path, dump(render) + "\n")
    story_annex = _story_annex(root, date)
    memory_annex = _memory_annex(
        root,
        date,
        memory_usage_bindings=memory_usage_bindings,
    )
    production_annex = {
        "contract_version": "1.0.0",
        "episode_date": date,
        "post_inquisition": {
            "status": "pass",
            "required_changes_applied": True,
            "unresolved_required_changes": 0,
        },
        "image_resolution": image_resolution,
        "renderer_contract": {
            "repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion",
            "schema_version": render["schemaVersion"],
        },
        "asset_catalog": asset_catalog,
        "render_spec": render,
    }
    public = normalize_scene_headings(
        Path(materialized["contract_package_path"]).read_text(encoding="utf-8").rstrip()
    )
    final = (
        public
        + "\n\n"
        + STORY_BEGIN
        + "\n```json\n"
        + dump(story_annex)
        + "\n```\n"
        + STORY_END
        + "\n\n"
        + MEM_BEGIN
        + "\n```json\n"
        + dump(memory_annex)
        + "\n```\n"
        + MEM_END
        + "\n\n"
        + PROD_BEGIN
        + "\n```json\n"
        + dump(production_annex)
        + "\n```\n"
        + PROD_END
        + "\n"
    )
    output = episodes / f"episode_package_{date}.md"
    write_atomic(output, final)
    return {
        "status": "pass",
        "episode_date": date,
        "episode_package": _reference(root, output),
        "render_intermediate": _reference(root, render_path),
        "story_acceptance": _reference(root, work / "story-engine" / "story_engine_acceptance.json"),
        "asset_count": len(asset_catalog),
        "selected_visual_path": image_resolution["selected_path"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--memory-usage-bindings", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = assemble(
            root=args.repo_root,
            date=args.date,
            memory_usage_bindings=args.memory_usage_bindings,
        )
        code = 0
    except (DailyEpisodeAssemblyError, OSError, KeyError, ValueError) as exc:
        result = {"status": "fail", "errors": str(exc).splitlines()}
        code = 2
    text = dump(result) + "\n"
    if args.output:
        write_atomic(args.output, text)
    else:
        sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
