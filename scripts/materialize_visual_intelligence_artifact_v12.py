#!/usr/bin/env python3
"""Materialize one current Visual Intelligence canonical artifact from semantic input."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import visual_intelligence_artifacts_v12 as artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["requirements", "director", "critic"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    vi = args.root.resolve() / "working" / args.date / "visual-intelligence"
    try:
        if args.stage == "requirements":
            path = artifacts.materialize_requirements(vi_dir=vi, date=args.date)
        elif args.stage == "director":
            path = artifacts.materialize_director(vi_dir=vi, date=args.date)
        else:
            path = artifacts.materialize_critic(vi_dir=vi, date=args.date)
        result = {
            "status": "PASS",
            "episodeDate": args.date,
            "stage": args.stage,
            "path": str(path.relative_to(args.root.resolve())),
            "sha256": artifacts.sha256_file(path),
        }
        code = 0
    except (OSError, artifacts.VisualIntelligenceArtifactError) as exc:
        result = {
            "status": "FAIL",
            "episodeDate": args.date,
            "stage": args.stage,
            "errors": [str(exc)],
        }
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
