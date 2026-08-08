#!/usr/bin/env python3
"""Bind authored Story Engine artifacts to the validated daily dossier and validate them.

The Author/Critic judgment is completed before GitHub Actions. This materializer is
mechanical: it binds lineage fields, copies the pre-authored review unchanged, verifies
the sealed Critic request/receipt, and emits a single Story Engine acceptance artifact.
A repository-provenance receipt may validate the artifacts but is not production-eligible
until a real orchestrator produces an `orchestrator_signed` receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return value


def dump(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(root: Path, path: Path) -> dict[str, str]:
    return {"path": path.resolve().relative_to(root.resolve()).as_posix(), "sha256": sha(path)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--repo-root", type=Path, default=ROOT)
    args = ap.parse_args()
    root = args.repo_root.resolve()
    date = args.date
    work = root / "working" / date / "story-engine"
    templates = work / "templates"
    dossier = root / "research" / date / f"causal_research_dossier_{date}.json"
    plan_template = templates / "story_plan.template.json"
    script_template = templates / "story_script.template.json"
    review_template = templates / "creative_review.template.json"
    critic_request = templates / "critic_request.json"
    critic_receipt = templates / "critic_execution_receipt.json"
    plan_path = work / "story_plan.json"
    script_path = work / "story_script.json"
    review_path = work / "creative_review.json"
    acceptance_path = work / "story_engine_acceptance.json"

    required_inputs = (
        dossier,
        plan_template,
        script_template,
        review_template,
        critic_request,
        critic_receipt,
    )
    for path in required_inputs:
        if not path.is_file() or path.stat().st_size == 0:
            raise SystemExit(f"missing Story Engine input: {path.relative_to(root)}")

    receipt_validator = load_module(
        "critic_execution_receipt_validator",
        root / "scripts/story-engine/validate_critic_execution_receipt.py",
    )
    receipt_result = receipt_validator.validate(
        critic_request,
        critic_receipt,
        repo_root=root,
        request_schema=root / "skills/nasdaq-cafe-story-engine/contracts/critic_request.schema.json",
        receipt_schema=root / "skills/nasdaq-cafe-story-engine/contracts/critic_execution_receipt.schema.json",
    )
    if receipt_result["status"] != "pass":
        messages = [item.get("message", "critic receipt failed") for item in receipt_result.get("errors", [])]
        raise SystemExit("Independent Critic execution receipt failed: " + "; ".join(messages))

    plan = load(plan_template)
    plan["causal_dossier"] = ref(root, dossier)
    dump(plan_path, plan)

    plan_validator = load_module(
        "story_plan_validator",
        root / "skills/nasdaq-cafe-story-plan/validators/validate_story_plan.py",
    )
    plan_result = plan_validator.validate_story_plan(
        plan_path,
        dossier,
        repo_root=root,
        schema_path=root / "skills/nasdaq-cafe-story-plan/contracts/story_plan.schema.json",
    )
    if not plan_result.ok:
        raise SystemExit("Story Plan validation failed: " + "; ".join(plan_result.errors))

    script = load(script_template)
    script["story_plan"] = ref(root, plan_path)
    script["causal_dossier"] = ref(root, dossier)
    dump(script_path, script)

    # The Critic judgment is authored before Actions. Copy its JSON content unchanged.
    review = load(review_template)
    dump(review_path, review)

    bundle_validator = load_module(
        "story_engine_bundle_validator",
        root / "scripts/story-engine/validate_story_engine_bundle.py",
    )
    bundle_result = bundle_validator.validate_bundle(
        script_path,
        plan_path,
        dossier,
        story_contracts_dir=root / "skills/nasdaq-cafe-story-authoring/contracts",
        critic_contracts_dir=root / "skills/nasdaq-cafe-entertainment-critic/contracts",
        repo_root=root,
        review_path=review_path,
    )
    if not bundle_result.ok:
        raise SystemExit("Story Engine bundle validation failed: " + "; ".join(bundle_result.errors))
    if review.get("verdict") != "pass" or review.get("total_score", 0) < 25:
        raise SystemExit("final independent critic review must be PASS with score >=25")

    receipt = load(critic_receipt)
    production_eligible = receipt.get("provenance", {}).get("attestation_strength") == "orchestrator_signed"
    acceptance = {
        "contract_version": "1.1.0",
        "episode_date": date,
        "status": "pass",
        "production_eligible": production_eligible,
        "artifacts": {
            "causal_dossier": ref(root, dossier),
            "story_plan": ref(root, plan_path),
            "story_script": ref(root, script_path),
            "creative_review": ref(root, review_path),
            "critic_request": ref(root, critic_request),
            "critic_execution_receipt": ref(root, critic_receipt),
        },
        "validation": {
            "story_plan": "pass",
            "story_script": "pass",
            "independent_critic": "pass",
            "independent_critic_receipt": "pass",
            "causality_guard": "pass",
            "scene_order_guard": "pass",
            "scene_09_guard": "pass",
        },
        "critic": {
            "round": review["round"],
            "score": review["total_score"],
            "verdict": review["verdict"],
            "author_invocation_id": receipt["author_invocation_id"],
            "critic_invocation_id": receipt["critic_invocation_id"],
            "isolation_mode": receipt["isolation_mode"],
            "attestation_strength": receipt.get("provenance", {}).get("attestation_strength"),
            "execution_receipt": ref(root, critic_receipt),
        },
    }
    dump(acceptance_path, acceptance)

    acceptance_validator = load_module(
        "story_engine_acceptance_v1_1",
        root / "scripts/story-engine/validate_story_engine_acceptance_v1_1.py",
    )
    acceptance_result = acceptance_validator.validate_acceptance(
        acceptance_path,
        repo_root=root,
        require_production=False,
    )
    if acceptance_result["status"] != "pass":
        messages = [item.get("message", "acceptance failed") for item in acceptance_result.get("errors", [])]
        raise SystemExit("Story Engine v1.1 artifact acceptance failed: " + "; ".join(messages))

    print(json.dumps({
        "status": "pass",
        "production_eligible": production_eligible,
        "critic_isolation_mode": receipt["isolation_mode"],
        "critic_attestation_strength": receipt.get("provenance", {}).get("attestation_strength"),
        "paths": {
            "story_plan": str(plan_path),
            "story_script": str(script_path),
            "creative_review": str(review_path),
            "critic_request": str(critic_request),
            "critic_execution_receipt": str(critic_receipt),
            "acceptance": str(acceptance_path),
        },
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
