#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from memory_promotion_common import (
    CONTRACT_VERSION, ArtifactDigest, ConflictError, build_source_fingerprint,
    daily_markdown, episode_summary_markdown, plan_digest, pretty_json,
    repo_relative, resolve_repo_path, staged_operation, utc_now,
    validate_json_schema, write_json, next_revision,
)
from memory_promotion_preflight import source_preflight
from memory_promotion_conflicts import conflict_item, detect_conflicts
from memory_promotion_merge import merge_aliases, merge_claims, merge_lessons, merge_threads

def build_plan(
    record_path: Path,
    output_dir: Path,
    repo_root: Path,
    contracts_dir: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = resolve_repo_path(str(output_dir), repo_root, must_exist=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    staged_root = output_dir / "staged"
    if staged_root.exists():
        shutil.rmtree(staged_root)
    staged_root.mkdir(parents=True)

    record, preflight, resolved_sources = source_preflight(record_path, repo_root, contracts_dir)
    record_digest = ArtifactDigest(**preflight["publication_record"])
    source_fingerprint = build_source_fingerprint(record_digest, preflight["source_artifacts"])
    memory_root = repo_root / "editorial-memory"

    try:
        revision, supersedes, noop_revision, old_index = next_revision(record, memory_root, source_fingerprint)
    except ConflictError as exc:
        conflicts, warnings = detect_conflicts(record, memory_root)
        conflicts.append(
            conflict_item(
                "episode-revision",
                "immutable_episode_exists",
                str(record["episode_date"]),
                str(exc),
            )
        )
        revision, supersedes, noop_revision, old_index = "v000", None, False, None
    else:
        if noop_revision:
            conflicts, warnings = [], []
        else:
            conflicts, warnings = detect_conflicts(record, memory_root)

    conflict_report = {
        "contract_version": CONTRACT_VERSION,
        "episode_date": record["episode_date"],
        "blockers": conflicts,
        "warnings": warnings,
        "unresolved_count": len(conflicts),
        "safe_to_apply": not conflicts,
        "generated_at": utc_now(),
    }
    validate_json_schema(preflight, contracts_dir / "memory_source_preflight.schema.json")
    validate_json_schema(conflict_report, contracts_dir / "memory_conflict_report.schema.json")
    write_json(output_dir / "source_preflight.json", preflight)
    write_json(output_dir / "conflict_report.json", conflict_report)

    staged_values: dict[str, bytes] = {}
    operations: list[dict[str, Any]] = []
    archive_prefix = f"editorial-memory/episodes/{record['episode_date']}/revisions/{revision}"
    provenance_path = f"{archive_prefix}/provenance.json"
    episode_ref = f"{record['episode_date']}/{revision}"

    generated_ids = {"threads": [], "claims": [], "aliases": [], "lessons": []}
    if not conflicts and not noop_revision:
        staged_values[f"{archive_prefix}/publication_record.json"] = pretty_json(record).encode("utf-8")
        staged_values[f"{archive_prefix}/episode_package.md"] = resolved_sources["episode_package"].read_bytes()
        staged_values[f"{archive_prefix}/render_spec.json"] = resolved_sources["render_spec"].read_bytes()
        staged_values[f"{archive_prefix}/validator_report.json"] = resolved_sources["validator_report"].read_bytes()
        staged_values[f"{archive_prefix}/episode_summary.md"] = episode_summary_markdown(record, revision).encode("utf-8")

        generated_ids["threads"] = merge_threads(record, memory_root, episode_ref, staged_values)
        generated_ids["claims"] = merge_claims(record, memory_root, episode_ref, provenance_path, staged_values)
        generated_ids["aliases"] = merge_aliases(record, memory_root, episode_ref, staged_values)
        generated_ids["lessons"] = merge_lessons(record, memory_root, episode_ref, staged_values)

        index = old_index or {
            "contract_version": CONTRACT_VERSION,
            "episode_date": record["episode_date"],
            "revisions": [],
        }
        revisions = index.setdefault("revisions", [])
        revisions.append(
            {
                "revision": revision,
                "source_fingerprint": source_fingerprint,
                "supersedes_revision": supersedes,
                "correction_reason": record.get("correction_reason"),
                "approval_status": record["approval"]["status"],
                "approved_at": record["approval"]["approved_at"],
            }
        )
        index["current_revision"] = revision
        staged_values[f"editorial-memory/episodes/{record['episode_date']}/index.json"] = pretty_json(index).encode("utf-8")
        staged_values[f"editorial-memory/daily/{record['episode_date']}.md"] = daily_markdown(
            record, revision, provenance_path
        ).encode("utf-8")

        provisional_generated_at = utc_now()
        provisional_operations: list[dict[str, Any]] = []
        for relative, data in {**staged_values, provenance_path: b"{}\n"}.items():
            target_type = "episode" if "/episodes/" in relative else (
                "daily" if "/daily/" in relative else (
                    "thread" if "/threads/" in relative else (
                        "claim" if relative.endswith("claim_ledger.json") else (
                            "entity_alias" if relative.endswith("entity_aliases.json") else "lesson"
                        )
                    )
                )
            )
            provisional_operations.append(
                staged_operation(
                    repo_root,
                    relative,
                    data,
                    "update",
                    target_type,
                    episode_ref,
                    [provenance_path],
                )
            )
        provisional_plan = {
            "contract_version": CONTRACT_VERSION,
            "episode_id": record["episode_date"],
            "episode_date": record["episode_date"],
            "revision": revision,
            "publication_record_path": repo_relative(resolve_repo_path(str(record_path), repo_root), repo_root),
            "run_directory": repo_relative(output_dir, repo_root),
            "mode": "apply",
            "execution_state": "planned",
            "approval": {
                "status": record["approval"]["status"],
                "approved_at": record["approval"]["approved_at"],
                "verified": True,
            },
            "source_preflight_path": repo_relative(output_dir / "source_preflight.json", repo_root),
            "conflict_report_path": repo_relative(output_dir / "conflict_report.json", repo_root),
            "source_fingerprint": source_fingerprint,
            "source_hashes": {key: value["sha256"] for key, value in preflight["source_artifacts"].items()},
            "operations": provisional_operations,
            "conflicts": conflicts,
            "warnings": warnings,
            "safe_to_apply": not conflicts,
            "noop": False,
            "generated_at": provisional_generated_at,
        }
        digest = plan_digest(provisional_plan)
        provenance = {
            "contract_version": CONTRACT_VERSION,
            "episode_date": record["episode_date"],
            "revision": revision,
            "supersedes_revision": supersedes,
            "correction_reason": record.get("correction_reason"),
            "approval_status": record["approval"]["status"],
            "approved_at": record["approval"]["approved_at"],
            "promoted_at": provisional_generated_at,
            "source_fingerprint": source_fingerprint,
            "source_artifacts": {
                key: {
                    "original_path": value["path"],
                    "archive_path": f"{archive_prefix}/{ {'episode_package': 'episode_package.md', 'render_spec': 'render_spec.json', 'validator_report': 'validator_report.json'}[key] }",
                    "sha256": value["sha256"],
                    "bytes": value["bytes"],
                }
                for key, value in preflight["source_artifacts"].items()
            },
            "publication_record": preflight["publication_record"],
            "generated_memory_ids": generated_ids,
            "promotion_plan_digest": digest,
        }
        validate_json_schema(provenance, contracts_dir / "immutable_episode.schema.json")
        staged_values[provenance_path] = pretty_json(provenance).encode("utf-8")

    for relative, data in staged_values.items():
        target_type = "episode" if "/episodes/" in relative else (
            "daily" if "/daily/" in relative else (
                "thread" if "/threads/" in relative else (
                    "claim" if relative.endswith("claim_ledger.json") else (
                        "entity_alias" if relative.endswith("entity_aliases.json") else "lesson"
                    )
                )
            )
        )
        operations.append(
            staged_operation(
                repo_root,
                relative,
                data,
                "update",
                target_type,
                episode_ref,
                [provenance_path],
            )
        )
        staged_path = staged_root / relative
        staged_path.parent.mkdir(parents=True, exist_ok=True)
        staged_path.write_bytes(data)

    if noop_revision and not conflicts:
        operations = []

    plan = {
        "contract_version": CONTRACT_VERSION,
        "episode_id": record["episode_date"],
        "episode_date": record["episode_date"],
        "revision": revision,
        "publication_record_path": repo_relative(resolve_repo_path(str(record_path), repo_root), repo_root),
        "run_directory": repo_relative(output_dir, repo_root),
        "mode": "apply",
        "execution_state": "planned",
        "approval": {
            "status": record["approval"]["status"],
            "approved_at": record["approval"]["approved_at"],
            "verified": True,
        },
        "source_preflight_path": repo_relative(output_dir / "source_preflight.json", repo_root),
        "conflict_report_path": repo_relative(output_dir / "conflict_report.json", repo_root),
        "source_fingerprint": source_fingerprint,
        "source_hashes": {key: value["sha256"] for key, value in preflight["source_artifacts"].items()},
        "operations": operations,
        "conflicts": conflicts,
        "warnings": warnings,
        "safe_to_apply": not conflicts,
        "noop": noop_revision,
        "generated_at": utc_now(),
    }
    plan["plan_digest"] = plan_digest(plan)
    validate_json_schema(plan, contracts_dir / "memory_promotion_plan.schema.json")
    write_json(output_dir / "promotion_plan.json", plan)

    report_lines = [
        f"# Memory promotion dry-run｜{record['episode_date']}",
        "",
        f"- Revision: `{revision}`",
        f"- Safe to apply: `{str(not conflicts).lower()}`",
        f"- No-op: `{str(noop_revision).lower()}`",
        f"- Blocking conflicts: `{len(conflicts)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- Planned file operations: `{len([op for op in operations if op['action'] != 'noop'])}`",
        "",
        "このdry-runでは`editorial-memory/`を変更していません。",
    ]
    if conflicts:
        report_lines.extend(["", "## Blockers", ""] + [f"- {item['detail']}" for item in conflicts])
    (output_dir / "dry_run_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return plan

