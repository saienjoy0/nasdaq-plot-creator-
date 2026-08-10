from __future__ import annotations

from typing import Any


class VisualEvidenceCoverageError(ValueError):
    pass


def _source_text(source: dict[str, Any]) -> str:
    values = [
        source.get("title"),
        source.get("publisher"),
        source.get("reference"),
        *(source.get("usedFor") or []),
    ]
    return " ".join(str(value) for value in values if value is not None).lower()


def _is_source_document_worthy(source: dict[str, Any]) -> bool:
    source_type = source.get("sourceType")
    if source_type == "official":
        return True
    if source_type not in {"company", "company-ir"}:
        return False
    reference = str(source.get("reference") or "")
    return reference.startswith("research/") or "/evidence/" in reference


def _is_verified_intraday_source(source: dict[str, Any]) -> bool:
    text = _source_text(source)
    return any(token in text for token in ("1分足", "分足", "intraday", "minute-close", "minute series"))


def _referenced_source_ids(render: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for scene in render.get("scenes", []):
        if scene.get("sceneNumber") == 9 or str(scene.get("sceneRole", "")).startswith("closing"):
            continue
        result.update(item for item in scene.get("evidenceSourceIds", []) if isinstance(item, str))
        for beat in scene.get("visualBeats", []):
            result.update(item for item in beat.get("evidenceSourceIds", []) if isinstance(item, str))
    return result


def _intent_source_ids(intents: list[dict[str, Any]]) -> set[str]:
    return {
        source_id
        for intent in intents
        for source_id in intent.get("sourceIds", [])
        if isinstance(source_id, str)
    }


def _intraday_financial_source_ids(render: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for scene in render.get("scenes", []):
        for beat in scene.get("visualBeats", []):
            if beat.get("visualTemplate") != "event-reaction-timeline":
                continue
            config = (beat.get("templateConfig") or {}).get("reactionTimeline") or {}
            if config.get("precision") != "verified-intraday-series":
                continue
            if len(config.get("seriesObjectIds") or []) < 2:
                continue
            trace = beat.get("financialVisualTrace") or {}
            trace_sources = trace.get("sourceIds") or beat.get("evidenceSourceIds") or []
            result.update(item for item in trace_sources if isinstance(item, str))
    return result


def validate_visual_evidence_coverage(
    *, render: dict[str, Any], intents: list[dict[str, Any]]
) -> None:
    sources = {
        source["sourceId"]: source
        for source in render.get("sources", [])
        if isinstance(source, dict) and isinstance(source.get("sourceId"), str)
    }
    referenced = _referenced_source_ids(render)
    intent_sources = _intent_source_ids(intents)

    source_document_required = {
        source_id
        for source_id in referenced
        if source_id in sources and _is_source_document_worthy(sources[source_id])
    }
    missing_source_documents = sorted(source_document_required - intent_sources)
    if missing_source_documents:
        raise VisualEvidenceCoverageError(
            "E_VISUAL_SOURCE_DOCUMENT_UNCOVERED: real source evidence is referenced but no Visual Source Intent covers "
            + ", ".join(missing_source_documents)
        )

    intraday_required = {
        source_id
        for source_id in referenced
        if source_id in sources and _is_verified_intraday_source(sources[source_id])
    }
    intraday_covered = _intraday_financial_source_ids(render)
    missing_intraday = sorted(intraday_required - intraday_covered)
    if missing_intraday:
        raise VisualEvidenceCoverageError(
            "E_FINANCIAL_VISUAL_INTRADAY_UNCOVERED: verified intraday evidence must use event-reaction-timeline/verified-intraday-series for "
            + ", ".join(missing_intraday)
        )
