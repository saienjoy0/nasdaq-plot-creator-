#!/usr/bin/env python3
"""Guard renderer handoff with persisted episode-memory hardening evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]


class HardenedHandoffError(ValueError):
    pass


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise HardenedHandoffError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _real_builder(**kwargs):
    module = _load_module(
        "renderer_handoff_base", ROOT / "scripts/build_renderer_handoff.py"
    )
    return module.build_handoff(**kwargs)


def _load_preflight(source_root: Path, date: str) -> dict[str, Any]:
    path = (source_root / f"verification/{date}/official_execution_preflight.json").resolve()
    root = source_root.resolve()
    if path != root and root not in path.parents:
        raise HardenedHandoffError("preflight path escapes source root")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HardenedHandoffError(f"invalid preflight: {exc}") from exc
    if not isinstance(value, dict):
        raise HardenedHandoffError("preflight must be an object")
    wanted = {"pre_build": "pass", "public_artifacts": "pass"}
    if value.get("episode_memory_hardening") != wanted:
        raise HardenedHandoffError(
            f"preflight episode_memory_hardening must be {wanted!r}"
        )
    return value


def _verify_bundled_preflight(result: dict[str, Any]) -> None:
    bundle = Path(str(result.get("bundle_path", "")))
    path = bundle / "production/official_execution_preflight.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HardenedHandoffError(f"bundled preflight invalid: {exc}") from exc
    wanted = {"pre_build": "pass", "public_artifacts": "pass"}
    if value.get("episode_memory_hardening") != wanted:
        raise HardenedHandoffError(
            "bundled preflight lost episode-memory hardening evidence"
        )


def build_handoff_hardened(
    *,
    source_root: Path,
    bundle_root: Path,
    date: str,
    mode: str,
    plot_commit: str,
    renderer_commit: str,
    renderer_contract_version: str,
    approval_path: Path | None = None,
    builder: Callable[..., dict[str, Any]] = _real_builder,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    _load_preflight(source_root, date)
    result = builder(
        source_root=source_root,
        bundle_root=bundle_root,
        date=date,
        mode=mode,
        plot_commit=plot_commit,
        renderer_commit=renderer_commit,
        renderer_contract_version=renderer_contract_version,
        approval_path=approval_path,
    )
    if not isinstance(result, dict) or result.get("status") not in {"created", "noop"}:
        raise HardenedHandoffError(
            "base handoff builder did not return created/noop"
        )
    try:
        _verify_bundled_preflight(result)
    except Exception:
        if result.get("status") == "created":
            shutil.rmtree(Path(str(result.get("bundle_path", ""))), ignore_errors=True)
        raise
    result["episode_memory_hardening"] = "pass"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--bundle-root", required=True, type=Path)
    parser.add_argument("--episode-date", required=True)
    parser.add_argument("--mode", choices=["preview", "final"], default="preview")
    parser.add_argument("--plot-commit", required=True)
    parser.add_argument("--renderer-commit", required=True)
    parser.add_argument("--renderer-contract-version", required=True)
    parser.add_argument("--approval-record", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = build_handoff_hardened(
            source_root=args.source_root,
            bundle_root=args.bundle_root,
            date=args.episode_date,
            mode=args.mode,
            plot_commit=args.plot_commit,
            renderer_commit=args.renderer_commit,
            renderer_contract_version=args.renderer_contract_version,
            approval_path=args.approval_record,
        )
        code = 0
    except (HardenedHandoffError, OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"status": "fail", "errors": [str(exc)]}
        code = 1
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
