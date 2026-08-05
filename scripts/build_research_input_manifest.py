#!/usr/bin/env python3
"""Build a deterministic, lineage-verified research input manifest.

The builder freezes current production inputs. It does not choose a lead story,
certify remembered claims, or decide market causality.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator, FormatChecker

from editorial_memory_retrieval import retrieve

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
RetrievalRunner = Callable[..., dict[str, Any]]


class ManifestBuildError(ValueError):
    """Raised when research intake cannot be frozen safely."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestBuildError(f"missing input file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestBuildError(f"invalid JSON at {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def format_path(parts: Any) -> str:
    values = list(parts)
    return "" if not values else "." + ".".join(str(value) for value in values)


def validate_schema(instance: Any, schema_path: Path, label: str) -> None:
    schema = load_json(schema_path)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{label}{format_path(error.absolute_path)}: {error.message}"
            for error in errors
        )
        raise ManifestBuildError(details)


def ensure_repo_path(
    path: Path,
    repo_root: Path,
    label: str,
    *,
    must_exist: bool = True,
) -> Path:
    root = repo_root.resolve()
    resolved = path.resolve()
    if resolved != root and root not in resolved.parents:
        raise ManifestBuildError(f"{label} escapes repository root: {path}")
    if must_exist and not resolved.is_file():
        raise ManifestBuildError(f"missing {label}: {path}")
    return resolved


def repo_relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def date_from_filename(path: Path) -> str | None:
    match = DATE_RE.search(path.name)
    return match.group(0) if match else None


def normalized_selected_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_type": item["item_type"],
        "item_id": item["item_id"],
        "path": item["path"],
        "historical_confidence": item.get("historical_confidence", "unknown"),
        "provenance_paths": sorted(item.get("provenance_paths", [])),
        "requires_current_revalidation": bool(
            item.get("requires_current_revalidation", False)
        ),
        "retrieval_status": item.get("status", "unknown"),
    }


def expected_bucket(item: dict[str, Any]) -> str:
    use_mode = item["use_mode"]
    if item.get("requires_current_revalidation") or use_mode == "current_revalidation_required":
        return "current_revalidation_required"
    if use_mode == "historical_context":
        return "historical_context_only"
    if use_mode == "procedural":
        return "procedural"
    raise ManifestBuildError(
        f"unsupported retrieval use_mode for {item['item_id']}: {use_mode}"
    )


