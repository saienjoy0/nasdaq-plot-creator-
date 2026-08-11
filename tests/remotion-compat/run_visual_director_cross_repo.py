#!/usr/bin/env python3
"""Run the 2026-08-10 Golden render through the real pinned Visual Director."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import visual_director_bridge as bridge  # noqa: E402


def canonical_sha(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def identity_plan(spec: dict, catalog: dict) -> dict:
    by_beat: dict[str, list[dict]] = {}
    for candidate in catalog["candidates"]:
        by_beat.setdefault(candidate["visualBeatId"], []).append(candidate)
    keys = (
        "visualTemplate",
        "templateVariant",
        "screenState",
        "visualMode",
        "templateConfig",
        "objectIds",
        "assetPlacementIds",
    )
    selections = []
    for scene in spec["scenes"]:
        for beat in scene["visualBeats"]:
            matches = [
                candidate
                for candidate in by_beat[beat["beatId"]]
                if all(candidate[key] == beat[key] for key in keys)
            ]
            if not matches:
                raise AssertionError(f"Golden Beat lacks identity candidate: {beat['beatId']}")
            selections.append(
                {
                    "visualBeatId": beat["beatId"],
                    "candidateId": matches[0]["candidateId"],
                }
            )
    return {
        "contractVersion": "1.0.0",
        "episodeDate": spec["episode"]["targetDate"],
        "candidateCatalogSha256": canonical_sha(catalog),
        "selections": selections,
    }


def run(renderer_root: Path) -> dict:
    renderer_root = renderer_root.resolve()
    date = "2026-08-10"
    spec = json.loads(
        (renderer_root / f"render-specs/{date}/render_spec.json").read_text(
            encoding="utf-8"
        )
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=renderer_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    with tempfile.TemporaryDirectory(prefix="nasdaq-visual-director-cross-") as temp:
        output_root = Path(temp)
        try:
            bridge.prepare_and_compile(
                render=spec,
                output_root=output_root,
                date=date,
                renderer_root=renderer_root,
                expected_renderer_commit=commit,
            )
        except bridge.VisualDirectorBridgeError as exc:
            if "E_VISUAL_DIRECTION_PLAN_REQUIRED" not in str(exc):
                raise
        else:
            raise AssertionError("Visual Director must pause when its plan is missing")
        catalog_path = output_root / f"working/{date}/visual_candidate_catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        plan_path = output_root / f"working/{date}/visual_direction_plan.json"
        plan = identity_plan(spec, catalog)
        plan_path.write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        result = bridge.prepare_and_compile(
            render=spec,
            output_root=output_root,
            date=date,
            renderer_root=renderer_root,
            expected_renderer_commit=commit,
        )
        if result["render"] != spec:
            raise AssertionError("Golden identity selection changed render bytes semantically")
        report = json.loads(result["report_path"].read_text(encoding="utf-8"))
        if report.get("semanticDiff") != "PASS":
            raise AssertionError("Golden Protected Semantic Diff did not PASS")
        return {
            "status": "PASS",
            "candidateCount": len(catalog["candidates"]),
            "selectionCount": len(plan["selections"]),
            "warningCount": len(report.get("warnings", [])),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renderer-root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.renderer_root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
