#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from memory_promotion_common import CLAIM_TRANSITIONS, CONFIDENCE_ORDER, read_json

def read_thread_question(path: Path) -> str | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    marker = "## このthreadが答える問い"
    if marker not in text:
        return None
    tail = text.split(marker, 1)[1].lstrip()
    lines: list[str] = []
    for line in tail.splitlines():
        if line.startswith("## "):
            break
        if line.strip():
            lines.append(line.strip())
    return " ".join(lines) or None


def conflict_item(conflict_id: str, kind: str, target_id: str, detail: str) -> dict[str, Any]:
    return {
        "conflict_id": conflict_id,
        "severity": "blocker",
        "type": kind,
        "target_id": target_id,
        "detail": detail,
        "resolution_required": True,
    }


def warning_item(warning_id: str, kind: str, target_id: str, detail: str) -> dict[str, Any]:
    return {
        "warning_id": warning_id,
        "severity": "warning",
        "type": kind,
        "target_id": target_id,
        "detail": detail,
    }


def detect_conflicts(record: Mapping[str, Any], memory_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    conflicts: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    ledger_path = memory_root / "claim_ledger.json"
    ledger = read_json(ledger_path) if ledger_path.exists() else {"claims": []}
    existing_claims = {
        item.get("claim_id"): item
        for item in ledger.get("claims", [])
        if isinstance(item, Mapping) and isinstance(item.get("claim_id"), str)
    }
    for update in record.get("claim_updates", []):
        if not isinstance(update, Mapping):
            continue
        claim_id = str(update["claim_id"])
        existing = existing_claims.get(claim_id)
        if existing is None:
            continue
        if existing.get("claim") != update.get("claim") or existing.get("subject") != update.get("subject"):
            conflicts.append(
                conflict_item(
                    f"claim-identity-{claim_id}",
                    "claim_identity_collision",
                    claim_id,
                    "existing claim ID refers to different subject or claim text",
                )
            )
            continue
        old_status = str(existing.get("status", "unknown"))
        new_status = str(update.get("status", "unknown"))
        if new_status not in CLAIM_TRANSITIONS.get(old_status, set()):
            conflicts.append(
                conflict_item(
                    f"claim-transition-{claim_id}",
                    "status_regression",
                    claim_id,
                    f"claim status transition {old_status} -> {new_status} is not permitted",
                )
            )
        old_conf = str(existing.get("confidence", "unknown"))
        new_conf = str(update.get("confidence", "unknown"))
        if abs(CONFIDENCE_ORDER.get(old_conf, 0) - CONFIDENCE_ORDER.get(new_conf, 0)) >= 2:
            warnings.append(
                warning_item(
                    f"claim-confidence-{claim_id}",
                    "confidence_jump",
                    claim_id,
                    f"confidence changes by two or more levels: {old_conf} -> {new_conf}",
                )
            )

    aliases_path = memory_root / "entity_aliases.json"
    aliases_doc = read_json(aliases_path) if aliases_path.exists() else {"entities": []}
    alias_owner: dict[str, str] = {}
    for entity in aliases_doc.get("entities", []):
        if not isinstance(entity, Mapping):
            continue
        canonical = str(entity.get("entity_id", entity.get("canonical_id", entity.get("id", ""))))
        for alias in entity.get("aliases", []):
            if isinstance(alias, str):
                alias_owner[alias.casefold()] = canonical
    for update in record.get("alias_updates", []):
        if not isinstance(update, Mapping):
            continue
        canonical = str(update.get("canonical_id", ""))
        for alias in update.get("aliases", []):
            if not isinstance(alias, str):
                continue
            owner = alias_owner.get(alias.casefold())
            if owner and owner != canonical:
                conflicts.append(
                    conflict_item(
                        f"alias-{hashlib.sha1(alias.casefold().encode()).hexdigest()[:12]}",
                        "alias_collision",
                        alias,
                        f"alias already belongs to canonical entity {owner}, not {canonical}",
                    )
                )

    thread_index_path = memory_root / "threads" / "index.json"
    thread_index = read_json(thread_index_path) if thread_index_path.exists() else {"threads": []}
    existing_threads = {
        item.get("id"): item
        for item in thread_index.get("threads", [])
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    for update in record.get("thread_updates", []):
        if not isinstance(update, Mapping):
            continue
        thread_id = str(update["thread_id"])
        existing = existing_threads.get(thread_id)
        if existing is None:
            continue
        path = memory_root / str(existing.get("path", f"threads/{thread_id}.md"))
        old_question = read_thread_question(path)
        if old_question and old_question != update.get("question"):
            conflicts.append(
                conflict_item(
                    f"thread-question-{thread_id}",
                    "thread_identity_collision",
                    thread_id,
                    "existing thread ID is being reused for a different question",
                )
            )
        elif existing.get("title") != update.get("title"):
            warnings.append(
                warning_item(
                    f"thread-title-{thread_id}",
                    "thread_title_changed",
                    thread_id,
                    "thread title changes while the question remains the same",
                )
            )

    return conflicts, warnings
