#!/usr/bin/env python3
"""Promote an approved NASDAQ Cafe publication record into durable memory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "editorial-memory"
DEFAULT_SCHEMA = (
    ROOT
    / "skills"
    / "nasdaq-cafe-editorial-memory"
    / "contracts"
    / "publication_record.schema.json"
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate(record: Any, schema_path: Path) -> None:
    if not isinstance(record, dict):
        raise ValueError("publication record root must be an object")
    try:
        import jsonschema  # type: ignore
    except ImportError:
        required = {
            "contract_version",
            "episode_date",
            "title",
            "main_story",
            "story_spine",
            "central_hypothesis",
            "source_paths",
            "approval",
        }
        missing = sorted(required - set(record))
        if missing:
            raise ValueError("missing required keys: " + ", ".join(missing))
    else:
        schema = load_json(schema_path)
        jsonschema.Draft202012Validator(schema).validate(record)

    approval = record.get("approval", {})
    if not isinstance(approval, dict) or approval.get("status") not in {
        "approved_preview",
        "published",
    }:
        raise ValueError("memory promotion requires approved_preview or published status")


def daily_markdown(record: dict[str, Any]) -> str:
    hypothesis = record["central_hypothesis"]
    contrary = record.get("contrary_evidence", [])
    watch_next = record.get("watch_next", [])
    thread_ids = [item["thread_id"] for item in record.get("thread_updates", [])]
    claim_ids = [item["claim_id"] for item in record.get("claim_updates", [])]
    sources = record["source_paths"]

    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "- なし"

    return f"""# {record['episode_date']}｜{record['title']}

## 主役

{record['main_story']}

## ストーリーの背骨

{record['story_spine']}

## 中心仮説

- 仮説：{hypothesis['text']}
- 確信度：{hypothesis['confidence']}

## 重要な反対材料

{bullets(contrary)}

## 次に見る点

{bullets(watch_next)}

## 更新した記憶

- Threads: {', '.join(thread_ids) if thread_ids else 'なし'}
- Claims: {', '.join(claim_ids) if claim_ids else 'なし'}

## 正式成果物

- Episode package: `{sources['episode_package']}`
- Render spec: `{sources['render_spec']}`
- Validator report: `{sources['validator_report']}`
- Approval: `{record['approval']['status']}` at `{record['approval']['approved_at']}`
"""


def update_threads(record: dict[str, Any]) -> None:
    index_path = MEMORY / "threads" / "index.json"
    index = load_json(index_path) if index_path.exists() else {"contract_version": "1.0.0", "threads": []}
    items = index.setdefault("threads", [])
    by_id = {
        item.get("id"): item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    for update in record.get("thread_updates", []):
        thread_id = update["thread_id"]
        relative_path = f"threads/{thread_id}.md"
        path = MEMORY / relative_path
        if path.exists():
            text = path.read_text(encoding="utf-8").rstrip()
        else:
            text = (
                f"# {update['title']}\n\n"
                f"## このthreadが答える問い\n\n{update['question']}\n\n"
                f"## 現在の見方\n\n未確定。更新履歴を参照。\n\n"
                f"## 更新履歴\n"
            )
        text += (
            f"\n### {record['episode_date']}\n\n"
            f"{update['summary']}\n\n"
            f"- Status: `{update['status']}`\n"
            f"- Claims: {', '.join(update['claim_ids']) if update['claim_ids'] else 'なし'}\n"
            f"- Episode: `{record['source_paths']['episode_package']}`\n"
        )
        path.write_text(text.rstrip() + "\n", encoding="utf-8")

        entry = by_id.get(thread_id)
        payload = {
            "id": thread_id,
            "title": update["title"],
            "path": relative_path,
            "triggers": sorted(set(update["triggers"])),
            "entities": sorted(set(update["entities"])),
            "topics": sorted(set(update["topics"])),
            "status": update["status"],
            "updated_at": record["episode_date"],
        }
        if entry is None:
            items.append(payload)
            by_id[thread_id] = payload
        else:
            entry.update(payload)

    items.sort(key=lambda item: str(item.get("id", "")))
    write_json(index_path, index)


def update_claims(record: dict[str, Any]) -> None:
    path = MEMORY / "claim_ledger.json"
    ledger = load_json(path) if path.exists() else {"contract_version": "1.0.0", "claims": []}
    claims = ledger.setdefault("claims", [])
    by_id = {
        claim.get("claim_id"): claim
        for claim in claims
        if isinstance(claim, dict) and isinstance(claim.get("claim_id"), str)
    }

    for update in record.get("claim_updates", []):
        claim_id = update["claim_id"]
        existing = by_id.get(claim_id)
        history_item = {
            "date": record["episode_date"],
            "status": update["status"],
            "confidence": update["confidence"],
            "reason": update["reason"],
            "evidence_paths": update["evidence_paths"],
            "episode_package": record["source_paths"]["episode_package"],
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
                "history": [history_item],
            }
            claims.append(existing)
            by_id[claim_id] = existing
        else:
            existing.update(
                {
                    "subject": update["subject"],
                    "claim": update["claim"],
                    "status": update["status"],
                    "confidence": update["confidence"],
                    "last_updated": record["episode_date"],
                    "thread_ids": sorted(set(existing.get("thread_ids", [])) | set(update["thread_ids"])),
                    "entities": sorted(set(existing.get("entities", [])) | set(update["entities"])),
                    "topics": sorted(set(existing.get("topics", [])) | set(update["topics"])),
                }
            )
            existing.setdefault("history", []).append(history_item)

    claims.sort(key=lambda item: str(item.get("claim_id", "")))
    write_json(path, ledger)


def update_lessons(record: dict[str, Any]) -> None:
    lessons = [item.strip() for item in record.get("production_lessons", []) if item.strip()]
    if not lessons:
        return
    path = MEMORY / "production-lessons.md"
    text = path.read_text(encoding="utf-8").rstrip() if path.exists() else "# Production Lessons"
    existing = set(text.splitlines())
    additions = [f"- {record['episode_date']}: {lesson}" for lesson in lessons]
    additions = [item for item in additions if item not in existing]
    if additions:
        text += "\n\n## Promoted lessons\n\n" + "\n".join(additions)
        path.write_text(text.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--replace-daily", action="store_true")
    args = parser.parse_args()

    record = load_json(args.record)
    validate(record, args.schema)

    daily_path = MEMORY / "daily" / f"{record['episode_date']}.md"
    if daily_path.exists() and not args.replace_daily:
        raise SystemExit(f"REFUSE: daily memory already exists: {daily_path.relative_to(ROOT)}")
    daily_path.parent.mkdir(parents=True, exist_ok=True)
    daily_path.write_text(daily_markdown(record), encoding="utf-8")

    update_threads(record)
    update_claims(record)
    update_lessons(record)

    print(f"WROTE {daily_path.relative_to(ROOT)}")
    print(f"UPDATED_THREADS {len(record.get('thread_updates', []))}")
    print(f"UPDATED_CLAIMS {len(record.get('claim_updates', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
