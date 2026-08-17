#!/usr/bin/env python3
"""Materialize authoritative Research artifacts before canonical editorial acceptance.

This is an extraction of the Research half of the historical daily materializer. It reads
only explicitly authored Research inputs, materializes the memory/manifest chain, writes
the official Causal Dossier, and invokes the official Causal Research validator. It never
creates Story meaning, review judgments, production state, or a semantic freeze.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

DATE_RE = __import__("re").compile(r"\d{4}-\d{2}-\d{2}")


class ResearchMaterializationError(ValueError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResearchMaterializationError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise ResearchMaterializationError(f"{label} root must be an object: {path}")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_ref(root: Path, path: Path) -> dict[str, str]:
    resolved_root = root.resolve()
    resolved = path.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ResearchMaterializationError(f"path escapes repository root: {path}")
    if not resolved.is_file():
        raise ResearchMaterializationError(f"missing file: {resolved}")
    return {
        "path": resolved.relative_to(resolved_root).as_posix(),
        "sha256": sha256_file(resolved),
    }


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _candidate_values(piece: dict[str, Any], field: str) -> list[Any]:
    values: list[Any] = []
    research = piece.get("researchAuthoring")
    if isinstance(research, dict) and field in research:
        values.append(research[field])
    if field in piece:
        values.append(piece[field])
    # Transitional support for the historical authoring shape: a root causalDossier
    # object is a Research draft only when it is clearly a Dossier body, not a fileRef.
    if field == "causalDossierDraft":
        legacy = piece.get("causalDossier")
        if isinstance(legacy, dict) and "contract_version" in legacy:
            values.append(legacy)
    return values


def extract_exactly_one(parts: Iterable[Path], *, field: str) -> Any:
    matches: list[tuple[Path, Any]] = []
    for path in parts:
        piece = load_json(path, "daily authoring part")
        for value in _candidate_values(piece, field):
            matches.append((path, value))
    if len(matches) != 1:
        sources = [p.as_posix() for p, _ in matches]
        raise ResearchMaterializationError(
            f"Research authoring field {field} must be defined exactly once; "
            f"found={len(matches)} sources={sources}"
        )
    return copy.deepcopy(matches[0][1])


def normalize_memory_locator(value: Any) -> Any:
    """Keep the existing historical memory locator compatibility as representation only."""
    if isinstance(value, str):
        return value.replace(
            "memory_context.json#threads.ai-capex-payback",
            "memory_context.json#memory_selection.threads[0]",
        )
    if isinstance(value, list):
        return [normalize_memory_locator(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_memory_locator(item) for key, item in value.items()}
    return value


def run(root: Path, *args: str) -> None:
    command = list(args)
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=root, check=False)
    if completed.returncode != 0:
        raise ResearchMaterializationError(
            f"command failed ({completed.returncode}): {' '.join(command)}"
        )


def _resolve_bound_file(root: Path, binding: dict[str, Any], label: str) -> Path:
    raw = binding.get("path")
    if not isinstance(raw, str) or not raw:
        raise ResearchMaterializationError(f"{label}.path missing")
    relative = Path(raw)
    if relative.is_absolute():
        raise ResearchMaterializationError(f"{label}.path must be relative")
    resolved_root = root.resolve()
    resolved = (resolved_root / relative).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ResearchMaterializationError(f"{label}.path escapes repository root")
    if not resolved.is_file():
        raise ResearchMaterializationError(f"{label} missing: {raw}")
    actual = sha256_file(resolved)
    if binding.get("sha256") != actual:
        raise ResearchMaterializationError(
            f"{label}.sha256 mismatch: declared={binding.get('sha256')} actual={actual}"
        )
    return resolved


def verify_validation_receipt(root: Path, date: str, receipt_path: Path) -> dict[str, Any]:
    receipt = load_json(receipt_path, "Causal Dossier validation receipt")
    if receipt.get("contractVersion") != "1.0.0":
        raise ResearchMaterializationError("Causal Dossier validation receipt contractVersion mismatch")
    if receipt.get("status") != "pass" or receipt.get("episodeDate") != date:
        raise ResearchMaterializationError("Causal Dossier validation receipt must PASS for the same episode")
    for key in ("dossier", "researchInputManifest", "memoryRetrievalReport", "validator"):
        binding = receipt.get(key)
        if not isinstance(binding, dict):
            raise ResearchMaterializationError(f"Causal Dossier receipt {key} binding missing")
        _resolve_bound_file(root, binding, f"receipt.{key}")
    schema_bindings = receipt.get("schemaBindings")
    if not isinstance(schema_bindings, list) or not schema_bindings:
        raise ResearchMaterializationError("Causal Dossier receipt schemaBindings missing")
    for index, binding in enumerate(schema_bindings):
        if not isinstance(binding, dict):
            raise ResearchMaterializationError(f"receipt.schemaBindings[{index}] invalid")
        _resolve_bound_file(root, binding, f"receipt.schemaBindings[{index}]")
    if receipt.get("errors") != []:
        raise ResearchMaterializationError("PASS Causal Dossier receipt contains errors")
    return receipt


def materialize(
    *,
    root: Path,
    date: str,
    market_date: str,
    information_cutoff: str,
) -> dict[str, str]:
    root = root.resolve()
    if not DATE_RE.fullmatch(date) or not DATE_RE.fullmatch(market_date):
        raise ResearchMaterializationError("date/market-date must be YYYY-MM-DD")
    if not information_cutoff.strip():
        raise ResearchMaterializationError("information-cutoff must be non-empty")

    parts_dir = root / "daily-authoring-parts" / date
    parts = sorted(parts_dir.glob("*.json"))
    if not parts:
        raise ResearchMaterializationError(f"no authoring parts: {parts_dir}")
    query_plan = extract_exactly_one(parts, field="memoryQueryPlan")
    dossier_draft = extract_exactly_one(parts, field="causalDossierDraft")
    if not isinstance(query_plan, dict):
        raise ResearchMaterializationError("memoryQueryPlan must be an object")
    if not isinstance(dossier_draft, dict):
        raise ResearchMaterializationError("causalDossierDraft must be an object")
    if dossier_draft.get("episode_date") != date:
        raise ResearchMaterializationError("causalDossierDraft episode_date mismatch")

    work = root / "working" / date
    research = root / "research" / date
    work.mkdir(parents=True, exist_ok=True)
    research.mkdir(parents=True, exist_ok=True)
    query_path = work / "memory_query_plan.json"
    context_path = work / f"memory_context_{date}.md"
    report_path = work / f"memory_retrieval_report_{date}.json"
    manifest_path = research / "research_input_manifest.json"
    dossier_path = research / f"causal_research_dossier_{date}.json"
    receipt_path = research / "causal_dossier_validation.json"
    daily_path = root / "daily-inputs" / date / f"daily_source_package_{date}.md"
    if not daily_path.is_file():
        raise ResearchMaterializationError(f"daily source package missing: {daily_path}")

    atomic_write_json(query_path, query_plan)
    run(
        root,
        sys.executable,
        "scripts/editorial_memory_retrieval.py",
        "--query-plan", query_path.relative_to(root).as_posix(),
        "--context-output", context_path.relative_to(root).as_posix(),
        "--report-output", report_path.relative_to(root).as_posix(),
        "--repo-root", str(root),
    )
    run(
        root,
        sys.executable,
        "scripts/build_research_input_manifest.py",
        "--episode-date", date,
        "--market-date", market_date,
        "--timezone", "America/New_York",
        "--information-cutoff", information_cutoff,
        "--daily-source-package", str(daily_path),
        "--memory-query-plan", str(query_path),
        "--memory-context", str(context_path),
        "--memory-retrieval-report", str(report_path),
        "--output", str(manifest_path),
        "--repo-root", str(root),
    )

    dossier = normalize_memory_locator(dossier_draft)
    manifest_binding = dossier.get("research_input_manifest")
    if not isinstance(manifest_binding, dict):
        raise ResearchMaterializationError("causalDossierDraft.research_input_manifest binding missing")
    manifest_binding["path"] = manifest_path.relative_to(root).as_posix()
    manifest_binding["sha256"] = sha256_file(manifest_path)
    atomic_write_json(dossier_path, dossier)

    # The official validator publishes the SHA-bound receipt atomically after this PR.
    run(
        root,
        sys.executable,
        "skills/nasdaq-cafe-causal-research/validators/validate_causal_research_dossier.py",
        str(dossier_path),
        "--research-input-manifest", str(manifest_path),
        "--memory-retrieval-report", str(report_path),
        "--repo-root", str(root),
        "--json-output", str(receipt_path),
    )
    verify_validation_receipt(root, date, receipt_path)
    return {
        "dossier": dossier_path.relative_to(root).as_posix(),
        "dossierSha256": sha256_file(dossier_path),
        "validationReceipt": receipt_path.relative_to(root).as_posix(),
        "validationReceiptSha256": sha256_file(receipt_path),
        "researchInputManifest": manifest_path.relative_to(root).as_posix(),
        "researchInputManifestSha256": sha256_file(manifest_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--market-date", required=True)
    parser.add_argument("--information-cutoff", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        result = materialize(
            root=args.repo_root,
            date=args.date,
            market_date=args.market_date,
            information_cutoff=args.information_cutoff,
        )
        payload = {"status": "PASS", "episodeDate": args.date, **result}
        code = 0
    except (OSError, ResearchMaterializationError) as exc:
        payload = {"status": "FAIL", "episodeDate": args.date, "error": str(exc)}
        code = 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
