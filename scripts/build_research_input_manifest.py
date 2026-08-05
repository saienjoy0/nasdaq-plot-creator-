#!/usr/bin/env python3
"""Build a deterministic research input manifest for causal research.

This script does not decide the lead story or current market causality. It only
freezes the daily input and editorial-memory retrieval artifacts, verifies their
contracts, hashes them, and classifies selected memory by permitted use mode.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


class ManifestBuildError(ValueError):
    """Raised when the research input contract cannot be built safely."""


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


def validate_schema(instance: Any, schema_path: Path, label: str) -> None:
    schema = load_json(schema_path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{label}{format_path(error.absolute_path)}: {error.message}"
            for error in errors
        )
        raise ManifestBuildError(details)


def format_path(parts: Any) -> str:
    values = list(parts)
    if not values:
        return ""
    return "." + ".".join(str(value) for value in values)


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


def classify_memory(report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    intake: dict[str, list[dict[str, Any]]] = {
        "current_revalidation_required": [],
        "historical_context_only": [],
        "procedural": [],
        "not_selected": [],
    }

    for item in report["selected"]:
        normalized = normalized_selected_item(item)
        use_mode = item["use_mode"]
        if (
            item.get("requires_current_revalidation")
            or use_mode == "current_revalidation_required"
        ):
            bucket = "current_revalidation_required"
        elif use_mode == "historical_context":
            bucket = "historical_context_only"
        elif use_mode == "procedural":
            bucket = "procedural"
        else:
            raise ManifestBuildError(
                f"unsupported retrieval use_mode for {item['item_id']}: {use_mode}"
            )
        intake[bucket].append(normalized)

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
) -> dict[str, Any]:
    paths = {
        "daily_source_package": daily_source_package,
        "memory_query_plan": memory_query_plan,
        "memory_context": memory_context,
        "memory_retrieval_report": memory_retrieval_report,
    }
    for label, path in paths.items():
        if not path.is_file():
            raise ManifestBuildError(f"missing {label}: {path}")

    query_plan = load_json(memory_query_plan)
    report = load_json(memory_retrieval_report)
    validate_schema(
        query_plan,
        contracts_dir
        / "../../nasdaq-cafe-editorial-memory/contracts/memory_query_plan.schema.json",
        "memory_query_plan",
    )
    validate_schema(
        report,
        contracts_dir
        / "../../nasdaq-cafe-editorial-memory/contracts/memory_retrieval_report.schema.json",
        "memory_retrieval_report",
    )

    if query_plan["episode_date"] != episode_date:
        raise ManifestBuildError(
            "episode date mismatch: "
            f"query plan={query_plan['episode_date']} requested={episode_date}"
        )
    if report["episode_date"] != episode_date:
        raise ManifestBuildError(
            "episode date mismatch: "
            f"retrieval report={report['episode_date']} requested={episode_date}"
        )

    daily_filename_date = date_from_filename(daily_source_package)
    if daily_filename_date and daily_filename_date != episode_date:
        raise ManifestBuildError(
            "episode date mismatch: "
            f"daily package filename={daily_filename_date} requested={episode_date}"
        )
    query_filename_date = date_from_filename(memory_query_plan)
    if query_filename_date and query_filename_date != episode_date:
        raise ManifestBuildError(
            "episode date mismatch: "
            f"query plan filename={query_filename_date} requested={episode_date}"
        )
    context_filename_date = date_from_filename(memory_context)
    if context_filename_date and context_filename_date != episode_date:
        raise ManifestBuildError(
            "episode date mismatch: "
            f"memory context filename={context_filename_date} requested={episode_date}"
        )
    report_filename_date = date_from_filename(memory_retrieval_report)
    if report_filename_date and report_filename_date != episode_date:
        raise ManifestBuildError(
            "episode date mismatch: "
            f"retrieval report filename={report_filename_date} requested={episode_date}"
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
                "path": path.as_posix(),
                "sha256": sha256_file(path),
            }
            for label, path in paths.items()
        },
        "memory_intake": classify_memory(report),
        "validation": {
            "status": "pass",
            "errors": [],
            "warnings": [],
        },
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
        )
    except ManifestBuildError as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"PASS: wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
