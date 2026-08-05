#!/usr/bin/env python3
"""Compatibility wrapper for the auditable editorial-memory retriever."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from editorial_memory_retrieval import DEFAULT_ROOT, retrieve


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Episode date in YYYY-MM-DD")
    parser.add_argument("--topic", action="append", default=[])
    parser.add_argument("--entity", action="append", default=[])
    parser.add_argument("--max-threads", type=int, default=5)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report-output", type=Path)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    topics = [item for item in args.topic if item.strip()]
    entities = [item for item in args.entity if item.strip()]
    lead_candidates = topics or entities or ["editorial memory lookup"]
    plan = {
        "contract_version": "1.0.0",
        "episode_date": args.date,
        "lead_candidates": lead_candidates,
        "entities": [
            {
                "raw": item,
                "canonical": item,
                "entity_id": None,
                "resolution": "unresolved",
            }
            for item in entities
        ],
        "topics": topics,
        "technologies": [],
        "policies": [],
        "indicators": [],
        "relations": [],
        "time_window": {"from": None, "to": args.date},
        "comparison_questions": [],
        "limits": {
            "max_threads": max(0, min(5, args.max_threads)),
            "max_claims": 10,
            "max_episodes": 3,
            "max_lessons": 3,
            "max_characters": 18000,
        },
    }
    plan_path = repo_root / "working" / f"memory_query_plan_{args.date}.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    context_output = args.output or Path(f"working/memory_context_{args.date}.md")
    report_output = args.report_output or Path(
        f"working/memory_retrieval_report_{args.date}.json"
    )
    report = retrieve(
        plan_path,
        context_output,
        report_output,
        repo_root=repo_root,
    )
    print(f"QUERY_PLAN {plan_path.relative_to(repo_root)}")
    print(f"SELECTED_THREADS {report['usage']['threads']}")
    print(f"SELECTED_CLAIMS {report['usage']['claims']}")
    print(f"SELECTED_EPISODES {report['usage']['episodes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
