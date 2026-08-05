#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from memory_promotion_common import load_json_or, pretty_json

def merge_threads(
    record: Mapping[str, Any],
    memory_root: Path,
    episode_ref: str,
    staged_values: dict[str, bytes],
) -> list[str]:
    index_path = memory_root / "threads" / "index.json"
    index = load_json_or(index_path, {"contract_version": "1.0.0", "threads": []})
    items = index.setdefault("threads", [])
    by_id = {item.get("id"): item for item in items if isinstance(item, dict)}
    generated: list[str] = []

    for update in record.get("thread_updates", []):
        thread_id = update["thread_id"]
        relative = f"editorial-memory/threads/{thread_id}.md"
        source_path = memory_root / "threads" / f"{thread_id}.md"
        if source_path.exists():
            text = source_path.read_text(encoding="utf-8").rstrip()
        else:
            text = (
                f"# {update['title']}\n\n"
                f"## このthreadが答える問い\n\n{update['question']}\n\n"
                f"## 現在の見方\n\n未確定。更新履歴を参照。\n\n"
                f"## 更新履歴\n"
            )
        entry_marker = f"### {record['episode_date']} {episode_ref.split('/')[-1]}"
        if entry_marker not in text:
            text += (
                f"\n{entry_marker}\n\n{update['summary']}\n\n"
                f"- Status: `{update['status']}`\n"
                f"- Claims: {', '.join(update['claim_ids']) if update['claim_ids'] else 'なし'}\n"
                f"- Episode revision: `{episode_ref}`\n"
            )
        staged_values[relative] = (text.rstrip() + "\n").encode("utf-8")
        payload = {
            "id": thread_id,
            "title": update["title"],
            "path": f"threads/{thread_id}.md",
            "triggers": sorted(set(update["triggers"])),
            "entities": sorted(set(update["entities"])),
            "topics": sorted(set(update["topics"])),
            "status": update["status"],
            "updated_at": record["episode_date"],
            "last_episode_revision": episode_ref,
        }
        if thread_id in by_id:
            by_id[thread_id].update(payload)
        else:
            items.append(payload)
            by_id[thread_id] = payload
        generated.append(thread_id)
    items.sort(key=lambda item: str(item.get("id", "")))
    staged_values["editorial-memory/threads/index.json"] = pretty_json(index).encode("utf-8")
    return generated


def merge_claims(
    record: Mapping[str, Any],
    memory_root: Path,
    episode_ref: str,
    provenance_path: str,
    staged_values: dict[str, bytes],
) -> list[str]:
    path = memory_root / "claim_ledger.json"
    ledger = load_json_or(path, {"contract_version": "1.0.0", "claims": []})
    claims = ledger.setdefault("claims", [])
    by_id = {claim.get("claim_id"): claim for claim in claims if isinstance(claim, dict)}
    generated: list[str] = []

    for update in record.get("claim_updates", []):
        claim_id = update["claim_id"]
        existing = by_id.get(claim_id)
        history_item = {
            "date": record["episode_date"],
            "status": update["status"],
            "confidence": update["confidence"],
            "reason": update["reason"],
            "evidence_paths": update["evidence_paths"],
            "episode_revision": episode_ref,
            "provenance_path": provenance_path,
        }
        if existing is None:
            existing = {
                "claim_id": claim_id,
                "subject": update["subject"],
                "claim": update["claim"],
                "status": update["status"],
                "confidence": update["confidence"],
                "first_seen": record["episode_date"],
                "last_updated": record["episode_date"],
                "thread_ids": sorted(set(update["thread_ids"])),
                "entities": sorted(set(update["entities"])),
                "topics": sorted(set(update["topics"])),
                "source_episode_revision": episode_ref,
                "history": [history_item],
            }
            claims.append(existing)
            by_id[claim_id] = existing
        else:
            existing.update(
                {
                    "status": update["status"],
                    "confidence": update["confidence"],
                    "last_updated": record["episode_date"],
                    "thread_ids": sorted(set(existing.get("thread_ids", [])) | set(update["thread_ids"])),
                    "entities": sorted(set(existing.get("entities", [])) | set(update["entities"])),
                    "topics": sorted(set(existing.get("topics", [])) | set(update["topics"])),
                    "source_episode_revision": episode_ref,
                }
            )
            history = existing.setdefault("history", [])
            if not history or history[-1] != history_item:
                history.append(history_item)
        generated.append(claim_id)
    claims.sort(key=lambda item: str(item.get("claim_id", "")))
    staged_values["editorial-memory/claim_ledger.json"] = pretty_json(ledger).encode("utf-8")
    return generated


def merge_aliases(
    record: Mapping[str, Any],
    memory_root: Path,
    episode_ref: str,
    provenance_path: str,
    staged_values: dict[str, bytes],
) -> list[str]:
    path = memory_root / "entity_aliases.json"
    doc = load_json_or(path, {"contract_version": "1.0.0", "entities": []})
    entities = doc.setdefault("entities", [])
    by_id = {
        str(item.get("entity_id", item.get("canonical_id", item.get("id")))): item
        for item in entities
        if isinstance(item, dict) and (item.get("entity_id") or item.get("canonical_id") or item.get("id"))
    }
    generated: list[str] = []
    for update in record.get("alias_updates", []):
        canonical_id = update["canonical_id"]
        existing = by_id.get(canonical_id)
        if existing is None:
            existing = {
                "entity_id": canonical_id,
                "canonical_name": update["display_name"],
                "entity_type": update.get("entity_type", "company"),
                "aliases": sorted(set(update["aliases"])),
                "tickers": [],
                "identifiers": {},
                "status": "active",
                "superseded_by": None,
                "updated_at": record["episode_date"],
                "source_paths": [provenance_path],
            }
            entities.append(existing)
            by_id[canonical_id] = existing
        else:
            existing["canonical_name"] = update["display_name"]
            existing["aliases"] = sorted(set(existing.get("aliases", [])) | set(update["aliases"]))
            existing["updated_at"] = record["episode_date"]
            existing["source_paths"] = sorted(set(existing.get("source_paths", [])) | {provenance_path})
        generated.append(canonical_id)
    entities.sort(key=lambda item: str(item.get("entity_id", item.get("canonical_id", item.get("id", "")))))
    staged_values["editorial-memory/entity_aliases.json"] = pretty_json(doc).encode("utf-8")
    return generated


def merge_lessons(
    record: Mapping[str, Any],
    memory_root: Path,
    episode_ref: str,
    staged_values: dict[str, bytes],
) -> list[str]:
    lessons = [str(item).strip() for item in record.get("production_lessons", []) if str(item).strip()]
    path = memory_root / "production-lessons.md"
    text = path.read_text(encoding="utf-8").rstrip() if path.exists() else "# Production Lessons"
    generated: list[str] = []
    additions: list[str] = []
    for lesson in lessons:
        lesson_id = "lesson-" + hashlib.sha256(lesson.encode("utf-8")).hexdigest()[:12]
        line = f"- `{lesson_id}` [{episode_ref}]: {lesson}"
        if line not in text:
            additions.append(line)
        generated.append(lesson_id)
    if additions:
        text += "\n\n## Promoted lessons\n\n" + "\n".join(additions)
    staged_values["editorial-memory/production-lessons.md"] = (text.rstrip() + "\n").encode("utf-8")
    return generated
