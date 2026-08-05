#!/usr/bin/env python3
"""Validate memory references used by a final episode package.

This validator is intentionally deterministic. It does not decide whether a
memory should be used or whether the narration is editorially good. It only
checks that every declared memory use is traceable to the validated causal
research dossier and that the public use is permitted by the current
revalidation status.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

EVIDENCE_RE = re.compile(r"^E-[0-9]{3}$")
SCENE_RE = re.compile(r"^scene-0[1-9]$")

ALLOWED_PUBLIC_USAGE: dict[str, set[str]] = {
    "supported": {
        "current_supported_context",
        "historical_comparison",
        "monitoring_point",
        "internal_only",
    },
    "partially_supported": {
        "current_supported_context",
        "historical_comparison",
        "counterevidence",
        "monitoring_point",
        "internal_only",
    },
    "historical_context_only": {"historical_comparison", "internal_only"},
    "weakened": {"counterevidence", "historical_comparison", "internal_only"},
    "invalidated": {"counterevidence", "historical_comparison", "internal_only"},
    "unresolved": {"internal_only"},
    "not_used": {"internal_only"},
}

PUBLIC_MODES = {
    "current_supported_context",
    "historical_comparison",
    "counterevidence",
    "monitoring_point",
}

REQUIRED_REFERENCE_FIELDS = {
    "memory_reference_type",
    "memory_reference_id",
    "historical_confidence",
    "current_revalidation_status",
    "current_evidence_ids",
    "difference_from_previous",
    "editorial_use",
    "scene_ids",
    "public_usage_mode",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON must be an object: {path}")
    return value


def ref_key(item: dict[str, Any]) -> tuple[str, str]:
    return (str(item.get("memory_reference_type", "")), str(item.get("memory_reference_id", "")))


def validate(dossier: dict[str, Any], episode_refs: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if dossier.get("validation", {}).get("status") != "pass":
        errors.append("dossier.validation.status must be pass")

    episode_date = episode_refs.get("episode_date")
    if episode_date != dossier.get("episode_date"):
        errors.append(
            f"episode_date mismatch: references={episode_date!r} dossier={dossier.get('episode_date')!r}"
        )

    references = episode_refs.get("references")
    if not isinstance(references, list):
        errors.append("references must be an array")
        return errors, warnings

    dossier_evidence = dossier.get("evidence", [])
    evidence_ids = {
        item.get("evidence_id")
        for item in dossier_evidence
        if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
    }

    revalidations = dossier.get("memory_revalidation", [])
    if not isinstance(revalidations, list):
        errors.append("dossier.memory_revalidation must be an array")
        revalidations = []

    revalidation_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for index, item in enumerate(revalidations):
        if not isinstance(item, dict):
            errors.append(f"dossier.memory_revalidation[{index}] must be an object")
            continue
        key = ref_key(item)
        if key in revalidation_by_key:
            errors.append(f"duplicate dossier memory revalidation: {key[0]}:{key[1]}")
            continue
        revalidation_by_key[key] = item

    seen: set[tuple[str, str]] = set()
    for index, ref in enumerate(references):
        prefix = f"references[{index}]"
        if not isinstance(ref, dict):
            errors.append(f"{prefix} must be an object")
            continue

        missing = sorted(REQUIRED_REFERENCE_FIELDS - set(ref))
        if missing:
            errors.append(f"{prefix} missing fields: {', '.join(missing)}")
            continue

        key = ref_key(ref)
        if not all(key):
            errors.append(f"{prefix} has empty memory reference identity")
            continue
        if key in seen:
            errors.append(f"duplicate episode memory reference: {key[0]}:{key[1]}")
            continue
        seen.add(key)

        source = revalidation_by_key.get(key)
        if source is None:
            errors.append(f"{prefix} not found in dossier memory_revalidation: {key[0]}:{key[1]}")
            continue

        exact_fields = {
            "historical_confidence": "historical_confidence",
            "current_revalidation_status": "revalidation_status",
            "difference_from_previous": "difference_from_previous",
            "editorial_use": "editorial_use",
        }
        for target_field, source_field in exact_fields.items():
            if ref.get(target_field) != source.get(source_field):
                errors.append(
                    f"{prefix}.{target_field} does not match dossier {source_field}: "
                    f"{ref.get(target_field)!r} != {source.get(source_field)!r}"
                )

        current_ids = ref.get("current_evidence_ids")
        if not isinstance(current_ids, list):
            errors.append(f"{prefix}.current_evidence_ids must be an array")
            current_ids = []
        source_ids = source.get("current_evidence_ids")
        if current_ids != source_ids:
            errors.append(
                f"{prefix}.current_evidence_ids must exactly match dossier order and contents"
            )
        for evidence_id in current_ids:
            if not isinstance(evidence_id, str) or not EVIDENCE_RE.fullmatch(evidence_id):
                errors.append(f"{prefix} has invalid evidence id: {evidence_id!r}")
            elif evidence_id not in evidence_ids:
                errors.append(f"{prefix} references missing dossier evidence: {evidence_id}")

        status = ref.get("current_revalidation_status")
        usage = ref.get("public_usage_mode")
        allowed = ALLOWED_PUBLIC_USAGE.get(str(status), set())
        if usage not in allowed:
            errors.append(
                f"{prefix}.public_usage_mode={usage!r} is not permitted for status={status!r}"
            )

        scene_ids = ref.get("scene_ids")
        if not isinstance(scene_ids, list):
            errors.append(f"{prefix}.scene_ids must be an array")
            scene_ids = []
        if len(scene_ids) != len(set(scene_ids)):
            errors.append(f"{prefix}.scene_ids contains duplicates")
        for scene_id in scene_ids:
            if not isinstance(scene_id, str) or not SCENE_RE.fullmatch(scene_id):
                errors.append(f"{prefix} has invalid scene id: {scene_id!r}")

        if usage in PUBLIC_MODES and not scene_ids:
            errors.append(f"{prefix} public usage requires at least one scene_id")
        if usage == "internal_only" and scene_ids:
            errors.append(f"{prefix} internal_only must not declare public scene_ids")

        if status in {"supported", "partially_supported", "weakened", "invalidated"} and not current_ids:
            errors.append(f"{prefix} status={status} requires current evidence ids")
        if status in {"unresolved", "not_used", "historical_context_only"} and usage == "current_supported_context":
            errors.append(f"{prefix} status={status} cannot be current supported context")
        if status == "not_used" and ref.get("editorial_use") != "not_used":
            errors.append(f"{prefix} not_used status requires editorial_use=not_used")
        if status == "unresolved" and usage != "internal_only":
            errors.append(f"{prefix} unresolved memory cannot be publicly used")
        if status in {"weakened", "invalidated"} and usage == "current_supported_context":
            errors.append(f"{prefix} weakened/invalidated memory cannot support the central current claim")

        if usage == "current_supported_context" and ref.get("editorial_use") not in {
            "explanation_context",
            "comparison",
            "monitoring_point",
        }:
            errors.append(
                f"{prefix} current_supported_context requires an explanatory/comparison/monitoring editorial_use"
            )
        if usage == "counterevidence" and ref.get("editorial_use") != "counterevidence":
            errors.append(f"{prefix} counterevidence public mode requires editorial_use=counterevidence")
        if usage == "monitoring_point" and ref.get("editorial_use") != "monitoring_point":
            errors.append(f"{prefix} monitoring_point public mode requires editorial_use=monitoring_point")

    if not references:
        warnings.append("episode uses no editorial memory; this is allowed")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dossier", required=True, type=Path)
    parser.add_argument("--episode-memory-references", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    try:
        dossier = load_json(args.dossier)
        refs = load_json(args.episode_memory_references)
        errors, warnings = validate(dossier, refs)
    except ValueError as exc:
        errors, warnings = [str(exc)], []

    result = {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "warnings": warnings,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
