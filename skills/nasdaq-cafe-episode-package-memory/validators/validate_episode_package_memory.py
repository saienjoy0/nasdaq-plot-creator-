#!/usr/bin/env python3
"""Validate an episode package's machine-readable editorial-memory usage annex."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
PARSER_DIR = ROOT / "skills/nasdaq-cafe-episode-package-memory/parsers"
if str(PARSER_DIR) not in sys.path:
    sys.path.insert(0, str(PARSER_DIR))

from episode_package_memory_parser import MARKER_RE, EpisodePackageParseError, MarkerLocation, parse_episode_package  # noqa: E402

STATUS_USAGE = {
    "supported": {"current_supported_context", "historical_comparison", "monitoring_point"},
    "partially_supported": {"historical_comparison", "change_from_previous", "monitoring_point"},
    "weakened": {"change_from_previous", "counterevidence", "monitoring_point"},
    "invalidated": {"correction", "counterevidence"},
    "unresolved": {"monitoring_point", "internal_only"},
    "historical_context_only": {"historical_comparison", "internal_only"},
    "not_used": {"internal_only"},
}
CURRENT_CLAIM_MODES = {"current_fact", "current_reported_interpretation", "current_grounded_inference"}
TITLE_SURFACES = {"title", "thumbnail"}
PUBLIC_SURFACES = {"scene_narration", "scene_connection", "main_telop", "support_telop", "visual_text", "title", "thumbnail", "description"}
FORBIDDEN_PERSONAL_PATTERNS = [
    re.compile(r"僕も.{0,20}(?:失敗|損した|間違えた)"),
    re.compile(r"僕は.{0,20}(?:保有|持っています|買いました|売りました)"),
    re.compile(r"(?:取得価格|含み損|含み益|取引履歴|証券口座)"),
    re.compile(r"履修登録で失敗"),
    re.compile(r"乗り換えを間違え"),
]
OVERCLAIM_PATTERNS = [re.compile(r"的中"), re.compile(r"また同じ"), re.compile(r"予言")]


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {"status": "pass" if self.ok else "fail", "errors": self.errors, "warnings": self.warnings}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON must be an object: {path}")
    return value


def safe_repo_file(repo_root: Path, relative: str, label: str, errors: list[str]) -> Path | None:
    path = Path(relative)
    if path.is_absolute():
        errors.append(f"{label}: absolute paths are forbidden: {relative}")
        return None
    root = repo_root.resolve()
    resolved = (root / path).resolve()
    if resolved != root and root not in resolved.parents:
        errors.append(f"{label}: path escapes repository root: {relative}")
        return None
    if not resolved.is_file():
        errors.append(f"{label}: referenced file does not exist: {relative}")
        return None
    return resolved


def schema_errors(instance: Any, schema_path: Path) -> list[str]:
    try:
        schema = load_json(schema_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot load annex schema {schema_path}: {exc}"]
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"annex.{'.'.join(str(x) for x in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
    ]


def _load_pr6_validator(repo_root: Path):
    path = repo_root / "skills/nasdaq-cafe-causal-research/validators/validate_causal_research_dossier.py"
    spec = importlib.util.spec_from_file_location("pr6_dossier_validator", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import PR6 dossier validator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def replay_dossier_validation(repo_root: Path, dossier_path: Path) -> ValidationResult:
    errors: list[str] = []
    dossier = load_json(dossier_path)
    manifest_ref = dossier.get("research_input_manifest", {})
    manifest_path = safe_repo_file(repo_root, str(manifest_ref.get("path", "")), "dossier manifest", errors)
    if manifest_path is None:
        return ValidationResult(errors or ["dossier manifest cannot be resolved"], [])
    manifest = load_json(manifest_path)
    report_ref = manifest.get("inputs", {}).get("memory_retrieval_report", {})
    report_path = safe_repo_file(repo_root, str(report_ref.get("path", "")), "retrieval report", errors)
    if report_path is None:
        return ValidationResult(errors or ["retrieval report cannot be resolved"], [])
    module = _load_pr6_validator(repo_root)
    result = module.validate_dossier(
        dossier_path,
        manifest_path,
        report_path,
        contracts_dir=repo_root / "skills/nasdaq-cafe-causal-research/contracts",
        repo_root=repo_root,
    )
    return ValidationResult(list(result.errors), list(result.warnings))


def _dossier_memory_index(dossier: dict[str, Any], errors: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for index, item in enumerate(dossier.get("memory_revalidation", [])):
        if not isinstance(item, dict):
            errors.append(f"dossier.memory_revalidation[{index}] must be an object")
            continue
        key = (str(item.get("memory_reference_type", "")), str(item.get("memory_reference_id", "")))
        if key in result:
            errors.append(f"duplicate dossier memory revalidation: {key[0]}:{key[1]}")
        else:
            result[key] = item
    return result


def _evidence_index(dossier: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("evidence_id")): item for item in dossier.get("evidence", []) if isinstance(item, dict) and item.get("evidence_id")}


def _current_quality(item: dict[str, Any]) -> bool:
    return (
        item.get("evidence_class") in {"fact", "reported_interpretation"}
        and item.get("source_tier") in {"tier_1", "tier_2"}
        and bool(str(item.get("source_reference", "")).strip())
        and "editorial-memory/" not in str(item.get("source_reference", "")).replace("\\", "/").lower()
    )


def _marker_index(markers: list[MarkerLocation], errors: list[str]) -> dict[tuple[str, str], MarkerLocation]:
    result: dict[tuple[str, str], MarkerLocation] = {}
    for marker in markers:
        key = (marker.reference_id, marker.usage_id)
        if key in result:
            errors.append(f"duplicate marker: {marker.marker}")
        else:
            result[key] = marker
    return result


def validate_episode_package_memory(
    *,
    repo_root: Path,
    episode_package_path: Path,
    schema_path: Path | None = None,
    dossier_replay: Callable[[Path, Path], ValidationResult] | None = None,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    repo_root = repo_root.resolve()
    episode_package_path = episode_package_path.resolve()
    if episode_package_path != repo_root and repo_root not in episode_package_path.parents:
        return ValidationResult([f"episode package path escapes repository root: {episode_package_path}"], [])
    if not episode_package_path.is_file():
        return ValidationResult([f"episode package does not exist: {episode_package_path}"], [])
    markdown = episode_package_path.read_text(encoding="utf-8")
    try:
        parsed = parse_episode_package(markdown)
    except EpisodePackageParseError as exc:
        return ValidationResult([str(exc)], [])
    schema_path = schema_path or repo_root / "skills/nasdaq-cafe-episode-package-memory/contracts/episode_package_memory_annex.schema.json"
    errors.extend(schema_errors(parsed.annex, schema_path))
    if errors:
        return ValidationResult(errors, warnings)
    annex = parsed.annex
    dossier_ref = annex["causal_dossier"]
    dossier_path = safe_repo_file(repo_root, dossier_ref["path"], "causal dossier", errors)
    if dossier_path:
        actual_sha = sha256_file(dossier_path)
        if actual_sha != dossier_ref["sha256"]:
            errors.append(f"causal dossier SHA-256 mismatch: declared={dossier_ref['sha256']} actual={actual_sha}")
    if errors or dossier_path is None:
        return ValidationResult(errors, warnings)
    try:
        dossier = load_json(dossier_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult([f"cannot load causal dossier: {exc}"], warnings)
    if annex["episode_date"] != dossier.get("episode_date"):
        errors.append(f"episode date mismatch: annex={annex['episode_date']} dossier={dossier.get('episode_date')}")
    if annex["episode_date"] not in episode_package_path.name and annex["episode_date"] not in str(episode_package_path.parent):
        warnings.append("episode date is not visible in the episode package path")
    replay = dossier_replay or replay_dossier_validation
    replay_result = replay(repo_root, dossier_path)
    if replay_result.errors:
        errors.extend(f"PR6 dossier replay: {item}" for item in replay_result.errors)
    warnings.extend(f"PR6 dossier replay: {item}" for item in replay_result.warnings)
    dossier_index = _dossier_memory_index(dossier, errors)
    evidence_index = _evidence_index(dossier)
    marker_index = _marker_index(parsed.markers, errors)
    references = annex["references"]
    reference_ids: set[str] = set()
    usage_ids: set[str] = set()
    annex_usage_keys: set[tuple[str, str]] = set()
    memory_keys: set[tuple[str, str]] = set()
    for r_index, reference in enumerate(references):
        prefix = f"references[{r_index}]"
        reference_id = reference["reference_id"]
        if reference_id in reference_ids:
            errors.append(f"duplicate reference_id: {reference_id}")
        reference_ids.add(reference_id)
        memory_key = (reference["memory_reference_type"], reference["memory_reference_id"])
        if memory_key in memory_keys:
            errors.append(f"same memory appears more than once in annex: {memory_key[0]}:{memory_key[1]}")
        memory_keys.add(memory_key)
        dossier_entry = dossier_index.get(memory_key)
        if dossier_entry is None:
            errors.append(f"{prefix}: memory is not present in dossier: {memory_key[0]}:{memory_key[1]}")
            continue
        equality = {
            "historical_confidence": "historical_confidence",
            "current_revalidation_status": "revalidation_status",
            "dossier_editorial_use": "editorial_use",
            "dossier_current_evidence_ids": "current_evidence_ids",
            "difference_from_previous": "difference_from_previous",
        }
        for annex_field, dossier_field in equality.items():
            if reference[annex_field] != dossier_entry.get(dossier_field):
                errors.append(f"{prefix}.{annex_field} differs from dossier {dossier_field}")
        status = reference["current_revalidation_status"]
        public_mode = reference["public_usage_mode"]
        if public_mode not in STATUS_USAGE.get(status, set()):
            errors.append(f"{prefix}: public_usage_mode={public_mode} is forbidden for status={status}")
        if status == "partially_supported" and not reference["scope_limit"].strip():
            errors.append(f"{prefix}: partially_supported requires scope_limit")
        if status == "not_used" and reference["usages"]:
            errors.append(f"{prefix}: not_used memory cannot have public usages")
        if public_mode == "internal_only" and reference["usages"]:
            errors.append(f"{prefix}: internal_only memory cannot have public usages")
        if len(reference["usages"]) >= 3:
            warnings.append(f"{prefix}: same memory is used in three or more public locations")
        dossier_ids = set(reference["dossier_current_evidence_ids"])
        for u_index, usage in enumerate(reference["usages"]):
            u_prefix = f"{prefix}.usages[{u_index}]"
            usage_id = usage["usage_id"]
            if usage_id in usage_ids:
                errors.append(f"duplicate usage_id: {usage_id}")
            usage_ids.add(usage_id)
            key = (reference_id, usage_id)
            annex_usage_keys.add(key)
            expected_marker = f"<!--MEMREF:{reference_id}:{usage_id}-->"
            if usage["marker"] != expected_marker:
                errors.append(f"{u_prefix}: marker does not match reference_id and usage_id")
            marker = marker_index.get(key)
            if marker is None:
                errors.append(f"{u_prefix}: declared usage has no marker in episode package")
            else:
                if marker.surface != usage["surface"]:
                    errors.append(f"{u_prefix}: surface mismatch: annex={usage['surface']} actual={marker.surface}")
                if marker.scene_id != usage["scene_id"]:
                    errors.append(f"{u_prefix}: scene mismatch: annex={usage['scene_id']} actual={marker.scene_id}")
            anchor = usage["anchor_text"]
            if parsed.public_text.count(anchor) != 1:
                errors.append(f"{u_prefix}: anchor_text must appear exactly once in public episode text")
            if parsed.public_text.count(usage["marker"]) != 1:
                errors.append(f"{u_prefix}: marker must appear exactly once in public episode text")
            if anchor + usage["marker"] not in parsed.public_text:
                errors.append(f"{u_prefix}: marker must immediately follow anchor_text")
            if usage["surface"] in TITLE_SURFACES:
                if usage["scene_id"] is not None:
                    errors.append(f"{u_prefix}: title/thumbnail scene_id must be null")
                if status != "supported":
                    errors.append(f"{u_prefix}: only supported memory may be used in title/thumbnail")
                if usage["title_thumbnail_permission"] != "allowed":
                    errors.append(f"{u_prefix}: title/thumbnail usage requires permission=allowed")
                if not usage["evidence_ids"]:
                    errors.append(f"{u_prefix}: title/thumbnail usage requires current evidence")
                if any(pattern.search(anchor) for pattern in OVERCLAIM_PATTERNS):
                    errors.append(f"{u_prefix}: title/thumbnail overclaims remembered material")
                warnings.append(f"{u_prefix}: memory is used in title or thumbnail")
            else:
                if usage["surface"] in PUBLIC_SURFACES and usage["surface"].startswith("scene_") and usage["scene_id"] is None:
                    errors.append(f"{u_prefix}: Scene surface requires scene_id")
                if usage["title_thumbnail_permission"] == "allowed":
                    warnings.append(f"{u_prefix}: non-title usage declares title/thumbnail permission")
            usage_ids_set = set(usage["evidence_ids"])
            if not usage_ids_set.issubset(dossier_ids):
                errors.append(f"{u_prefix}: usage Evidence IDs must be a subset of dossier current evidence")
            for evidence_id in usage["evidence_ids"]:
                if evidence_id not in evidence_index:
                    errors.append(f"{u_prefix}: missing dossier evidence {evidence_id}")
            if public_mode == "current_supported_context":
                if status != "supported":
                    errors.append(f"{u_prefix}: current_supported_context requires supported status")
                if usage["claim_mode"] not in CURRENT_CLAIM_MODES:
                    errors.append(f"{u_prefix}: current_supported_context requires a current claim_mode")
                if not usage["evidence_ids"]:
                    errors.append(f"{u_prefix}: current_supported_context requires current evidence")
                for evidence_id in usage["evidence_ids"]:
                    if not _current_quality(evidence_index.get(evidence_id, {})):
                        errors.append(f"{u_prefix}: {evidence_id} is not tier-1/tier-2 current quality evidence")
            if status == "partially_supported":
                if usage["claim_mode"] in CURRENT_CLAIM_MODES:
                    errors.append(f"{u_prefix}: partially_supported cannot be presented as a current fact")
                if usage["wording_strength"] not in {"qualified", "historical", "uncertain"}:
                    errors.append(f"{u_prefix}: partially_supported requires qualified wording")
            if status == "weakened":
                if usage["claim_mode"] not in {"change", "counterevidence", "monitoring", "historical"}:
                    errors.append(f"{u_prefix}: weakened memory may only explain change/counterevidence/monitoring")
                if usage["wording_strength"] == "direct":
                    errors.append(f"{u_prefix}: weakened memory cannot use direct wording")
            if status == "invalidated":
                if usage["claim_mode"] not in {"correction", "counterevidence"}:
                    errors.append(f"{u_prefix}: invalidated memory requires correction or counterevidence")
                if usage["wording_strength"] != "corrective":
                    errors.append(f"{u_prefix}: invalidated memory requires corrective wording")
                if not usage["evidence_ids"]:
                    errors.append(f"{u_prefix}: invalidated correction requires current contrary evidence")
            if status == "unresolved":
                if usage["claim_mode"] != "monitoring":
                    errors.append(f"{u_prefix}: unresolved memory may only be a monitoring point")
                if usage["scene_id"] != "SCENE-08":
                    errors.append(f"{u_prefix}: unresolved public monitoring is limited to SCENE-08")
                if usage["wording_strength"] != "uncertain":
                    errors.append(f"{u_prefix}: unresolved memory requires uncertain wording")
            if status == "historical_context_only" and usage["claim_mode"] != "historical":
                errors.append(f"{u_prefix}: historical_context_only must use historical claim_mode")
            if usage["scene_id"] == "SCENE-04" and usage["claim_mode"] in CURRENT_CLAIM_MODES:
                errors.append(f"{u_prefix}: Scene 4 Expected cannot be sourced from editorial memory")
            if usage["scene_id"] == "SCENE-06" and usage["claim_mode"] in CURRENT_CLAIM_MODES:
                errors.append(f"{u_prefix}: Scene 6 price causality cannot be sourced from editorial memory")
            if usage["scene_id"] == "SCENE-01" and status in {"unresolved", "weakened", "invalidated"}:
                errors.append(f"{u_prefix}: weak or unresolved memory cannot replace the Scene 1 current hook")
            if len(anchor) > 240:
                warnings.append(f"{u_prefix}: anchor_text is unusually long")
            if usage.get("public_difference_summary") and status in {"weakened", "invalidated", "unresolved"}:
                if any(pattern.search(usage["public_difference_summary"]) for pattern in OVERCLAIM_PATTERNS):
                    warnings.append(f"{u_prefix}: public_difference_summary may be stronger than dossier difference")
    for key in sorted(set(marker_index) - annex_usage_keys):
        errors.append(f"orphan MEMREF marker is not declared in annex: {key[0]}:{key[1]}")
    for pattern in FORBIDDEN_PERSONAL_PATTERNS:
        if pattern.search(parsed.public_text):
            errors.append("episode package contains a concrete fox personal-history claim without a dedicated personal-memory contract")
            break
    for reference in references:
        for usage in reference["usages"]:
            if usage["marker"] in usage["anchor_text"]:
                errors.append("MEMREF marker is embedded in public anchor text")
    return ValidationResult(errors, warnings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-package", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = validate_episode_package_memory(repo_root=args.repo_root, episode_package_path=args.episode_package, schema_path=args.schema)
    text = json.dumps(result.as_dict(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
