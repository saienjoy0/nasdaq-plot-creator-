#!/usr/bin/env python3
"""One-shot VG-5 cross-repository contract sync and integration patch."""

from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDERER_COMMIT = "750f993bd00cf2f67fdb4ab18907e82ed0dc68df"
RAW_ROOT = (
    "https://raw.githubusercontent.com/saienjoy0/"
    "saienjoy0-nasdaq-cafe-remotion/"
    f"{RENDERER_COMMIT}"
)


def download(relative: str) -> bytes:
    with urllib.request.urlopen(f"{RAW_ROOT}/{relative}", timeout=30) as response:
        return response.read()


def replace_once(source: str, before: str, after: str, label: str) -> str:
    count = source.count(before)
    if count != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {count}")
    return source.replace(before, after, 1)


def main() -> int:
    mirrors = (
        "contracts/visual_grammar_timing_report.schema.json",
        "contracts/visual_grammar_renderer_compatibility.json",
    )
    for relative in mirrors:
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(download(relative))
        print(f"synced {relative}")

    script_path = ROOT / "scripts/visual_grammar_cross_artifact.py"
    source = script_path.read_text(encoding="utf-8")
    if "visual_grammar_report_recompute import" not in source:
        source = replace_once(
            source,
            "from jsonschema import Draft202012Validator\n",
            "from jsonschema import Draft202012Validator\n\n"
            "from visual_grammar_report_recompute import (\n"
            "    VisualGrammarReportRecomputeError,\n"
            "    validate_structural_report_against_render,\n"
            "    validate_timing_report_metrics,\n"
            ")\n",
            "report recomputation import",
        )
    if "validate_structural_report_against_render(" not in source:
        anchor = (
            "    _validate_timing_rows(timing_report, measured_render_beats, compatibility)\n"
        )
        addition = anchor + (
            "    try:\n"
            "        validate_structural_report_against_render(\n"
            "            render_spec, structural_report, semantics_registry\n"
            "        )\n"
            "        validate_timing_report_metrics(timing_report)\n"
            "    except VisualGrammarReportRecomputeError as exc:\n"
            "        raise VisualGrammarCrossArtifactError(str(exc)) from exc\n"
        )
        source = replace_once(
            source,
            anchor,
            addition,
            "report recomputation invocation",
        )
    script_path.write_text(source, encoding="utf-8")
    print("patched scripts/visual_grammar_cross_artifact.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
