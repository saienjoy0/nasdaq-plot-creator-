#!/usr/bin/env python3
"""Build one fresh Current handoff for Renderer runtime qualification.

This is a qualification-only runner. It reuses the shared Current runtime authoring
fixture, Current closure state machine, Visual Intelligence pause/materializer contracts,
and official 2.4 handoff builder. It does not mutate a real production attempt and does
not authorize or render Final.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def copy_missing_tree(source: Path, target: Path) -> None:
    skipped = {".git", ".renderer", "node_modules", "__pycache__", ".pytest_cache", "build"}
    for src in source.rglob("*"):
        rel = src.relative_to(source)
        if any(part in skipped for part in rel.parts):
            continue
        dst = target / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        elif src.is_file() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def run(command: list[str], *, cwd: Path, env: dict[str, str], ok_codes: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if completed.returncode not in ok_codes:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}")
    return completed


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON root must be object: {path}")
    return value


def gate(root: Path, date: str) -> dict[str, Any]:
    return load_json(root / "verification" / date / "renderer_closure_gate_v12.json")


def prepare_fixture(source_root: Path, work_parent: Path) -> tuple[Path, Any, dict[str, Any]]:
    fixture_path = source_root / "tests/current-spine/current_authoring_runtime_fixture.py"
    runtime_fixture = load_module("renderer_qualification_current_runtime_fixture", fixture_path)
    work_parent.mkdir(parents=True, exist_ok=True)
    root, fx, authoring = runtime_fixture.build_workspace(work_parent)
    copy_missing_tree(source_root, root)

    authoring_path = root / "daily-authoring" / f"{fx.DATE}.json"
    write_json(authoring_path, authoring)

    semantic = load_module(
        "renderer_qualification_semantic_boundary",
        root / "scripts/validate_editorial_semantic_boundary.py",
    )
    acceptance = semantic.validate_boundary(root, fx.DATE, authoring_path)
    acceptance_path = root / "verification" / fx.DATE / "editorial_semantic_acceptance.json"
    semantic.atomic_write_json(acceptance_path, acceptance)
    semantic.verify_acceptance(root, fx.DATE, acceptance_path)

    closure_validator = load_module(
        "renderer_qualification_authoring_closure",
        root / "scripts/validate_chatgpt_daily_authoring_closure.py",
    )
    registry = load_json(root / "contracts/financial_recipe_registry.json")
    closure_validator.validate_or_raise(authoring, registry)

    freeze = load_module(
        "renderer_qualification_semantic_freeze",
        root / "scripts/chatgpt_semantic_freeze.py",
    )
    freeze_path = root / "semantic-freezes" / f"{fx.DATE}.json"
    freeze.write_manifest(root, fx.DATE, freeze_path)
    freeze.verify_manifest(root, fx.DATE, freeze_path)

    predicted = authoring["storyScript"]["story_plan"]
    sidecar = root / predicted["path"]
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_bytes(fx.canonical_projection_bytes(authoring["storyPlan"]))
    if fx.sha(sidecar) != predicted["sha256"]:
        raise RuntimeError("synthetic Story Plan projection SHA mismatch")
    return root, fx, authoring


def install_renderer_binding(root: Path, renderer_root: Path, renderer_commit: str, renderer_contract: str) -> str:
    binding_path = root / "contracts/renderer_binding.json"
    binding = load_json(binding_path)
    renderer = binding["renderer"]
    registry_rel = renderer["registrySnapshotPath"]
    registry = renderer_root / registry_rel
    if not registry.is_file():
        raise RuntimeError(f"Renderer registry missing: {registry}")
    registry_sha = sha256_file(registry)
    renderer["commit"] = renderer_commit
    renderer["contractVersion"] = renderer_contract
    renderer["registrySnapshotSha256"] = registry_sha
    write_json(binding_path, binding)
    return registry_sha


def closure(root: Path, renderer_root: Path, date: str, phase: str, env: dict[str, str]) -> dict[str, Any]:
    run(
        [
            sys.executable,
            "scripts/run_daily_renderer_closure_v12.py",
            "--phase",
            phase,
            "--date",
            date,
            "--repo-root",
            ".",
            "--renderer-root",
            str(renderer_root),
        ],
        cwd=root,
        env=env,
    )
    return gate(root, date)


def run_fixture_semantic_writer(root: Path, mode: str, env: dict[str, str]) -> None:
    code = r'''
import importlib.util, json, pathlib, sys
root = pathlib.Path.cwd()
sys.path.insert(0, str(root / "scripts"))
module_path = root / "tests/remotion-compat/run_visual_intelligence_v12_cross_repo.py"
spec = importlib.util.spec_from_file_location("qualification_cross_repo_fixture", module_path)
if not spec or not spec.loader:
    raise SystemExit("cannot load existing cross-repo fixture")
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
date = m.generate_current_fixture(pathlib.Path(sys.argv[2]))["episode"]["targetDate"] if False else sys.argv[3]
vi = root / "working" / date / "visual-intelligence"
render = json.loads((root / "render-specs" / date / "render_spec.json").read_text(encoding="utf-8"))
mode = sys.argv[1]
if mode == "requirements":
    intents, requirements = m.requirement_rows(render)
    m.write_json(
        vi / m.artifacts.REQUIREMENTS_SEMANTIC,
        {
            "semanticPayloadVersion": "1.0.0",
            "episodeDate": date,
            "intent": {"beats": intents},
            "provisionalDirection": {"requirements": requirements},
        },
    )
elif mode == "director":
    catalog = json.loads((vi / "visual_candidate_catalog.json").read_text(encoding="utf-8"))
    by_beat = {}
    for candidate in catalog["candidates"]:
        by_beat.setdefault(candidate["visualBeatId"], []).append(candidate)
    selections = []
    beats = [beat for scene in render["scenes"] for beat in scene["visualBeats"]]
    for beat in beats:
        legal = by_beat[beat["beatId"]]
        selected = m.identity_candidate(beat, legal)
        alternative = next((item for item in legal if item["candidateId"] != selected["candidateId"]), None)
        selections.append({
            "visualBeatId": beat["beatId"],
            "selectedCandidateId": selected["candidateId"],
            "strongestAlternativeCandidateId": alternative["candidateId"] if alternative else None,
            "whySelected": "identity-preserving synthetic runtime qualification",
            "whyNotAlternative": "fixture validates machinery, not editorial preference" if alternative else "",
        })
    m.write_json(
        vi / m.artifacts.DIRECTOR_SEMANTIC,
        {"semanticPayloadVersion": "1.0.0", "episodeDate": date, "selections": selections},
    )
elif mode == "critic":
    m.write_json(
        vi / m.artifacts.CRITIC_SEMANTIC,
        {
            "semanticPayloadVersion": "1.0.0",
            "episodeDate": date,
            "reviewRounds": [{
                "round": 1,
                "status": "PASS",
                "findings": [],
                "viewerImpact": "none in synthetic runtime qualification fixture",
                "reason": "existing fixture-only post-compile review",
            }],
        },
    )
else:
    raise SystemExit(f"unknown mode: {mode}")
'''
    run(
        [sys.executable, "-c", code, mode, "unused-renderer-root", env["QUALIFICATION_DATE"]],
        cwd=root,
        env=env,
    )


def expect_gate(value: dict[str, Any], *, status: str, action: str | None = None) -> None:
    if value.get("status") != status:
        raise RuntimeError(f"unexpected closure status: expected={status} actual={value}")
    if action is not None and value.get("requiredAction") != action:
        raise RuntimeError(f"unexpected closure action: expected={action} actual={value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-root", required=True, type=Path)
    parser.add_argument("--renderer-root", required=True, type=Path)
    parser.add_argument("--renderer-commit", required=True)
    parser.add_argument("--renderer-contract-version", default="2.4.0")
    parser.add_argument("--work-parent", required=True, type=Path)
    parser.add_argument("--bundle-root", required=True, type=Path)
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--plot-commit", required=True)
    args = parser.parse_args()

    source_root = args.plot_root.resolve()
    renderer_root = args.renderer_root.resolve()
    actual_renderer = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=renderer_root, check=True, capture_output=True, text=True
    ).stdout.strip()
    if actual_renderer != args.renderer_commit:
        raise RuntimeError(
            f"Renderer checkout mismatch: expected={args.renderer_commit} actual={actual_renderer}"
        )

    root, fx, _authoring = prepare_fixture(source_root, args.work_parent.resolve())
    date = fx.DATE
    registry_sha = install_renderer_binding(
        root, renderer_root, args.renderer_commit, args.renderer_contract_version
    )

    freeze_path = root / "semantic-freezes" / f"{date}.json"
    env = os.environ.copy()
    env["NASDAQ_CAFE_SEMANTIC_FREEZE_PATH"] = str(freeze_path)
    env["NASDAQ_CAFE_SEMANTIC_FREEZE_SHA256"] = sha256_file(freeze_path)
    env["NASDAQ_CAFE_RENDERER_ROOT"] = str(renderer_root)
    env["PYTHONPATH"] = str(root / "scripts")
    env["QUALIFICATION_DATE"] = date

    first = closure(root, renderer_root, date, "prepare", env)
    expect_gate(first, status="PREPARED", action="AUTHOR_VISUAL_REQUIREMENTS")
    run_fixture_semantic_writer(root, "requirements", env)

    second = closure(root, renderer_root, date, "prepare", env)
    expect_gate(second, status="PREPARED", action="AUTHOR_VISUAL_INTELLIGENCE_DECISION")
    run_fixture_semantic_writer(root, "director", env)

    third = closure(root, renderer_root, date, "compile", env)
    expect_gate(third, status="REVIEW_REQUIRED")
    run_fixture_semantic_writer(root, "critic", env)

    final_gate = closure(root, renderer_root, date, "compile", env)
    expect_gate(final_gate, status="PASS")

    state = load_json(root / "working" / date / "production_state.json")
    if state.get("current_state") != "production_package_valid":
        raise RuntimeError(f"qualification did not reach production_package_valid: {state.get('current_state')}")

    bundle_root = args.bundle_root.resolve()
    completed = run(
        [
            sys.executable,
            "scripts/run_daily_production_v12.py",
            "--workspace",
            ".",
            "build-handoff",
            "--episode-date",
            date,
            "--bundle-root",
            str(bundle_root),
            "--plot-commit",
            args.plot_commit,
        ],
        cwd=root,
        env=env,
    )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"cannot parse build-handoff result: {exc}") from exc
    manifest_path = Path(result["manifest_path"]).resolve()
    bundle_path = Path(result["bundle_path"]).resolve()
    bundle_id = result["bundle_id"]
    if not manifest_path.is_file() or not bundle_path.is_dir():
        raise RuntimeError("qualification handoff output is missing")

    artifact_root = args.artifact_root.resolve()
    shutil.rmtree(artifact_root, ignore_errors=True)
    artifact_root.mkdir(parents=True)
    shutil.copytree(bundle_path, artifact_root / bundle_id)
    receipt = {
        "status": "PASS",
        "qualificationOnly": True,
        "episodeDate": date,
        "bundleId": bundle_id,
        "manifestSha256": sha256_file(manifest_path),
        "rendererCommit": args.renderer_commit,
        "rendererContractVersion": args.renderer_contract_version,
        "registrySnapshotSha256": registry_sha,
        "plotCommit": args.plot_commit,
        "finalAuthorized": False,
    }
    write_json(artifact_root / "qualification_receipt.json", receipt)
    print("QUALIFICATION_RECEIPT=" + json.dumps(receipt, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
