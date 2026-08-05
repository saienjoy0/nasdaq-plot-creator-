#!/usr/bin/env python3
"""Explicitly apply a previously generated safe memory-promotion plan."""

from __future__ import annotations

import argparse
from pathlib import Path

from memory_promotion_lib import PromotionError, apply_plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--apply", action="store_true", help="required acknowledgement")
    parser.add_argument("--no-commit", action="store_true", help="isolated CI/test use only")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if not args.apply:
        parser.exit(2, "REFUSE: --apply is required; no files were changed\n")
    repo_root = args.repo_root.resolve()
    contracts = repo_root / "skills" / "nasdaq-cafe-editorial-memory" / "contracts"
    try:
        report = apply_plan(args.plan, repo_root, contracts, commit=not args.no_commit)
    except PromotionError as exc:
        parser.exit(2, f"REFUSE: {exc}\n")
    print(f"STATUS {report['status']}")
    print(f"REVISION {report['revision']}")
    print(f"CHANGED_PATHS {len(report['changed_paths'])}")
    if report.get("git_commit"):
        print(f"GIT_COMMIT {report['git_commit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
