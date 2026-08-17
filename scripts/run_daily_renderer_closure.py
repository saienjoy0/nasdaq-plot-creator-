#!/usr/bin/env python3
"""Run the exact daily package through the pre-Preview renderer closure boundary.

This is an orchestration-only gate. It reuses the existing authoring/materialization,
Visual Grammar, Financial Visual, Visual Director, and official Renderer validators.
It does not render Preview, create a Preview request, choose a candidate, choose a
fallback, or alter narration/market causality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import materializer_runtime_binding


RENDERER_COMMIT = "6a44cdeb04d401dc45379783862e279a5c2f04a5"
RENDERER_CONTRACT_VERSION = "2.4.0"


class ClosureError(RuntimeError):
    pass


def run(root: Path, *args: str, env: dict[str, str] | None = None) -> None:
    command = list(args)
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=root, env=env, check=False)
    if completed.returncode != 0:
        raise ClosureError(f"command failed ({completed.returncode}): {' '.join(command)}")


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ClosureError(f"JSON root must be object: {path}")
    return value


def materializer_runtime_args(root: Path, date: str) -> list[str]:
    try:
        binding = materializer_runtime_binding.MaterializerRuntimeBinding.from_workspace(
            root, date
        )
    except materializer_runtime_binding.MaterializerRuntimeBindingError as exc:
        raise ClosureError(str(exc)) from exc
    return binding.cli_args()


def ensure_renderer(renderer_root: Path) -> None:
    if not (renderer_root / "scripts" / "spec-cli.ts").is_file():
        raise ClosureError(f"renderer checkout invalid: {renderer_root}")
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=renderer_root,
        capture_output=True,
        text=True,
        check=False,
    )
    actual = completed.stdout.strip()
    if completed.returncode != 0 or actual != RENDERER_COMMIT:
        raise ClosureError(
            f"renderer SHA mismatch: expected={RENDERER_COMMIT} actual={actual or 'unavailable'}"
        )


def sync_renderer_owned_contracts(root: Path, renderer_root: Path) -> None:
    source = renderer_root / "contracts" / "visual_grammar_renderer_compatibility.json"
    target = root / "contracts" / "visual_grammar_renderer_compatibility.json"
    if not source.is_file():
        raise ClosureError(f"pinned Renderer compatibility registry missing: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    target_sha = hashlib.sha256(target.read_bytes()).hexdigest()
    if source_sha != target_sha:
        raise ClosureError(
            "Renderer compatibility registry sync mismatch: "
            f"source={source_sha} target={target_sha}"
        )
    print(f"BOUND_RENDERER_VISUAL_GRAMMAR_REGISTRY sha256={source_sha}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--renderer-root", type=Path, required=True)
    args = parser.parse_args()

    date = args.date
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise SystemExit("--date must be YYYY-MM-DD")
    root = args.repo_root.resolve()
    renderer_root = args.renderer_root.resolve()
    ensure_renderer(renderer_root)

    if not (root / "daily-authoring-parts" / date).is_dir():
        raise SystemExit(f"daily authoring parts missing for {date}")
    if not (root / "daily-inputs" / date / f"daily_source_package_{date}.md").is_file():
        raise SystemExit(f"daily source package missing for {date}")

    verification = root / "verification" / date
    verification.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["NASDAQ_CAFE_RENDERER_ROOT"] = str(renderer_root)

    try:
        run(root, "python", "scripts/assemble_chatgpt_daily_authoring_parts.py", "--date", date, "--repo-root", ".", env=env)
        run(root, "python", "scripts/materialize_chatgpt_daily_authoring.py", "--date", date, "--repo-root", ".", env=env)
        run(root, "python", "scripts/fixup_chatgpt_daily_materialization.py", "--date", date, "--repo-root", ".", env=env)
        run(
            root,
            "python",
            "scripts/validate_chatgpt_daily_authoring_closure.py",
            "--authoring",
            f"daily-authoring/{date}.json",
            "--registry",
            "contracts/financial_recipe_registry.json",
            "--json-output",
            f"verification/{date}/authoring_renderer_closure.json",
            env=env,
        )
        runtime_args = materializer_runtime_args(root, date)
        run(
            root,
            "python",
            "scripts/pre_tts_visual_gate.py",
            "--render-spec",
            f"render-specs/{date}/render_spec.json",
            "--story-bindings",
            f"working/{date}/story-engine/story_production_bindings.json",
            "--output",
            f"verification/{date}/pre_tts_visual_gate.json",
            env=env,
        )
        run(root, "python", "scripts/prepare_visual_sources.py", "--date", date, "--repo-root", ".", env=env)
        run(
            root,
            "python",
            "scripts/materialize_daily_episode.py",
            "--date",
            date,
            "--repo-root",
            ".",
            *runtime_args,
            env=env,
        )
        run(root, "python", "scripts/materialize_financial_contract_1_0.py", "--date", date, "--repo-root", ".", env=env)
        run(
            root,
            "python",
            "scripts/run_daily_production_hardened.py",
            "--workspace",
            ".",
            "init",
            "--episode-date",
            date,
            "--daily-source-package",
            f"daily-inputs/{date}/daily_source_package_{date}.md",
            "--requested-scope",
            "preview",
            "--renderer-commit",
            RENDERER_COMMIT,
            "--renderer-contract-version",
            RENDERER_CONTRACT_VERSION,
            env=env,
        )

        story = f"working/{date}/story-engine"
        states = [
            (
                "research_inputs_bound",
                [f"research/{date}/research_input_manifest.json"],
            ),
            (
                "causal_dossier_valid",
                [
                    f"research/{date}/causal_research_dossier_{date}.json",
                    f"research/{date}/causal_dossier_validation.json",
                ],
            ),
            (
                "episode_package_final",
                [
                    f"episodes/{date}/episode_package_{date}.md",
                    f"{story}/story_engine_acceptance.json",
                    f"{story}/story_projection_report.json",
                    f"verification/{date}/pre_tts_visual_gate.json",
                ],
            ),
            (
                "memory_usage_valid",
                [f"research/{date}/causal_dossier_validation.json"],
            ),
            (
                "assets_resolved",
                [
                    f"verification/{date}/asset_resolution_log.json",
                    f"verification/{date}/image_generation_log.json",
                ],
            ),
        ]
        for state, evidence in states:
            run(
                root,
                "python",
                "scripts/run_daily_production_hardened.py",
                "--workspace",
                ".",
                "advance",
                "--episode-date",
                date,
                "--state",
                state,
                "--evidence",
                *evidence,
                env=env,
            )

        shutil.copyfile(
            root / "contracts" / "financial_visual_compatibility_2_4.json",
            root / "contracts" / "financial_visual_compatibility.json",
        )
        sync_renderer_owned_contracts(root, renderer_root)
        run(
            root,
            "python",
            "scripts/run_daily_production_hardened.py",
            "--workspace",
            ".",
            "build-production",
            "--episode-date",
            date,
            "--episode-package",
            f"episodes/{date}/episode_package_{date}.md",
            env=env,
        )
        run(
            root,
            "python",
            "scripts/run_daily_production_hardened.py",
            "--workspace",
            ".",
            "status",
            "--episode-date",
            date,
            env=env,
        )
    except ClosureError as exc:
        report = {
            "contractVersion": "1.0.0",
            "episodeDate": date,
            "rendererCommit": RENDERER_COMMIT,
            "rendererContractVersion": RENDERER_CONTRACT_VERSION,
            "status": "FAIL",
            "error": str(exc),
        }
        (verification / "renderer_closure_gate.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
        return 2

    report = {
        "contractVersion": "1.0.0",
        "episodeDate": date,
        "rendererCommit": RENDERER_COMMIT,
        "rendererContractVersion": RENDERER_CONTRACT_VERSION,
        "status": "PASS",
        "previewRendered": False,
        "finalRendered": False,
    }
    (verification / "renderer_closure_gate.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())