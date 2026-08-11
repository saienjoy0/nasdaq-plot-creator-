#!/usr/bin/env python3
"""Compatibility wrapper for the revised 2026-08-10 Interest fixture.

The base Interest materializer owns editorial meaning. This wrapper only aligns the
Scene 3 NASDAQ-support fact with the existing bundle validator by attaching the
already-authorized Reuters/NASDAQ-wide evidence E-004 alongside the direct price
snapshot E-001. It adds no fact or causal meaning.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

BASE = Path(__file__).with_name("materialize_revised_interest_fixture.py")


def load_base():
    spec = importlib.util.spec_from_file_location("interest_fixture_base", BASE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def materialize(root: Path) -> dict:
    base = load_base()
    result = dict(base.materialize(root))
    script_path = root / f"working/{base.DATE}/story-engine/templates/story_script.template.json"
    script = base.load(script_path)
    scene = next(row for row in script["scenes"] if row["scene_id"] == "scene-03")
    if "E-004" not in scene["evidence_ids"]:
        scene["evidence_ids"].append("E-004")
    claim = next(row for row in scene["causal_claims"] if row["claim_id"] == "claim-03")
    if claim["scope"] != "nasdaq_support" or claim["claim_type"] != "fact":
        raise SystemExit("Scene 3 claim-03 contract drift")
    if "E-004" not in claim["evidence_ids"]:
        claim["evidence_ids"].append("E-004")
    result["story_script_template_sha256"] = base.write_json(script_path, script)
    result["compatibility_alignment"] = "scene-03 direct price fact E-001 + existing nasdaq-wide E-004"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = materialize(args.repo_root.resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
