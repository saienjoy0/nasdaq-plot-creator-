#!/usr/bin/env python3
"""Run the pinned Remotion Visual Director before renderer validation/freeze.

This bridge makes no editorial choice. It persists the exact strict render input,
projects the already-authored Visual Template into a fail-closed Visual Director
policy when no explicit policy sidecar exists, asks the pinned renderer to build a
deterministic candidate catalog, requires a ChatGPT-authored candidate-ID-only plan,
and asks the same renderer checkout to compile it. Missing selection is a deliberate
production pause, not a fallback.
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


_TEMPLATE_CAPABILITY: dict[str, str] = {
    "source-receipt": "source-document",
    "news-media": "source-document",
    "event-reaction-timeline": "time-series",
    "index-return-bars": "comparison-set",
    "diverging-stock-bars": "comparison-set",
    "split-comparison": "comparison-set",
    "focus-matrix": "comparison-set",
    "expected-actual-bullet": "gap",
    "expected-actual-gap-flow": "gap",
    "earnings-surprise": "gap",
    "causal-lane": "causal-graph",
    "macro-pressure": "causal-graph",
    "tailwind-headwind": "causal-graph",
    "entity-card-full": "entity",
    "analogy-steps": "image-media",
    "verification-checklist": "verification",
    "verification-matrix": "verification",
    "evidence-boundary": "verification",
}


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


def _authored_beats(render: dict[str, Any]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    scenes = render.get("scenes")
    if not isinstance(scenes, list):
        raise VisualDirectorBridgeError("Visual Director render scenes must be an array")
    for scene_index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise VisualDirectorBridgeError(
                f"Visual Director render scene must be object: index={scene_index}"
            )
        beats = scene.get("visualBeats")
        if not isinstance(beats, list):
            raise VisualDirectorBridgeError(
                f"Visual Director render visualBeats must be array: scene={scene_index}"
            )
        for beat_index, beat in enumerate(beats):
            if not isinstance(beat, dict):
                raise VisualDirectorBridgeError(
                    f"Visual Director Beat must be object: scene={scene_index} beat={beat_index}"
                )
            beat_id = beat.get("beatId")
            template = beat.get("visualTemplate")
            if not isinstance(beat_id, str) or not beat_id:
                raise VisualDirectorBridgeError(
                    f"Visual Director Beat ID missing: scene={scene_index} beat={beat_index}"
                )
            if beat_id in seen:
                raise VisualDirectorBridgeError(f"duplicate Visual Director Beat ID: {beat_id}")
            if not isinstance(template, str) or not template:
                raise VisualDirectorBridgeError(
                    f"Visual Director authored template missing: beat={beat_id}"
                )
            seen.add(beat_id)
            rows.append((beat_id, template))
    return rows


def _validate_explicit_hints(
    hints: dict[str, Any],
    *,
    date: str,
    authored_beats: list[tuple[str, str]],
) -> None:
    if hints.get("contractVersion") != "1.1.0":
        raise VisualDirectorBridgeError(
            "Visual Director hints must use contractVersion 1.1.0 with templatePolicy"
        )
    if hints.get("episodeDate") != date:
        raise VisualDirectorBridgeError("Visual Director hints episodeDate mismatch")
    beats = hints.get("beats")
    if not isinstance(beats, list):
        raise VisualDirectorBridgeError("Visual Director hints beats must be an array")
    expected = {beat_id for beat_id, _ in authored_beats}
    observed: set[str] = set()
    for index, row in enumerate(beats):
        if not isinstance(row, dict):
            raise VisualDirectorBridgeError(
                f"Visual Director hint Beat must be object: index={index}"
            )
        beat_id = row.get("visualBeatId")
        if not isinstance(beat_id, str) or beat_id not in expected:
            raise VisualDirectorBridgeError(
                f"Visual Director hint targets unknown Beat: {beat_id}"
            )
        if beat_id in observed:
            raise VisualDirectorBridgeError(
                f"duplicate Visual Director hint Beat: {beat_id}"
            )
        capabilities = row.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities or not all(
            isinstance(item, str) and item for item in capabilities
        ):
            raise VisualDirectorBridgeError(
                f"Visual Director hint capabilities invalid: beat={beat_id}"
            )
        policy = row.get("templatePolicy")
        if not isinstance(policy, dict) or policy.get("mode") not in {
            "authored-only",
            "allow-list",
        }:
            raise VisualDirectorBridgeError(
                f"Visual Director templatePolicy missing or invalid: beat={beat_id}"
            )
        if policy.get("mode") == "allow-list":
            allowed = policy.get("allowedTemplateIds")
            if not isinstance(allowed, list) or not allowed or not all(
                isinstance(item, str) and item for item in allowed
            ):
                raise VisualDirectorBridgeError(
                    f"Visual Director allow-list invalid: beat={beat_id}"
                )
        observed.add(beat_id)
    missing = sorted(expected - observed)
    if missing:
        raise VisualDirectorBridgeError(
            "Visual Director hints must cover every Beat: missing=" + ",".join(missing)
        )


def _ensure_template_policy_hints(
    *,
    render: dict[str, Any],
    hints_path: Path,
    date: str,
) -> dict[str, Any]:
    authored_beats = _authored_beats(render)
    if hints_path.is_file():
        hints = load_json(hints_path, "Visual Capability Hints")
        _validate_explicit_hints(hints, date=date, authored_beats=authored_beats)
        return hints

    hints = {
        "contractVersion": "1.1.0",
        "episodeDate": date,
        "beats": [
            {
                "visualBeatId": beat_id,
                "capabilities": [_TEMPLATE_CAPABILITY.get(template, "text-only")],
                "templatePolicy": {"mode": "authored-only"},
            }
            for beat_id, template in authored_beats
        ],
    }
    write_atomic(hints_path, hints)
    return hints


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

    _ensure_template_policy_hints(render=render, hints_path=hints_path, date=date)
    build_arguments = [
        "--spec",
        str(input_path),
        "--catalog",
        str(catalog_path),
        "--hints",
        str(hints_path),
    ]
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
        "hints_path": hints_path,
        "warnings": report.get("warnings", []),
    }
