#!/usr/bin/env python3
"""Validate editorial-memory schemas, fixtures, seeds, and safety invariants.

This validator checks storage contracts only. It never decides market causality,
which hypotheses should be promoted, or whether a remembered claim is currently
true.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "skills" / "nasdaq-cafe-editorial-memory" / "contracts"
REQUIRED_FILES = [
    ROOT / "editorial-memory" / "memory_policy.md",
    ROOT / "editorial-memory" / "core" / "fox_editorial_state.md",
    ROOT / "editorial-memory" / "entity_aliases.json",
]
HASH = "a" * 64


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def samples() -> dict[str, dict[str, Any]]:
    artifact = {"path": "production/file.json", "sha256": HASH, "bytes": 100}
    source_artifact = {
        "original_path": "production/file.json",
        "archive_path": "editorial-memory/episodes/2026-08-05/revisions/v001/file.json",
        "sha256": HASH,
        "bytes": 100,
    }
    blocker = {
        "conflict_id": "c1",
        "severity": "blocker",
        "type": "hash_mismatch",
        "target_id": "2026-08-05",
        "detail": "fixture",
        "resolution_required": True,
    }
    publication = {
        "contract_version": "1.0.0",
        "episode_date": "2026-08-05",
        "title": "Sample",
        "main_story": "Sample story",
        "story_spine": "Sample spine",
        "central_hypothesis": {"text": "Sample hypothesis", "confidence": "medium"},
        "contrary_evidence": [],
        "watch_next": [],
        "topics": [],
        "entities": [],
        "thread_updates": [],
        "claim_updates": [],
        "alias_updates": [],
        "production_lessons": [],
        "source_paths": {
            "episode_package": "production/episode.md",
            "render_spec": "render-specs/2026-08-05/render_spec.json",
            "validator_report": "production/validator.json",
        },
        "approval": {"status": "approved_preview", "approved_at": "2026-08-05T08:00:00Z"},
    }
    promotion_plan = {
        "contract_version": "2.0.0",
        "episode_id": "2026-08-05",
        "episode_date": "2026-08-05",
        "revision": "v001",
        "publication_record_path": "production/publication_record_2026-08-05.json",
        "run_directory": "working/memory-promotion/2026-08-05",
        "mode": "apply",
        "execution_state": "planned",
        "approval": {"status": "approved_preview", "approved_at": "2026-08-05T08:00:00Z", "verified": True},
        "source_preflight_path": "working/memory-promotion/2026-08-05/source_preflight.json",
        "conflict_report_path": "working/memory-promotion/2026-08-05/conflict_report.json",
        "source_fingerprint": HASH,
        "source_hashes": {"episode_package": HASH, "render_spec": HASH, "validator_report": HASH},
        "operations": [],
        "conflicts": [],
        "warnings": [],
        "safe_to_apply": True,
        "noop": True,
        "generated_at": "2026-08-05T09:00:00Z",
        "plan_digest": HASH,
    }
    return {
        "publication_record.schema.json": publication,
        "immutable_episode.schema.json": {
            "contract_version": "2.0.0",
            "episode_date": "2026-08-05",
            "revision": "v001",
            "supersedes_revision": None,
            "correction_reason": None,
            "approval_status": "approved_preview",
            "approved_at": "2026-08-05T08:00:00Z",
            "promoted_at": "2026-08-05T09:00:00Z",
            "source_fingerprint": HASH,
            "source_artifacts": {
                "episode_package": source_artifact,
                "render_spec": source_artifact,
                "validator_report": source_artifact,
            },
            "publication_record": artifact,
            "generated_memory_ids": {"threads": [], "claims": [], "aliases": [], "lessons": []},
            "promotion_plan_digest": HASH,
        },
        "memory_source_preflight.schema.json": {
            "contract_version": "2.0.0",
            "status": "pass",
            "episode_date": "2026-08-05",
            "approval_status": "approved_preview",
            "publication_record": artifact,
            "source_artifacts": {
                "episode_package": artifact,
                "render_spec": artifact,
                "validator_report": artifact,
            },
            "checks": {"approval": "pass"},
            "generated_at": "2026-08-05T09:00:00Z",
        },
        "memory_conflict_report.schema.json": {
            "contract_version": "2.0.0",
            "episode_date": "2026-08-05",
            "blockers": [],
            "warnings": [],
            "unresolved_count": 0,
            "safe_to_apply": True,
            "generated_at": "2026-08-05T09:00:00Z",
        },
        "memory_promotion_plan.schema.json": promotion_plan,
        "memory_promotion_report.schema.json": {
            "contract_version": "2.0.0",
            "status": "applied",
            "episode_date": "2026-08-05",
            "revision": "v001",
            "plan_digest": HASH,
            "changed_paths": ["editorial-memory/daily/2026-08-05.md"],
            "git_commit": "a" * 40,
            "applied_at": "2026-08-05T09:00:00Z",
        },
        "temporal_claim.schema.json": {
            "contract_version": "2.0.0",
            "claim_id": "ai-capex-evaluation-axis",
            "subject": "AI設備投資",
            "claim": "市場は回収経路も評価する",
            "status": "active",
            "confidence": "medium",
            "first_observed_at": "2026-08-05",
            "last_observed_at": "2026-08-05",
            "valid_from": "2026-08-05",
            "valid_to": None,
            "supersedes": None,
            "episode_ids": ["2026-08-05"],
            "evidence_paths": ["editorial-memory/episodes/2026-08-05/revisions/v001/provenance.json"],
            "counter_evidence": [],
            "thread_ids": [],
            "entities": [],
            "topics": [],
            "current_use": "premise_after_revalidation",
            "history": [{
                "date": "2026-08-05",
                "episode_id": "2026-08-05",
                "status": "active",
                "confidence": "medium",
                "reason": "fixture",
                "evidence_paths": ["editorial-memory/episodes/2026-08-05/revisions/v001/provenance.json"],
                "counter_evidence": [],
            }],
        },
        "entity_aliases.schema.json": {
            "contract_version": "1.0.0",
            "entities": [{
                "entity_id": "microsoft",
                "canonical_name": "Microsoft",
                "entity_type": "company",
                "aliases": ["Microsoft", "MSFT"],
                "tickers": ["MSFT"],
                "identifiers": {},
                "status": "active",
                "superseded_by": None,
                "updated_at": "2026-08-05",
                "source_paths": ["editorial-memory/episodes/2026-08-05/revisions/v001/provenance.json"],
            }],
        },
        "_blocker": blocker,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-jsonschema", action="store_true")
    args = parser.parse_args()
    failures: list[str] = []
    schemas: dict[str, Any] = {}
    ids: set[str] = set()

    for path in sorted(CONTRACTS.glob("*.schema.json")):
        try:
            schema = load_json(path)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
            continue
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            failures.append(f"missing $id: {path.relative_to(ROOT)}")
        elif schema_id in ids:
            failures.append(f"duplicate $id: {schema_id}")
        else:
            ids.add(schema_id)
        schemas[path.name] = schema

    for path in REQUIRED_FILES:
        if not path.exists():
            failures.append(f"missing required file: {path.relative_to(ROOT)}")

    try:
        import jsonschema  # type: ignore
    except ImportError:
        if args.require_jsonschema:
            failures.append("jsonschema package is required but unavailable")
    else:
        fixture_set = samples()
        for name, schema in schemas.items():
            try:
                jsonschema.Draft202012Validator.check_schema(schema)
                sample = fixture_set.get(name)
                if sample is not None:
                    jsonschema.Draft202012Validator(
                        schema, format_checker=jsonschema.FormatChecker()
                    ).validate(sample)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"fixture failed for {name}: {exc}")

        # Publication 1.1 Temporal contract must remain additive and backward-readable.
        if "publication_record.schema.json" in schemas:
            legacy_publication = copy.deepcopy(fixture_set["publication_record.schema.json"])
            temporal_publication = copy.deepcopy(legacy_publication)
            temporal_publication["contract_version"] = "1.1.0"
            temporal_publication["temporal_evidence"] = {
                "carryover_results": [],
                "validation_obligations": [],
            }
            try:
                publication_validator = jsonschema.Draft202012Validator(
                    schemas["publication_record.schema.json"],
                    format_checker=jsonschema.FormatChecker(),
                )
                publication_validator.validate(legacy_publication)
                publication_validator.validate(temporal_publication)
                missing_temporal = copy.deepcopy(temporal_publication)
                missing_temporal.pop("temporal_evidence")
                if not list(publication_validator.iter_errors(missing_temporal)):
                    failures.append("publication 1.1 accepted missing temporal_evidence")
            except Exception as exc:  # noqa: BLE001
                failures.append(f"publication temporal compatibility fixture failed: {exc}")

        alias_seed = ROOT / "editorial-memory" / "entity_aliases.json"
        if alias_seed.exists() and "entity_aliases.schema.json" in schemas:
            try:
                jsonschema.Draft202012Validator(schemas["entity_aliases.schema.json"]).validate(load_json(alias_seed))
            except Exception as exc:  # noqa: BLE001
                failures.append(f"entity alias seed failed schema: {exc}")

        temporal = copy.deepcopy(fixture_set["temporal_claim.schema.json"])
        temporal.update({"status": "invalidated", "valid_to": None, "current_use": "premise_after_revalidation"})
        try:
            jsonschema.Draft202012Validator(schemas["temporal_claim.schema.json"]).validate(temporal)
        except jsonschema.ValidationError:
            pass
        else:
            failures.append("temporal claim accepted invalidated claim as current premise")

        unsafe = copy.deepcopy(fixture_set["memory_promotion_plan.schema.json"])
        unsafe.update({"noop": False, "safe_to_apply": True, "conflicts": [fixture_set["_blocker"]]})
        try:
            jsonschema.Draft202012Validator(schemas["memory_promotion_plan.schema.json"]).validate(unsafe)
        except jsonschema.ValidationError:
            pass
        else:
            failures.append("promotion plan accepted safe_to_apply=true with blockers")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(f"PASS: {len(schemas)} schemas parsed")
    print("PASS: representative v1/v2 fixtures")
    print("PASS: required policy, core-memory, and seed files")
    print("PASS: memory safety invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
