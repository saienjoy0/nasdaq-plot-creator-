#!/usr/bin/env python3
"""Materialize explicit renderer-side source contracts from an approved daily episode.

This module performs no editorial selection. It projects already-approved
Visual Grammar declarations and explicit financial bindings into deterministic
sidecars consumed by the existing Final Episode Contract and recipe compiler.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

FINANCIAL_BEGIN = "<!--BEGIN_FINANCIAL_VISUAL_ANNEX-->"
FINANCIAL_END = "<!--END_FINANCIAL_VISUAL_ANNEX-->"
VISUAL_BEGIN = "<!--BEGIN_VISUAL_GRAMMAR_ANNEX-->"
VISUAL_END = "<!--END_VISUAL_GRAMMAR_ANNEX-->"
BEAT_HEADING_RE = re.compile(r"(?m)^- \*\*(scene-0[1-9]-beat-[0-9]{3})\*\*$")

SOURCE_TYPE_MAP = {
    "official": "official",
    "company": "company",
    "company-ir": "company",
    "major-media": "major-media",
    "analyst": "analyst",
    "market-data": "market-data",
    "other": "other",
}
VISUAL_MODE_MAP = {
    "verification": "verification-points",
    "closing-recap": "conclusion-card",
}
FINANCIAL_TEMPLATES = {
    "market-pulse-grid", "earnings-surprise", "dual-asset-split",
    "macro-pressure", "source-receipt",
}

class RendererSourceError(ValueError):
    pass

def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RendererSourceError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise RendererSourceError(f"{label} must be an object")
    return value

def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)

def _canonical_beat_maps(render: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    source_to_canonical: dict[str, str] = {}
    canonical_to_source: dict[str, str] = {}
    for scene_index, scene in enumerate(render.get("scenes", []), start=1):
        expected_scene = f"scene-{scene_index:02d}"
        if scene.get("sceneId") != expected_scene:
            raise RendererSourceError(
                f"scene order mismatch: expected {expected_scene}, got {scene.get('sceneId')}"
            )
        for beat_index, beat in enumerate(scene.get("visualBeats", []), start=1):
            source_id = beat.get("beatId")
            if not isinstance(source_id, str) or not source_id:
                raise RendererSourceError(f"{expected_scene} Beat {beat_index} lacks beatId")
            canonical = f"vb-{scene_index:02d}-{beat_index:02d}"
            if source_id in source_to_canonical or canonical in canonical_to_source:
                raise RendererSourceError("duplicate Visual Beat identity")
            source_to_canonical[source_id] = canonical
            canonical_to_source[canonical] = source_id
    return source_to_canonical, canonical_to_source

def normalize_render_base(render: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Project producer JSON into a renderer-oriented intermediate contract."""
    result = copy.deepcopy(render)
    source_to_canonical, _ = _canonical_beat_maps(result)
    for key in (
        "visualGrammarContractVersion",
        "expectedConfirmed",
        "tts",
        "imageSelection",
    ):
        result.pop(key, None)

    normalized_sources: list[dict[str, Any]] = []
    accepted_source_ids: set[str] = set()
    for source in result.get("sources", []):
        source_id = source.get("sourceId")
        source_type = source.get("sourceType")
        if not isinstance(source_id, str):
            continue
        if source_type == "historical-memory" or not source_id.startswith("source-"):
            continue
        mapped = SOURCE_TYPE_MAP.get(source_type)
        if mapped is None:
            raise RendererSourceError(
                f"unsupported renderer sourceType {source_type!r} for {source_id}"
            )
        item = copy.deepcopy(source)
        item["sourceType"] = mapped
        if not isinstance(item.get("narrationAttribution"), str) or not item["narrationAttribution"].strip():
            item["narrationAttribution"] = item.get("publisher") or "出典"
        normalized_sources.append(item)
        accepted_source_ids.add(source_id)
    if not normalized_sources:
        raise RendererSourceError("renderer source registry would be empty")
    result["sources"] = normalized_sources

    for scene in result.get("scenes", []):
        scene["visualMode"] = VISUAL_MODE_MAP.get(scene.get("visualMode"), scene.get("visualMode"))
        scene["evidenceSourceIds"] = [
            value for value in scene.get("evidenceSourceIds", []) if value in accepted_source_ids
        ]
        for beat in scene.get("visualBeats", []):
            source_id = beat["beatId"]
            declared = beat.get("visualBeatId")
            if declared is not None and declared != source_id:
                raise RendererSourceError(f"{source_id}: visualBeatId disagrees with beatId")
            canonical = source_to_canonical[source_id]
            beat["beatId"] = canonical
            beat["visualBeatId"] = canonical
            beat["visualMode"] = VISUAL_MODE_MAP.get(beat.get("visualMode"), beat.get("visualMode"))
            beat["evidenceSourceIds"] = [
                value for value in beat.get("evidenceSourceIds", []) if value in accepted_source_ids
            ]
            config = beat.get("templateConfig")
            if not isinstance(config, dict):
                raise RendererSourceError(f"{source_id}: templateConfig is required")
            beat["templateVariant"] = config.get("variant", "default")
            grammar = beat.get("visualGrammar")
            if not isinstance(grammar, dict):
                raise RendererSourceError(f"{source_id}: approved visualGrammar is missing")
            if grammar.get("contractVersion") != "1.0.0":
                raise RendererSourceError(f"{source_id}: Visual Grammar version mismatch")
    result["schemaVersion"] = "2.4.0"
    return result, source_to_canonical

