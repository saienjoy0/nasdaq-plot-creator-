#!/usr/bin/env python3
"""Materialize Visual-independent editorial context before AI-B requirements."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import financial_candidate_provider
import visual_intelligence_bridge


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-spec", required=True, type=Path)
    parser.add_argument("--date", required=True)
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.output_root.resolve()
    render = json.loads(args.render_spec.read_text(encoding="utf-8"))
    if render.get("episode", {}).get("targetDate") != args.date:
        raise SystemExit("editorial context render episodeDate mismatch")
    directory = root / "working" / args.date / "visual-intelligence"
    editorial_path = directory / "editorial_snapshot.json"
    financial_path = directory / "financial_candidate_provider.json"
    visual_intelligence_bridge.write_json(
        editorial_path,
        visual_intelligence_bridge.build_editorial_snapshot(render),
    )
    financial_candidate_provider.write(financial_path, financial_candidate_provider.build(render))
    result = {
        "status": "PASS",
        "episodeDate": args.date,
        "editorialSnapshot": str(editorial_path),
        "editorialSnapshotSha256": sha256_file(editorial_path),
        "financialCandidateProvider": str(financial_path),
        "financialCandidateProviderSha256": sha256_file(financial_path),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
