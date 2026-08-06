#!/usr/bin/env python3
"""Create the renderer-facing Financial Final Episode Contract 1.0 projection.

The full Visual Grammar Final Episode Contract 1.1 remains the source of truth.
This file contains the same approved financial annex and public Beat references,
with Visual Grammar-only fields removed for the pinned renderer's Financial
Visual contract. Both files retain independent real SHA-256 identities.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import financial_final_episode_contract_1_0 as financial_contract_v1
import financial_recipe_compiler

class ProjectionError(ValueError):
    pass

def canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

def write_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(canonical_json(value), encoding="utf-8")
    tmp.replace(path)

def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProjectionError(f"JSON root must be an object: {path}")
    return value

def project(full: dict) -> dict:
    if full.get("contractVersion") != "1.1.0":
        raise ProjectionError("full Final Episode Contract must be 1.1.0")
    scenes = []
    for scene in full["scenes"]:
        beats = []
        for beat in scene["visualBeats"]:
            beats.append({
                "visualBeatId": beat["visualBeatId"],
                "headline": beat["headline"],
                "screenQuestion": beat["screenQuestion"],
                "startCue": beat["startCue"],
                "endCue": beat["endCue"],
                "returnTarget": beat["returnTarget"],
                "fallbackHeadline": beat["fallbackHeadline"],
                "fallbackQuestion": beat["fallbackQuestion"],
            })
        scenes.append({"sceneId": scene["sceneId"], "visualBeats": beats})
    return {
        "contractVersion": "1.0.0",
        "episodeDate": full["episodeDate"],
        "episodePackage": copy.deepcopy(full["episodePackage"]),
        "review": copy.deepcopy(full["review"]),
        "sourceRegistry": copy.deepcopy(full["sourceRegistry"]),
        "scenes": scenes,
        "financialVisuals": copy.deepcopy(full["financialVisuals"]),
    }

def materialize(*, root: Path, date: str) -> dict:
    root = root.resolve()
    work = root / "working" / date
    full_path = work / "final_episode_contract.json"
    financial_path = work / "financial_final_episode_contract.json"
    recipe_path = work / "financial_recipe_plan.json"
    full = load_json(full_path)
    financial = project(full)
    write_atomic(financial_path, financial)
    validation = financial_contract_v1.validate_contract(
        financial_path,
        root,
        root / "contracts/financial_visual_candidate_plan.schema.json",
    )
    original = financial_recipe_compiler.final_contract_module.validate_contract
    def validate_adapter(contract_path, repo_root, final_schema_path, candidate_schema_path, *args):
        return financial_contract_v1.validate_contract(
            contract_path, repo_root, candidate_schema_path
        )
    financial_recipe_compiler.final_contract_module.validate_contract = validate_adapter
    try:
        plan = financial_recipe_compiler.compile_recipe_plan(
            financial_path,
            root,
            root / "contracts/financial_recipe_registry.json",
            root / "contracts/financial_recipe_plan.schema.json",
            root / "contracts/final_episode_contract.schema.json",
            root / "contracts/financial_visual_candidate_plan.schema.json",
        )
    finally:
        financial_recipe_compiler.final_contract_module.validate_contract = original
    financial_recipe_compiler.write_json_atomic(recipe_path, plan)
    return {
        "status": "PASS",
        "fullFinalEpisodeContract": str(full_path),
        "financialFinalEpisodeContract": str(financial_path),
        "financialRecipePlan": str(recipe_path),
        "validation": validation,
    }
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        result = materialize(root=args.repo_root, date=args.date)
        code = 0
    except (
        OSError, KeyError, json.JSONDecodeError, ProjectionError,
        financial_contract_v1.ContractError, financial_recipe_compiler.CompileError,
    ) as exc:
        result = {"status": "FAIL", "errors": str(exc).splitlines()}
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code
if __name__ == "__main__":
    raise SystemExit(main())