def classify_memory(report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    intake: dict[str, list[dict[str, Any]]] = {
        "current_revalidation_required": [],
        "historical_context_only": [],
        "procedural": [],
        "not_selected": [],
    }
    seen: set[tuple[str, str]] = set()
    for item in report["selected"]:
        key = (item["item_type"], item["item_id"])
        if key in seen:
            raise ManifestBuildError(f"duplicate selected memory in report: {key}")
        seen.add(key)
        intake[expected_bucket(item)].append(normalized_selected_item(item))

    for item in report["rejected"]:
        intake["not_selected"].append(
            {
                "item_type": item["item_type"],
                "item_id": item["item_id"],
                "reason": item["reason"],
                "detail": item.get("detail", ""),
            }
        )

    for values in intake.values():
        values.sort(key=lambda item: (item["item_type"], item["item_id"]))
    return intake


def verify_retrieval_lineage(
    *,
    memory_query_plan: Path,
    memory_context: Path,
    memory_retrieval_report: Path,
    repo_root: Path,
    editorial_contracts_dir: Path,
    retrieval_runner: RetrievalRunner = retrieve,
) -> None:
    """Replay deterministic retrieval and compare Context and Report bytes."""
    report = load_json(memory_retrieval_report)
    declared_query = report.get("query_plan_path")
    actual_query = repo_relative(memory_query_plan, repo_root)
    if declared_query != actual_query:
        raise ManifestBuildError(
            "retrieval report query_plan_path mismatch: "
            f"declared={declared_query!r} actual={actual_query!r}"
        )

    with tempfile.TemporaryDirectory(prefix=".retrieval-replay-", dir=repo_root) as tmp:
        tmp_root = Path(tmp)
        replay_context = tmp_root / "context.md"
        replay_report = tmp_root / "report.json"
        retrieval_runner(
            memory_query_plan,
            replay_context,
            replay_report,
            repo_root=repo_root,
            contracts_dir=editorial_contracts_dir,
        )
        if replay_context.read_bytes() != memory_context.read_bytes():
            raise ManifestBuildError(
                "memory context does not match deterministic retrieval replay"
            )
        if replay_report.read_bytes() != memory_retrieval_report.read_bytes():
            raise ManifestBuildError(
                "memory retrieval report does not match deterministic retrieval replay"
            )


def build_manifest(
    *,
    episode_date: str,
    market_date: str,
    timezone: str,
    information_cutoff: str,
    daily_source_package: Path,
    memory_query_plan: Path,
    memory_context: Path,
    memory_retrieval_report: Path,
    output: Path,
    contracts_dir: Path,
    repo_root: Path,
    retrieval_runner: RetrievalRunner = retrieve,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    paths = {
        "daily_source_package": ensure_repo_path(
            daily_source_package, repo_root, "daily_source_package"
        ),
        "memory_query_plan": ensure_repo_path(
            memory_query_plan, repo_root, "memory_query_plan"
        ),
        "memory_context": ensure_repo_path(memory_context, repo_root, "memory_context"),
        "memory_retrieval_report": ensure_repo_path(
            memory_retrieval_report, repo_root, "memory_retrieval_report"
        ),
    }
    output = ensure_repo_path(output, repo_root, "output", must_exist=False)
    contracts_dir = ensure_repo_path(
        contracts_dir / "research_input_manifest.schema.json",
        repo_root,
        "research_input_manifest schema",
    ).parent
    editorial_contracts = ensure_repo_path(
        contracts_dir
        / "../../nasdaq-cafe-editorial-memory/contracts/memory_query_plan.schema.json",
        repo_root,
        "memory_query_plan schema",
    ).parent

    query_plan = load_json(paths["memory_query_plan"])
    report = load_json(paths["memory_retrieval_report"])
    validate_schema(
        query_plan,
        editorial_contracts / "memory_query_plan.schema.json",
        "memory_query_plan",
    )
    validate_schema(
        report,
        editorial_contracts / "memory_retrieval_report.schema.json",
        "memory_retrieval_report",
    )

    if query_plan["episode_date"] != episode_date:
        raise ManifestBuildError(
            f"episode date mismatch: query plan={query_plan['episode_date']} requested={episode_date}"
        )
    if report["episode_date"] != episode_date:
        raise ManifestBuildError(
            f"episode date mismatch: retrieval report={report['episode_date']} requested={episode_date}"
        )

    for label, path in paths.items():
        filename_date = date_from_filename(path)
        if filename_date and filename_date != episode_date:
            raise ManifestBuildError(
                f"episode date mismatch: {label} filename={filename_date} requested={episode_date}"
            )

    verify_retrieval_lineage(
        memory_query_plan=paths["memory_query_plan"],
        memory_context=paths["memory_context"],
        memory_retrieval_report=paths["memory_retrieval_report"],
        repo_root=repo_root,
        editorial_contracts_dir=editorial_contracts,
        retrieval_runner=retrieval_runner,
    )

    manifest = {
        "contract_version": "1.0.0",
        "episode_date": episode_date,
        "session": {
            "market_date": market_date,
            "timezone": timezone,
            "information_cutoff": information_cutoff,
        },
        "inputs": {
            label: {
                "path": repo_relative(path, repo_root),
                "sha256": sha256_file(path),
            }
            for label, path in paths.items()
        },
        "memory_intake": classify_memory(report),
        "validation": {"status": "pass", "errors": [], "warnings": []},
    }
    validate_schema(
        manifest,
        contracts_dir / "research_input_manifest.schema.json",
        "research_input_manifest",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-date", required=True)
    parser.add_argument("--market-date", required=True)
    parser.add_argument("--timezone", required=True)
    parser.add_argument("--information-cutoff", required=True)
    parser.add_argument("--daily-source-package", type=Path, required=True)
    parser.add_argument("--memory-query-plan", type=Path, required=True)
    parser.add_argument("--memory-context", type=Path, required=True)
    parser.add_argument("--memory-retrieval-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--contracts-dir",
        type=Path,
        default=Path("skills/nasdaq-cafe-causal-research/contracts"),
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        build_manifest(
            episode_date=args.episode_date,
            market_date=args.market_date,
            timezone=args.timezone,
            information_cutoff=args.information_cutoff,
            daily_source_package=args.daily_source_package,
            memory_query_plan=args.memory_query_plan,
            memory_context=args.memory_context,
            memory_retrieval_report=args.memory_retrieval_report,
            output=args.output,
            contracts_dir=args.contracts_dir,
            repo_root=args.repo_root,
        )
    except ManifestBuildError as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"PASS: wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
