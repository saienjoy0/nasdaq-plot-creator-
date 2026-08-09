#!/usr/bin/env python3
"""Freeze a validated daily production run as the Visual Source baseline.

This script does not create or edit editorial content. It records the exact
post-production artifacts, renderer pin, Story Engine certification status and
immutable handoff identity after the existing hardened pipeline has passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class BaselineError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise BaselineError(f"{label} root must be an object")
    return value


def safe_file(root: Path, relative: str, label: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise BaselineError(f"{label} path must be safe and relative: {relative}")
    root = root.resolve()
    resolved = (root / path).resolve()
    if resolved != root and root not in resolved.parents:
        raise BaselineError(f"{label} path escapes repository: {relative}")
    if not resolved.is_file() or resolved.stat().st_size == 0:
        raise BaselineError(f"{label} missing or empty: {relative}")
    return resolved


def find_handoff_manifest(
    bundle_root: Path,
    *,
    episode_date: str,
    plot_commit: str,
    renderer_commit: str,
    renderer_contract_version: str,
) -> tuple[Path, dict[str, Any]]:
    date_root = bundle_root / episode_date
    if not date_root.is_dir():
        raise BaselineError(f"handoff date directory missing: {date_root}")
    matches: list[tuple[Path, dict[str, Any]]] = []
    for manifest_path in sorted(date_root.glob("*/handoff_manifest.json")):
        manifest = load_json(manifest_path, "handoff manifest")
        if manifest.get("episode_date") != episode_date:
            continue
        if manifest.get("mode") != "preview":
            continue
        plot = manifest.get("plot_creator", {})
        renderer = manifest.get("renderer", {})
        if not isinstance(plot, dict) or not isinstance(renderer, dict):
            continue
        if plot.get("commit") != plot_commit:
            continue
        if renderer.get("expected_base_commit") != renderer_commit:
            continue
        if renderer.get("expected_contract_version") != renderer_contract_version:
            continue
        matches.append((manifest_path, manifest))
    if len(matches) != 1:
        raise BaselineError(
            "expected exactly one matching preview handoff manifest; "
            f"found={len(matches)}"
        )
    return matches[0]


def build_baseline(
    *,
    repo_root: Path,
    episode_date: str,
    plot_commit: str,
    renderer_commit: str,
    renderer_contract_version: str,
    bundle_root: Path,
) -> dict[str, Any]:
    if not DATE_RE.fullmatch(episode_date):
        raise BaselineError("episode_date must be YYYY-MM-DD")
    if not SHA40_RE.fullmatch(plot_commit):
        raise BaselineError("plot_commit must be a 40-character lowercase hex SHA")
    if not SHA40_RE.fullmatch(renderer_commit):
        raise BaselineError("renderer_commit must be a 40-character lowercase hex SHA")

    root = repo_root.resolve()
    paths = {
        "episode_package": f"episodes/{episode_date}/episode_package_{episode_date}.md",
        "spoken_script": f"episodes/{episode_date}/spoken_script_{episode_date}.md",
        "asset_manifest": f"episodes/{episode_date}/asset_manifest.json",
        "render_spec": f"render-specs/{episode_date}/render_spec.json",
        "official_execution_preflight": f"verification/{episode_date}/official_execution_preflight.json",
        "production_consistency_report": f"verification/{episode_date}/production_consistency_report.json",
        "story_engine_acceptance": f"working/{episode_date}/story-engine/story_engine_acceptance.json",
    }
    resolved = {key: safe_file(root, value, key) for key, value in paths.items()}

    preflight = load_json(resolved["official_execution_preflight"], "official preflight")
    if preflight.get("status") != "pass" or preflight.get("unresolved_states") != 0:
        raise BaselineError("official preflight must pass with zero unresolved states")
    if preflight.get("preview_authorized") is not True:
        raise BaselineError("official preflight must authorize preview")
    if preflight.get("final_authorized") is True:
        raise BaselineError("baseline must not be final-authorized")

    consistency = load_json(
        resolved["production_consistency_report"], "production consistency report"
    )
    if consistency.get("status") != "pass" or consistency.get("unresolved_states") != 0:
        raise BaselineError("production consistency report must pass")

    render_spec = load_json(resolved["render_spec"], "render spec")
    if render_spec.get("schemaVersion") != renderer_contract_version:
        raise BaselineError("strict render_spec schemaVersion does not match renderer contract")
    episode = render_spec.get("episode", {})
    if not isinstance(episode, dict) or episode.get("targetDate") != episode_date:
        raise BaselineError("strict render_spec targetDate mismatch")

    acceptance = load_json(resolved["story_engine_acceptance"], "Story Engine acceptance")
    critic = acceptance.get("critic", {})
    if not isinstance(critic, dict):
        raise BaselineError("Story Engine acceptance critic must be an object")
    external_status = critic.get("external_critic_status", "not_certified")
    critic_certified = bool(critic.get("critic_certified", False))
    production_policy = acceptance.get("production_policy") or critic.get("production_policy")
    production_allowed = acceptance.get("production_allowed_by_policy")
    if production_allowed is not True:
        raise BaselineError("Story Engine production must be allowed by the selected policy")

    handoff_path, handoff = find_handoff_manifest(
        bundle_root.resolve(),
        episode_date=episode_date,
        plot_commit=plot_commit,
        renderer_commit=renderer_commit,
        renderer_contract_version=renderer_contract_version,
    )
    bundle_id = handoff.get("bundle_id")
    if not isinstance(bundle_id, str) or not SHA256_RE.fullmatch(bundle_id):
        raise BaselineError("handoff bundle_id must be a SHA-256")

    artifacts = {
        key: {
            "path": paths[key],
            "sha256": sha256_file(path),
        }
        for key, path in resolved.items()
    }
    return {
        "contract_version": "1.0.0",
        "episode_date": episode_date,
        "status": "pass",
        "purpose": "visual-source-preimplementation-baseline",
        "plot": {
            "repository": "saienjoy0/nasdaq-plot-creator-",
            "commit": plot_commit,
        },
        "renderer": {
            "repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion",
            "commit": renderer_commit,
            "contract_version": renderer_contract_version,
        },
        "story_engine": {
            "production_allowed_by_policy": True,
            "production_policy": production_policy,
            "critic_certified": critic_certified,
            "external_critic_status": external_status,
        },
        "artifacts": artifacts,
        "handoff": {
            "bundle_id": bundle_id,
            "manifest_path": handoff_path.relative_to(root).as_posix()
            if root in handoff_path.resolve().parents
            else handoff_path.as_posix(),
            "manifest_sha256": sha256_file(handoff_path),
            "mode": "preview",
        },
        "validation": {
            "official_preflight": "pass",
            "production_consistency": "pass",
            "strict_renderer_contract": "pass",
            "unresolved_states": 0,
            "final_authorized": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--episode-date", required=True)
    parser.add_argument("--plot-commit", required=True)
    parser.add_argument("--renderer-commit", required=True)
    parser.add_argument("--renderer-contract-version", required=True)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        value = build_baseline(
            repo_root=args.repo_root,
            episode_date=args.episode_date,
            plot_commit=args.plot_commit,
            renderer_commit=args.renderer_commit,
            renderer_contract_version=args.renderer_contract_version,
            bundle_root=args.bundle_root,
        )
        code = 0
    except (BaselineError, OSError, json.JSONDecodeError, ValueError) as exc:
        value = {"status": "fail", "errors": [str(exc)]}
        code = 1
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    if code:
        print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
