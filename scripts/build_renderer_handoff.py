#!/usr/bin/env python3
"""Build an immutable, SHA-bound renderer handoff bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

REQUIRED_ROLES = {
    "episode_package": "episodes/{date}/episode_package_{date}.md",
    "spoken_script": "episodes/{date}/spoken_script_{date}.md",
    "asset_manifest": "episodes/{date}/asset_manifest.json",
    "render_spec": "render-specs/{date}/render_spec.json",
    "preflight": "verification/{date}/official_execution_preflight.json",
    "consistency_report": "verification/{date}/production_consistency_report.json",
}


class HandoffError(ValueError):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def safe_resolve(root: Path, relative: str, label: str, *, must_exist: bool = True) -> Path:
    path = Path(relative)
    if path.is_absolute():
        raise HandoffError(f"{label}: absolute path is forbidden: {relative}")
    root = root.resolve()
    resolved = (root / path).resolve()
    if resolved != root and root not in resolved.parents:
        raise HandoffError(f"{label}: path escapes root: {relative}")
    if must_exist and not resolved.is_file():
        raise HandoffError(f"{label}: file does not exist: {relative}")
    return resolved


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HandoffError(f"{label}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise HandoffError(f"{label}: top-level JSON must be an object")
    return value


def validate_preflight(preflight: dict[str, Any], date: str, mode: str) -> None:
    if preflight.get("status") != "pass":
        raise HandoffError("preflight.status must be pass")
    if preflight.get("episode_date") != date:
        raise HandoffError("preflight episode_date mismatch")
    if preflight.get("unresolved_states") != 0:
        raise HandoffError("preflight unresolved_states must be zero")
    if preflight.get("preview_authorized") is not True:
        raise HandoffError("preflight preview_authorized must be true")
    if mode == "preview" and preflight.get("final_authorized") is True:
        raise HandoffError("preview handoff cannot use a final-authorized preflight")
    if mode == "final" and preflight.get("final_authorized") is not True:
        raise HandoffError("final handoff requires final_authorized preflight")


def validate_approval(record: dict[str, Any] | None, date: str, mode: str) -> dict[str, Any] | None:
    if mode == "preview":
        if record is not None:
            raise HandoffError("preview mode must not include a final approval record")
        return None
    if record is None:
        raise HandoffError("final mode requires an explicit approval record")
    required = {"episode_date": date, "approval_status": "approved_preview", "final_requested": True}
    for key, wanted in required.items():
        if record.get(key) != wanted:
            raise HandoffError(f"approval_record.{key} must be {wanted!r}")
    preview_manifest_sha = record.get("preview_manifest_sha256")
    if not isinstance(preview_manifest_sha, str) or len(preview_manifest_sha) != 64:
        raise HandoffError("approval_record.preview_manifest_sha256 must be a 64-hex SHA")
    try:
        int(preview_manifest_sha, 16)
    except ValueError as exc:
        raise HandoffError("approval_record.preview_manifest_sha256 must be hexadecimal") from exc
    return record


def destination_for(role: str, source: Path, date: str) -> str:
    if role == "render_spec":
        return f"render-specs/{date}/render_spec.json"
    if role == "asset":
        return f"assets/{source.name}"
    return f"production/{source.name}"


def build_manifest_without_id(*, date: str, mode: str, plot_commit: str, renderer_commit: str, renderer_contract_version: str, files: list[dict[str, Any]], preflight_sha: str, final_authorized: bool, approval_record: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "contract_version": "1.0.0",
        "episode_date": date,
        "mode": mode,
        "plot_creator": {"repository": "saienjoy0/nasdaq-plot-creator-", "commit": plot_commit},
        "renderer": {
            "repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion",
            "expected_contract_version": renderer_contract_version,
            "expected_base_commit": renderer_commit,
        },
        "files": sorted(files, key=lambda item: (item["role"], item["destination_path"])),
        "validation": {"production_package": "pass", "unresolved_states": 0, "source_preflight_sha256": preflight_sha},
        "final_authorized": final_authorized,
        "approval_record": approval_record,
    }


def validate_manifest_paths(manifest: dict[str, Any]) -> None:
    destinations: set[str] = set()
    source_paths: set[str] = set()
    for index, item in enumerate(manifest["files"]):
        for field in ("source_path", "destination_path"):
            value = item[field]
            path = Path(value)
            if path.is_absolute() or ".." in path.parts:
                raise HandoffError(f"files[{index}].{field} must be safe and relative")
        if item["destination_path"] in destinations:
            raise HandoffError(f"duplicate destination_path: {item['destination_path']}")
        destinations.add(item["destination_path"])
        if item["source_path"] in source_paths and item["role"] != "asset":
            raise HandoffError(f"duplicate source_path: {item['source_path']}")
        source_paths.add(item["source_path"])
    roles = {item["role"] for item in manifest["files"]}
    missing = set(REQUIRED_ROLES) - roles
    if missing:
        raise HandoffError(f"handoff manifest missing required roles: {sorted(missing)}")


def build_handoff(*, source_root: Path, bundle_root: Path, date: str, mode: str, plot_commit: str, renderer_commit: str, renderer_contract_version: str, approval_path: Path | None = None) -> dict[str, Any]:
    if mode not in {"preview", "final"}:
        raise HandoffError("mode must be preview or final")
    for label, value in (("plot_commit", plot_commit), ("renderer_commit", renderer_commit)):
        if len(value) != 40:
            raise HandoffError(f"{label} must be a 40-character commit SHA")
        try:
            int(value, 16)
        except ValueError as exc:
            raise HandoffError(f"{label} must be hexadecimal") from exc

    source_root = source_root.resolve()
    bundle_root = bundle_root.resolve()
    sources: dict[str, Path] = {}
    for role, template in REQUIRED_ROLES.items():
        relative = template.format(date=date)
        sources[role] = safe_resolve(source_root, relative, role)

    preflight = load_json(sources["preflight"], "preflight")
    validate_preflight(preflight, date, mode)
    consistency = load_json(sources["consistency_report"], "consistency report")
    if consistency.get("status") != "pass" or consistency.get("unresolved_states") != 0:
        raise HandoffError("production consistency report must pass with zero unresolved states")
    render_spec = load_json(sources["render_spec"], "render spec")
    if render_spec.get("episode", {}).get("targetDate") != date:
        raise HandoffError("render spec targetDate mismatch")
    if render_spec.get("schemaVersion") != renderer_contract_version:
        raise HandoffError("render spec schemaVersion does not match renderer contract version")
    asset_manifest = load_json(sources["asset_manifest"], "asset manifest")
    if asset_manifest.get("episode_date") != date:
        raise HandoffError("asset manifest episode_date mismatch")
    if asset_manifest.get("selected_path") not in {"primary", "fallback", "not-required"}:
        raise HandoffError("asset manifest selected_path is unresolved")

    approval_record = load_json(approval_path.resolve(), "approval record") if approval_path else None
    approval_record = validate_approval(approval_record, date, mode)

    file_records: list[dict[str, Any]] = []
    copy_plan: list[tuple[Path, str]] = []
    for role, source in sources.items():
        rel_source = source.relative_to(source_root).as_posix()
        destination = destination_for(role, source, date)
        file_records.append({
            "role": role, "source_path": rel_source, "destination_path": destination,
            "sha256": sha256_file(source), "size": source.stat().st_size, "required": True,
        })
        copy_plan.append((source, destination))

    for asset in asset_manifest.get("assets", []):
        if not isinstance(asset, dict):
            raise HandoffError("asset manifest assets must be objects")
        if asset.get("status") == "not-required":
            continue
        asset_id = asset.get("asset_id")
        path_value = asset.get("path")
        if not isinstance(asset_id, str) or not isinstance(path_value, str):
            raise HandoffError("asset manifest ready asset requires asset_id and path")
        source = safe_resolve(source_root, path_value, f"asset {asset_id}")
        declared_sha = asset.get("sha256")
        actual_sha = sha256_file(source)
        if declared_sha is not None and declared_sha != actual_sha:
            raise HandoffError(f"asset {asset_id} SHA mismatch")
        destination = f"assets/{asset_id}/{source.name}"
        file_records.append({
            "role": "asset", "source_path": source.relative_to(source_root).as_posix(),
            "destination_path": destination, "sha256": actual_sha,
            "size": source.stat().st_size, "required": True,
        })
        copy_plan.append((source, destination))

    preflight_sha = sha256_file(sources["preflight"])
    manifest_core = build_manifest_without_id(
        date=date, mode=mode, plot_commit=plot_commit, renderer_commit=renderer_commit,
        renderer_contract_version=renderer_contract_version, files=file_records,
        preflight_sha=preflight_sha, final_authorized=(mode == "final"), approval_record=approval_record,
    )
    validate_manifest_paths(manifest_core)
    bundle_id = sha256_bytes(canonical_json(manifest_core))
    manifest = {"contract_version": manifest_core.pop("contract_version"), "bundle_id": bundle_id, **manifest_core}

    target = bundle_root / date / bundle_id
    if target.exists():
        existing_manifest = target / "handoff_manifest.json"
        if not existing_manifest.is_file():
            raise HandoffError("existing bundle directory lacks handoff_manifest.json")
        existing = load_json(existing_manifest, "existing handoff manifest")
        if existing != manifest:
            raise HandoffError("existing bundle ID contains different manifest content")
        for item in manifest["files"]:
            copied = target / item["destination_path"]
            if not copied.is_file() or sha256_file(copied) != item["sha256"]:
                raise HandoffError(f"existing bundle file is missing or modified: {item['destination_path']}")
        return {"status": "noop", "bundle_id": bundle_id, "bundle_path": str(target), "manifest_path": str(existing_manifest)}

    staging = bundle_root / date / f".{bundle_id}.staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    try:
        for source, destination in copy_plan:
            dest = safe_resolve(staging, destination, "bundle destination", must_exist=False)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
        manifest_path = staging / "handoff_manifest.json"
        manifest_path.write_bytes(canonical_json(manifest))
        for item in manifest["files"]:
            copied = staging / item["destination_path"]
            if sha256_file(copied) != item["sha256"] or copied.stat().st_size != item["size"]:
                raise HandoffError(f"staged file verification failed: {item['destination_path']}")
        staging.replace(target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {"status": "created", "bundle_id": bundle_id, "bundle_path": str(target), "manifest_path": str(target / "handoff_manifest.json")}


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
        result = build_handoff(
            source_root=args.source_root, bundle_root=args.bundle_root, date=args.episode_date,
            mode=args.mode, plot_commit=args.plot_commit, renderer_commit=args.renderer_commit,
            renderer_contract_version=args.renderer_contract_version, approval_path=args.approval_record,
        )
        code = 0
    except (HandoffError, OSError, json.JSONDecodeError) as exc:
        result = {"status": "fail", "errors": [str(exc)]}
        code = 1
    data = canonical_json(result)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_bytes(data)
    else:
        sys.stdout.buffer.write(data)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
