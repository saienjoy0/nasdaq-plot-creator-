#!/usr/bin/env python3
"""Compatibility wrapper for the safe two-phase memory promotion flow.

The old direct-write behavior has been removed.  Without ``--apply`` this
command only creates a dry-run plan.  With ``--apply`` it immediately applies
that freshly generated plan after the same safety checks.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from memory_promotion_lib import PromotionError, apply_plan, build_plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--no-commit", action="store_true", help="isolated CI/test use only")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    run_id = args.record.stem.replace("publication_record_", "")
    output = args.output or (repo_root / "working" / "memory-promotion" / run_id)
    contracts = repo_root / "skills" / "nasdaq-cafe-editorial-memory" / "contracts"
    try:
        plan = build_plan(args.record, output, repo_root, contracts)
        print(f"PLAN {output / 'promotion_plan.json'}")
        print(f"SAFE_TO_APPLY {str(plan['safe_to_apply']).lower()}")
        if not args.apply:
            print("DRY_RUN_ONLY true")
            return 0 if plan["safe_to_apply"] else 3
        if not plan["safe_to_apply"]:
            parser.exit(3, "REFUSE: plan contains unresolved conflicts\n")
        report = apply_plan(output / "promotion_plan.json", repo_root, contracts, commit=not args.no_commit)
    except PromotionError as exc:
        parser.exit(2, f"REFUSE: {exc}\n")
    print(f"STATUS {report['status']}")
    if report.get("git_commit"):
        print(f"GIT_COMMIT {report['git_commit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
