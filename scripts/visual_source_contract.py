#!/usr/bin/env python3
"""Validate and attach Visual Source Intent to the Final Episode Contract.

The intent file is authored upstream with the final editorial package. This
module performs only structural/semantic checks and copies the approved intent
into the Final Episode Contract. It does not search, fetch, choose Primary vs
Fallback, or change narration/causality/Visual Grammar.

Visual Evidence Planning is explicit: a missing intent document is an error.
An existing document with ``intents: []`` is the only valid no-Visual-Source
result.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class VisualSourceContractError(ValueError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualSourceContractError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualSourceContractError(f"{label} root must be an object")
    return value


def write_atomic(path: Path, value: dict[str, Any]) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(f".{path.name}.visual-source.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def empty_visual_sources() -> dict[str, Any]:
    return {"contractVersion": "1.0.0", "intents": []}


def load_intent_document(path: Path | None, episode_date: str) -> dict[str, Any]:
    if path is None or not path.is_file():
        raise VisualSourceContractError(
            "E_VISUAL_SOURCE_PLANNING_MISSING: visual_source_intents.json is required even when no Visual Source is needed"
        )
    value = load_json(path, "Visual Source intent")
    if value.get("contractVersion") != "1.0.0":
        raise VisualSourceContractError("Visual Source contractVersion must be 1.0.0")
    if value.get("episodeDate") != episode_date:
        raise VisualSourceContractError("Visual Source intent episodeDate mismatch")
    intents = value.get("intents")
    if not isinstance(intents, list):
        raise VisualSourceContractError("Visual Source intents must be an array")
    return {"contractVersion": "1.0.0", "intents": intents}


def _locator_keys(candidate: dict[str, Any]) -> set[str]:
    locator = candidate.get("sourceLocator")
    if not isinstance(locator, dict):
        return set()
    return set(locator)


def _validate_candidate(
    *,
    intent_id: str,
    path_name: str,
    candidate: dict[str, Any],
    errors: list[str],
) -> None:
    source_kind = candidate["sourceKind"]
    capture = candidate["captureMethod"]
    locator = candidate["sourceLocator"]
    keys = _locator_keys(candidate)
    prefix = f"{intent_id}.{path_name}"
    if "query" in keys:
        errors.append(f"{prefix}: generic search query is forbidden")

    allowed: dict[str, tuple[set[str], set[str]]] = {
        "existing-asset": ({"assetId"}, {"registry-reference"}),
        "collector-document": (
            {"documentId", "localPath"},
            {"archive-file", "pdf-page-render", "webpage-screenshot"},
        ),
        "official-url": (
            {"url"},
            {"direct-download", "pdf-page-render", "webpage-screenshot"},
        ),
        "web-page": ({"url"}, {"webpage-screenshot"}),
        "social-post": ({"url"}, {"social-capture"}),
        "wikimedia": ({"pageId", "url"}, {"mediawiki-fetch"}),
        "generated-image": ({"localPath"}, {"local-file-validation"}),
    }
    required_locator_keys, allowed_methods = allowed[source_kind]
    if not keys.intersection(required_locator_keys):
        errors.append(
            f"{prefix}: {source_kind} requires one of {sorted(required_locator_keys)}"
        )
    if capture not in allowed_methods:
        errors.append(
            f"{prefix}: captureMethod {capture!r} is invalid for {source_kind}"
        )
    if source_kind == "existing-asset":
        if locator.get("assetId") != candidate["assetId"]:
            errors.append(f"{prefix}: existing asset locator must equal candidate assetId")
        if candidate["rightsStatus"] not in {"cleared", "not-required"}:
            errors.append(f"{prefix}: existing asset cannot remain user-review-required")
    if source_kind == "generated-image" and candidate["rightsStatus"] == "not-required":
        errors.append(f"{prefix}: generated image rightsStatus must be cleared or user-review-required")
    if capture == "pdf-page-render":
        spec = candidate.get("captureSpec")
        if not isinstance(spec, dict) or not isinstance(spec.get("pageNumber"), int):
            errors.append(f"{prefix}: pdf-page-render requires captureSpec.pageNumber")


def validate_visual_sources(
    *, contract: dict[str, Any], visual_sources: dict[str, Any], schema: dict[str, Any]
) -> dict[str, Any]:
    # The base Final Episode Contract was already validated by the existing
    # validator, including its external Financial Visual candidate-plan ref.
    # Validate only the new extension against the exact same $defs to avoid
    # re-resolving unrelated external refs or duplicating existing validation.
    extension_schema = {
        "$schema": schema.get("$schema", "https://json-schema.org/draft/2020-12/schema"),
        "$defs": schema["$defs"],
        "$ref": "#/$defs/visualSources",
    }
    validator = Draft202012Validator(extension_schema)
    schema_errors = sorted(validator.iter_errors(visual_sources), key=lambda e: list(e.path))
    if schema_errors:
        formatted = []
        for error in schema_errors:
            location = "$.visualSources" + "".join(
                f"[{part}]" if isinstance(part, int) else f".{part}"
                for part in error.path
            )
            formatted.append(f"{location}: {error.message}")
        raise VisualSourceContractError("\n".join(formatted))

    errors: list[str] = []
    beat_keys = {
        (scene["sceneId"], beat["visualBeatId"])
        for scene in contract["scenes"]
        for beat in scene["visualBeats"]
    }
    source_ids = {item["sourceId"] for item in contract["sourceRegistry"]}
    seen_intents: set[str] = set()
    seen_targets: set[tuple[str, str]] = set()
    seen_candidates: set[str] = set()
    seen_placements: set[str] = set()

    for intent in visual_sources["intents"]:
        intent_id = intent["intentId"]
        if intent_id in seen_intents:
            errors.append(f"duplicate Visual Source intentId: {intent_id}")
        seen_intents.add(intent_id)
        target = (intent["target"]["sceneId"], intent["target"]["visualBeatId"])
        if target not in beat_keys:
            errors.append(f"{intent_id}: target Visual Beat does not exist: {target}")
        if target in seen_targets:
            errors.append(f"{intent_id}: only one Visual Source Intent is allowed per Visual Beat")
        seen_targets.add(target)
        unknown_sources = set(intent["sourceIds"]) - source_ids
        if unknown_sources:
            errors.append(f"{intent_id}: unknown sourceIds: {sorted(unknown_sources)}")
        placement_id = intent["placement"]["placementId"]
        if placement_id in seen_placements:
            errors.append(f"duplicate Visual Source placementId: {placement_id}")
        seen_placements.add(placement_id)

        primary = intent["primary"]
        fallback = intent["fallback"]
        if primary["candidateId"] == fallback["candidateId"]:
            errors.append(f"{intent_id}: Primary and Fallback candidateId must differ")
        if primary["assetId"] == fallback["assetId"]:
            errors.append(f"{intent_id}: Primary and Fallback assetId must differ")
        for path_name, candidate in (("primary", primary), ("fallback", fallback)):
            candidate_id = candidate["candidateId"]
            if candidate_id in seen_candidates:
                errors.append(f"duplicate Visual Source candidateId: {candidate_id}")
            seen_candidates.add(candidate_id)
            _validate_candidate(
                intent_id=intent_id,
                path_name=path_name,
                candidate=candidate,
                errors=errors,
            )

        if intent["presentationClass"] == "generated-illustration":
            if primary["sourceKind"] != "generated-image" and fallback["sourceKind"] != "generated-image":
                errors.append(
                    f"{intent_id}: generated-illustration requires a generated-image candidate"
                )

    if errors:
        raise VisualSourceContractError("\n".join(errors))
    candidate_contract = dict(contract)
    candidate_contract["visualSources"] = visual_sources
    return candidate_contract


def attach_visual_sources(
    *, contract_path: Path, intent_path: Path | None, schema_path: Path
) -> dict[str, Any]:
    contract = load_json(contract_path, "Final Episode Contract")
    schema = load_json(schema_path, "Final Episode Contract schema")
    visual_sources = load_intent_document(intent_path, contract["episodeDate"])
    updated = validate_visual_sources(
        contract=contract,
        visual_sources=visual_sources,
        schema=schema,
    )
    write_atomic(contract_path, updated)
    return {
        "status": "PASS",
        "episodeDate": contract["episodeDate"],
        "intentCount": len(visual_sources["intents"]),
        "contractPath": str(contract_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--intents", type=Path)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("contracts/final_episode_contract.schema.json"),
    )
    args = parser.parse_args(argv)
    try:
        result = attach_visual_sources(
            contract_path=args.contract,
            intent_path=args.intents,
            schema_path=args.schema,
        )
        code = 0
    except (VisualSourceContractError, OSError, KeyError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "errors": str(exc).splitlines()}
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
