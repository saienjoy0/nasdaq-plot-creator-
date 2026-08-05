#!/usr/bin/env python3
"""Validate causal research dossier v0.2 and editorial-memory revalidation.

Passing this validator means the artifact is structurally complete and that
past memory has not silently become current evidence. It does not certify that
the editorial interpretation is true.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator


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
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def format_json_path(parts: Iterable[Any]) -> str:
    values = list(parts)
    return ".".join(str(value) for value in values) or "<root>"


def schema_errors(
    instance: Any,
    schema_path: Path,
    label: str,
) -> list[str]:
    try:
        schema = load_json(schema_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{label}: cannot load schema {schema_path}: {exc}"]
    return [
        f"{label}.{format_json_path(error.absolute_path)}: {error.message}"
        for error in sorted(
            Draft202012Validator(schema).iter_errors(instance),
            key=lambda item: list(item.absolute_path),
        )
    ]


def resolve_path(value: str, repo_root: Path, anchor: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    repo_candidate = repo_root / path
    if repo_candidate.exists():
        return repo_candidate
    return anchor.parent / path


def is_memory_reference(value: str) -> bool:
    lowered = value.replace("\\", "/").lower()
    return (
        "editorial-memory/" in lowered
        or lowered.startswith("memory:")
        or "memory_context_" in lowered
        or "memory_retrieval_report_" in lowered
    )


def evidence_quality_for_current_use(item: dict[str, Any]) -> bool:
    return (
        item.get("evidence_class") in {"fact", "reported_interpretation"}
        and item.get("source_tier") in {"tier_1", "tier_2"}
        and not is_memory_reference(item.get("source_reference", ""))
    )


def flatten_manifest_selected(manifest: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    selected: dict[tuple[str, str], dict[str, Any]] = {}
    for bucket in (
        "current_revalidation_required",
        "historical_context_only",
        "procedural",
    ):
        for item in manifest["memory_intake"][bucket]:
            item = dict(item)
            item["_manifest_bucket"] = bucket
            selected[(item["item_type"], item["item_id"])] = item
    return selected


def validate_file_hash(
    *,
    label: str,
    declared_path: str,
    declared_sha: str,
    repo_root: Path,
    anchor: Path,
    errors: list[str],
) -> Path | None:
    resolved = resolve_path(declared_path, repo_root, anchor)
    if not resolved.is_file():
        errors.append(f"{label}: referenced file does not exist: {declared_path}")
        return None
    actual = sha256_file(resolved)
    if actual != declared_sha:
        errors.append(
            f"{label}: SHA-256 mismatch for {declared_path}: "
            f"declared={declared_sha} actual={actual}"
        )
    return resolved


def validate_dossier(
    dossier_path: Path,
    manifest_path: Path,
    retrieval_report_path: Path,
    *,
    contracts_dir: Path,
    repo_root: Path,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        dossier = load_json(dossier_path)
    except (OSError, json.JSONDecodeError) as exc:
        return ValidationResult([f"dossier: cannot read {dossier_path}: {exc}"], [])
    try:
        manifest = load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        return ValidationResult([f"manifest: cannot read {manifest_path}: {exc}"], [])
    try:
        report = load_json(retrieval_report_path)
    except (OSError, json.JSONDecodeError) as exc:
        return ValidationResult(
            [f"retrieval report: cannot read {retrieval_report_path}: {exc}"], []
        )

    errors.extend(
        schema_errors(
            dossier,
            contracts_dir / "causal_research_dossier_v0.2.schema.json",
            "dossier",
        )
    )
    errors.extend(
        schema_errors(
            manifest,
            contracts_dir / "research_input_manifest.schema.json",
            "manifest",
        )
    )
    report_schema = (
        contracts_dir
        / "../../nasdaq-cafe-editorial-memory/contracts/memory_retrieval_report.schema.json"
    )
    errors.extend(schema_errors(report, report_schema, "retrieval_report"))
    if errors:
        return ValidationResult(errors, warnings)

    if dossier["episode_date"] != manifest["episode_date"]:
        errors.append(
            "episode date mismatch: "
            f"dossier={dossier['episode_date']} manifest={manifest['episode_date']}"
        )
    if dossier["episode_date"] != report["episode_date"]:
        errors.append(
            "episode date mismatch: "
            f"dossier={dossier['episode_date']} report={report['episode_date']}"
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
        anchor=dossier_path,
        errors=errors,
    )
    if resolved_manifest and resolved_manifest.resolve() != manifest_path.resolve():
        errors.append(
            "dossier research_input_manifest path does not resolve to the supplied manifest"
        )

    manifest_inputs = manifest["inputs"]
    resolved_inputs: dict[str, Path | None] = {}
    for label, file_ref in manifest_inputs.items():
        resolved_inputs[label] = validate_file_hash(
            label=f"manifest.inputs.{label}",
            declared_path=file_ref["path"],
            declared_sha=file_ref["sha256"],
            repo_root=repo_root,
            anchor=manifest_path,
            errors=errors,
        )

    resolved_report = resolved_inputs.get("memory_retrieval_report")
    if resolved_report and resolved_report.resolve() != retrieval_report_path.resolve():
        errors.append(
            "manifest memory_retrieval_report path does not resolve to the supplied report"
        )

    selected_from_manifest = flatten_manifest_selected(manifest)
    selected_from_report = {
        (item["item_type"], item["item_id"]): item
        for item in report["selected"]
        if item["item_type"] != "core"
    }

    report_core = [
        item for item in report["selected"] if item["item_type"] == "core"
    ]
    if report_core:
        procedural_core = {
            (item["item_type"], item["item_id"])
            for item in manifest["memory_intake"]["procedural"]
        }
        for core in report_core:
            if ("core", core["item_id"]) not in procedural_core:
                errors.append(
                    f"selected core memory is not classified as procedural: {core['item_id']}"
                )

    manifest_non_core = {
        key: item for key, item in selected_from_manifest.items() if key[0] != "core"
    }
    if set(manifest_non_core) != set(selected_from_report):
        missing = sorted(set(selected_from_report) - set(manifest_non_core))
        extra = sorted(set(manifest_non_core) - set(selected_from_report))
        if missing:
            errors.append(f"manifest omits selected memory: {missing}")
        if extra:
            errors.append(f"manifest contains memory not selected by report: {extra}")

    revalidations = dossier["memory_revalidation"]
    entries: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in revalidations:
        key = (entry["memory_reference_type"], entry["memory_reference_id"])
        if key in entries:
            errors.append(f"duplicate memory revalidation entry: {key}")
        entries[key] = entry

    if set(entries) != set(selected_from_report):
        missing = sorted(set(selected_from_report) - set(entries))
        extra = sorted(set(entries) - set(selected_from_report))
        if missing:
            errors.append(f"selected memory has no revalidation result: {missing}")
        if extra:
            errors.append(f"revalidation references unselected memory: {extra}")

    evidence = {item["evidence_id"]: item for item in dossier["evidence"]}
    if len(evidence) != len(dossier["evidence"]):
        errors.append("duplicate evidence_id in dossier")

    supported_statuses = {
        "supported", "partially_supported", "weakened", "invalidated"
    }
    current_editorial_uses = {
        "research_lead", "comparison", "counterevidence",
        "explanation_context", "monitoring_point"
    }

    for key, entry in entries.items():
        report_item = selected_from_report.get(key)
        manifest_item = manifest_non_core.get(key)
        if not report_item or not manifest_item:
            continue

        if entry["retrieval_use_mode"] != report_item["use_mode"]:
            errors.append(
                f"{key}: retrieval_use_mode differs from retrieval report"
            )
        if entry["historical_confidence"] != report_item.get(
            "historical_confidence", "unknown"
        ):
            errors.append(f"{key}: historical_confidence differs from retrieval report")

        status = entry["revalidation_status"]
        editorial_use = entry["editorial_use"]
        current_ids = entry["current_evidence_ids"]

        if report_item.get("status") in {"invalidated", "resolved"} and status not in {
            "historical_context_only", "not_used"
        }:
            errors.append(
                f"{key}: {report_item.get('status')} memory cannot be a current premise"
            )

        if report_item["use_mode"] == "historical_context" and status not in {
            "historical_context_only", "not_used"
        }:
            errors.append(
                f"{key}: historical-context retrieval cannot be marked {status}"
            )
        if status == "historical_context_only" and report_item[
            "use_mode"
        ] != "historical_context":
            errors.append(
                f"{key}: historical_context_only requires historical_context retrieval"
            )
        if status == "not_used" and editorial_use != "not_used":
            errors.append(f"{key}: not_used status requires editorial_use=not_used")
        if editorial_use == "procedural_only" and report_item[
            "use_mode"
        ] != "procedural":
            errors.append(f"{key}: procedural_only requires procedural retrieval")
        if editorial_use in current_editorial_uses and status in {
            "not_used", "unresolved"
        }:
            errors.append(
                f"{key}: editorial_use={editorial_use} is incompatible with status={status}"
            )
        if (
            status == "historical_context_only"
            and editorial_use not in {"comparison", "explanation_context", "not_used"}
        ):
            errors.append(
                f"{key}: historical_context_only permits only comparison, "
                "explanation_context, or not_used"
            )

        if status in supported_statuses and not current_ids:
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

        if status == "supported":
            if not current_evidence:
                pass
            elif not all(evidence_quality_for_current_use(item) for item in current_evidence):
                errors.append(
                    f"{key}: supported requires tier_1/tier_2 current fact or "
                    "reported interpretation evidence"
                )
        if status in {"weakened", "invalidated"} and not current_evidence:
            errors.append(f"{key}: {status} requires current contrary evidence")
        if (
            report_item.get("requires_current_revalidation")
            and status not in {
                "not_used", "supported", "partially_supported",
                "weakened", "invalidated", "unresolved"
            }
        ):
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
        if any(
            item.get("directness") == "context" for item in current_evidence
        ) and status == "supported":
            warnings.append(f"{key}: supported status includes context-only evidence")

    all_evidence_id_fields: list[tuple[str, list[str]]] = []
    expected_ids = dossier["expected_actual_gap"]["expected"]["evidence_ids"]
    actual_ids = dossier["expected_actual_gap"]["actual"]["evidence_ids"]
    all_evidence_id_fields.append(("expected", expected_ids))
    all_evidence_id_fields.append(("actual", actual_ids))
    for edge in dossier["causal_edges"]:
        all_evidence_id_fields.append((f"causal edge {edge['id']}", edge["evidence_ids"]))
    for item in dossier["timeline"]:
        all_evidence_id_fields.append((f"timeline {item['id']}", item["evidence_ids"]))
    for item in dossier["contrary_evidence"]:
        all_evidence_id_fields.append(("contrary evidence", item["evidence_ids"]))

    for label, ids in all_evidence_id_fields:
        for evidence_id in ids:
            if evidence_id not in evidence:
                errors.append(f"{label}: unknown evidence id {evidence_id}")

    expected_basis = dossier["expected_actual_gap"]["expected"]["basis_class"]
    if expected_basis not in {"unconfirmed", "not_applicable"}:
        if not expected_ids:
            errors.append("Expected is confirmed/classified but has no current evidence")
        elif all(
            evidence_id in evidence
            and is_memory_reference(evidence[evidence_id]["source_reference"])
            for evidence_id in expected_ids
        ):
            errors.append("Expected cannot be grounded only in editorial memory")

    for edge in dossier["causal_edges"]:
        edge_evidence = [
            evidence[evidence_id]
            for evidence_id in edge["evidence_ids"]
            if evidence_id in evidence
        ]
        if edge["scope"] == "nasdaq_wide":
            if not any(evidence_quality_for_current_use(item) for item in edge_evidence):
                errors.append(
                    f"{edge['id']}: NASDAQ-wide edge requires current tier_1/tier_2 evidence"
                )
        if all(
            is_memory_reference(item.get("source_reference", ""))
            for item in edge_evidence
        ):
            errors.append(
                f"{edge['id']}: causal edge cannot be supported only by editorial memory"
            )

    for item in dossier["evidence"]:
        if item["source_tier"] in {"discovery_only", "unavailable"}:
            used_by_supported = any(
                item["evidence_id"] in entry["current_evidence_ids"]
                and entry["revalidation_status"] == "supported"
                for entry in entries.values()
            )
            if used_by_supported:
                errors.append(
                    f"{item['evidence_id']}: discovery-only/unavailable evidence "
                    "cannot support revalidation"
                )

    warnings[:] = sorted(set(warnings))
    errors[:] = sorted(set(errors))
    return ValidationResult(errors, warnings)


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
    payload = result.as_dict()
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    for error in result.errors:
        print(f"ERROR: {error}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("PASS" if result.ok else "FAIL")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
