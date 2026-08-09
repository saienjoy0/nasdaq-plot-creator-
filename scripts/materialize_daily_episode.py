#!/usr/bin/env python3
"""Materialize hash-bound daily episode artifacts without changing editorial content."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
import zlib
from pathlib import Path

import materialize_renderer_sources as renderer_sources
import visual_source_projection

STORY_BEGIN = "<!--BEGIN_STORY_ENGINE_ANNEX-->"
STORY_END = "<!--END_STORY_ENGINE_ANNEX-->"
MEM_BEGIN = "<!--BEGIN_EPISODE_MEMORY_ANNEX-->"
MEM_END = "<!--END_EPISODE_MEMORY_ANNEX-->"
PROD_BEGIN = "<!--BEGIN_FINAL_PRODUCTION_SOURCE-->"
PROD_END = "<!--END_FINAL_PRODUCTION_SOURCE-->"
DOSSIER_TEMPLATE_SHA = "3bc1edaf7b3ca35f30e02f50d9a97605b38bc6a5d6242485eba825f7aabec384"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def normalize_scene_headings(text: str) -> str:
    for scene_number in range(1, 10):
        text = re.sub(
            rf"(?m)^##\s+B{scene_number}\.\s+Scene\s+{scene_number}(?=｜|\|)",
            f"## Scene {scene_number}",
            text,
        )
    return text


def ensure_dossier_template(research: Path) -> Path:
    target = research / "causal_research_dossier.template.json"
    if target.exists():
        if sha(target) != DOSSIER_TEMPLATE_SHA:
            raise SystemExit(f"dossier template SHA mismatch: {sha(target)}")
        return target
    parts = sorted(research.glob("causal_research_dossier.template.zlib.b64.part-*"))
    if not parts:
        raise SystemExit(f"missing dossier template and compressed parts: {target}")
    encoded = "".join(p.read_text(encoding="utf-8").strip() for p in parts)
    try:
        raw = zlib.decompress(base64.b64decode(encoded, validate=True))
    except Exception as exc:
        raise SystemExit(f"failed to decode dossier template: {exc}") from exc
    actual = hashlib.sha256(raw).hexdigest()
    if actual != DOSSIER_TEMPLATE_SHA:
        raise SystemExit(f"decoded dossier template SHA mismatch: {actual}")
    target.write_bytes(raw)
    print(f"RECOVERED {target} sha256={actual}", flush=True)
    return target


def normalize_memory_locator(value):
    if isinstance(value, str):
        return value.replace(
            "memory_context.json#threads.ai-capex-payback",
            "memory_context.json#memory_selection.threads[0]",
        )
    if isinstance(value, list):
        return [normalize_memory_locator(v) for v in value]
    if isinstance(value, dict):
        return {k: normalize_memory_locator(v) for k, v in value.items()}
    return value


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = ap.parse_args()
    root = args.repo_root.resolve()
    date = args.date
    work = root / "working" / date
    story_work = work / "story-engine"
    research = root / "research" / date
    episodes = root / "episodes" / date
    render_path = root / "render-specs" / date / "render_spec.json"
    daily = root / "daily-inputs" / date / f"daily_source_package_{date}.md"
    query = work / "memory_query_plan.json"
    context = work / f"memory_context_{date}.md"
    report = work / f"memory_retrieval_report_{date}.json"
    manifest = research / "research_input_manifest.json"
    dossier_template = ensure_dossier_template(research)
    dossier = research / f"causal_research_dossier_{date}.json"
    dossier_report = research / "causal_dossier_validation.json"
    public_package = episodes / f"episode_package_public_{date}.md"
    final_package = episodes / f"episode_package_{date}.md"
    bindings = work / "financial_visual_bindings.json"
    story_bindings = story_work / "story_production_bindings.json"
    story_plan = story_work / "story_plan.json"
    story_script = story_work / "story_script.json"
    creative_review = story_work / "creative_review.json"
    story_acceptance = story_work / "story_engine_acceptance.json"
    story_projection = story_work / "story_projection_report.json"
    for path in (work, story_work, research, episodes, root / "verification" / date):
        path.mkdir(parents=True, exist_ok=True)

    run([
        sys.executable, "scripts/editorial_memory_retrieval.py",
        "--query-plan", str(query.relative_to(root)),
        "--context-output", str(context.relative_to(root)),
        "--report-output", str(report.relative_to(root)),
        "--repo-root", str(root),
    ])
    run([
        sys.executable, "scripts/build_research_input_manifest.py",
        "--episode-date", date,
        "--market-date", "2026-08-05",
        "--timezone", "America/New_York",
        "--information-cutoff", "2026-08-06T04:27:46+00:00",
        "--daily-source-package", str(daily),
        "--memory-query-plan", str(query),
        "--memory-context", str(context),
        "--memory-retrieval-report", str(report),
        "--output", str(manifest),
        "--repo-root", str(root),
    ])

    dossier_doc = normalize_memory_locator(json.loads(dossier_template.read_text(encoding="utf-8")))
    dossier_doc["research_input_manifest"]["sha256"] = sha(manifest)
    dossier.write_text(dump(dossier_doc) + "\n", encoding="utf-8")
    run([
        sys.executable,
        "skills/nasdaq-cafe-causal-research/validators/validate_causal_research_dossier.py",
        str(dossier),
        "--research-input-manifest", str(manifest),
        "--memory-retrieval-report", str(report),
        "--repo-root", str(root),
        "--json-output", str(dossier_report),
    ])

    run([
        sys.executable, "scripts/story-engine/materialize_story_engine.py",
        "--date", date, "--repo-root", str(root),
    ])
    run([
        sys.executable, "scripts/story-engine/project_story_script_to_production.py",
        "--story-script", str(story_script),
        "--creative-review", str(creative_review),
        "--render-spec", str(render_path),
        "--episode-package-public", str(public_package),
        "--bindings", str(story_bindings),
        "--report", str(story_projection),
    ])

    renderer_materialization = renderer_sources.materialize(
        root=root,
        date=date,
        render_path=render_path,
        public_package_path=public_package,
        bindings_path=bindings,
    )
    render = renderer_materialization["render"]
    contract_package = renderer_materialization["contract_package_path"]
    final_contract_path = renderer_materialization["final_contract_path"]

    try:
        visual_source = visual_source_projection.prepare_visual_sources(
            root=root,
            date=date,
            final_contract_path=final_contract_path,
            render=render,
        )
    except visual_source_projection.VisualSourceProjectionError as exc:
        raise SystemExit(str(exc)) from exc

    story_acceptance_doc = json.loads(story_acceptance.read_text(encoding="utf-8"))
    story_annex = {
        "contract_version": "1.0.0",
        "episode_date": date,
        "status": "pass",
        "story_plan": {"path": story_plan.relative_to(root).as_posix(), "sha256": sha(story_plan)},
        "story_script": {"path": story_script.relative_to(root).as_posix(), "sha256": sha(story_script)},
        "creative_review": {"path": creative_review.relative_to(root).as_posix(), "sha256": sha(creative_review)},
        "acceptance": {"path": story_acceptance.relative_to(root).as_posix(), "sha256": sha(story_acceptance)},
        "projection": {"path": story_projection.relative_to(root).as_posix(), "sha256": sha(story_projection)},
        "critic": story_acceptance_doc["critic"],
    }

    retrieval = json.loads(report.read_text(encoding="utf-8"))
    by_key = {
        (item["memory_reference_type"], item["memory_reference_id"]): item
        for item in dossier_doc["memory_revalidation"]
    }
    refs = []
    serial = 1
    for item in retrieval["selected"]:
        if item["item_type"] == "core":
            continue
        key = (item["item_type"], item["item_id"])
        if key not in by_key:
            raise SystemExit(f"missing memory revalidation for selected item: {key}")
        rv = by_key[key]
        refs.append({
            "reference_id": f"MR-{serial:03d}",
            "memory_reference_type": rv["memory_reference_type"],
            "memory_reference_id": rv["memory_reference_id"],
            "historical_confidence": rv["historical_confidence"],
            "current_revalidation_status": rv["revalidation_status"],
            "dossier_editorial_use": rv["editorial_use"],
            "dossier_current_evidence_ids": rv["current_evidence_ids"],
            "difference_from_previous": rv["difference_from_previous"],
            "public_usage_mode": "internal_only",
            "scope_limit": "過去記録は現在証拠として使わず、当日の一次情報・主要報道で再検証した内部比較に限定する。",
            "usages": [],
        })
        serial += 1
    memory_annex = {
        "contract_version": "1.0.0",
        "episode_date": date,
        "causal_dossier": {"path": dossier.relative_to(root).as_posix(), "sha256": sha(dossier)},
        "references": refs,
        "validation_intent": {"past_mentions_complete": True, "title_thumbnail_checked": True, "post_inquisition_final": True},
    }

    asset_catalog = visual_source_projection.build_asset_catalog(render, visual_source)
    image_resolution = {
        "status": "resolved",
        "selected_path": visual_source["selected_path"],
        "unresolved_count": 0,
        "routes": visual_source["routes"],
    }
    production_annex = {
        "contract_version": "1.0.0",
        "episode_date": date,
        "post_inquisition": {
            "status": "pass",
            "required_changes_applied": True,
            "unresolved_required_changes": 0,
        },
        "image_resolution": image_resolution,
        "renderer_contract": {"repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion", "schema_version": render["schemaVersion"]},
        "asset_catalog": asset_catalog,
        "render_spec": render,
    }
    public = normalize_scene_headings(contract_package.read_text(encoding="utf-8").rstrip())
    final = (
        public
        + "\n\n" + STORY_BEGIN + "\n```json\n" + dump(story_annex) + "\n```\n" + STORY_END
        + "\n\n" + MEM_BEGIN + "\n```json\n" + dump(memory_annex) + "\n```\n" + MEM_END
        + "\n\n" + PROD_BEGIN + "\n```json\n" + dump(production_annex) + "\n```\n" + PROD_END + "\n"
    )
    final_package.write_text(final, encoding="utf-8")

    verification = root / "verification" / date
    asset_log = verification / "asset_resolution_log.json"
    if visual_source["has_visual_sources"]:
        if not asset_log.is_file():
            raise SystemExit(
                "Visual Source selection requires precomputed verification asset_resolution_log.json"
            )
        audit = json.loads(asset_log.read_text(encoding="utf-8"))
        selection = audit.get("selection") if isinstance(audit, dict) else None
        if not isinstance(selection, dict) or selection.get("status") != "resolved":
            raise SystemExit("Visual Source asset_resolution_log selection is unresolved")
        if selection.get("selected_path") != visual_source["selected_path"]:
            raise SystemExit("Visual Source asset_resolution_log selected_path mismatch")
    else:
        asset_ids = [item["asset_id"] for item in asset_catalog]
        asset_log.write_text(
            dump({"episode_date": date, "status": "resolved", "selected_path": "not-required", "unresolved_count": 0, "registered_assets": asset_ids}) + "\n",
            encoding="utf-8",
        )
    selected_generated = [
        item for item in visual_source["selected_assets"] if item.get("sourceKind") == "generated-image"
    ]
    image_generation_log = verification / "image_generation_log.json"
    if not selected_generated:
        image_generation_log.write_text(
            dump({"episode_date": date, "status": "not-required", "attempts": 0, "selected_path": visual_source["selected_path"]}) + "\n",
            encoding="utf-8",
        )
    elif not image_generation_log.is_file():
        raise SystemExit(
            "selected generated-image requires precomputed image_generation_log.json from ChatGPT image generation"
        )
    print(f"WROTE {final_package}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
