#!/usr/bin/env python3
"""Prepare Visual Source resolution before full daily materialization.

This entrypoint reuses the existing renderer-source materializer to build the
same Final Episode Contract that the normal daily materializer will later
regenerate. It then attaches the pre-authored Visual Source Intent, resolves
both candidates, validates an explicit selection, and freezes the selected
asset projection. The later daily materializer rechecks the Final Contract SHA
before consuming the selected projection, so any Story/contract drift fails
closed.

Visual Evidence Planning is explicit. A missing intent document means the
planning step was skipped and is a production error. In a complete production
workspace, an empty ``intents`` array is accepted only after the evidence-first
quality gate confirms that no approved original evidence or verified intraday
series materially requires a real visual surface. Minimal contract-only test
fixtures without a render shell retain the legacy explicit-not-required path.
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
import visual_evidence_quality_gate
import visual_source_contract


class PrepareVisualSourceError(ValueError):
    pass


def _write_quality_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _run_quality_gate(
    *, render_path: Path, intents_path: Path, quality_path: Path
) -> dict:
    render = visual_evidence_quality_gate.load_json(render_path, "render spec")
    intents_doc = visual_evidence_quality_gate.load_json(
        intents_path, "Visual Source intents"
    )
    quality = visual_evidence_quality_gate.validate_visual_evidence(
        render=render,
        intents_doc=intents_doc,
    )
    _write_quality_report(quality_path, quality)
    if quality["status"] != "PASS":
        raise visual_evidence_quality_gate.VisualEvidenceQualityError(
            "\n".join(
                f"{item['code']} {item['path']}: {item['message']}"
                for item in quality["violations"]
            )
        )
    return quality


def _print_failure(message: str) -> int:
    print(
        json.dumps(
            {"status": "FAIL", "errors": str(message).splitlines()},
            ensure_ascii=False,
            indent=2,
        ),
        file=sys.stderr,
    )
    return 2


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
    render_path = root / "render-specs" / date / "render_spec.json"
    quality_path = verification / "visual_evidence_quality_gate.json"

    if not intents_path.is_file():
        return _print_failure(
            "E_VISUAL_SOURCE_PLANNING_MISSING: visual_source_intents.json is required even when no Visual Source is needed"
        )

    try:
        visual_sources = visual_source_contract.load_intent_document(intents_path, date)
    except (
        OSError,
        json.JSONDecodeError,
        visual_source_contract.VisualSourceContractError,
    ) as exc:
        return _print_failure(str(exc))

    # Preserve the established explicit-not-required contract for tiny unit
    # fixtures that intentionally exercise only the planning document. Real
    # Daily Production always has a render shell and therefore still runs the
    # fail-closed evidence-first gate before accepting zero intents.
    if not visual_sources["intents"]:
        quality_gate_value: str | None = None
        if render_path.is_file():
            try:
                _run_quality_gate(
                    render_path=render_path,
                    intents_path=intents_path,
                    quality_path=quality_path,
                )
                quality_gate_value = str(quality_path)
            except (
                OSError,
                json.JSONDecodeError,
                visual_evidence_quality_gate.VisualEvidenceQualityError,
            ) as exc:
                return _print_failure(str(exc))
        result = {
            "status": "not-required",
            "episodeDate": date,
            "reason": "visual evidence planning explicitly completed with zero intents",
            "intentDocument": str(intents_path),
        }
        if quality_gate_value is not None:
            result["qualityGate"] = quality_gate_value
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    # Keep the long-standing fail-fast ordering: an authored non-empty plan
    # requires an explicit Primary/Fallback selection before we do any render
    # materialization or network-resolution work.
    if not selection_path.is_file():
        return _print_failure(
            "E_VISUAL_SOURCE_SELECTED_PATH_INVALID: visual_source_selection.json is required for non-empty Visual Source intents"
        )

    try:
        _run_quality_gate(
            render_path=render_path,
            intents_path=intents_path,
            quality_path=quality_path,
        )
    except (
        OSError,
        json.JSONDecodeError,
        visual_evidence_quality_gate.VisualEvidenceQualityError,
    ) as exc:
        return _print_failure(str(exc))

    try:
        renderer = materialize_renderer_sources.materialize(
            root=root,
            date=date,
            render_path=render_path,
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
            "qualityGate": str(quality_path),
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
        return _print_failure(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
