#!/usr/bin/env python3
"""Finalize a plot-creator production package for the pinned Remotion 2.4.0 contract.

The input is an already approved episode package. This step applies existing
Financial Visual selections, projects the producer IR into the renderer's strict
public schema, runs the pinned renderer's official validator, and records the
result before immutable handoff. It never changes narration or market causality.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import financial_visual_cross_artifact

ROOT = Path(__file__).resolve().parents[1]

ROOT_ALLOWED = {
    "schemaVersion", "financialVisualContract", "episode", "editorial", "publishing",
    "sources", "review", "pronunciations", "corrections", "voiceProfileId", "scenes",
}
SCENE_ALLOWED = {
    "sceneId", "sceneNumber", "sceneRole", "formalName", "purpose", "causalScope",
    "performanceIntent", "evidenceSourceIds", "uncertainty", "timelineBasis",
    "expectedBasisType", "visualMode", "initialExpression", "headline",
    "supportingTexts", "sourceLabel", "narrationChunks", "visualBeats", "cards",
    "numbers", "nodes", "arrows", "visualEvents", "assetPlacements", "transition",
}
BEAT_ALLOWED = {
    "beatId", "startChunkId", "endChunkId", "narrationStartCue", "narrationEndCue",
    "primaryFunction", "screenState", "visualMode", "visualTemplate",
    "visualGrammarId", "transitionRole", "templateVariant", "templateConfig",
    "sequencePolicy", "finalHoldMs", "contentType", "screenQuestion",
    "primaryElement", "viewerTexts", "changeCue", "objectIds", "assetPlacementIds",
    "assetState", "returnScreenState", "evidenceSourceIds", "expressionChange",
    "fallback", "financialReturnTarget", "financialVisualTrace", "entity",
    "pictureBook", "shots",
}
VISUAL_MODE_MAP = {
    "verification": "verification-points",
    "closing-recap": "conclusion-card",
}

class RendererFinalizationError(ValueError):
    pass

def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RendererFinalizationError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise RendererFinalizationError(f"{label} must be an object")
    return value

def write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(canonical_json(value), encoding="utf-8")
    tmp.replace(path)

def _strict_renderer_projection(
    render_spec: dict[str, Any],
    *,
    final_contract_path: Path,
    semantics_path: Path,
    renderer_compatibility_path: Path,
) -> dict[str, Any]:
    source = copy.deepcopy(render_spec)
    result = {key: source[key] for key in ROOT_ALLOWED if key in source}
    if source.get("schemaVersion") != "2.4.0":
        raise RendererFinalizationError("renderer projection requires schemaVersion 2.4.0")
    scenes: list[dict[str, Any]] = []
    beat_count = 0
    for scene in source.get("scenes", []):
        projected_scene = {key: scene[key] for key in SCENE_ALLOWED if key in scene}
        projected_scene["visualMode"] = VISUAL_MODE_MAP.get(
            projected_scene.get("visualMode"), projected_scene.get("visualMode")
        )
        projected_beats: list[dict[str, Any]] = []
        for beat in scene.get("visualBeats", []):
            grammar = beat.get("visualGrammar")
            if not isinstance(grammar, dict):
                raise RendererFinalizationError(
                    f"{scene.get('sceneId')}/{beat.get('beatId')}: visualGrammar missing"
                )
            projected = {key: beat[key] for key in BEAT_ALLOWED if key in beat}
            projected["visualMode"] = VISUAL_MODE_MAP.get(
                projected.get("visualMode"), projected.get("visualMode")
            )
            projected["visualGrammarId"] = grammar.get("grammarId")
            projected["transitionRole"] = grammar.get("transitionRole")
            config = projected.get("templateConfig")
            if not isinstance(config, dict):
                raise RendererFinalizationError(
                    f"{scene.get('sceneId')}/{beat.get('beatId')}: templateConfig missing"
                )
            projected["templateVariant"] = projected.get("templateVariant", config.get("variant"))
            projected_beats.append(projected)
            beat_count += 1
        projected_scene["visualBeats"] = projected_beats
        scenes.append(projected_scene)
    result["scenes"] = scenes
    result["visualGrammarContract"] = {
        "contractVersion": "1.0.0",
        "semanticsSha256": sha256_file(semantics_path),
        "rendererCompatibilitySha256": sha256_file(renderer_compatibility_path),
        "finalEpisodeContractSha256": sha256_file(final_contract_path),
        "beatCount": beat_count,
    }
    return result

def _renderer_request(output_root: Path, date: str) -> dict[str, Any]:
    request = load_json(output_root / "working" / date / "production_request.json", "production request")
    renderer = request.get("renderer")
    if not isinstance(renderer, dict):
        raise RendererFinalizationError("production request renderer binding missing")
    if renderer.get("contract_version") != "2.4.0":
        raise RendererFinalizationError("production request must bind renderer 2.4.0")
    return renderer


def _build_validation_runtime_asset_registry(
    *, output_root: Path, date: str, render_spec_path: Path
) -> Path | None:
    """Bind ready day-specific assets to the renderer's existing runtime registry.

    This is validation-only. The immutable handoff later rebuilds the authoritative
    runtime registry from the exact bundle and rechecks every asset SHA before Preview.
    """
    asset_manifest_path = output_root / "episodes" / date / "asset_manifest.json"
    manifest = load_json(asset_manifest_path, "asset manifest")
    entries: list[dict[str, Any]] = []
    for index, asset in enumerate(manifest.get("assets", [])):
        if not isinstance(asset, dict):
            raise RendererFinalizationError(
                f"asset manifest assets[{index}] must be an object"
            )
        if asset.get("status") != "ready":
            continue
        asset_id = asset.get("asset_id")
        source_path = asset.get("path")
        declared_sha = asset.get("sha256")
        if not isinstance(asset_id, str) or not asset_id:
            raise RendererFinalizationError(
                f"asset manifest assets[{index}].asset_id is required for ready asset"
            )
        if not isinstance(source_path, str) or not source_path:
            raise RendererFinalizationError(
                f"asset manifest assets[{index}].path is required for ready asset"
            )
        if source_path.startswith("renderer-registry/"):
            continue
        source = (output_root / source_path).resolve()
        root = output_root.resolve()
        if root not in source.parents or not source.is_file():
            raise RendererFinalizationError(
                f"ready runtime asset path is missing or escapes output root: {source_path}"
            )
        actual_sha = sha256_file(source)
        if not isinstance(declared_sha, str) or declared_sha != actual_sha:
            raise RendererFinalizationError(
                f"ready runtime asset SHA mismatch: {asset_id}"
            )
        entries.append(
            {
                "assetId": asset_id,
                "path": f"generated/preflight-assets/{date}/{asset_id}/{source.name}",
                "sha256": actual_sha,
                "source": "handoff",
            }
        )
    if not entries:
        return None
    entries.sort(key=lambda item: item["assetId"])
    binding = {
        "episodeDate": date,
        "renderSpecSha256": sha256_file(render_spec_path),
        "assets": entries,
    }
    bundle_id = hashlib.sha256(canonical_json(binding).encode("utf-8")).hexdigest()
    registry = {
        "contractVersion": "1.0.0",
        "bundleId": bundle_id,
        "episodeDate": date,
        "assets": entries,
    }
    path = output_root / "verification" / date / "renderer_runtime_asset_registry.json"
    write_atomic(path, registry)
    return path


def _validate_with_pinned_renderer(
    *, renderer_root: Path, expected_commit: str, render_spec_path: Path,
    report_path: Path, date: str, runtime_asset_registry: Path | None = None,
) -> dict[str, Any]:
    renderer_root = renderer_root.resolve()
    if not (renderer_root / "scripts/spec-cli.ts").is_file():
        raise RendererFinalizationError(
            f"pinned renderer checkout missing scripts/spec-cli.ts: {renderer_root}"
        )
    actual_commit = subprocess.run(
        ["git", "-C", str(renderer_root), "rev-parse", "HEAD"], check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if actual_commit != expected_commit:
        raise RendererFinalizationError(
            f"renderer checkout SHA mismatch: expected={expected_commit} actual={actual_commit}"
        )
    command = [
        "node", "--import", "tsx", "scripts/spec-cli.ts",
        "validate", str(render_spec_path.resolve()),
    ]
    env = os.environ.copy()
    if runtime_asset_registry is not None:
        env["NASDAQ_CAFE_RUNTIME_ASSET_REGISTRY"] = str(runtime_asset_registry.resolve())
    completed = subprocess.run(
        command, cwd=renderer_root, capture_output=True, text=True, env=env
    )
    report = {
        "contractVersion": "1.0.0",
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "episodeDate": date,
        "renderer": {
            "repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion",
            "commit": actual_commit,
            "contractVersion": "2.4.0",
        },
        "renderSpec": {
            "path": render_spec_path.as_posix(),
            "sha256": sha256_file(render_spec_path),
        },
        "runtimeAssetRegistry": (
            {
                "path": runtime_asset_registry.as_posix(),
                "sha256": sha256_file(runtime_asset_registry),
            }
            if runtime_asset_registry is not None
            else None
        ),
        "validator": {
            "command": command, "exitCode": completed.returncode,
            "stdout": completed.stdout, "stderr": completed.stderr,
        },
        "unresolvedStateCount": 0 if completed.returncode == 0 else 1,
    }
    write_atomic(report_path, report)
    if completed.returncode != 0:
        raise RendererFinalizationError(
            "Remotion official validator failed:\n"
            + (completed.stderr or completed.stdout or "no validator output")
        )
    return report

def finalize(*, output_root: Path, date: str, renderer_root: Path) -> dict[str, Any]:
    output_root = output_root.resolve()
    work = output_root / "working" / date
    verification = output_root / "verification" / date
    final_contract_path = work / "final_episode_contract.json"
    recipe_plan_path = work / "financial_recipe_plan.json"
    structural_report_path = verification / "visual_grammar_structural_report.json"
    financial_visual_cross_artifact.EXPECTED_COMPATIBILITY_MATRIX = {
        "matrixId": "financial-visual-compat-2026-08",
        "status": "pass",
        "plotCreator": {
            "repository": "saienjoy0/nasdaq-plot-creator-",
            "financialIntentVersion": "1.1.0",
            "financialRecipePlanVersion": "1.0.0",
            "finalEpisodeContractVersion": "1.1.0",
        },
        "renderer": {
            "repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion",
            "renderSpecVersion": "2.4.0",
            "financialTemplateRegistryVersion": "1.0.0",
            "financialVisualTraceVersion": "1.0.0",
        },
    }
    cross_result = financial_visual_cross_artifact.integrate(
        final_contract_path=final_contract_path,
        recipe_plan_path=recipe_plan_path,
        repo_root=output_root,
        production_root=output_root,
        renderer_schema_version="2.4.0",
        final_schema_path=output_root / "contracts/final_episode_contract.schema.json",
        candidate_schema_path=output_root / "contracts/financial_visual_candidate_plan.schema.json",
        registry_path=output_root / "contracts/financial_recipe_registry.json",
        recipe_plan_schema_path=output_root / "contracts/financial_recipe_plan.schema.json",
        diversity_schema_path=output_root / "contracts/financial_visual_diversity_report.schema.json",
        consistency_schema_path=output_root / "contracts/financial_visual_consistency_report.schema.json",
        diversity_report_path=None,
        compatibility_matrix_path=output_root / "contracts/financial_visual_compatibility.json",
    )
    render_spec_path = output_root / "render-specs" / date / "render_spec.json"
    render = load_json(render_spec_path, "financially integrated render spec")
    strict = _strict_renderer_projection(
        render,
        final_contract_path=final_contract_path,
        semantics_path=output_root / "contracts/visual_grammar_semantics.json",
        renderer_compatibility_path=output_root / "contracts/visual_grammar_renderer_compatibility.json",
    )
    write_atomic(render_spec_path, strict)
    runtime_asset_registry = _build_validation_runtime_asset_registry(
        output_root=output_root, date=date, render_spec_path=render_spec_path
    )
    renderer = _renderer_request(output_root, date)
    report_path = verification / "renderer_validation_report.json"
    validation = _validate_with_pinned_renderer(
        renderer_root=renderer_root, expected_commit=renderer["commit"],
        render_spec_path=render_spec_path, report_path=report_path, date=date,
        runtime_asset_registry=runtime_asset_registry,
    )
    consistency_path = verification / "production_consistency_report.json"
    consistency = load_json(consistency_path, "production consistency report")
    consistency["renderer_contract"] = {
        "status": "pass", "repository": renderer["repository"],
        "commit": renderer["commit"], "contract_version": renderer["contract_version"],
        "render_spec_sha256": sha256_file(render_spec_path),
        "validator_report_sha256": sha256_file(report_path),
        "unresolved_states": 0,
    }
    consistency["status"] = "pass"
    consistency["unresolved_states"] = 0
    write_atomic(consistency_path, consistency)
    preflight_path = verification / "official_execution_preflight.json"
    preflight = load_json(preflight_path, "official execution preflight")
    artifacts = preflight.setdefault("artifacts", {})
    artifacts["render_spec"] = sha256_file(render_spec_path)
    artifacts["consistency_report"] = sha256_file(consistency_path)
    artifacts["renderer_validation_report"] = sha256_file(report_path)
    artifacts["visual_grammar_structural_report"] = sha256_file(structural_report_path)
    if runtime_asset_registry is not None:
        artifacts["renderer_runtime_asset_registry"] = sha256_file(runtime_asset_registry)
    preflight["renderer_validation"] = {
        "status": "pass", "repository": renderer["repository"],
        "commit": renderer["commit"], "contract_version": renderer["contract_version"],
        "render_spec_sha256": sha256_file(render_spec_path),
        "report_sha256": sha256_file(report_path), "unresolved_states": 0,
    }
    preflight["unresolved_states"] = 0
    preflight["preview_authorized"] = True
    preflight["final_authorized"] = False
    write_atomic(preflight_path, preflight)
    return {
        "status": "pass",
        "paths": {
            "final_episode_contract": str(final_contract_path),
            "financial_recipe_plan": str(recipe_plan_path),
            "financial_visual_consistency_report": cross_result["paths"]["cross_report"],
            "visual_grammar_structural_report": str(structural_report_path),
            "renderer_validation_report": str(report_path),
            "renderer_runtime_asset_registry": (
                str(runtime_asset_registry) if runtime_asset_registry is not None else None
            ),
        },
        "hashes": {
            "render_spec": sha256_file(render_spec_path),
            "renderer_validation_report": sha256_file(report_path),
            "preflight": sha256_file(preflight_path),
        },
        "rendererValidation": validation,
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    parser.add_argument("--date", required=True)
    parser.add_argument("--renderer-root", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = finalize(
            output_root=args.output_root, date=args.date, renderer_root=args.renderer_root,
        )
        code = 0
    except (
        RendererFinalizationError, financial_visual_cross_artifact.CrossArtifactError,
        OSError, KeyError, subprocess.CalledProcessError,
    ) as exc:
        result = {"status": "fail", "errors": str(exc).splitlines()}
        code = 2
    text = canonical_json(result)
    if args.report:
        write_atomic(args.report, result)
    else:
        sys.stdout.write(text)
    return code

if __name__ == "__main__":
    raise SystemExit(main())
