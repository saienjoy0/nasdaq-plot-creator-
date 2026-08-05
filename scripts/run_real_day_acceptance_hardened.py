#!/usr/bin/env python3
"""Guard real-day preview acceptance with bundled episode-memory evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]


class HardenedAcceptanceError(ValueError):
    pass


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise HardenedAcceptanceError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _real_validator(**kwargs):
    module = _load_module(
        "real_day_acceptance_base", ROOT / "scripts/run_real_day_acceptance.py"
    )
    return module.validate_acceptance(**kwargs)


def _safe_file(root: Path, value: Path, label: str) -> Path:
    root = root.resolve()
    resolved = value.resolve() if value.is_absolute() else (root / value).resolve()
    if resolved != root and root not in resolved.parents:
        raise HardenedAcceptanceError(f"{label} escapes root: {value}")
    if not resolved.is_file():
        raise HardenedAcceptanceError(f"{label} does not exist: {value}")
    return resolved


def _verify_bundle_hardening(bundle_root: Path, manifest_path: Path) -> None:
    manifest_file = _safe_file(bundle_root, manifest_path, "handoff manifest")
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HardenedAcceptanceError(f"invalid handoff manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise HardenedAcceptanceError("handoff manifest must be an object")
    preflight_items = [
        item
        for item in manifest.get("files", [])
        if isinstance(item, dict) and item.get("role") == "preflight"
    ]
    if len(preflight_items) != 1:
        raise HardenedAcceptanceError(
            f"handoff manifest must contain exactly one preflight role: found={len(preflight_items)}"
        )
    destination = preflight_items[0].get("destination_path")
    if not isinstance(destination, str):
        raise HardenedAcceptanceError("preflight destination_path is required")
    preflight_path = _safe_file(manifest_file.parent, Path(destination), "bundled preflight")
    try:
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HardenedAcceptanceError(f"invalid bundled preflight: {exc}") from exc
    wanted = {"pre_build": "pass", "public_artifacts": "pass"}
    if not isinstance(preflight, dict) or preflight.get("episode_memory_hardening") != wanted:
        raise HardenedAcceptanceError(
            "bundled preflight lacks complete episode-memory hardening evidence"
        )


def validate_acceptance_hardened(
    *,
    episode_date: str,
    daily_source_root: Path,
    daily_source_path: Path,
    bundle_root: Path,
    handoff_manifest_path: Path,
    renderer_artifact_root: Path,
    technical_report_path: Path,
    user_review_path: Path | None = None,
    validator: Callable[..., dict[str, Any]] = _real_validator,
) -> dict[str, Any]:
    _verify_bundle_hardening(bundle_root, handoff_manifest_path)
    result = validator(
        episode_date=episode_date,
        daily_source_root=daily_source_root,
        daily_source_path=daily_source_path,
        bundle_root=bundle_root,
        handoff_manifest_path=handoff_manifest_path,
        renderer_artifact_root=renderer_artifact_root,
        technical_report_path=technical_report_path,
        user_review_path=user_review_path,
    )
    if not isinstance(result, dict) or result.get("validation", {}).get("status") != "pass":
        raise HardenedAcceptanceError(
            "base real-day acceptance did not return validation PASS"
        )
    result["episode_memory_hardening"] = "pass"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-date", required=True)
    parser.add_argument("--daily-source-root", required=True, type=Path)
    parser.add_argument("--daily-source-package", required=True, type=Path)
    parser.add_argument("--bundle-root", required=True, type=Path)
    parser.add_argument("--handoff-manifest", required=True, type=Path)
    parser.add_argument("--renderer-artifact-root", required=True, type=Path)
    parser.add_argument("--technical-report", required=True, type=Path)
    parser.add_argument("--user-review", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate_acceptance_hardened(
            episode_date=args.episode_date,
            daily_source_root=args.daily_source_root,
            daily_source_path=args.daily_source_package,
            bundle_root=args.bundle_root,
            handoff_manifest_path=args.handoff_manifest,
            renderer_artifact_root=args.renderer_artifact_root,
            technical_report_path=args.technical_report,
            user_review_path=args.user_review,
        )
        base = _load_module(
            "real_day_acceptance_writer", ROOT / "scripts/run_real_day_acceptance.py"
        )
        paths = base.write_report(result, args.output_dir)
        output = {"status": "pass", "mvp_status": result["mvp_status"], "paths": paths}
        code = 0
    except (HardenedAcceptanceError, OSError, ValueError, json.JSONDecodeError) as exc:
        output = {"status": "fail", "errors": [str(exc)]}
        code = 1
    sys.stdout.write(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
