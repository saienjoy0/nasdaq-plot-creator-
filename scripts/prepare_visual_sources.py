#!/usr/bin/env python3
"""Prepare Visual Source resolution before full daily materialization.

This entrypoint reuses the existing renderer-source materializer to build the
same Final Episode Contract that the normal daily materializer will later
regenerate. It then attaches the pre-authored Visual Source Intent, resolves
both candidates, validates an explicit selection, and freezes the selected
asset projection. The later daily materializer rechecks the Final Contract SHA
before consuming the selected projection, so any Story/contract drift fails
closed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import materialize_renderer_sources
import resolve_visual_sources
import select_visual_sources
import visual_source_contract


class PrepareVisualSourceError(ValueError):
    pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--collector-root", type=Path)
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    date = args.date
    work = root / "working" / date
    verification = root / "verification" / date
    intents_path = work / "visual_source_intents.json"
    selection_path = work / "visual_source_selection.json"

    if not intents_path.is_file():
        print(json.dumps({
            "status": "not-required",
            "episodeDate": date,
            "reason": "visual_source_intents.json is absent",
        }, ensure_ascii=False, indent=2))
        return 0
    if not selection_path.is_file():
        print(json.dumps({
            "status": "FAIL",
            "errors": ["E_VISUAL_SOURCE_SELECTED_PATH_INVALID: visual_source_selection.json is required"],
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    try:
        renderer = materialize_renderer_sources.materialize(
            root=root,
            date=date,
            render_path=root / "render-specs" / date / "render_spec.json",
            public_package_path=root / "episodes" / date / f"episode_package_public_{date}.md",
            bindings_path=work / "financial_visual_bindings.json",
        )
        contract_path = renderer["final_contract_path"]
        visual_source_contract.attach_visual_sources(
            contract_path=contract_path,
            intent_path=intents_path,
            schema_path=root / "contracts/final_episode_contract.schema.json",
        )
        verification.mkdir(parents=True, exist_ok=True)
        raw_resolution = verification / "asset_resolution_raw.json"
        collector_root = args.collector_root
        if collector_root is None and os.environ.get("NASDAQ_CAFE_COLLECTOR_ROOT"):
            collector_root = Path(os.environ["NASDAQ_CAFE_COLLECTOR_ROOT"])
        resolution = resolve_visual_sources.resolve_all(
            contract_path=contract_path,
            repo_root=root,
            output_path=raw_resolution,
            asset_root=root / "daily-assets",
            collector_root=collector_root,
        )
        selected_output = work / "visual_source_selected_assets.json"
        audit_output = verification / "asset_resolution_log.json"
        selected = select_visual_sources.select(
            contract_path=contract_path,
            resolution_path=raw_resolution,
            selection_path=selection_path,
            selected_output=selected_output,
            audit_output=audit_output,
        )
        result = {
            "status": "PASS",
            "episodeDate": date,
            "finalEpisodeContract": str(contract_path),
            "candidateResolutionStatus": resolution["status"],
            "selectedPath": selected["selectedPath"],
            "selectedAssetCount": len(selected["selectedAssets"]),
            "assetResolutionRaw": str(raw_resolution),
            "assetResolutionLog": str(audit_output),
            "selectedProjection": str(selected_output),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (
        OSError,
        KeyError,
        json.JSONDecodeError,
        materialize_renderer_sources.RendererSourceError,
        visual_source_contract.VisualSourceContractError,
        resolve_visual_sources.VisualSourceResolutionError,
        select_visual_sources.VisualSourceSelectionError,
    ) as exc:
        print(json.dumps({
            "status": "FAIL",
            "errors": str(exc).splitlines(),
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
