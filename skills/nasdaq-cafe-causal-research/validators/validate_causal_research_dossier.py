#!/usr/bin/env python3
"""Validate causal dossier v0.2 and the complete memory-revalidation chain."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_research_input_manifest import (  # noqa: E402
    ManifestBuildError,
    expected_bucket,
    normalized_selected_item,
    verify_retrieval_lineage,
)
from editorial_memory_retrieval import retrieve  # noqa: E402


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "pass" if self.ok else "fail",
            "errors": self.errors,
            "warnings": self.warnings,
        }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def format_json_path(parts: Iterable[Any]) -> str:
    values = list(parts)
    return ".".join(str(value) for value in values) or "<root>"


def schema_errors(instance: Any, schema_path: Path, label: str) -> list[str]:
    try:
        schema = load_json(schema_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{label}: cannot load schema {schema_path}: {exc}"]
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{label}.{format_json_path(error.absolute_path)}: {error.message}"
        for error in sorted(
            validator.iter_errors(instance),
            key=lambda item: list(item.absolute_path),
        )
    ]


def resolve_repo_reference(
    value: str,
    repo_root: Path,
    label: str,
    errors: list[str],
) -> Path | None:
    path = Path(value)
    if path.is_absolute():
        errors.append(f"{label}: absolute paths are forbidden: {value}")
        return None
    root = repo_root.resolve()
    resolved = (root / path).resolve()
    if resolved != root and root not in resolved.parents:
        errors.append(f"{label}: path escapes repository root: {value}")
        return None
    if not resolved.is_file():
        errors.append(f"{label}: referenced file does not exist: {value}")
        return None
    return resolved


def validate_file_hash(
    *,
    label: str,
    declared_path: str,
    declared_sha: str,
    repo_root: Path,
    errors: list[str],
) -> Path | None:
    resolved = resolve_repo_reference(declared_path, repo_root, label, errors)
    if not resolved:
        return None
    actual = sha256_file(resolved)
    if actual != declared_sha:
        errors.append(
            f"{label}: SHA-256 mismatch for {declared_path}: "
            f"declared={declared_sha} actual={actual}"
        )
    return resolved


def is_memory_reference(value: str) -> bool:
    lowered = value.replace("\\", "/").lower()
    return (
        "editorial-memory/" in lowered
        or lowered.startswith("memory:")
        or "memory_context_" in lowered
        or "memory_retrieval_report_" in lowered
    )


def evidence_quality_for_current_use(item: dict[str, Any]) -> bool:
    source_reference = str(item.get("source_reference", "")).strip()
    return (
        item.get("evidence_class") in {"fact", "reported_interpretation"}
        and item.get("source_tier") in {"tier_1", "tier_2"}
        and bool(source_reference)
        and not is_memory_reference(source_reference)
    )


def manifest_selected(
    manifest: dict[str, Any], errors: list[str]
) -> dict[tuple[str, str], tuple[str, dict[str, Any]]]:
    result: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {}
    for bucket in (
        "current_revalidation_required",
        "historical_context_only",
        "procedural",
    ):
        for item in manifest["memory_intake"][bucket]:
            key = (item["item_type"], item["item_id"])
            if key in result:
                errors.append(
                    f"manifest selected memory appears in multiple buckets: {key}"
                )
            else:
                result[key] = (bucket, item)
    return result


def report_selected(
    report: dict[str, Any], errors: list[str]
) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for item in report["selected"]:
        key = (item["item_type"], item["item_id"])
        if key in result:
            errors.append(f"duplicate selected memory in retrieval report: {key}")
        else:
            result[key] = item
    return result


def compare_manifest_to_report(
    manifest: dict[str, Any], report: dict[str, Any], errors: list[str]
) -> tuple[
    dict[tuple[str, str], tuple[str, dict[str, Any]]],
    dict[tuple[str, str], dict[str, Any]],
]:
    manifest_items = manifest_selected(manifest, errors)
    report_items = report_selected(report, errors)
    if set(manifest_items) != set(report_items):
        missing = sorted(set(report_items) - set(manifest_items))
        extra = sorted(set(manifest_items) - set(report_items))
        if missing:
            errors.append(f"manifest omits selected memory: {missing}")
        if extra:
            errors.append(f"manifest contains memory not selected by report: {extra}")

    for key in sorted(set(manifest_items) & set(report_items)):
        bucket, manifest_item = manifest_items[key]
        report_item = report_items[key]
        try:
            wanted_bucket = expected_bucket(report_item)
        except ManifestBuildError as exc:
            errors.append(str(exc))
            continue
        if bucket != wanted_bucket:
            errors.append(
                f"{key}: manifest bucket={bucket} but retrieval requires {wanted_bucket}"
            )
        wanted_item = normalized_selected_item(report_item)
        if manifest_item != wanted_item:
            errors.append(
                f"{key}: manifest selected metadata differs from retrieval report"
            )
    return manifest_items, report_items


def collect_all_evidence_references(dossier: dict[str, Any]) -> list[tuple[str, list[str]]]:
    refs: list[tuple[str, list[str]]] = [
        ("expected", dossier["expected_actual_gap"]["expected"]["evidence_ids"]),
        ("actual", dossier["expected_actual_gap"]["actual"]["evidence_ids"]),
    ]
    for question in dossier["research_questions"]:
        refs.append((f"research question {question['id']}", question.get("evidence_ids", [])))
    for edge in dossier["causal_edges"]:
        refs.append((f"causal edge {edge['id']}", edge["evidence_ids"]))
    for item in dossier["timeline"]:
        refs.append((f"timeline {item['id']}", item["evidence_ids"]))
    for item in dossier["contrary_evidence"]:
        refs.append(("contrary evidence", item["evidence_ids"]))
    for alt in dossier["alternative_hypotheses"]:
        refs.append(
            (f"alternative hypothesis {alt['id']} supporting", alt["supporting_evidence_ids"])
        )
        refs.append(
            (f"alternative hypothesis {alt['id']} weakening", alt["weakening_evidence_ids"])
        )
    return refs


def validate_dossier(
    dossier_path: Path,
    manifest_path: Path,
    retrieval_report_path: Path,
    *,
    contracts_dir: Path,
    repo_root: Path,
    retrieval_runner=retrieve,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    repo_root = repo_root.resolve()
    contracts_dir = contracts_dir.resolve()
    if contracts_dir != repo_root and repo_root not in contracts_dir.parents:
        return ValidationResult(
            [f"contracts directory escapes repository root: {contracts_dir}"], []
        )

    supplied: dict[str, Path] = {}
    for label, path in (
        ("dossier", dossier_path),
        ("manifest", manifest_path),
        ("retrieval report", retrieval_report_path),
    ):
        try:
            resolved = path.resolve()
            if resolved != repo_root and repo_root not in resolved.parents:
                errors.append(f"{label}: supplied path escapes repository root: {path}")
            elif not resolved.is_file():
                errors.append(f"{label}: file does not exist: {path}")
            else:
                supplied[label] = resolved
        except OSError as exc:
            errors.append(f"{label}: cannot resolve path {path}: {exc}")
    if errors:
        return ValidationResult(sorted(set(errors)), warnings)

    try:
        dossier = load_json(supplied["dossier"])
        manifest = load_json(supplied["manifest"])
        report = load_json(supplied["retrieval report"])
    except (OSError, json.JSONDecodeError) as exc:
        return ValidationResult([f"cannot read validation input: {exc}"], [])

    dossier_version = dossier.get("contract_version")
    if dossier_version == "0.3.0":
        dossier_schema_name = "causal_research_dossier_v0.3.schema.json"
    elif dossier_version == "0.2.0":
        dossier_schema_name = "causal_research_dossier_v0.2.schema.json"
    else:
        return ValidationResult(
            [f"unsupported Causal Dossier contract_version: {dossier_version!r}"], warnings
        )
    errors.extend(
        schema_errors(dossier, contracts_dir / dossier_schema_name, "dossier")
    )
    errors.extend(
        schema_errors(
            manifest,
            contracts_dir / "research_input_manifest.schema.json",
            "manifest",
        )
    )
    editorial_contracts = (
        contracts_dir / "../../nasdaq-cafe-editorial-memory/contracts"
    ).resolve()
    errors.extend(
        schema_errors(
            report,
            editorial_contracts / "memory_retrieval_report.schema.json",
            "retrieval_report",
        )
    )
    if errors:
        return ValidationResult(sorted(set(errors)), warnings)

    if dossier["episode_date"] != manifest["episode_date"]:
        errors.append(
            f"episode date mismatch: dossier={dossier['episode_date']} manifest={manifest['episode_date']}"
        )
    if dossier["episode_date"] != report["episode_date"]:
        errors.append(
            f"episode date mismatch: dossier={dossier['episode_date']} report={report['episode_date']}"
        )
    if dossier["session"] != manifest["session"]:
        errors.append("dossier session does not match research input manifest session")
    if manifest["validation"]["status"] != "pass":
        errors.append("research input manifest validation status is not pass")

    dossier_manifest_ref = dossier["research_input_manifest"]
    resolved_manifest = validate_file_hash(
        label="research_input_manifest",
        declared_path=dossier_manifest_ref["path"],
        declared_sha=dossier_manifest_ref["sha256"],
        repo_root=repo_root,
        errors=errors,
    )
    if resolved_manifest and resolved_manifest != supplied["manifest"]:
        errors.append(
            "dossier research_input_manifest path does not resolve to the supplied manifest"
        )

    resolved_inputs: dict[str, Path | None] = {}
    for label, file_ref in manifest["inputs"].items():
        resolved_inputs[label] = validate_file_hash(
            label=f"manifest.inputs.{label}",
            declared_path=file_ref["path"],
            declared_sha=file_ref["sha256"],
            repo_root=repo_root,
            errors=errors,
        )
    resolved_report = resolved_inputs.get("memory_retrieval_report")
    if resolved_report and resolved_report != supplied["retrieval report"]:
        errors.append(
            "manifest memory_retrieval_report path does not resolve to the supplied report"
        )

    query_path = resolved_inputs.get("memory_query_plan")
    context_path = resolved_inputs.get("memory_context")
    if query_path and context_path and resolved_report:
        try:
            verify_retrieval_lineage(
                memory_query_plan=query_path,
                memory_context=context_path,
                memory_retrieval_report=resolved_report,
                repo_root=repo_root,
                editorial_contracts_dir=editorial_contracts,
                retrieval_runner=retrieval_runner,
                include_temporal_carryover=(
                    manifest.get("contract_version") == "1.1.0"
                ),
            )
        except ManifestBuildError as exc:
            errors.append(f"retrieval lineage: {exc}")

    _, report_items = compare_manifest_to_report(manifest, report, errors)
    report_non_core = {key: item for key, item in report_items.items() if key[0] != "core"}

    entries: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in dossier["memory_revalidation"]:
        key = (entry["memory_reference_type"], entry["memory_reference_id"])
        if key in entries:
            errors.append(f"duplicate memory revalidation entry: {key}")
        else:
            entries[key] = entry
    if set(entries) != set(report_non_core):
        missing = sorted(set(report_non_core) - set(entries))
        extra = sorted(set(entries) - set(report_non_core))
        if missing:
            errors.append(f"selected memory has no revalidation result: {missing}")
        if extra:
            errors.append(f"revalidation references unselected memory: {extra}")

    evidence = {item["evidence_id"]: item for item in dossier["evidence"]}
    if len(evidence) != len(dossier["evidence"]):
        errors.append("duplicate evidence_id in dossier")
    for evidence_id, item in evidence.items():
        if is_memory_reference(item.get("source_reference", "")):
            errors.append(
                f"{evidence_id}: editorial memory cannot be registered as current evidence"
            )

    conclusion_statuses = {
        "supported",
        "partially_supported",
        "weakened",
        "invalidated",
    }
    current_editorial_uses = {
        "research_lead",
        "comparison",
        "counterevidence",
        "explanation_context",
        "monitoring_point",
    }

    for key, entry in entries.items():
        report_item = report_non_core.get(key)
        if not report_item:
            continue
        if entry["retrieval_use_mode"] != report_item["use_mode"]:
            errors.append(f"{key}: retrieval_use_mode differs from retrieval report")
        if entry["historical_confidence"] != report_item.get(
            "historical_confidence", "unknown"
        ):
            errors.append(f"{key}: historical_confidence differs from retrieval report")

        status = entry["revalidation_status"]
        editorial_use = entry["editorial_use"]
        current_ids = entry["current_evidence_ids"]

        if report_item.get("status") in {"invalidated", "resolved"} and status not in {
            "historical_context_only",
            "not_used",
        }:
            errors.append(
                f"{key}: {report_item.get('status')} memory cannot be a current premise"
            )
        if report_item["use_mode"] == "historical_context" and status not in {
            "historical_context_only",
            "not_used",
        }:
            errors.append(
                f"{key}: historical-context retrieval cannot be marked {status}"
            )
        if status == "historical_context_only" and report_item["use_mode"] != "historical_context":
            errors.append(
                f"{key}: historical_context_only requires historical_context retrieval"
            )
        if status == "not_used":
            if editorial_use != "not_used":
                errors.append(f"{key}: not_used status requires editorial_use=not_used")
            if current_ids:
                errors.append(f"{key}: not_used must not retain current_evidence_ids")
        if editorial_use == "procedural_only":
            errors.append(f"{key}: non-core memory cannot use editorial_use=procedural_only")
        if editorial_use in current_editorial_uses and status in {"not_used", "unresolved"}:
            errors.append(
                f"{key}: editorial_use={editorial_use} is incompatible with status={status}"
            )
        if status == "historical_context_only" and editorial_use not in {
            "comparison",
            "explanation_context",
            "not_used",
        }:
            errors.append(
                f"{key}: historical_context_only permits only comparison, explanation_context, or not_used"
            )

        if status in conclusion_statuses and not current_ids:
            errors.append(f"{key}: {status} requires current_evidence_ids")
        if editorial_use == "research_lead" and not current_ids:
            errors.append(f"{key}: research_lead requires current evidence")

        current_evidence: list[dict[str, Any]] = []
        for evidence_id in current_ids:
            item = evidence.get(evidence_id)
            if not item:
                errors.append(f"{key}: unknown current evidence id {evidence_id}")
                continue
            current_evidence.append(item)
            if is_memory_reference(item.get("source_reference", "")):
                errors.append(
                    f"{key}: past memory cannot be used as current evidence ({evidence_id})"
                )

        if status in conclusion_statuses and current_evidence:
            if not all(evidence_quality_for_current_use(item) for item in current_evidence):
                errors.append(
                    f"{key}: {status} requires tier_1/tier_2 current fact or reported interpretation evidence"
                )
        if report_item.get("requires_current_revalidation") and status not in {
            "not_used",
            "supported",
            "partially_supported",
            "weakened",
            "invalidated",
            "unresolved",
        }:
            errors.append(
                f"{key}: current-revalidation-required memory has invalid status {status}"
            )

        if entry["historical_confidence"] == "low":
            warnings.append(f"{key}: historical confidence is low")
        if current_evidence and all(
            item.get("source_tier") == "tier_2" for item in current_evidence
        ):
            warnings.append(f"{key}: current evidence is tier_2 only")
        if status != "not_used" and not entry["difference_from_previous"].strip():
            warnings.append(f"{key}: difference_from_previous is empty")
        if status == "supported" and any(
            item.get("directness") == "context" for item in current_evidence
        ):
            warnings.append(f"{key}: supported status includes context-only evidence")

    for label, ids in collect_all_evidence_references(dossier):
        for evidence_id in ids:
            if evidence_id not in evidence:
                errors.append(f"{label}: unknown evidence id {evidence_id}")

    expected = dossier["expected_actual_gap"]["expected"]
    expected_ids = expected["evidence_ids"]
    if expected["basis_class"] not in {"unconfirmed", "not_applicable"}:
        if not expected_ids:
            errors.append("Expected is confirmed/classified but has no current evidence")
        elif all(
            evidence_id in evidence
            and is_memory_reference(evidence[evidence_id]["source_reference"])
            for evidence_id in expected_ids
        ):
            errors.append("Expected cannot be grounded only in editorial memory")

    actual = dossier["expected_actual_gap"]["actual"]
    actual_ids = actual["evidence_ids"]
    if actual["statement"].strip() and not actual_ids:
        errors.append("Actual has a statement but no current evidence")
    elif actual_ids and all(
        evidence_id in evidence
        and is_memory_reference(evidence[evidence_id]["source_reference"])
        for evidence_id in actual_ids
    ):
        errors.append("Actual cannot be grounded only in editorial memory")

    for edge in dossier["causal_edges"]:
        edge_evidence = [
            evidence[evidence_id]
            for evidence_id in edge["evidence_ids"]
            if evidence_id in evidence
        ]
        if edge["scope"] == "nasdaq_wide" and not any(
            evidence_quality_for_current_use(item) for item in edge_evidence
        ):
            errors.append(
                f"{edge['id']}: NASDAQ-wide edge requires current tier_1/tier_2 evidence"
            )
        if any(
            is_memory_reference(item.get("source_reference", ""))
            for item in edge_evidence
        ):
            errors.append(
                f"{edge['id']}: causal edge cannot reference editorial memory as evidence"
            )

    daily_ref = manifest["inputs"]["daily_source_package"]
    if not any(
        item["role"] == "daily_input"
        and item["path_or_reference"] == daily_ref["path"]
        and item["version_or_hash"] == daily_ref["sha256"]
        for item in dossier["input_provenance"]
    ):
        errors.append(
            "input_provenance must include the manifest-bound daily source package path and SHA-256"
        )


    if dossier.get("contract_version") == "0.3.0":
        # Temporal Evidence is additive. Current evidence remains authoritative;
        # memory and candidate-pool items may not become evidence by reference alone.
        for index, result in enumerate(dossier.get("carryover_results", [])):
            status = result.get("status")
            ids = result.get("current_evidence_ids", [])
            if status in {"supports", "weakens", "contradicts"} and not ids:
                errors.append(f"carryover_results[{index}]: {status} requires Current Evidence ID")
            if status == "expired" and not isinstance(result.get("completed_observation_sessions"), int):
                errors.append(f"carryover_results[{index}]: expired requires completed_observation_sessions")
            for evidence_id in ids:
                item = evidence.get(evidence_id)
                if not item:
                    errors.append(f"carryover_results[{index}]: unknown evidence id {evidence_id}")
                elif item.get("source_tier") in {"discovery_only", "unavailable"}:
                    errors.append(f"carryover_results[{index}]: Candidate/Coverage item cannot be current evidence ({evidence_id})")

        cross = dossier.get("cross_market_assessment", {})
        materiality = cross.get("materiality")
        alternatives = cross.get("alternatives", [])
        if materiality == "material":
            ids = [item.get("hypothesis_id") for item in alternatives]
            if set(ids) != {"H1", "H2", "H3", "H4"} or len(ids) != 4:
                errors.append("material cross-market assessment must compare H1/H2/H3/H4 exactly once")
        elif alternatives:
            errors.append("cross-market deep alternatives are allowed only when materiality=material")
        for evidence_id in cross.get("evidence_ids", []):
            if evidence_id not in evidence:
                errors.append(f"cross_market_assessment: unknown evidence id {evidence_id}")
        for alt in alternatives:
            for key in ("supporting_evidence_ids", "weakening_evidence_ids"):
                for evidence_id in alt.get(key, []):
                    if evidence_id not in evidence:
                        errors.append(f"cross_market_assessment {alt.get('hypothesis_id')}: unknown evidence id {evidence_id}")

        candidate_keys: set[str] = set()
        for index, candidate in enumerate(dossier.get("validation_candidates", [])):
            target = candidate.get("observation_target")
            if not isinstance(target, dict):
                errors.append(f"validation_candidates[{index}]: observation_target must be one object")
                continue
            if target.get("session") != "next_completed_regular_session":
                errors.append(f"validation_candidates[{index}]: session must be next_completed_regular_session")
            if any(isinstance(value, (dict, list)) for value in target.values()):
                errors.append(f"validation_candidates[{index}]: 1 VO = 1 observation target")
            if not str(candidate.get("strengthen_condition", "")).strip() or not str(candidate.get("weaken_condition", "")).strip():
                errors.append(f"validation_candidates[{index}]: strengthen/weaken conditions are required")
            key = json.dumps(
                {
                    "hypothesis_reference": candidate.get("hypothesis_reference"),
                    "observation_target": target,
                    "strengthen_condition": candidate.get("strengthen_condition"),
                    "weaken_condition": candidate.get("weaken_condition"),
                },
                ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            )
            if key in candidate_keys:
                errors.append(f"validation_candidates[{index}]: duplicate semantic validation candidate")
            candidate_keys.add(key)

        for index, need in enumerate(dossier.get("visual_evidence_needs", [])):
            for evidence_id in need.get("evidence_ids", []):
                if evidence_id not in evidence:
                    errors.append(f"visual_evidence_needs[{index}]: unknown evidence id {evidence_id}")

        collector_ref = manifest.get("inputs", {}).get("collector_source_pack")
        if collector_ref and not any(
            item.get("path_or_reference") == collector_ref.get("path")
            and item.get("version_or_hash") == collector_ref.get("sha256")
            for item in dossier.get("input_provenance", [])
        ):
            errors.append("input_provenance must include optional collector_source_pack path and SHA-256")

    return ValidationResult(sorted(set(errors)), sorted(set(warnings)))



def _repo_ref(repo_root: Path, path: Path) -> dict[str, str]:
    root = repo_root.resolve()
    resolved = path.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path escapes repository root: {path}")
    if not resolved.is_file():
        raise ValueError(f"missing receipt-bound file: {path}")
    return {"path": resolved.relative_to(root).as_posix(), "sha256": sha256_file(resolved)}


def _receipt_episode_date(dossier_path: Path, manifest_path: Path) -> str | None:
    for path in (dossier_path, manifest_path):
        try:
            value = load_json(path)
        except Exception:
            continue
        candidate = value.get("episode_date")
        if isinstance(candidate, str):
            return candidate
    return None


def build_validation_receipt(
    *,
    result: ValidationResult,
    dossier_path: Path,
    manifest_path: Path,
    retrieval_report_path: Path,
    contracts_dir: Path,
    repo_root: Path,
) -> dict[str, Any]:
    root = repo_root.resolve()
    try:
        dossier = load_json(dossier_path)
        version = dossier.get("contract_version")
    except Exception:
        version = None
    if version == "0.3.0":
        dossier_schema = contracts_dir / "causal_research_dossier_v0.3.schema.json"
    elif version == "0.2.0":
        dossier_schema = contracts_dir / "causal_research_dossier_v0.2.schema.json"
    else:
        # Bind both known schemas on unsupported/malformed input so the FAIL receipt
        # still records the exact validator contract surface that rejected it.
        dossier_schema = contracts_dir / "causal_research_dossier_v0.3.schema.json"
    editorial_contracts = (contracts_dir / "../../nasdaq-cafe-editorial-memory/contracts").resolve()
    receipt_schema = contracts_dir / "causal_dossier_validation_receipt.schema.json"
    validator_path = Path(__file__).resolve()
    return {
        "contractVersion": "1.0.0",
        "status": "pass" if result.ok else "fail",
        "episodeDate": _receipt_episode_date(dossier_path, manifest_path),
        "dossier": _repo_ref(root, dossier_path),
        "researchInputManifest": _repo_ref(root, manifest_path),
        "memoryRetrievalReport": _repo_ref(root, retrieval_report_path),
        "validator": _repo_ref(root, validator_path),
        "schemaBindings": [
            _repo_ref(root, dossier_schema),
            _repo_ref(root, contracts_dir / "research_input_manifest.schema.json"),
            _repo_ref(root, editorial_contracts / "memory_query_plan.schema.json"),
            _repo_ref(root, editorial_contracts / "memory_retrieval_report.schema.json"),
            _repo_ref(root, receipt_schema),
            _repo_ref(root, root / "scripts/build_research_input_manifest.py"),
            _repo_ref(root, root / "scripts/editorial_memory_retrieval.py"),
            _repo_ref(root, root / "scripts/temporal_evidence.py"),
        ],
        "errors": result.errors,
        "warnings": result.warnings,
    }


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _validate_receipt_schema(payload: dict[str, Any], schema_path: Path) -> list[str]:
    return schema_errors(payload, schema_path, "causal_dossier_validation_receipt")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--research-input-manifest", type=Path, required=True)
    parser.add_argument("--memory-retrieval-report", type=Path, required=True)
    parser.add_argument(
        "--contracts-dir",
        type=Path,
        default=Path("skills/nasdaq-cafe-causal-research/contracts"),
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_dossier(
        args.dossier,
        args.research_input_manifest,
        args.memory_retrieval_report,
        contracts_dir=args.contracts_dir,
        repo_root=args.repo_root,
    )
    payload = build_validation_receipt(
        result=result,
        dossier_path=args.dossier,
        manifest_path=args.research_input_manifest,
        retrieval_report_path=args.memory_retrieval_report,
        contracts_dir=args.contracts_dir.resolve(),
        repo_root=args.repo_root.resolve(),
    )
    receipt_schema = args.contracts_dir.resolve() / "causal_dossier_validation_receipt.schema.json"
    receipt_errors = _validate_receipt_schema(payload, receipt_schema)
    if receipt_errors:
        payload["status"] = "fail"
        payload["errors"] = sorted(set([*payload.get("errors", []), *receipt_errors]))
        result.errors.extend(receipt_errors)
    if args.json_output:
        _atomic_json(args.json_output, payload)
    for error in result.errors:
        print(f"ERROR: {error}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("PASS" if result.ok else "FAIL")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
