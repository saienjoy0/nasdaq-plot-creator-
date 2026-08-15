#!/usr/bin/env python3
"""Real-day pre-Preview closure for visual-intelligence-bridge/1.2.0.

`prepare` regenerates the exact real-day machine inputs, resolves assets, produces
vNext CandidateInput/Capability/Catalog, then requires the machine bridge to stop
at DECISION_REQUIRED. `compile` repeats the same deterministic preparation with an
AI-B-authored Director decision present. Director-only decisions compile the actual
visual output and warnings, then stop normally at REVIEW_REQUIRED. A decision that
became stale against the current legal Catalog returns to DECISION_REQUIRED instead
of being treated as a renderer failure. Only a Critic PASS bound to those exact
outputs may advance the validated production states.

Neither phase renders Preview or auto-requests Final.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import renderer_binding
import run_daily_renderer_closure as legacy


class VisualIntelligenceClosureError(RuntimeError):
    pass


def run(root: Path, *args: str, env: dict[str, str] | None = None, ok_codes=(0,)) -> int:
    command = list(args)
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=root, env=env, check=False)
    if completed.returncode not in ok_codes:
        raise VisualIntelligenceClosureError(
            f"command failed ({completed.returncode}): {' '.join(command)}"
        )
    return completed.returncode


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VisualIntelligenceClosureError(f"JSON root must be object: {path}")
    return value


def ensure_renderer(root: Path, renderer_root: Path) -> dict:
    try:
        return renderer_binding.verify_renderer_checkout(root, renderer_root)
    except renderer_binding.RendererBindingError as exc:
        raise VisualIntelligenceClosureError(str(exc)) from exc


def evidence_if_exists(root: Path, values: list[str]) -> list[str]:
    return [value for value in values if (root / value).is_file()]


def advance(
    root: Path,
    *,
    date: str,
    state: str,
    evidence: list[str],
    env: dict[str, str],
) -> None:
    if not evidence:
        raise VisualIntelligenceClosureError(f"{state} has no evidence")
    run(
        root,
        "python3",
        "scripts/run_daily_production_v12.py",
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


def prepare_common(
    *,
    root: Path,
    renderer_root: Path,
    date: str,
    env: dict[str, str],
    binding: dict,
) -> None:
    if not (root / "daily-authoring-parts" / date).is_dir():
        raise VisualIntelligenceClosureError(f"daily authoring parts missing for {date}")
    daily_source = root / "daily-inputs" / date / f"daily_source_package_{date}.md"
    if not daily_source.is_file():
        raise VisualIntelligenceClosureError(f"daily source package missing for {date}")

    run(root, "python3", "scripts/assemble_chatgpt_daily_authoring_parts.py", "--date", date, "--repo-root", ".", env=env)
    run(root, "python3", "scripts/materialize_chatgpt_daily_authoring.py", "--date", date, "--repo-root", ".", env=env)
    run(root, "python3", "scripts/fixup_chatgpt_daily_materialization.py", "--date", date, "--repo-root", ".", env=env)
    run(
        root,
        "python3",
        "scripts/validate_chatgpt_daily_authoring_closure.py",
        "--authoring",
        f"daily-authoring/{date}.json",
        "--registry",
        "contracts/financial_recipe_registry.json",
        "--json-output",
        f"verification/{date}/authoring_renderer_closure.json",
        env=env,
    )
    legacy.bind_legacy_materializer(root, date)
    run(
        root,
        "python3",
        "scripts/pre_tts_visual_gate.py",
        "--render-spec",
        f"render-specs/{date}/render_spec.json",
        "--story-bindings",
        f"working/{date}/story-engine/story_production_bindings.json",
        "--output",
        f"verification/{date}/pre_tts_visual_gate.json",
        env=env,
    )

    run(
        root,
        "python3",
        "scripts/visual_intelligence_story_context.py",
        "--render-spec",
        f"render-specs/{date}/render_spec.json",
        "--date",
        date,
        "--output-root",
        ".",
        env=env,
    )
    vi = root / "working" / date / "visual-intelligence"
    requirements = vi / "visual_requirements.json"
    if not requirements.is_file():
        raise VisualIntelligenceClosureError(
            "AI-B Visual Requirements missing: working/<date>/visual-intelligence/visual_requirements.json"
        )
    run(
        root,
        "python3",
        "scripts/visual_intelligence_requirements.py",
        "--requirements",
        str(requirements.relative_to(root)),
        "--render-spec",
        f"render-specs/{date}/render_spec.json",
        "--editorial-snapshot",
        f"working/{date}/visual-intelligence/editorial_snapshot.json",
        "--date",
        date,
        "--output",
        f"working/{date}/visual-intelligence/visual_requirements_validation.json",
        env=env,
    )
    source_intents = root / "working" / date / "visual_source_intents.json"
    if not source_intents.is_file():
        raise VisualIntelligenceClosureError(f"Visual Source intents missing: {source_intents}")
    run(
        root,
        "python3",
        "scripts/visual_intelligence_asset_plan.py",
        "--requirements",
        str(requirements.relative_to(root)),
        "--visual-source-intents",
        str(source_intents.relative_to(root)),
        "--date",
        date,
        "--output",
        f"working/{date}/visual-intelligence/visual_asset_plan_validation.json",
        env=env,
    )
    run(root, "python3", "scripts/prepare_visual_sources.py", "--date", date, "--repo-root", ".", env=env)
    run(root, "python3", "scripts/materialize_daily_episode.py", "--date", date, "--repo-root", ".", env=env)
    run(root, "python3", "scripts/materialize_financial_contract_1_0.py", "--date", date, "--repo-root", ".", env=env)

    renderer = binding["renderer"]
    run(
        root,
        "python3",
        "scripts/run_daily_production_v12.py",
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
        renderer["commit"],
        "--renderer-contract-version",
        renderer["contractVersion"],
        "--visual-intelligence-bridge-version",
        binding["bridgeContractVersion"],
        env=env,
    )

    advance(
        root,
        date=date,
        state="research_inputs_bound",
        evidence=[f"research/{date}/research_input_manifest.json"],
        env=env,
    )
    advance(
        root,
        date=date,
        state="causal_dossier_valid",
        evidence=[
            f"research/{date}/causal_research_dossier_{date}.json",
            f"research/{date}/causal_dossier_validation.json",
        ],
        env=env,
    )
    advance(
        root,
        date=date,
        state="editorial_snapshot_valid",
        evidence=[
            f"working/{date}/visual-intelligence/editorial_snapshot.json",
            f"working/{date}/visual-intelligence/financial_candidate_provider.json",
        ],
        env=env,
    )
    advance(
        root,
        date=date,
        state="visual_requirements_planned",
        evidence=[
            f"working/{date}/visual-intelligence/visual_requirements.json",
            f"working/{date}/visual-intelligence/visual_requirements_validation.json",
            f"working/{date}/visual-intelligence/visual_asset_plan_validation.json",
        ],
        env=env,
    )
    asset_evidence = evidence_if_exists(
        root,
        [
            f"working/{date}/visual_source_intents.json",
            f"working/{date}/visual-intelligence/visual_asset_plan_validation.json",
            f"verification/{date}/asset_resolution_log.json",
            f"verification/{date}/image_generation_log.json",
        ],
    )
    advance(root, date=date, state="assets_resolved", evidence=asset_evidence, env=env)


def _write_prepared_result(
    *,
    verification: Path,
    binding: dict,
    date: str,
    reason: str | None = None,
) -> None:
    result = {
        "contractVersion": "1.0.0",
        "bridgeContractVersion": binding["bridgeContractVersion"],
        "episodeDate": date,
        "rendererCommit": binding["renderer"]["commit"],
        "status": "PREPARED",
        "candidateCatalog": f"working/{date}/visual-intelligence/visual_candidate_catalog.json",
        "previewRendered": False,
        "finalRendered": False,
    }
    if reason:
        result["reason"] = reason
    (verification / "renderer_closure_gate_v12.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["prepare", "compile"], required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--renderer-root", required=True, type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        raise SystemExit("--date must be YYYY-MM-DD")
    root = args.repo_root.resolve()
    renderer_root = args.renderer_root.resolve()
    date = args.date
    verification = root / "verification" / date
    verification.mkdir(parents=True, exist_ok=True)
    binding = ensure_renderer(root, renderer_root)
    env = os.environ.copy()
    env["NASDAQ_CAFE_RENDERER_ROOT"] = str(renderer_root)

    try:
        prepare_common(
            root=root,
            renderer_root=renderer_root,
            date=date,
            env=env,
            binding=binding,
        )
        vi_command = [
            "python3",
            "scripts/run_visual_intelligence_v12.py",
            "--root",
            ".",
            "--date",
            date,
            "--render-spec",
            f"render-specs/{date}/render_spec.json",
            "--renderer-root",
            str(renderer_root),
        ]
        if args.phase == "prepare":
            code = run(root, *vi_command, env=env, ok_codes=(3,))
            report = load(verification / "visual_intelligence_validation.json")
            if code != 3 or report.get("status") != "DECISION_REQUIRED":
                raise VisualIntelligenceClosureError(
                    "prepare phase must stop at DECISION_REQUIRED after Candidate Catalog generation"
                )
            _write_prepared_result(
                verification=verification,
                binding=binding,
                date=date,
            )
            return 0

        decision = root / "working" / date / "visual-intelligence" / "visual_intelligence_decision.json"
        if not decision.is_file():
            raise VisualIntelligenceClosureError(
                "compile phase requires AI-B visual_intelligence_decision.json"
            )
        code = run(root, *vi_command, env=env, ok_codes=(0, 3, 4))
        vi_report = load(verification / "visual_intelligence_validation.json")
        if code == 3:
            if vi_report.get("status") != "DECISION_REQUIRED":
                raise VisualIntelligenceClosureError(
                    "compile phase exit 3 must correspond to DECISION_REQUIRED"
                )
            reasons = vi_report.get("errors")
            reason = reasons[0] if isinstance(reasons, list) and reasons else "Director decision requires reselection"
            _write_prepared_result(
                verification=verification,
                binding=binding,
                date=date,
                reason=str(reason),
            )
            return 0
        if code == 4:
            if vi_report.get("status") != "REVIEW_REQUIRED":
                raise VisualIntelligenceClosureError(
                    "compile phase exit 4 must correspond to REVIEW_REQUIRED"
                )
            result = {
                "contractVersion": "1.0.0",
                "bridgeContractVersion": binding["bridgeContractVersion"],
                "episodeDate": date,
                "rendererCommit": binding["renderer"]["commit"],
                "status": "REVIEW_REQUIRED",
                "compiledVisual": vi_report.get("compiledVisual"),
                "compiledVisualSha256": vi_report.get("compiledVisualSha256"),
                "warningReport": vi_report.get("warningReport"),
                "warningReportSha256": vi_report.get("warningReportSha256"),
                "previewRendered": False,
                "finalRendered": False,
            }
            if not result["compiledVisualSha256"] or not result["warningReportSha256"]:
                raise VisualIntelligenceClosureError(
                    "REVIEW_REQUIRED must expose compiled visual and warning report SHA"
                )
            (verification / "renderer_closure_gate_v12.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if vi_report.get("status") != "PASS":
            raise VisualIntelligenceClosureError(
                "compile phase may advance only after Visual Intelligence PASS"
            )

        advance(
            root,
            date=date,
            state="visual_intelligence_valid",
            evidence=[
                f"working/{date}/visual-intelligence/visual_intelligence_package.json",
                f"verification/{date}/visual_intelligence_validation.json",
            ],
            env=env,
        )
        story = f"working/{date}/story-engine"
        advance(
            root,
            date=date,
            state="episode_package_final",
            evidence=[
                f"episodes/{date}/episode_package_{date}.md",
                f"{story}/story_engine_acceptance.json",
                f"{story}/story_projection_report.json",
                f"verification/{date}/pre_tts_visual_gate.json",
            ],
            env=env,
        )
        advance(
            root,
            date=date,
            state="memory_usage_valid",
            evidence=[f"research/{date}/causal_dossier_validation.json"],
            env=env,
        )
        shutil.copyfile(
            root / "contracts/financial_visual_compatibility_2_4.json",
            root / "contracts/financial_visual_compatibility.json",
        )
        legacy.sync_renderer_owned_contracts(root, renderer_root)
        run(
            root,
            "python3",
            "scripts/run_daily_production_v12.py",
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
            "python3",
            "scripts/run_daily_production_v12.py",
            "--workspace",
            ".",
            "status",
            "--episode-date",
            date,
            env=env,
        )
    except VisualIntelligenceClosureError as exc:
        result = {
            "contractVersion": "1.0.0",
            "bridgeContractVersion": binding["bridgeContractVersion"],
            "episodeDate": date,
            "rendererCommit": binding["renderer"]["commit"],
            "status": "FAIL",
            "error": str(exc),
            "previewRendered": False,
            "finalRendered": False,
        }
        (verification / "renderer_closure_gate_v12.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    result = {
        "contractVersion": "1.0.0",
        "bridgeContractVersion": binding["bridgeContractVersion"],
        "episodeDate": date,
        "rendererCommit": binding["renderer"]["commit"],
        "status": "PASS",
        "previewRendered": False,
        "finalRendered": False,
    }
    (verification / "renderer_closure_gate_v12.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
