#!/usr/bin/env python3
"""Guard renderer handoff with persisted and rechecked episode-memory evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]

BASE_HARDENING = {"pre_build": "pass", "public_artifacts": "pass"}
HANDOFF_HARDENING = {
    "pre_build": "pass",
    "public_artifacts": "pass",
    "handoff_recheck": "pass",
}


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


def _real_gate(source_root: Path, package: Path, artifacts: list[Path]):
    module = _load_module(
        "episode_memory_handoff_recheck",
        source_root
        / "skills/nasdaq-cafe-episode-package-memory/validators/validate_episode_package_memory_hardening.py",
    )
    return module.validate_hardening(
        repo_root=source_root,
        episode_package=package,
        public_artifacts=artifacts,
    )


def _safe_file(source_root: Path, path: Path, label: str) -> Path:
    root = source_root.resolve()
    resolved = path.resolve()
    if resolved != root and root not in resolved.parents:
        raise HardenedHandoffError(f"{label} escapes source root: {path}")
    if not resolved.is_file():
        raise HardenedHandoffError(f"{label} does not exist: {path}")
    return resolved


def _preflight_path(source_root: Path, date: str) -> Path:
    return _safe_file(
        source_root,
        source_root / f"verification/{date}/official_execution_preflight.json",
        "preflight",
    )


def _load_preflight(source_root: Path, date: str) -> tuple[Path, dict[str, Any]]:
    path = _preflight_path(source_root, date)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HardenedHandoffError(f"invalid preflight: {exc}") from exc
    if not isinstance(value, dict):
        raise HardenedHandoffError("preflight must be an object")
    hardening = value.get("episode_memory_hardening")
    if not isinstance(hardening, dict) or any(
        hardening.get(key) != expected for key, expected in BASE_HARDENING.items()
    ):
        raise HardenedHandoffError(
            f"preflight episode_memory_hardening must contain {BASE_HARDENING!r}"
        )
    return path, value


def _current_public_artifacts(source_root: Path, date: str) -> tuple[Path, list[Path]]:
    package = _safe_file(
        source_root,
        source_root / f"episodes/{date}/episode_package_{date}.md",
        "episode package",
    )
    artifacts = [
        _safe_file(
            source_root,
            source_root / f"episodes/{date}/spoken_script_{date}.md",
            "spoken script",
        ),
        _safe_file(
            source_root,
            source_root / f"episodes/{date}/asset_manifest.json",
            "asset manifest",
        ),
        _safe_file(
            source_root,
            source_root / f"render-specs/{date}/render_spec.json",
            "render spec",
        ),
    ]
    return package, artifacts


def _gate_errors(result: Any) -> list[str]:
    errors = getattr(result, "errors", None)
    if isinstance(errors, list):
        return list(errors)
    if isinstance(result, dict) and result.get("status") == "fail":
        value = result.get("errors", [])
        return list(value) if isinstance(value, list) else [str(value)]
    return []


def _persist_handoff_recheck(path: Path, value: dict[str, Any]) -> None:
    value = dict(value)
    hardening = dict(value.get("episode_memory_hardening", {}))
    hardening.update(HANDOFF_HARDENING)
    value["episode_memory_hardening"] = hardening
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(path.name + ".handoff-hardening.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _restore_preflight(path: Path, original_bytes: bytes) -> None:
    tmp = path.with_name(path.name + ".handoff-restore.tmp")
    try:
        tmp.write_bytes(original_bytes)
        tmp.replace(path)
    except OSError as exc:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise HardenedHandoffError(
            f"failed to restore immutable production preflight: {exc}"
        ) from exc


def _verify_bundled_preflight(result: dict[str, Any]) -> None:
    bundle = Path(str(result.get("bundle_path", "")))
    path = bundle / "production/official_execution_preflight.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HardenedHandoffError(f"bundled preflight invalid: {exc}") from exc
    if not isinstance(value, dict) or value.get("episode_memory_hardening") != HANDOFF_HARDENING:
        raise HardenedHandoffError(
            "bundled preflight lost complete episode-memory hardening evidence"
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
    gate: Callable[[Path, Path, list[Path]], Any] = _real_gate,
    builder: Callable[..., dict[str, Any]] = _real_builder,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    preflight_path, preflight = _load_preflight(source_root, date)
    package, artifacts = _current_public_artifacts(source_root, date)
    gate_result = gate(source_root, package, artifacts)
    errors = _gate_errors(gate_result)
    if errors:
        raise HardenedHandoffError(
            "handoff-time episode-memory recheck failed:\n" + "\n".join(errors)
        )

    # production_package_valid has already hash-bound the source preflight.
    # Temporarily augment only the copy consumed by the handoff builder, then
    # restore the exact original bytes before returning or raising.
    original_preflight = preflight_path.read_bytes()
    _persist_handoff_recheck(preflight_path, preflight)
    result: dict[str, Any] | None = None
    try:
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
    finally:
        _restore_preflight(preflight_path, original_preflight)

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
