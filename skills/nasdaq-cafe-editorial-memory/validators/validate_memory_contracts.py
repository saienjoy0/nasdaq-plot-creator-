#!/usr/bin/env python3
"""Validate NASDAQ Cafe editorial-memory schemas and seed files.

This validator checks contract syntax unconditionally. When jsonschema is
installed, it also validates representative fixtures and negative invariants.
It does not validate market causality or certify remembered claims as current.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "skills" / "nasdaq-cafe-editorial-memory" / "contracts"

SCHEMAS = {
    "immutable_episode": CONTRACTS / "immutable_episode.schema.json",
    "temporal_claim": CONTRACTS / "temporal_claim.schema.json",
    "entity_aliases": CONTRACTS / "entity_aliases.schema.json",
    "memory_query_plan": CONTRACTS / "memory_query_plan.schema.json",
    "memory_retrieval_report": CONTRACTS / "memory_retrieval_report.schema.json",
    "memory_promotion_plan": CONTRACTS / "memory_promotion_plan.schema.json",
    "publication_record": CONTRACTS / "publication_record.schema.json",
}

REQUIRED_FILES = [
    ROOT / "editorial-memory" / "memory_policy.md",
    ROOT / "editorial-memory" / "core" / "fox_editorial_state.md",
    ROOT / "editorial-memory" / "entity_aliases.json",
]

HASH = "a" * 64


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sample_documents() -> dict[str, dict[str, Any]]:
    return {
        "immutable_episode": {
            "contract_version": "1.0.0",
            "episode_id": "2026-08-05",
            "episode_date": "2026-08-05",
            "revision": 1,
            "immutable": True,
            "title": "Sample",
            "supersedes": None,
            "approval": {
                "status": "approved_preview",
                "approved_at": "2026-08-05T08:00:00+09:00",
                "approved_by": "user",
                "note": "fixture",
            },
            "source_artifacts": {
                "episode_package": {"path": "episode.md", "sha256": HASH, "bytes": 100},
                "render_spec": {"path": "render.json", "sha256": HASH, "bytes": 100},
                "validator_report": {"path": "validator.json", "sha256": HASH, "bytes": 100},
            },
            "promoted_at": "2026-08-05T09:00:00+09:00",
            "promotion_record_path": "promotion.json",
            "memory_outputs": {"thread_ids": [], "claim_ids": [], "lesson_ids": []},
        },
        "temporal_claim": {
            "contract_version": "2.0.0",
            "claim_id": "ai-capex-evaluation-axis",
            "subject": "AI設備投資",
            "claim": "市場の評価軸は回収速度へ移りつつある",
            "status": "active",
            "confidence": "medium",
            "first_observed_at": "2026-07-10",
            "last_observed_at": "2026-08-05",
            "valid_from": "2026-07-10",
            "valid_to": None,
            "supersedes": None,
            "episode_ids": ["2026-07-10", "2026-08-05"],
            "evidence_paths": ["episodes/2026-08-05/provenance.json"],
            "counter_evidence": [],
            "thread_ids": ["ai-capex-monetization"],
            "entities": ["Microsoft"],
            "topics": ["AI設備投資"],
            "current_use": "premise_after_revalidation",
            "history": [
                {
                    "date": "2026-08-05",
                    "episode_id": "2026-08-05",
                    "status": "active",
                    "confidence": "medium",
                    "reason": "fixture",
                    "evidence_paths": ["episodes/2026-08-05/provenance.json"],
                    "counter_evidence": [],
                }
            ],
        },
        "entity_aliases": {
            "contract_version": "1.0.0",
            "entities": [
                {
                    "entity_id": "microsoft",
                    "canonical_name": "Microsoft",
                    "entity_type": "company",
                    "aliases": ["Microsoft", "MSFT", "マイクロソフト"],
                    "tickers": ["MSFT"],
                    "identifiers": {},
                    "status": "active",
                    "superseded_by": None,
                    "updated_at": "2026-08-05",
                    "source_paths": ["episodes/2026-08-05/provenance.json"],
                }
            ],
        },
        "memory_query_plan": {
            "contract_version": "1.0.0",
            "episode_date": "2026-08-05",
            "lead_candidates": ["AI設備投資"],
            "entities": [
                {
                    "raw": "MSFT",
                    "canonical": "Microsoft",
                    "entity_id": "microsoft",
                    "resolution": "alias",
                }
            ],
            "topics": ["AI設備投資"],
            "technologies": ["データセンター"],
            "policies": [],
            "indicators": ["米10年債利回り"],
            "relations": [
                {"source": "Microsoft", "relation": "invests_in", "target": "データセンター"}
            ],
            "time_window": {"from": "2026-05-01", "to": "2026-08-05"},
            "comparison_questions": ["前回から評価軸は変わったか"],
            "limits": {
                "max_threads": 5,
                "max_claims": 10,
                "max_episodes": 3,
                "max_lessons": 3,
                "max_characters": 12000,
            },
        },
        "memory_retrieval_report": {
            "contract_version": "1.0.0",
            "episode_date": "2026-08-05",
            "query_plan_path": "working/memory_query_plan_2026-08-05.json",
            "selected": [
                {
                    "item_type": "claim",
                    "item_id": "ai-capex-evaluation-axis",
                    "path": "editorial-memory/claim_ledger.json",
                    "score": 18,
                    "reasons": ["entity alias match", "active claim"],
                    "provenance_paths": ["episodes/2026-07-10/provenance.json"],
                    "status": "active",
                    "use_mode": "current_revalidation_required",
                    "requires_current_revalidation": True,
                    "historical_confidence": "medium",
                    "episode_ids": ["2026-07-10"],
                }
            ],
            "rejected": [],
            "limits": {
                "max_threads": 5,
                "max_claims": 10,
                "max_episodes": 3,
                "max_lessons": 3,
                "max_characters": 12000,
            },
            "usage": {"threads": 0, "claims": 1, "episodes": 0, "lessons": 0, "characters": 500},
            "diversity": {
                "distinct_episode_ids": ["2026-07-10"],
                "distinct_thread_ids": [],
                "duplicate_groups_removed": 0,
            },
            "warnings": [],
        },
        "memory_promotion_plan": {
            "contract_version": "1.0.0",
            "episode_id": "2026-08-05",
            "publication_record_path": "publication_record_2026-08-05.json",
            "immutable_episode_path": "editorial-memory/episodes/2026-08-05/publication_record.v1.json",
            "mode": "dry_run",
            "approval": {
                "status": "approved_preview",
                "approved_at": "2026-08-05T08:00:00+09:00",
                "verified": True,
            },
            "source_hashes": {
                "episode_package": HASH,
                "render_spec": HASH,
                "validator_report": HASH,
            },
            "operations": [],
            "conflicts": [],
            "warnings": [],
            "safe_to_apply": True,
            "generated_at": "2026-08-05T09:00:00+09:00",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-jsonschema",
        action="store_true",
        help="Fail when the jsonschema package is unavailable.",
    )
    args = parser.parse_args()

    failures: list[str] = []
    schema_ids: set[str] = set()
    schemas: dict[str, Any] = {}

    for name, path in SCHEMAS.items():
        if not path.exists():
            failures.append(f"missing schema: {path.relative_to(ROOT)}")
            continue
        try:
            schema = load_json(path)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
            continue
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            failures.append(f"missing $id: {path.relative_to(ROOT)}")
        elif schema_id in schema_ids:
            failures.append(f"duplicate $id: {schema_id}")
        else:
            schema_ids.add(schema_id)
        schemas[name] = schema

    for path in REQUIRED_FILES:
        if not path.exists():
            failures.append(f"missing required file: {path.relative_to(ROOT)}")

    alias_seed = ROOT / "editorial-memory" / "entity_aliases.json"
    if alias_seed.exists():
        try:
            load_json(alias_seed)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"invalid seed JSON {alias_seed.relative_to(ROOT)}: {exc}")

    try:
        import jsonschema  # type: ignore
    except ImportError:
        if args.require_jsonschema:
            failures.append("jsonschema package is required but unavailable")
        else:
            print("WARN: jsonschema unavailable; fixture validation skipped")
    else:
        for name, sample in sample_documents().items():
            schema = schemas.get(name)
            if schema is None:
                continue
            try:
                jsonschema.Draft202012Validator.check_schema(schema)
                jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(sample)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"fixture failed for {name}: {exc}")

        alias_schema = schemas.get("entity_aliases")
        if alias_schema is not None and alias_seed.exists():
            try:
                jsonschema.Draft202012Validator(alias_schema).validate(load_json(alias_seed))
            except Exception as exc:  # noqa: BLE001
                failures.append(f"entity alias seed failed schema: {exc}")

        temporal_schema = schemas.get("temporal_claim")
        if temporal_schema is not None:
            invalid = sample_documents()["temporal_claim"]
            invalid["status"] = "invalidated"
            invalid["valid_to"] = None
            invalid["current_use"] = "premise_after_revalidation"
            try:
                jsonschema.Draft202012Validator(
                    temporal_schema,
                    format_checker=jsonschema.FormatChecker(),
                ).validate(invalid)
            except jsonschema.ValidationError:
                pass
            else:
                failures.append("temporal_claim accepted invalidated claim as current premise")

        promotion_schema = schemas.get("memory_promotion_plan")
        if promotion_schema is not None:
            unsafe_apply = sample_documents()["memory_promotion_plan"]
            unsafe_apply["mode"] = "apply"
            unsafe_apply["safe_to_apply"] = False
            unsafe_apply["conflicts"] = [
                {
                    "conflict_id": "c1",
                    "type": "hash_mismatch",
                    "target_id": "2026-08-05",
                    "detail": "fixture",
                    "resolution_required": True,
                }
            ]
            try:
                jsonschema.Draft202012Validator(
                    promotion_schema,
                    format_checker=jsonschema.FormatChecker(),
                ).validate(unsafe_apply)
            except jsonschema.ValidationError:
                pass
            else:
                failures.append("promotion plan accepted unsafe apply with conflicts")

    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        return 1

    print(f"PASS: {len(schemas)} schemas parsed")
    print("PASS: required policy and core-memory files exist")
    print("PASS: seed registry parsed")
    print("PASS: memory contract invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
