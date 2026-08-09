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


def validate_acceptance(
    path: Path,
    *,
    repo_root: Path,
    require_production: bool = False,
    allow_uncertified_production: bool = False,
) -> dict[str, Any]:
    """Validate Story Engine acceptance.

    Editorial review + causality/scene guards are always mandatory. External Critic
    certification is optional only when the caller explicitly allows uncertified
    production. Absence of certification is reported, never upgraded or implied.
    """
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

    core_required = {"causal_dossier", "story_plan", "story_script", "creative_review"}
    missing = core_required - set(artifacts)
    if missing:
        errors.append(Item("E_ARTIFACTS", f"acceptance missing core artifacts: {sorted(missing)}", "artifacts"))

    has_request = "critic_request" in artifacts
    has_receipt = "critic_execution_receipt" in artifacts
    if has_request != has_receipt:
        errors.append(Item("E_ARTIFACTS", "external Critic request and receipt must be present together", "artifacts"))
    has_external = has_request and has_receipt

    names_to_resolve = set(core_required)
    if has_external:
        names_to_resolve |= {"critic_request", "critic_execution_receipt"}

    resolved: dict[str, Path] = {}
    for name in sorted(names_to_resolve & set(artifacts)):
        ref = artifacts.get(name)
        if not isinstance(ref, dict):
            errors.append(Item("E_ARTIFACTS", f"artifact ref is not an object: {name}", f"artifacts.{name}"))
            continue
        target = safe(root, ref, f"artifacts.{name}", errors)
        if target:
            resolved[name] = target

    if errors:
        return {"contract_version": "1.1.0", "episode_date": date, "status": "fail", "errors": [x.as_dict() for x in errors], "warnings": []}

    # Re-run the editorial bundle validator from the hash-bound artifacts. This is the
    # mandatory quality gate regardless of external Critic certification.
    bundle_validator = load_module(
        "story_engine_bundle_validator_acceptance",
        root / "scripts/story-engine/validate_story_engine_bundle.py",
    )
    bundle_result = bundle_validator.validate_bundle(
        resolved["story_script"],
        resolved["story_plan"],
        resolved["causal_dossier"],
        story_contracts_dir=root / "skills/nasdaq-cafe-story-authoring/contracts",
        critic_contracts_dir=root / "skills/nasdaq-cafe-entertainment-critic/contracts",
        repo_root=root,
        review_path=resolved["creative_review"],
    )
    if not bundle_result.ok:
        for message in bundle_result.errors:
            errors.append(Item("E_EDITORIAL_BUNDLE", message, "artifacts"))

    review_runtime = load(resolved["creative_review"])
    if review_runtime.get("episode_date") != date:
        errors.append(Item("E_REVIEW_DATE", "creative review date differs from acceptance", "artifacts.creative_review"))
    if review_runtime.get("verdict") != "pass" or int(review_runtime.get("total_score", 0)) < 25:
        errors.append(Item("E_REVIEW_PASS", "editorial review must PASS with score >=25", "artifacts.creative_review"))

    critic = acceptance.get("critic", {})
    if not isinstance(critic, dict):
        errors.append(Item("E_CRITIC", "critic must be an object", "critic"))
        critic = {}
    if critic.get("verdict") != review_runtime.get("verdict") or int(critic.get("score", -1)) != int(review_runtime.get("total_score", -2)):
        errors.append(Item("E_CRITIC_REVIEW_BINDING", "acceptance critic score/verdict differs from creative review", "critic"))

    critic_certified = False
    external_critic_status = "not_run"
    attestation_strength = None

    if has_external:
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

        review_source = load((root / receipt["review"]["path"]).resolve())
        if review_runtime != review_source:
            errors.append(Item("E_REVIEW_DRIFT", "materialized review differs from the externally reviewed source artifact", "artifacts.creative_review"))

        if critic.get("author_invocation_id") != receipt.get("author_invocation_id"):
            errors.append(Item("E_AUTHOR_ID", "acceptance author invocation differs from receipt", "critic.author_invocation_id"))
        if critic.get("critic_invocation_id") != receipt.get("critic_invocation_id"):
            errors.append(Item("E_CRITIC_ID", "acceptance critic invocation differs from receipt", "critic.critic_invocation_id"))
        if critic.get("isolation_mode") != "separate_invocation":
            errors.append(Item("E_ISOLATION", "external Critic lineage requires separate_invocation", "critic.isolation_mode"))

        attestation_strength = receipt.get("provenance", {}).get("attestation_strength")
        critic_certified = attestation_strength == "orchestrator_signed"
        external_critic_status = "certified" if critic_certified else "not_certified"
    else:
        if critic.get("reviewer") not in {None, review_runtime.get("reviewer")}:
            errors.append(Item("E_CRITIC_REVIEWER", "acceptance reviewer differs from creative review", "critic.reviewer"))
        if critic.get("critic_certified") not in {None, False}:
            errors.append(Item("E_CERTIFICATION_CLAIM", "acceptance cannot claim Critic certification without an external receipt", "critic.critic_certified"))
        declared_status = critic.get("external_critic_status")
        if declared_status not in {None, "not_run", "not_certified"}:
            errors.append(Item("E_EXTERNAL_STATUS", "invalid external Critic status without receipt", "critic.external_critic_status"))

    if production_eligible and not critic_certified:
        errors.append(Item("E_PRODUCTION_ELIGIBILITY_CLAIM", "production_eligible=true requires orchestrator-signed Critic certification", "production_eligible"))

    validation = acceptance.get("validation", {})
    required_checks = {"story_plan", "story_script", "causality_guard", "scene_order_guard", "scene_09_guard"}
    for key in sorted(required_checks):
        if validation.get(key) != "pass":
            errors.append(Item("E_VALIDATION", f"validation check is not PASS: {key}", f"validation.{key}"))
    if validation.get("editorial_review") != "pass" and validation.get("independent_critic") != "pass":
        errors.append(Item("E_VALIDATION", "editorial review validation is not PASS", "validation.editorial_review"))
    if "understanding_progression" in validation and validation.get("understanding_progression") != "pass":
        errors.append(Item("E_VALIDATION", "understanding progression validation is not PASS", "validation.understanding_progression"))
    if has_external and validation.get("independent_critic_receipt") != "pass" and validation.get("independent_critic_receipt") is not None:
        errors.append(Item("E_VALIDATION", "external Critic receipt validation is not PASS", "validation.independent_critic_receipt"))

    production_policy = (
        "external_critic_optional"
        if require_production and allow_uncertified_production
        else "external_critic_required"
        if require_production
        else "artifact_validation_only"
    )

    if require_production:
        if allow_uncertified_production:
            if not critic_certified:
                warnings.append(Item(
                    "W_EXTERNAL_CRITIC_NOT_CERTIFIED",
                    "production is allowed by explicit optional-Critic policy, but no orchestrator-signed external Critic certification exists",
                    "critic",
                ))
        else:
            if not production_eligible:
                errors.append(Item("E_PRODUCTION_ELIGIBILITY", "Story Engine acceptance is not production eligible", "production_eligible"))
            if not critic_certified:
                errors.append(Item(
                    "E_CRITIC_PROCESS_NOT_PROVEN",
                    "strict production requires orchestrator-signed proof of a distinct Critic execution",
                    "critic",
                ))
    elif not critic_certified:
        warnings.append(Item(
            "W_EXTERNAL_CRITIC_NOT_CERTIFIED",
            "Story Engine editorial artifacts are valid, but external Critic certification is absent",
            "critic",
        ))

    production_allowed_by_policy = not errors and (
        not require_production
        or critic_certified
        or allow_uncertified_production
    )

    return {
        "contract_version": "1.1.0",
        "episode_date": date,
        "production_eligible": production_eligible,
        "production_allowed_by_policy": production_allowed_by_policy,
        "production_policy": production_policy,
        "critic_certified": critic_certified,
        "external_critic_status": external_critic_status,
        "attestation_strength": attestation_strength,
        "status": "fail" if errors else "pass",
        "errors": [x.as_dict() for x in errors],
        "warnings": [x.as_dict() for x in warnings],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=ROOT)
    ap.add_argument("--acceptance", type=Path, required=True)
    ap.add_argument("--require-production", action="store_true")
    ap.add_argument("--allow-uncertified-production", action="store_true")
    args = ap.parse_args()
    root = args.repo_root.resolve()
    acceptance = args.acceptance if args.acceptance.is_absolute() else root / args.acceptance
    result = validate_acceptance(
        acceptance,
        repo_root=root,
        require_production=args.require_production,
        allow_uncertified_production=args.allow_uncertified_production,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
