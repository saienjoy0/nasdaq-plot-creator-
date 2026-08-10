#!/usr/bin/env python3
"""Fail closed when authored real evidence is collapsed into abstract-only visuals.

This gate is presentation-only. It does not choose a lead, infer causality, change
narration, select a Visual Source candidate, or invent evidence. It only verifies
that evidence which the approved render authoring already claims to use is given an
appropriate visual path when one is materially required:

- official / company / social primary evidence must receive an explicit Visual Source
  plan when it anchors the approved story;
- verified intraday evidence used to make a timing claim must be shown as a verified
  series rather than only restated as cards or prose;
- a Visual Source intent must target a Beat that already cites at least one of the
  same approved source IDs.

The planner remains editorially responsible for choosing the exact Primary and
Approved Fallback. This module only blocks silent downgrade to ``not-required``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class VisualEvidenceQualityError(ValueError):
    pass


ORIGINAL_SOURCE_TYPES = {"official", "company", "social", "social-post"}
ANCHOR_FUNCTIONS = {"Anchor", "Evidence"}
EARNINGS_MARKERS = (
    "financial results",
    "earnings",
    "quarter",
    "results for",
    "決算",
    "売上",
    "eps",
    "guidance",
    "見通し",
)
INTRADAY_MARKERS = (
    "1分足",
    "1-minute",
    "1 minute",
    "intraday",
    "kline",
    "minute-close",
)
TIMING_BEAT_MARKERS = (
    "1分足",
    "初動",
    "発表時刻",
    "8:30",
    "intraday",
    "minute",
)


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualEvidenceQualityError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualEvidenceQualityError(f"{label} root must be an object")
    return value


def _lower_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, list):
        return " ".join(_lower_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_lower_text(item) for item in value.values())
    return str(value).lower()


def _source_rows(render: dict[str, Any]) -> list[dict[str, Any]]:
    rows = render.get("sources")
    if isinstance(rows, list):
        return [item for item in rows if isinstance(item, dict)]
    rows = render.get("sourceRegistry")
    if isinstance(rows, list):
        return [item for item in rows if isinstance(item, dict)]
    return []


def _source_id(source: dict[str, Any]) -> str | None:
    value = source.get("sourceId") or source.get("source_id")
    return value if isinstance(value, str) and value else None


def _source_type(source: dict[str, Any]) -> str:
    value = source.get("sourceType") or source.get("source_type") or ""
    return str(value).strip().lower()


def _source_text(source: dict[str, Any]) -> str:
    return _lower_text(
        {
            "title": source.get("title"),
            "publisher": source.get("publisher"),
            "reference": source.get("reference"),
            "usedFor": source.get("usedFor") or source.get("used_for"),
        }
    )


def _beat_id(beat: dict[str, Any]) -> str:
    value = beat.get("visualBeatId") or beat.get("beatId")
    return str(value) if value is not None else "<unknown-beat>"


def _iter_beats(render: dict[str, Any]):
    for scene_index, scene in enumerate(render.get("scenes", []), start=1):
        if not isinstance(scene, dict):
            continue
        scene_id = str(scene.get("sceneId") or f"scene-{scene_index:02d}")
        for beat_index, beat in enumerate(scene.get("visualBeats", []), start=1):
            if not isinstance(beat, dict):
                continue
            yield scene, scene_id, beat, beat_index


def _beat_source_ids(scene: dict[str, Any], beat: dict[str, Any]) -> set[str]:
    ids = beat.get("evidenceSourceIds")
    if not isinstance(ids, list):
        ids = scene.get("evidenceSourceIds")
    return {item for item in ids or [] if isinstance(item, str) and item}


def _beat_text(scene: dict[str, Any], beat: dict[str, Any]) -> str:
    return _lower_text(
        {
            "headline": scene.get("headline"),
            "purpose": scene.get("purpose"),
            "timelineBasis": scene.get("timelineBasis"),
            "sourceLabel": scene.get("sourceLabel"),
            "screenQuestion": beat.get("screenQuestion"),
            "primaryElement": beat.get("primaryElement"),
            "viewerTexts": beat.get("viewerTexts"),
            "contentType": beat.get("contentType"),
            "dataBasis": (beat.get("templateConfig") or {}).get("dataBasis")
            if isinstance(beat.get("templateConfig"), dict)
            else None,
            "narrationStartCue": beat.get("narrationStartCue"),
            "narrationEndCue": beat.get("narrationEndCue"),
        }
    )


def _intent_rows(intents_doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows = intents_doc.get("intents")
    if not isinstance(rows, list):
        raise VisualEvidenceQualityError("Visual Source intents must be an array")
    return [item for item in rows if isinstance(item, dict)]


def _intent_source_map(intents: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for intent in intents:
        for source_id in intent.get("sourceIds", []):
            if isinstance(source_id, str) and source_id:
                result.setdefault(source_id, []).append(intent)
    return result


def _target_key(intent: dict[str, Any]) -> tuple[str | None, str | None]:
    target = intent.get("target")
    if not isinstance(target, dict):
        return None, None
    scene_id = target.get("sceneId")
    beat_id = target.get("visualBeatId")
    return (
        scene_id if isinstance(scene_id, str) else None,
        beat_id if isinstance(beat_id, str) else None,
    )


def _is_earnings_source(source: dict[str, Any]) -> bool:
    if _source_type(source) != "company":
        return False
    text = _source_text(source)
    return any(marker in text for marker in EARNINGS_MARKERS)


def _is_intraday_source(source: dict[str, Any]) -> bool:
    text = _source_text(source)
    return any(marker in text for marker in INTRADAY_MARKERS)


def _beat_has_verified_series(scene: dict[str, Any], beat: dict[str, Any]) -> bool:
    if beat.get("visualTemplate") != "event-reaction-timeline":
        return False
    config = beat.get("templateConfig")
    if not isinstance(config, dict):
        return False
    reaction = config.get("reactionTimeline")
    if not isinstance(reaction, dict):
        return False
    precision = reaction.get("precision")
    variant = config.get("variant") or beat.get("templateVariant")
    series_ids = reaction.get("seriesObjectIds")
    if precision != "verified-intraday-series" or variant != "verified-series":
        return False
    if not isinstance(series_ids, list) or len(series_ids) < 3:
        return False
    number_map = {
        str(item.get("numberId") or item.get("key")): item
        for item in scene.get("numbers", [])
        if isinstance(item, dict)
    }
    for object_id in series_ids:
        item = number_map.get(str(object_id))
        if not isinstance(item, dict) or not isinstance(item.get("numericValue"), (int, float)):
            return False
    return True


def validate_visual_evidence(
    *, render: dict[str, Any], intents_doc: dict[str, Any]
) -> dict[str, Any]:
    intents = _intent_rows(intents_doc)
    intent_by_source = _intent_source_map(intents)
    sources = {
        sid: source
        for source in _source_rows(render)
        if (sid := _source_id(source)) is not None
    }
    beats = list(_iter_beats(render))
    violations: list[dict[str, Any]] = []

    # Intent targets must already cite at least one of the same approved source IDs.
    beat_lookup: dict[tuple[str, str], tuple[dict[str, Any], dict[str, Any]]] = {}
    for scene, scene_id, beat, _ in beats:
        beat_lookup[(scene_id, _beat_id(beat))] = (scene, beat)
    for intent in intents:
        scene_id, beat_id = _target_key(intent)
        target = beat_lookup.get((scene_id or "", beat_id or ""))
        if target is None:
            continue  # structural contract owns missing-target failure
        scene, beat = target
        authored = _beat_source_ids(scene, beat)
        planned = {
            item for item in intent.get("sourceIds", []) if isinstance(item, str) and item
        }
        if planned and not planned.intersection(authored):
            violations.append(
                {
                    "code": "VE_INTENT_SOURCE_NOT_BOUND_TO_BEAT",
                    "path": f"{scene_id}/{beat_id}",
                    "message": "Visual Source Intent must reuse a source already cited by the target Beat.",
                    "sourceIds": sorted(planned),
                }
            )

    # Real original evidence may not silently degrade to not-required when it is an
    # approved Anchor/Evidence. Company earnings and material social posts are also
    # required even when the Beat function is Explain/Compare.
    for source_id, source in sources.items():
        source_type = _source_type(source)
        if source_type not in ORIGINAL_SOURCE_TYPES:
            continue
        references: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
        for scene, scene_id, beat, _ in beats:
            if source_id in _beat_source_ids(scene, beat):
                references.append((scene_id, scene, beat))
        if not references:
            continue
        anchored = any(beat.get("primaryFunction") in ANCHOR_FUNCTIONS for _, _, beat in references)
        material_social = source_type in {"social", "social-post"}
        material_earnings = _is_earnings_source(source)
        if not (anchored or material_social or material_earnings):
            continue
        if source_id not in intent_by_source:
            violations.append(
                {
                    "code": "VE_ORIGINAL_EVIDENCE_NOT_PLANNED",
                    "path": f"source:{source_id}",
                    "message": (
                        "Approved original evidence is material to the story but has no explicit "
                        "Visual Source Primary/Fallback plan."
                    ),
                    "sourceType": source_type,
                    "title": source.get("title"),
                }
            )

    # If verified minute evidence is being used to state a release-time reaction,
    # at least one Beat citing that source must show actual numeric series points.
    for source_id, source in sources.items():
        if not _is_intraday_source(source):
            continue
        timing_refs: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
        for scene, scene_id, beat, _ in beats:
            if source_id not in _beat_source_ids(scene, beat):
                continue
            text = _beat_text(scene, beat)
            if any(marker in text for marker in TIMING_BEAT_MARKERS):
                timing_refs.append((scene_id, scene, beat))
        if not timing_refs:
            continue
        if not any(_beat_has_verified_series(scene, beat) for _, scene, beat in timing_refs):
            violations.append(
                {
                    "code": "VE_VERIFIED_INTRADAY_COLLAPSED_TO_ABSTRACT",
                    "path": f"source:{source_id}",
                    "message": (
                        "Verified intraday timing evidence is cited by the approved story, but no "
                        "citing Beat renders it with event-reaction-timeline / verified-series."
                    ),
                    "title": source.get("title"),
                }
            )

    status = "PASS" if not violations else "FAIL"
    return {
        "contractVersion": "1.0.0",
        "episodeDate": (render.get("episode") or {}).get("id")
        if isinstance(render.get("episode"), dict)
        else render.get("episodeDate"),
        "status": status,
        "intentCount": len(intents),
        "sourceCount": len(sources),
        "violations": violations,
    }


def enforce_visual_evidence(
    *, render: dict[str, Any], intents_doc: dict[str, Any]
) -> dict[str, Any]:
    report = validate_visual_evidence(render=render, intents_doc=intents_doc)
    if report["status"] != "PASS":
        lines = [
            f"{item['code']} {item['path']}: {item['message']}"
            for item in report["violations"]
        ]
        raise VisualEvidenceQualityError("\n".join(lines))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-spec", type=Path, required=True)
    parser.add_argument("--intents", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = validate_visual_evidence(
            render=load_json(args.render_spec, "render spec"),
            intents_doc=load_json(args.intents, "Visual Source intents"),
        )
        code = 0 if report["status"] == "PASS" else 2
    except (VisualEvidenceQualityError, OSError, json.JSONDecodeError) as exc:
        report = {"contractVersion": "1.0.0", "status": "FAIL", "violations": [{"code": "VE_GATE_ERROR", "path": "$", "message": str(exc)}]}
        code = 2
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
