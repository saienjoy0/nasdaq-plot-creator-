#!/usr/bin/env python3
"""Build and validate append-only research evidence supplement lineage."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


CONTRACT_VERSION = "1.0.0"
MAX_WAVES = 2


class SupplementError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SupplementError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SupplementError(f"{path}: root must be an object")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_repo_file(repo_root: Path, value: str, label: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        raise SupplementError(f"{label}: absolute paths are forbidden")
    root = repo_root.resolve()
    resolved = (root / path).resolve()
    if resolved != root and root not in resolved.parents:
        raise SupplementError(f"{label}: path escapes repository root: {value}")
    if not resolved.is_file():
        raise SupplementError(f"{label}: file does not exist: {value}")
    return resolved


def repo_relative(repo_root: Path, path: Path) -> str:
    root = repo_root.resolve()
    resolved = path.resolve()
    if resolved != root and root not in resolved.parents:
        raise SupplementError(f"path escapes repository root: {path}")
    return resolved.relative_to(root).as_posix()


def file_ref(repo_root: Path, path: Path) -> dict[str, str]:
    return {
        "path": repo_relative(repo_root, path),
        "sha256": sha256_file(path),
    }


def validate_manifest(
    manifest_path: Path,
    *,
    repo_root: Path,
    schema_path: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    manifest_path = manifest_path.resolve()
    if manifest_path != repo_root and repo_root not in manifest_path.parents:
        raise SupplementError("supplement manifest path escapes repository root")
    manifest = load_json(manifest_path)
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    schema_errors = sorted(validator.iter_errors(manifest), key=lambda error: list(error.path))
    if schema_errors:
        raise SupplementError(
            "\n".join(
                f"{'.'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
                for error in schema_errors
            )
        )

    base_ref = manifest["baseResearchInputManifest"]
    base_path = resolve_repo_file(repo_root, base_ref["path"], "baseResearchInputManifest")
    if sha256_file(base_path) != base_ref["sha256"]:
        raise SupplementError("baseResearchInputManifest SHA-256 mismatch")
    base_manifest = load_json(base_path)
    if base_manifest.get("episode_date") != manifest["episodeDate"]:
        raise SupplementError("base research manifest episode date mismatch")

    seen_waves: set[int] = set()
    for wave_entry in manifest["waves"]:
        wave = wave_entry["wave"]
        if wave in seen_waves:
            raise SupplementError(f"duplicate supplement wave: {wave}")
        seen_waves.add(wave)
        if not 1 <= wave <= MAX_WAVES:
            raise SupplementError(f"wave must be 1..{MAX_WAVES}")

        request_path = _check_ref(repo_root, wave_entry["request"], f"wave {wave} request")
        result_path = _check_ref(repo_root, wave_entry["result"], f"wave {wave} result")
        request = load_json(request_path)
        result = load_json(result_path)

        if request.get("contractVersion") != CONTRACT_VERSION:
            raise SupplementError(f"wave {wave}: request contractVersion mismatch")
        if result.get("contractVersion") != CONTRACT_VERSION:
            raise SupplementError(f"wave {wave}: result contractVersion mismatch")
        if request.get("episodeDate") != manifest["episodeDate"]:
            raise SupplementError(f"wave {wave}: request episodeDate mismatch")
        if result.get("episodeDate") != manifest["episodeDate"]:
            raise SupplementError(f"wave {wave}: result episodeDate mismatch")
        if request.get("wave") != wave or result.get("wave") != wave:
            raise SupplementError(f"wave {wave}: embedded wave mismatch")
        request_sha = sha256_file(request_path)
        if result.get("requestSha256") != request_sha:
            raise SupplementError(f"wave {wave}: result requestSha256 mismatch")
        if request.get("baseResearchInputManifestSha256") != base_ref["sha256"]:
            raise SupplementError(f"wave {wave}: request is bound to a different base manifest")

        request_ids = [item.get("requestId") for item in request.get("requests", []) if isinstance(item, dict)]
        result_items = {
            item.get("requestId"): item
            for item in result.get("results", [])
            if isinstance(item, dict) and item.get("requestId")
        }
        if set(request_ids) != set(result_items):
            raise SupplementError(f"wave {wave}: request/result requestId sets differ")

        declared_evidence: dict[str, dict[str, str]] = {}
        for evidence_ref in wave_entry["evidenceFiles"]:
            request_id = evidence_ref["requestId"]
            if request_id in declared_evidence:
                raise SupplementError(f"wave {wave}: duplicate evidence file for {request_id}")
            evidence_path = _check_ref(repo_root, evidence_ref, f"wave {wave} evidence {request_id}")
            declared_evidence[request_id] = evidence_ref
            result_item = result_items.get(request_id)
            if not result_item:
                raise SupplementError(f"wave {wave}: evidence references unknown request {request_id}")
            if result_item.get("status") != "success":
                raise SupplementError(f"wave {wave}: non-success request {request_id} cannot declare evidence")
            if result_item.get("sha256") != evidence_ref["sha256"]:
                raise SupplementError(f"wave {wave}: copied evidence SHA differs from collector result for {request_id}")
            if sha256_file(evidence_path) != evidence_ref["sha256"]:
                raise SupplementError(f"wave {wave}: evidence file SHA mismatch for {request_id}")

        successful_ids = {
            request_id
            for request_id, item in result_items.items()
            if item.get("status") == "success" and item.get("sha256")
        }
        if successful_ids != set(declared_evidence):
            missing = sorted(successful_ids - set(declared_evidence))
            extra = sorted(set(declared_evidence) - successful_ids)
            raise SupplementError(
                f"wave {wave}: evidence files must exactly match successful results; missing={missing} extra={extra}"
            )

    return manifest


def append_wave(
    *,
    manifest_path: Path,
    repo_root: Path,
    episode_date: str,
    base_manifest_path: Path,
    wave: int,
    request_path: Path,
    result_path: Path,
    evidence_bindings: list[str],
    collector_run_id: int | None,
    schema_path: Path,
) -> dict[str, Any]:
    if not 1 <= wave <= MAX_WAVES:
        raise SupplementError(f"wave must be 1..{MAX_WAVES}")

    base_ref = file_ref(repo_root, base_manifest_path)
    request_ref = file_ref(repo_root, request_path)
    result_ref = file_ref(repo_root, result_path)
    request = load_json(request_path)
    result = load_json(result_path)
    if request.get("episodeDate") != episode_date or result.get("episodeDate") != episode_date:
        raise SupplementError("request/result episodeDate mismatch")
    if request.get("wave") != wave or result.get("wave") != wave:
        raise SupplementError("request/result wave mismatch")
    if request.get("baseResearchInputManifestSha256") != base_ref["sha256"]:
        raise SupplementError("request baseResearchInputManifestSha256 mismatch")
    if result.get("requestSha256") != request_ref["sha256"]:
        raise SupplementError("result requestSha256 mismatch")

    evidence_files: list[dict[str, Any]] = []
    for binding in evidence_bindings:
        if "=" not in binding:
            raise SupplementError("--evidence must use REQUEST_ID=PATH")
        request_id, raw_path = binding.split("=", 1)
        request_id = request_id.strip()
        path = Path(raw_path)
        if not path.is_absolute():
            path = (repo_root / path).resolve()
        ref = file_ref(repo_root, path)
        evidence_files.append({"requestId": request_id, **ref})

    if manifest_path.is_file():
        manifest = load_json(manifest_path)
        if manifest.get("contractVersion") != CONTRACT_VERSION:
            raise SupplementError("existing supplement contractVersion mismatch")
        if manifest.get("episodeDate") != episode_date:
            raise SupplementError("existing supplement episodeDate mismatch")
        if manifest.get("baseResearchInputManifest") != base_ref:
            raise SupplementError("existing supplement is bound to a different base manifest")
    else:
        manifest = {
            "contractVersion": CONTRACT_VERSION,
            "episodeDate": episode_date,
            "baseResearchInputManifest": base_ref,
            "waves": [],
        }

    if any(item.get("wave") == wave for item in manifest["waves"]):
        raise SupplementError(f"wave {wave} already exists; append-only manifest cannot overwrite it")
    if len(manifest["waves"]) >= MAX_WAVES:
        raise SupplementError(f"supplement already contains {MAX_WAVES} waves")

    wave_entry: dict[str, Any] = {
        "wave": wave,
        "request": request_ref,
        "result": result_ref,
        "evidenceFiles": evidence_files,
    }
    if collector_run_id is not None:
        wave_entry["collectorRunId"] = collector_run_id
    manifest["waves"].append(wave_entry)
    manifest["waves"].sort(key=lambda item: item["wave"])

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temp = manifest_path.with_name(f".{manifest_path.name}.tmp")
    temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(manifest_path)
    validate_manifest(manifest_path, repo_root=repo_root, schema_path=schema_path)
    return manifest


def _check_ref(repo_root: Path, ref: dict[str, Any], label: str) -> Path:
    path = resolve_repo_file(repo_root, ref["path"], label)
    actual = sha256_file(path)
    if actual != ref["sha256"]:
        raise SupplementError(f"{label}: SHA-256 mismatch")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("skills/nasdaq-cafe-causal-research/contracts/research_evidence_supplement_manifest.schema.json"),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate_cmd = sub.add_parser("validate")
    validate_cmd.add_argument("manifest", type=Path)

    append_cmd = sub.add_parser("append")
    append_cmd.add_argument("--manifest", type=Path, required=True)
    append_cmd.add_argument("--episode-date", required=True)
    append_cmd.add_argument("--base-research-input-manifest", type=Path, required=True)
    append_cmd.add_argument("--wave", type=int, required=True)
    append_cmd.add_argument("--request", type=Path, required=True)
    append_cmd.add_argument("--result", type=Path, required=True)
    append_cmd.add_argument("--evidence", action="append", default=[])
    append_cmd.add_argument("--collector-run-id", type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        repo_root = args.repo_root.resolve()
        schema_path = (repo_root / args.schema).resolve() if not args.schema.is_absolute() else args.schema.resolve()
        if args.command == "validate":
            manifest_path = (repo_root / args.manifest).resolve() if not args.manifest.is_absolute() else args.manifest.resolve()
            manifest = validate_manifest(manifest_path, repo_root=repo_root, schema_path=schema_path)
        else:
            def resolved(path: Path) -> Path:
                return (repo_root / path).resolve() if not path.is_absolute() else path.resolve()
            manifest = append_wave(
                manifest_path=resolved(args.manifest),
                repo_root=repo_root,
                episode_date=args.episode_date,
                base_manifest_path=resolved(args.base_research_input_manifest),
                wave=args.wave,
                request_path=resolved(args.request),
                result_path=resolved(args.result),
                evidence_bindings=args.evidence,
                collector_run_id=args.collector_run_id,
                schema_path=schema_path,
            )
        print(json.dumps({"status": "PASS", "waveCount": len(manifest["waves"])}, ensure_ascii=False, indent=2))
        return 0
    except (SupplementError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "errors": str(exc).splitlines()}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
