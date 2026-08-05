#!/usr/bin/env python3
"""Build a selective editorial-memory context for a NASDAQ Cafe episode."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEMORY_ROOT = ROOT / "editorial-memory"


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def read_optional(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def safe_memory_path(relative_path: str) -> Path:
    candidate = (MEMORY_ROOT / relative_path).resolve()
    root = MEMORY_ROOT.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"memory path escapes editorial-memory: {relative_path}")
    return candidate


def as_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def score_thread(thread: dict[str, Any], needles: set[str]) -> int:
    fields: list[tuple[int, list[str]]] = [
        (5, as_strings(thread.get("entities"))),
        (4, as_strings(thread.get("triggers"))),
        (3, as_strings(thread.get("topics"))),
        (2, [str(thread.get("title", "")), str(thread.get("id", ""))]),
    ]
    score = 0
    for weight, values in fields:
        for raw in values:
            value = normalize(raw)
            if not value:
                continue
            if any(needle == value or needle in value or value in needle for needle in needles):
                score += weight
    return score


def score_claim(claim: dict[str, Any], needles: set[str], selected_threads: set[str]) -> int:
    score = 0
    values = [
        str(claim.get("subject", "")),
        str(claim.get("claim", "")),
        *as_strings(claim.get("entities")),
        *as_strings(claim.get("topics")),
        *as_strings(claim.get("tags")),
    ]
    for raw in values:
        value = normalize(raw)
        if value and any(needle == value or needle in value or value in needle for needle in needles):
            score += 2
    if selected_threads.intersection(as_strings(claim.get("thread_ids"))):
        score += 5
    return score


def render_section(title: str, source: str, content: str | None) -> str:
    if not content:
        return f"## {title}\n\n該当記録なし。\n"
    return f"## {title}\n\nSource: `{source}`\n\n{content}\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Episode date in YYYY-MM-DD")
    parser.add_argument("--topic", action="append", default=[])
    parser.add_argument("--entity", action="append", default=[])
    parser.add_argument("--max-threads", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    episode_date = date.fromisoformat(args.date)
    needles = {
        normalize(item)
        for item in [*args.topic, *args.entity]
        if isinstance(item, str) and normalize(item)
    }

    previous_date = episode_date - timedelta(days=1)
    iso_year, iso_week, _ = episode_date.isocalendar()

    active_path = MEMORY_ROOT / "active_context.md"
    daily_path = MEMORY_ROOT / "daily" / f"{previous_date.isoformat()}.md"
    weekly_path = MEMORY_ROOT / "weekly" / f"{iso_year}-W{iso_week:02d}.md"
    lessons_path = MEMORY_ROOT / "production-lessons.md"

    index = load_json(MEMORY_ROOT / "threads" / "index.json", {"threads": []})
    threads = index.get("threads", []) if isinstance(index, dict) else []
    ranked: list[tuple[int, str, dict[str, Any]]] = []
    for item in threads if isinstance(threads, list) else []:
        if not isinstance(item, dict) or item.get("status") == "archived":
            continue
        score = score_thread(item, needles)
        if score > 0:
            ranked.append((score, str(item.get("updated_at", "")), item))
    ranked.sort(key=lambda row: (row[0], row[1]), reverse=True)
    selected = [item for _, _, item in ranked[: max(0, args.max_threads)]]
    selected_thread_ids = {
        str(item.get("id")) for item in selected if isinstance(item.get("id"), str)
    }

    ledger = load_json(MEMORY_ROOT / "claim_ledger.json", {"claims": []})
    claims = ledger.get("claims", []) if isinstance(ledger, dict) else []
    selected_claims: list[tuple[int, dict[str, Any]]] = []
    for claim in claims if isinstance(claims, list) else []:
        if not isinstance(claim, dict):
            continue
        score = score_claim(claim, needles, selected_thread_ids)
        if score > 0:
            selected_claims.append((score, claim))
    selected_claims.sort(
        key=lambda row: (row[0], str(row[1].get("last_updated", ""))),
        reverse=True,
    )

    sections = [
        "# 朝のNASDAQカフェ｜Selected Memory Context",
        "",
        f"Episode date: `{episode_date.isoformat()}`",
        f"Topics: {', '.join(args.topic) if args.topic else '未指定'}",
        f"Entities: {', '.join(args.entity) if args.entity else '未指定'}",
        "",
        "> このファイルは過去記録の選択結果です。現在の事実を証明する資料ではありません。",
        "",
        render_section("Active context", str(active_path.relative_to(ROOT)), read_optional(active_path)),
        render_section("Previous day", str(daily_path.relative_to(ROOT)), read_optional(daily_path)),
        render_section("Current week", str(weekly_path.relative_to(ROOT)), read_optional(weekly_path)),
    ]

    sections.append("## Relevant topic threads\n")
    if not selected:
        sections.append("該当threadなし。\n")
    else:
        for item in selected:
            relative = item.get("path")
            if not isinstance(relative, str):
                continue
            path = safe_memory_path(relative)
            content = read_optional(path)
            sections.append(
                f"### {item.get('title') or item.get('id')}\n\n"
                f"Source: `{path.relative_to(ROOT)}`\n\n"
                f"{content or '記録本文なし。'}\n"
            )

    sections.append("## Relevant claims\n")
    if not selected_claims:
        sections.append("該当claimなし。\n")
    else:
        for _, claim in selected_claims[:10]:
            sections.append(
                "- "
                f"`{claim.get('claim_id', '?')}` "
                f"[{claim.get('status', 'unknown')}] "
                f"{claim.get('claim', '')} "
                f"(updated: {claim.get('last_updated', 'unknown')})"
            )
        sections.append("")

    sections.append(
        render_section(
            "Reusable production lessons",
            str(lessons_path.relative_to(ROOT)),
            read_optional(lessons_path),
        )
    )

    output = args.output or ROOT / "working" / f"memory_context_{episode_date.isoformat()}.md"
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(sections).rstrip() + "\n", encoding="utf-8")
    print(f"WROTE {output.relative_to(ROOT) if ROOT in output.parents else output}")
    print(f"SELECTED_THREADS {len(selected)}")
    print(f"SELECTED_CLAIMS {min(len(selected_claims), 10)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
