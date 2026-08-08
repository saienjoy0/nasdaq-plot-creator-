#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Item:
    code: str
    message: str
    path: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(root: Path, ref: dict[str, Any], label: str, errors: list[Item]) -> Path | None:
    raw = Path(str(ref.get("path", "")))
    if raw.is_absolute():
        errors.append(Item("E_PATH", "absolute path forbidden", label))
        return None
    root = root.resolve()
    path = (root / raw).resolve()
    if path != root and root not in path.parents:
        errors.append(Item("E_PATH", "path escapes repository root", label))
        return None
    if not path.is_file():
        errors.append(Item("E_PATH", f"missing file: {raw}", label))
        return None
    if sha256(path) != ref.get("sha256"):
        errors.append(Item("E_HASH", "SHA-256 mismatch", label))
    return path


def normalize_plan(runtime: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(runtime)
    value["causal_dossier"] = copy.deepcopy(template.get("causal_dossier"))
    return value


def normalize_script(runtime: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(runtime)
    value["story_plan"] = copy.deepcopy(template.get("story_plan"))
    value["causal_dossier"] = copy.deepcopy(template.get("causal_dossier"))
    return value


def validate_acceptance(path: Path, *, repo_root: Path, require_production: bool = False) -> dict[str, Any]:
    root = repo_root.resolve()
    errors: list[Item] = []
    warnings: list[Item] = []
    try:
        acceptance = load(path)
    except Exception as exc:
        return {"status": "fail", "errors": [Item("E_JSON", str(exc), str(path)).as_dict()], "warnings": []}

    if acceptance.get("contract_version") != "1.1.0":
        errors.append(Item("E_CONTRACT_VERSION", "Story Engine acceptance must be contract_version 1.1.0", "contract_version"))
    date = str(acceptance.get("episode_date", ""))
    if acceptance.get("status") != "pass":
        errors.append(Item("E_STATUS", "Story Engine artifact acceptance must be PASS", "status"))
    production_eligible = acceptance.get("production_eligible") is True

    artifacts = acceptance.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append(Item("E_ARTIFACTS", "artifacts must be an object", "artifacts"))
        return {"status": "fail", "errors": [x.as_dict() for x in errors], "warnings": []}

    required = {"causal_dossier", "story_plan", "story_script", "creative_review", "critic_request", "critic_execution_receipt"}
    missing = required - set(artifacts)
    if missing:
        errors.append(Item("E_ARTIFACTS", f"acceptance missing artifacts: {sorted(missing)}", "artifacts"))

    resolved: dict[str, Path] = {}
    for name in sorted(required & set(artifacts)):
        ref = artifacts.get(name)
        if not isinstance(ref, dict):
            errors.append(Item("E_ARTIFACTS", f"artifact ref is not an object: {name}", f"artifacts.{name}"))
            continue
        target = safe(root, ref, f"artifacts.{name}", errors)
        if target:
            resolved[name] = target

    if errors:
        return {"contract_version": "1.1.0", "episode_date": date, "status": "fail", "errors": [x.as_dict() for x in errors], "warnings": []}

    receipt_validator = load_module(
        "critic_receipt_validator_v1_1",
        root / "scripts/story-engine/validate_critic_execution_receipt.py",
    )
    receipt_result = receipt_validator.validate(
        resolved["critic_request"],
        resolved["critic_execution_receipt"],
        repo_root=root,
        request_schema=root / "skills/nasdaq-cafe-story-engine/contracts/critic_request.schema.json",
        receipt_schema=root / "skills/nasdaq-cafe-story-engine/contracts/critic_execution_receipt.schema.json",
    )
    if receipt_result["status"] != "pass":
        for item in receipt_result.get("errors", []):
            errors.append(Item("E_CRITIC_RECEIPT", item.get("message", "critic receipt failed"), item.get("path", "")))
    warnings.extend(Item(x.get("code", "W_CRITIC_RECEIPT"), x.get("message", ""), x.get("path", "")) for x in receipt_result.get("warnings", []))

    request = load(resolved["critic_request"])
    receipt = load(resolved["critic_execution_receipt"])
    if request.get("episode_date") != date or receipt.get("episode_date") != date:
        errors.append(Item("E_DATE", "critic artifacts must match acceptance episode_date", "episode_date"))

    inputs = {row["role"]: (root / row["path"]).resolve() for row in request.get("inputs", []) if isinstance(row, dict) and row.get("role") and row.get("path")}
    plan_template = inputs.get("story_plan_template")
    script_template = inputs.get("story_script_template")
    if plan_template and script_template:
        plan_runtime = load(resolved["story_plan"])
        plan_source = load(plan_template)
        if normalize_plan(plan_runtime, plan_source) != plan_source:
            errors.append(Item("E_SEMANTIC_DRIFT", "materialized Story Plan differs from the Critic-reviewed template beyond lineage binding", "artifacts.story_plan"))
        script_runtime = load(resolved["story_script"])
        script_source = load(script_template)
        if normalize_script(script_runtime, script_source) != script_source:
            errors.append(Item("E_SEMANTIC_DRIFT", "materialized Story Script differs from the Critic-reviewed template beyond lineage binding", "artifacts.story_script"))

    review_runtime = load(resolved["creative_review"])
    review_source = load((root / receipt["review"]["path"]).resolve())
    if review_runtime != review_source:
        errors.append(Item("E_REVIEW_DRIFT", "materialized review differs from the Critic-reviewed source artifact", "artifacts.creative_review"))

    critic = acceptance.get("critic", {})
    if critic.get("author_invocation_id") != receipt.get("author_invocation_id"):
        errors.append(Item("E_AUTHOR_ID", "acceptance author invocation differs from receipt", "critic.author_invocation_id"))
    if critic.get("critic_invocation_id") != receipt.get("critic_invocation_id"):
        errors.append(Item("E_CRITIC_ID", "acceptance critic invocation differs from receipt", "critic.critic_invocation_id"))
    if critic.get("isolation_mode") != "separate_invocation":
        errors.append(Item("E_ISOLATION", "acceptance requires separate_invocation Critic", "critic.isolation_mode"))
    if critic.get("verdict") != "pass" or int(critic.get("score", 0)) < 25:
        errors.append(Item("E_CRITIC_PASS", "final independent Critic must PASS with score >=25", "critic"))

    validation = acceptance.get("validation", {})
    required_checks = {"story_plan", "story_script", "independent_critic", "independent_critic_receipt", "causality_guard", "scene_order_guard", "scene_09_guard"}
    for key in sorted(required_checks):
        if validation.get(key) != "pass":
            errors.append(Item("E_VALIDATION", f"validation check is not PASS: {key}", f"validation.{key}"))

    attestation_strength = receipt.get("provenance", {}).get("attestation_strength")
    if require_production:
        if not production_eligible:
            errors.append(Item("E_PRODUCTION_ELIGIBILITY", "Story Engine acceptance is not production eligible", "production_eligible"))
        if attestation_strength != "orchestrator_signed":
            errors.append(Item(
                "E_CRITIC_PROCESS_NOT_PROVEN",
                "production requires orchestrator_signed proof of a distinct Critic execution; repository provenance is insufficient",
                "critic.execution_receipt",
            ))
    elif not production_eligible:
        warnings.append(Item(
            "W_PRODUCTION_BLOCKED",
            "Story Engine artifacts are valid but production remains blocked until an orchestrator_signed independent Critic receipt exists",
            "production_eligible",
        ))

    return {
        "contract_version": "1.1.0",
        "episode_date": date,
        "production_eligible": production_eligible,
        "status": "fail" if errors else "pass",
        "errors": [x.as_dict() for x in errors],
        "warnings": [x.as_dict() for x in warnings],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=ROOT)
    ap.add_argument("--acceptance", type=Path, required=True)
    ap.add_argument("--require-production", action="store_true")
    args = ap.parse_args()
    root = args.repo_root.resolve()
    acceptance = args.acceptance if args.acceptance.is_absolute() else root / args.acceptance
    result = validate_acceptance(acceptance, repo_root=root, require_production=args.require_production)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
