#!/usr/bin/env python3
"""Run the canonical causal dossier validator plus optional acquisition lineage checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from research_evidence_supplement import SupplementError, validate_manifest  # noqa: E402
from validate_causal_research_dossier import ValidationResult, validate_dossier  # noqa: E402


ACQUIRED_EVIDENCE_DIR = "research/{episode_date}/evidence/"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_relative(repo_root: Path, path: Path) -> str:
    root = repo_root.resolve()
    resolved = path.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path escapes repository root: {path}")
    return resolved.relative_to(root).as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def validate_dossier_with_supplement(
    dossier_path: Path,
    manifest_path: Path,
    retrieval_report_path: Path,
    *,
    supplement_path: Path | None,
    contracts_dir: Path,
    repo_root: Path,
    retrieval_runner=None,
) -> ValidationResult:
    kwargs: dict[str, Any] = {
        "contracts_dir": contracts_dir,
        "repo_root": repo_root,
    }
    if retrieval_runner is not None:
        kwargs["retrieval_runner"] = retrieval_runner
    base = validate_dossier(
        dossier_path,
        manifest_path,
        retrieval_report_path,
        **kwargs,
    )
    errors = list(base.errors)
    warnings = list(base.warnings)

    repo_root = repo_root.resolve()
    try:
        dossier = _load_json(dossier_path.resolve())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"supplement integration: cannot read dossier: {exc}")
        return ValidationResult(sorted(set(errors)), sorted(set(warnings)))

    episode_date = str(dossier.get("episode_date") or "")
    acquired_prefix = ACQUIRED_EVIDENCE_DIR.format(episode_date=episode_date)
    acquired_refs = {
        str(item.get("source_reference") or "").replace("\\", "/")
        for item in dossier.get("evidence", [])
        if isinstance(item, dict)
        and str(item.get("source_reference") or "").replace("\\", "/").startswith(acquired_prefix)
    }

    if supplement_path is None:
        if acquired_refs:
            errors.append(
                "acquired research evidence is referenced but no research evidence supplement manifest was supplied"
            )
        return ValidationResult(sorted(set(errors)), sorted(set(warnings)))

    try:
        supplement_resolved = supplement_path.resolve()
        supplement = validate_manifest(
            supplement_resolved,
            repo_root=repo_root,
            schema_path=(contracts_dir / "research_evidence_supplement_manifest.schema.json").resolve(),
        )
        supplement_rel = _repo_relative(repo_root, supplement_resolved)
        supplement_sha = sha256_file(supplement_resolved)
    except (SupplementError, OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"research evidence supplement: {exc}")
        return ValidationResult(sorted(set(errors)), sorted(set(warnings)))

    if supplement.get("episodeDate") != episode_date:
        errors.append("research evidence supplement episodeDate differs from dossier")

    try:
        supplied_manifest_rel = _repo_relative(repo_root, manifest_path.resolve())
        supplied_manifest_sha = sha256_file(manifest_path.resolve())
    except (OSError, ValueError) as exc:
        errors.append(f"research input manifest integration: {exc}")
        supplied_manifest_rel = ""
        supplied_manifest_sha = ""

    base_ref = supplement.get("baseResearchInputManifest", {})
    if base_ref.get("path") != supplied_manifest_rel or base_ref.get("sha256") != supplied_manifest_sha:
        errors.append("research evidence supplement is not bound to the supplied research input manifest")

    if not any(
        item.get("role") == "other"
        and str(item.get("path_or_reference") or "").replace("\\", "/") == supplement_rel
        and item.get("version_or_hash") == supplement_sha
        for item in dossier.get("input_provenance", [])
        if isinstance(item, dict)
    ):
        errors.append(
            "dossier input_provenance must bind the research evidence supplement manifest path and SHA-256"
        )

    declared_paths = {
        str(evidence_ref["path"]).replace("\\", "/")
        for wave in supplement.get("waves", [])
        for evidence_ref in wave.get("evidenceFiles", [])
        if isinstance(evidence_ref, dict) and evidence_ref.get("path")
    }

    for ref in sorted(acquired_refs):
        if ref not in declared_paths:
            errors.append(f"dossier acquired evidence is not supplement-bound: {ref}")

    for path in sorted(declared_paths):
        if not path.startswith(acquired_prefix):
            errors.append(
                f"supplement evidence must be copied under {acquired_prefix} before dossier use: {path}"
            )

    return ValidationResult(sorted(set(errors)), sorted(set(warnings)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--research-input-manifest", type=Path, required=True)
    parser.add_argument("--memory-retrieval-report", type=Path, required=True)
    parser.add_argument("--research-evidence-supplement-manifest", type=Path)
    parser.add_argument(
        "--contracts-dir",
        type=Path,
        default=Path("skills/nasdaq-cafe-causal-research/contracts"),
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_dossier_with_supplement(
        args.dossier,
        args.research_input_manifest,
        args.memory_retrieval_report,
        supplement_path=args.research_evidence_supplement_manifest,
        contracts_dir=args.contracts_dir,
        repo_root=args.repo_root,
    )
    payload = result.as_dict()
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    for error in result.errors:
        print(f"ERROR: {error}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("PASS" if result.ok else "FAIL")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