def _binding_map(bindings: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if bindings.get("contractVersion") != "1.0.0":
        raise RendererSourceError("financial bindings contractVersion must be 1.0.0")
    rows = bindings.get("bindings")
    if not isinstance(rows, list):
        raise RendererSourceError("financial bindings.bindings must be an array")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise RendererSourceError("financial binding must be an object")
        source_beat_id = row.get("sourceBeatId")
        if not isinstance(source_beat_id, str) or not source_beat_id:
            raise RendererSourceError("financial binding sourceBeatId is required")
        if source_beat_id in result:
            raise RendererSourceError(f"duplicate financial binding: {source_beat_id}")
        result[source_beat_id] = row
    return result

def _visual_grammar_sidecar(*, date: str, render: dict[str, Any], expected_confirmed: bool) -> dict[str, Any]:
    scenes = []
    for scene in render["scenes"]:
        beats = []
        for beat in scene["visualBeats"]:
            grammar = copy.deepcopy(beat["visualGrammar"])
            target = grammar.get("returnTargetBeatId")
            if target is not None:
                raise RendererSourceError(
                    f"{beat['beatId']}: returnTargetBeatId must already be canonical or null"
                )
            beats.append({"visualBeatId": beat["visualBeatId"], "visualGrammar": grammar})
        scenes.append({"sceneId": scene["sceneId"], "visualBeats": beats})
    return {
        "episodeDate": date,
        "visualGrammarContractVersion": "1.0.0",
        "expectedConfirmed": expected_confirmed,
        "scene5CausalExceptionReason": None,
        "scenes": scenes,
    }

def _find_render_beat(render: dict[str, Any], canonical_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    for scene in render["scenes"]:
        for beat in scene["visualBeats"]:
            if beat["beatId"] == canonical_id:
                return scene, beat
    raise RendererSourceError(f"target Beat not found: {canonical_id}")

def _metric_to_number(metric: dict[str, Any]) -> dict[str, Any]:
    value = metric.get("numericValue")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise RendererSourceError(f"{metric.get('metricId')}: numeric renderer object requires finite numericValue")
    return {
        "numberId": metric["metricId"],
        "label": metric["label"],
        "value": metric["valueText"],
        "numericValue": value,
        "precision": metric.get("precision", 2),
        "unit": metric.get("unit") or "",
        "comparison": None,
        "tone": metric.get("tone", "neutral"),
    }

def _metric_to_card(metric: dict[str, Any]) -> dict[str, Any]:
    return {
        "cardId": metric["metricId"],
        "role": None,
        "title": metric["label"],
        "lines": [{
            "label": "確認",
            "value": metric["valueText"],
            "tone": metric.get("tone", "neutral"),
        }],
    }

def _project_metric_objects(scene: dict[str, Any], metrics_raw: list[dict[str, Any]], source_beat_id: str) -> None:
    scene_numbers = scene.setdefault("numbers", [])
    scene_cards = scene.setdefault("cards", [])
    existing_number_ids = {item.get("numberId") for item in scene_numbers}
    existing_card_ids = {item.get("cardId") for item in scene_cards}
    if existing_number_ids & existing_card_ids:
        raise RendererSourceError(f"{source_beat_id}: renderer object IDs collide across numbers/cards")
    for metric in metrics_raw:
        metric_id = metric["metricId"]
        if metric_id in existing_number_ids or metric_id in existing_card_ids:
            continue
        numeric_value = metric.get("numericValue")
        if numeric_value is None:
            scene_cards.append(_metric_to_card(metric))
            existing_card_ids.add(metric_id)
        elif isinstance(numeric_value, bool) or not isinstance(numeric_value, (int, float)) or not math.isfinite(numeric_value):
            raise RendererSourceError(f"{source_beat_id}/{metric_id}: numericValue must be finite number or null")
        else:
            scene_numbers.append(_metric_to_number(metric))
            existing_number_ids.add(metric_id)

def _plan(*, plan_id: str, intent_id: str, path: str, recipe_id: str, template_id: str,
          variant: str, scene_id: str, beat_id: str, screen_state: str,
          metric_ids: list[str], causal_step_ids: list[str], display_order: list[str],
          comparison_basis: str, highlight_ids: list[str], source_ids: list[str]) -> dict[str, Any]:
    suffix_headline = "headline" if path == "preferred" else "fallbackHeadline"
    suffix_question = "screenQuestion" if path == "preferred" else "fallbackQuestion"
    prefix = f"episode://{scene_id}/{beat_id}"
    return {
        "planVersion": "1.0.0", "planId": plan_id, "intentId": intent_id,
        "path": path, "recipeId": recipe_id, "visualTemplateId": template_id,
        "templateVariant": variant, "sceneId": scene_id, "visualBeatId": beat_id,
        "screenState": screen_state, "metricIds": metric_ids,
        "causalStepIds": causal_step_ids, "displayOrder": display_order,
        "comparisonBasis": comparison_basis, "highlightObjectIds": highlight_ids,
        "headlineRef": f"{prefix}/{suffix_headline}",
        "screenQuestionRef": f"{prefix}/{suffix_question}",
        "startCueRef": f"{prefix}/startCue", "endCueRef": f"{prefix}/endCue",
        "returnTargetRef": f"{prefix}/returnTarget", "sourceIds": source_ids,
    }

def _financial_contract(*, render: dict[str, Any], bindings: dict[str, Any],
                        source_to_canonical: dict[str, str]) -> dict[str, Any]:
    binding_by_source = _binding_map(bindings)
    financial_source_beats = {
        source_id
        for source_id, canonical in source_to_canonical.items()
        for _, beat in [_find_render_beat(render, canonical)]
        if beat.get("visualTemplate") in FINANCIAL_TEMPLATES
    }
    if set(binding_by_source) != financial_source_beats:
        raise RendererSourceError(
            "financial binding set must exactly match selected financial templates: "
            f"missing={sorted(financial_source_beats-set(binding_by_source))} "
            f"extra={sorted(set(binding_by_source)-financial_source_beats)}"
        )
    intents: list[dict[str, Any]] = []
    plans: list[dict[str, Any]] = []
    all_source_ids = {source["sourceId"] for source in render["sources"]}
    for source_beat_id in sorted(binding_by_source):
        row = binding_by_source[source_beat_id]
        canonical = source_to_canonical[source_beat_id]
        scene, beat = _find_render_beat(render, canonical)
        if row.get("sceneId") != scene["sceneId"]:
            raise RendererSourceError(f"{source_beat_id}: binding sceneId mismatch")
        if row.get("selectedVisualTemplateId") != beat.get("visualTemplate"):
            raise RendererSourceError(f"{source_beat_id}: binding/template mismatch")
        source_ids = list(row.get("sourceIds", []))
        if not source_ids or not set(source_ids).issubset(all_source_ids):
            raise RendererSourceError(f"{source_beat_id}: binding sourceIds invalid")
        metrics_raw = copy.deepcopy(row.get("metrics", []))
        causal_steps = copy.deepcopy(row.get("causalSteps", []))
        if not metrics_raw and not causal_steps:
            raise RendererSourceError(f"{source_beat_id}: metrics or causalSteps required")
        metric_contract_keys = {
            "metricId", "label", "role", "valueText", "numericValue", "unit",
            "currency", "period", "entityId", "sessionDate", "sourceIds",
        }
        metrics = [
            {key: value for key, value in metric.items() if key in metric_contract_keys}
            for metric in metrics_raw
        ]
        metric_ids = [metric["metricId"] for metric in metrics]
        if len(metric_ids) != len(set(metric_ids)):
            raise RendererSourceError(f"{source_beat_id}: duplicate metricId")
        _project_metric_objects(scene, metrics_raw, source_beat_id)
        intent_id = row["intentId"]
        preferred = row["preferred"]
        fallback = row["fallback"]
        preferred_id = f"fvp-{intent_id.removeprefix('fvi-')}-preferred"
        fallback_id = f"fvp-{intent_id.removeprefix('fvi-')}-fallback"
        return_target_source = row.get("returnTargetSourceBeatId")
        if not isinstance(return_target_source, str) or return_target_source not in source_to_canonical:
            raise RendererSourceError(f"{source_beat_id}: returnTargetSourceBeatId invalid")
        beat["_financialReturnTarget"] = source_to_canonical[return_target_source]
        intents.append({
            "intentContractVersion": "1.1.0", "intentId": intent_id,
            "kind": row["kind"],
            "target": {"sceneId": scene["sceneId"], "visualBeatId": canonical},
            "metrics": metrics, "causalSteps": causal_steps, "sourceIds": source_ids,
            "dataPrecision": row["dataPrecision"], "chartPolicy": row["chartPolicy"],
            "preferredPlanId": preferred_id, "fallbackPlanId": fallback_id,
            "status": "approved", "editorialNote": row.get("editorialNote"),
            "selectionState": {
                "compilerSelection": "not-run", "selectedPlanId": None,
                "selectedRecipeId": None, "selectedVisualTemplateId": None,
                "compilerReasonCodes": [], "fallbackDiversityRecheck": "not-run",
            },
        })
        for path, config, plan_id in (
            ("preferred", preferred, preferred_id),
            ("fallback", fallback, fallback_id),
        ):
            plans.append(_plan(
                plan_id=plan_id, intent_id=intent_id, path=path,
                recipe_id=config["recipeId"], template_id=config["visualTemplateId"],
                variant=config["templateVariant"], scene_id=scene["sceneId"],
                beat_id=canonical, screen_state=config["screenState"],
                metric_ids=list(config.get("metricIds", metric_ids)),
                causal_step_ids=list(config.get("causalStepIds", [])),
                display_order=list(config["displayOrder"]),
                comparison_basis=config["comparisonBasis"],
                highlight_ids=list(config.get("highlightObjectIds", [])),
                source_ids=source_ids,
            ))
    return {"annexVersion": "1.0.0", "intents": intents, "candidatePlans": plans}

def _contract_scenes(render: dict[str, Any]) -> list[dict[str, Any]]:
    ordered: list[tuple[str, str]] = []
    for scene in render["scenes"]:
        for beat in scene["visualBeats"]:
            ordered.append((scene["sceneId"], beat["beatId"]))
    next_by_id = {
        beat_id: (ordered[index + 1][1] if index + 1 < len(ordered) else "episode-end")
        for index, (_, beat_id) in enumerate(ordered)
    }
    scenes = []
    for scene in render["scenes"]:
        beats = []
        for beat in scene["visualBeats"]:
            beats.append({
                "visualBeatId": beat["beatId"], "headline": beat["primaryElement"],
                "screenQuestion": beat["screenQuestion"],
                "startCue": beat["narrationStartCue"], "endCue": beat["narrationEndCue"],
                "returnTarget": beat.pop("_financialReturnTarget", next_by_id[beat["beatId"]]),
                "fallbackHeadline": beat["primaryElement"],
                "fallbackQuestion": beat["screenQuestion"],
                "visualGrammar": copy.deepcopy(beat["visualGrammar"]),
            })
        scenes.append({"sceneId": scene["sceneId"], "visualBeats": beats})
    return scenes

def _insert_markers(public_text: str, source_to_canonical: dict[str, str]) -> str:
    seen: set[str] = set()
    def repl(match: re.Match[str]) -> str:
        source_id = match.group(1)
        canonical = source_to_canonical.get(source_id)
        if canonical is None:
            raise RendererSourceError(f"public package contains undeclared Beat: {source_id}")
        seen.add(source_id)
        scene_id = source_id[:8]
        return f"<!--VISUAL_BEAT:{scene_id}:{canonical}-->\n{match.group(0)}"
    output = BEAT_HEADING_RE.sub(repl, public_text)
    missing = set(source_to_canonical) - seen
    if missing:
        raise RendererSourceError(f"public package missing Beat headings: {sorted(missing)}")
    return output.rstrip()

def materialize(*, root: Path, date: str, render_path: Path,
                public_package_path: Path, bindings_path: Path) -> dict[str, Any]:
    root = root.resolve()
    raw_render = load_json(render_path, "producer render spec")
    bindings = load_json(bindings_path, "financial bindings")
    if bindings.get("episodeDate") != date:
        raise RendererSourceError("financial bindings episodeDate mismatch")
    expected_confirmed = raw_render.get("expectedConfirmed")
    if not isinstance(expected_confirmed, bool):
        raise RendererSourceError("producer expectedConfirmed must be explicit")
    render, source_to_canonical = normalize_render_base(raw_render)
    financial_visuals = _financial_contract(
        render=render, bindings=bindings, source_to_canonical=source_to_canonical
    )
    sidecar = _visual_grammar_sidecar(
        date=date, render=render, expected_confirmed=expected_confirmed
    )
    work = root / "working" / date
    episodes = root / "episodes" / date
    sidecar_path = work / "visual_grammar_sidecar.json"
    contract_package_path = episodes / f"episode_package_contract_{date}.md"
    final_contract_path = work / "final_episode_contract.json"
    recipe_plan_path = work / "financial_recipe_plan.json"
    intermediate_render_path = work / "render_spec_intermediate.json"
    write_atomic(sidecar_path, canonical_json(sidecar))
    public = public_package_path.read_text(encoding="utf-8")
    marked = _insert_markers(public, source_to_canonical)
    contract_package = (
        marked + "\n\n" + FINANCIAL_BEGIN + "\n```json\n"
        + canonical_json(financial_visuals).rstrip() + "\n```\n" + FINANCIAL_END
        + "\n\n" + VISUAL_BEGIN + "\n```json\n"
        + canonical_json(sidecar).rstrip() + "\n```\n" + VISUAL_END + "\n"
    )
    write_atomic(contract_package_path, contract_package)
    scenes = _contract_scenes(render)
    final_contract = {
        "contractVersion": "1.1.0", "episodeDate": date,
        "episodePackage": {
            "path": contract_package_path.relative_to(root).as_posix(),
            "sha256": sha256_file(contract_package_path),
        },
        "visualGrammarSidecar": {
            "path": sidecar_path.relative_to(root).as_posix(),
            "sha256": sha256_file(sidecar_path),
        },
        "visualGrammarContractVersion": "1.0.0",
        "expectedConfirmed": expected_confirmed,
        "scene5CausalExceptionReason": None,
        "review": {
            "verdict": raw_render["review"]["verdict"],
            "postInquisitionFinal": True,
            "approvedForProduction": raw_render["review"].get("approvedForCodex") is True,
        },
        "sourceRegistry": [
            {"sourceId": source["sourceId"], "title": source["title"],
             "publisher": source["publisher"], "sourceType": source["sourceType"]}
            for source in render["sources"]
        ],
        "scenes": scenes, "financialVisuals": financial_visuals,
    }
    write_atomic(final_contract_path, canonical_json(final_contract))
    write_atomic(intermediate_render_path, canonical_json(render))
    subprocess.run(
        [sys.executable, "scripts/final_episode_contract.py", str(final_contract_path),
         "--repo-root", str(root)], cwd=root, check=True
    )
    structural_report_path = root / "verification" / date / "visual_grammar_structural_report.json"
    subprocess.run(
        [sys.executable, "scripts/visual_grammar_contract.py", str(sidecar_path),
         "--output", str(structural_report_path)], cwd=root, check=True
    )
    subprocess.run(
        [sys.executable, "scripts/financial_recipe_compiler.py", "compile",
         str(final_contract_path), "--repo-root", str(root), "--output",
         str(recipe_plan_path)], cwd=root, check=True
    )
    return {
        "render": render, "contract_package_path": contract_package_path,
        "sidecar_path": sidecar_path, "final_contract_path": final_contract_path,
        "recipe_plan_path": recipe_plan_path,
        "intermediate_render_path": intermediate_render_path,
        "structural_report_path": structural_report_path,
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--render-spec", type=Path)
    parser.add_argument("--public-package", type=Path)
    parser.add_argument("--financial-bindings", type=Path)
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    date = args.date
    try:
        result = materialize(
            root=root, date=date,
            render_path=args.render_spec or root / "render-specs" / date / "render_spec.json",
            public_package_path=args.public_package or root / "episodes" / date / f"episode_package_public_{date}.md",
            bindings_path=args.financial_bindings or root / "working" / date / "financial_visual_bindings.json",
        )
    except (RendererSourceError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "FAIL", "errors": [str(exc)]}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "PASS",
        "contractPackage": str(result["contract_package_path"]),
        "finalEpisodeContract": str(result["final_contract_path"]),
        "financialRecipePlan": str(result["recipe_plan_path"]),
        "visualGrammarSidecar": str(result["sidecar_path"]),
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
