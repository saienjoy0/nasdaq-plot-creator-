#!/usr/bin/env python3
"""Build a safe, non-mutating memory-promotion plan."""

from __future__ import annotations

import argparse
from pathlib import Path

from memory_promotion_lib import PromotionError, build_plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path, help="approved publication_record JSON")
    parser.add_argument("--output", type=Path, required=True, help="working/memory-promotion/<run_id>")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    contracts = repo_root / "skills" / "nasdaq-cafe-editorial-memory" / "contracts"
    try:
        plan = build_plan(args.record, args.output, repo_root, contracts)
    except PromotionError as exc:
        parser.exit(2, f"REFUSE: {exc}\n")
    print(f"PLAN {args.output / 'promotion_plan.json'}")
    print(f"SAFE_TO_APPLY {str(plan['safe_to_apply']).lower()}")
    print(f"NOOP {str(plan['noop']).lower()}")
    print(f"OPERATIONS {len(plan['operations'])}")
    return 0 if plan["safe_to_apply"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
