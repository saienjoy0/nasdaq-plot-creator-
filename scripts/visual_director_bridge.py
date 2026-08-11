#!/usr/bin/env python3
"""Run the pinned Remotion Visual Director before renderer validation/freeze.

This bridge owns no visual policy. It persists the exact strict render input,
asks the pinned renderer to build a deterministic candidate catalog, requires a
ChatGPT-authored candidate-ID-only plan, and asks the same renderer checkout to
compile it. Missing selection is a deliberate production pause, not a fallback.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any


class VisualDirectorBridgeError(ValueError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualDirectorBridgeError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualDirectorBridgeError(f"{label} root must be an object")
    return value


def write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temp = path.with_name(f".{path.name}.visual-director.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _renderer_head(renderer_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=renderer_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise VisualDirectorBridgeError(
            f"cannot inspect pinned renderer checkout: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _run_renderer(
    renderer_root: Path,
    command: str,
    arguments: list[str],
) -> None:
    cli = renderer_root / "scripts" / "visual-director-cli.ts"
    if not cli.is_file():
        raise VisualDirectorBridgeError(
            f"pinned renderer lacks Visual Director CLI: {cli}"
        )
    result = subprocess.run(
        ["node", "--import", "tsx", str(cli), command, *arguments],
        cwd=renderer_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise VisualDirectorBridgeError(
            f"Visual Director {command} failed: {detail}"
        )


def prepare_and_compile(
    *,
    render: dict[str, Any],
    output_root: Path,
    date: str,
    renderer_root: Path,
    expected_renderer_commit: str,
    runner: Callable[[Path, str, list[str]], None] = _run_renderer,
    renderer_head: Callable[[Path], str] = _renderer_head,
) -> dict[str, Any]:
    output_root = output_root.resolve()
    renderer_root = renderer_root.resolve()
    observed_commit = renderer_head(renderer_root)
    if observed_commit != expected_renderer_commit:
        raise VisualDirectorBridgeError(
            "Visual Director renderer checkout SHA mismatch: "
            f"expected={expected_renderer_commit} actual={observed_commit}"
        )
    if render.get("episode", {}).get("targetDate") != date:
        raise VisualDirectorBridgeError("Visual Director render episodeDate mismatch")

    work = output_root / "working" / date
    verification = output_root / "verification" / date
    verification.mkdir(parents=True, exist_ok=True)
    input_path = work / "visual_direction_input.json"
    catalog_path = work / "visual_candidate_catalog.json"
    hints_path = work / "visual_capability_hints.json"
    plan_path = work / "visual_direction_plan.json"
    compiled_path = work / "visual_direction_compiled_render.json"
    report_path = verification / "visual_direction_compile_report.json"
    write_atomic(input_path, render)

    build_arguments = ["--spec", str(input_path), "--catalog", str(catalog_path)]
    if hints_path.is_file():
        build_arguments.extend(["--hints", str(hints_path)])
    runner(renderer_root, "build", build_arguments)
    catalog = load_json(catalog_path, "Visual Candidate Catalog")
    if catalog.get("episodeDate") != date:
        raise VisualDirectorBridgeError("Visual Candidate Catalog episodeDate mismatch")
    if catalog.get("sourceRenderSpecSha256") != sha256_file(input_path):
        raise VisualDirectorBridgeError("Visual Candidate Catalog render SHA mismatch")
    if not plan_path.is_file():
        raise VisualDirectorBridgeError(
            "E_VISUAL_DIRECTION_PLAN_REQUIRED: review visual_candidate_catalog.json "
            "and author visual_direction_plan.json with candidate IDs only"
        )

    runner(
        renderer_root,
        "compile",
        [
            "--spec",
            str(input_path),
            "--catalog",
            str(catalog_path),
            "--plan",
            str(plan_path),
            "--output",
            str(compiled_path),
            "--report",
            str(report_path),
        ],
    )
    compiled = load_json(compiled_path, "Visual Director compiled render")
    report = load_json(report_path, "Visual Direction compile report")
    if report.get("semanticDiff") != "PASS":
        raise VisualDirectorBridgeError("Visual Director Protected Semantic Diff did not PASS")
    if report.get("sourceRenderSpecSha256") != sha256_file(input_path):
        raise VisualDirectorBridgeError("Visual Direction compile report render SHA mismatch")
    return {
        "render": compiled,
        "catalog_path": catalog_path,
        "plan_path": plan_path,
        "report_path": report_path,
        "input_path": input_path,
        "compiled_path": compiled_path,
        "warnings": report.get("warnings", []),
    }
