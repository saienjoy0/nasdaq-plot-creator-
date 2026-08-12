#!/usr/bin/env python3
"""Run historical 2026-08-10 semantics through the current Visual Director.

The committed historical render_spec stays byte-for-byte unchanged. This acceptance
creates an in-memory test copy, binds only the Renderer-owned compatibility SHA to
the current Renderer checkout, and then requires the current strict compiler to
validate every Grammar/Template pair before the identity plan can pass.
"""

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


def current_renderer_compatibility_sha(renderer_root: Path) -> str:
    registry = renderer_root / "contracts/visual_grammar_renderer_compatibility.json"
    if not registry.is_file():
        raise AssertionError(f"current Renderer compatibility registry missing: {registry}")
    return hashlib.sha256(registry.read_bytes()).hexdigest()


def current_contract_copy(historical: dict, renderer_root: Path) -> dict:
    rebound = json.loads(json.dumps(historical, ensure_ascii=False))
    root = rebound.get("visualGrammarContract")
    if not isinstance(root, dict):
        raise AssertionError("historical Golden lacks Visual Grammar root contract")
    root["rendererCompatibilitySha256"] = current_renderer_compatibility_sha(renderer_root)
    return rebound


def run(renderer_root: Path) -> dict:
    renderer_root = renderer_root.resolve()
    date = "2026-08-10"
    historical_path = renderer_root / f"render-specs/{date}/render_spec.json"
    historical_bytes = historical_path.read_bytes()
    historical = json.loads(historical_bytes.decode("utf-8"))
    spec = current_contract_copy(historical, renderer_root)
    if historical_path.read_bytes() != historical_bytes:
        raise AssertionError("historical Golden artifact was modified during test binding")
    old_sha = historical["visualGrammarContract"]["rendererCompatibilitySha256"]
    new_sha = spec["visualGrammarContract"]["rendererCompatibilitySha256"]
    if old_sha == new_sha:
        raise AssertionError("historical Golden must exercise a stale Renderer registry binding")

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
            raise AssertionError("Golden identity selection changed rebound render semantically")
        report = json.loads(result["report_path"].read_text(encoding="utf-8"))
        if report.get("semanticDiff") != "PASS":
            raise AssertionError("Golden Protected Semantic Diff did not PASS")
        if historical_path.read_bytes() != historical_bytes:
            raise AssertionError("historical Golden artifact changed after current-contract acceptance")
        return {
            "status": "PASS",
            "candidateCount": len(catalog["candidates"]),
            "selectionCount": len(plan["selections"]),
            "warningCount": len(report.get("warnings", [])),
            "historicalRegistrySha256": old_sha,
            "currentRegistrySha256": new_sha,
            "historicalArtifactUnchanged": True,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renderer-root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.renderer_root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
