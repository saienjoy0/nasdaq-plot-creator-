#!/usr/bin/env python3
"""Deterministic Temporal Evidence helpers for 朝のNASDAQカフェ.

This is a thin extension over the existing editorial-memory archive. It does
not create a Temporal DB, choose a lead, decide causality, or author narration.
It only replays approved publication revisions, validates Validation
Obligations, and renders the mandatory carryover block.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping

APPROVED_STATUSES = {"approved_preview", "published"}
RESULT_STATUSES = {
    "supports", "weakens", "contradicts", "inconclusive", "not_observed", "expired"
}
CLOSING_RESULT_STATUSES = {
    "supports", "weakens", "contradicts", "inconclusive", "expired"
}
EVIDENCE_REQUIRED_RESULTS = {"supports", "weakens", "contradicts"}


class TemporalEvidenceError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TemporalEvidenceError(f"JSON root must be an object: {path}")
    return value


def _day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise TemporalEvidenceError(f"invalid ISO date: {value}") from exc


def _norm_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def obligation_key(obligation: Mapping[str, Any]) -> str:
    """Stable semantic key used for duplicate-control without inventing IDs."""
    body = {
        "hypothesis_reference": obligation.get("hypothesis_reference"),
        "observation_target": obligation.get("observation_target"),
        "strengthen_condition": obligation.get("strengthen_condition"),
        "weaken_condition": obligation.get("weaken_condition"),
    }
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_obligation(obligation: Mapping[str, Any], *, label: str = "validation_obligation") -> None:
    required = (
        "obligation_id", "source_episode_date", "hypothesis_reference", "question",
        "observation_target", "strengthen_condition", "weaken_condition",
        "max_observation_sessions", "importance", "status", "watch_next_display_text",
    )
    missing = [key for key in required if key not in obligation]
    if missing:
        raise TemporalEvidenceError(f"{label}: missing fields: {missing}")
    if obligation.get("status") != "open":
        raise TemporalEvidenceError(f"{label}: status must be open")
    target = obligation.get("observation_target")
    if not isinstance(target, Mapping):
        raise TemporalEvidenceError(f"{label}: observation_target must be one object")
    target_required = ("market", "instrument_group", "metric", "session", "precision_required")
    target_missing = [key for key in target_required if not _norm_text(target.get(key))]
    if target_missing:
        raise TemporalEvidenceError(
            f"{label}: observation_target missing scalar fields: {target_missing}"
        )
    for key, value in target.items():
        if isinstance(value, (list, tuple, set, dict)):
            raise TemporalEvidenceError(
                f"{label}: 1 VO = 1 target; observation_target.{key} must be scalar"
            )
    if not _norm_text(obligation.get("strengthen_condition")):
        raise TemporalEvidenceError(f"{label}: strengthen_condition is required")
    if not _norm_text(obligation.get("weaken_condition")):
        raise TemporalEvidenceError(f"{label}: weaken_condition is required")
    sessions = obligation.get("max_observation_sessions")
    if not isinstance(sessions, int) or isinstance(sessions, bool) or sessions < 1:
        raise TemporalEvidenceError(f"{label}: max_observation_sessions must be >= 1")


def validate_result(result: Mapping[str, Any], *, label: str = "carryover_result") -> None:
    status = result.get("status")
    if status not in RESULT_STATUSES:
        raise TemporalEvidenceError(f"{label}: invalid status {status!r}")
    evidence_ids = result.get("current_evidence_ids", [])
    if not isinstance(evidence_ids, list) or any(not isinstance(x, str) for x in evidence_ids):
        raise TemporalEvidenceError(f"{label}: current_evidence_ids must be an array of strings")
    if status in EVIDENCE_REQUIRED_RESULTS and not evidence_ids:
        raise TemporalEvidenceError(f"{label}: {status} requires Current Evidence ID")


def iter_current_approved_publications(
    repo_root: Path, *, before_episode_date: str | None = None
) -> Iterable[tuple[str, str, dict[str, Any]]]:
    """Yield only current approved revisions in chronological episode order."""
    root = repo_root.resolve()
    episodes = root / "editorial-memory" / "episodes"
    if not episodes.is_dir():
        return
    upper = _day(before_episode_date) if before_episode_date else None
    for episode_dir in sorted(path for path in episodes.iterdir() if path.is_dir()):
        episode_date = episode_dir.name
        try:
            parsed = _day(episode_date)
        except TemporalEvidenceError:
            continue
        if upper is not None and parsed >= upper:
            continue
        index_path = episode_dir / "index.json"
        if not index_path.is_file():
            continue
        index = _load_json(index_path)
        revision = index.get("current_revision")
        if not isinstance(revision, str) or not revision:
            continue
        revision_meta = next(
            (
                row for row in index.get("revisions", [])
                if isinstance(row, Mapping) and row.get("revision") == revision
            ),
            None,
        )
        if revision_meta is None:
            # Legacy seeded archives may predate the revisions array. Provenance is authoritative.
            provenance_path = episode_dir / "revisions" / revision / "provenance.json"
            if not provenance_path.is_file():
                continue
            approval_status = _load_json(provenance_path).get("approval_status")
        else:
            approval_status = revision_meta.get("approval_status")
        if approval_status not in APPROVED_STATUSES:
            continue
        record_path = episode_dir / "revisions" / revision / "publication_record.json"
        if not record_path.is_file():
            continue
        record = _load_json(record_path)
        if record.get("approval", {}).get("status") not in APPROVED_STATUSES:
            continue
        yield episode_date, revision, record


@dataclass(frozen=True)
class OpenObligation:
    obligation: dict[str, Any]
    last_episode_date: str
    source_revision: str


def replay_open_validation_obligations(
    repo_root: Path, *, before_episode_date: str
) -> list[OpenObligation]:
    """Replay publication events; carry questions, never past conclusions."""
    open_by_id: dict[str, OpenObligation] = {}
    key_to_id: dict[str, str] = {}

    for episode_date, revision, record in iter_current_approved_publications(
        repo_root, before_episode_date=before_episode_date
    ):
        temporal = record.get("temporal_evidence")
        if not isinstance(temporal, Mapping):
            # Backward compatibility: old 1.0 records simply have no Temporal data.
            continue

        for index, result in enumerate(temporal.get("carryover_results", [])):
            if not isinstance(result, Mapping):
                raise TemporalEvidenceError(
                    f"{episode_date}/{revision}.carryover_results[{index}] must be an object"
                )
            validate_result(result, label=f"{episode_date}/{revision}.carryover_results[{index}]")
            obligation_id = result.get("obligation_id")
            if obligation_id not in open_by_id:
                # A result may reference an already-closed historical item; it must not recreate it.
                continue
            if result["status"] in CLOSING_RESULT_STATUSES:
                old = open_by_id.pop(obligation_id)
                key_to_id.pop(obligation_key(old.obligation), None)
            elif result["status"] == "not_observed":
                old = open_by_id[obligation_id]
                open_by_id[obligation_id] = OpenObligation(
                    obligation=old.obligation,
                    last_episode_date=episode_date,
                    source_revision=revision,
                )

        for index, raw in enumerate(temporal.get("validation_obligations", [])):
            if not isinstance(raw, Mapping):
                raise TemporalEvidenceError(
                    f"{episode_date}/{revision}.validation_obligations[{index}] must be an object"
                )
            obligation = dict(raw)
            validate_obligation(
                obligation,
                label=f"{episode_date}/{revision}.validation_obligations[{index}]",
            )
            obligation_id = obligation["obligation_id"]
            key = obligation_key(obligation)
            existing_id = key_to_id.get(key)
            if existing_id and existing_id != obligation_id:
                raise TemporalEvidenceError(
                    f"duplicate VO semantic key: existing={existing_id} new={obligation_id}"
                )
            if obligation_id in open_by_id:
                if obligation_key(open_by_id[obligation_id].obligation) != key:
                    raise TemporalEvidenceError(
                        f"VO {obligation_id} was reused with changed semantics"
                    )
                continue
            open_by_id[obligation_id] = OpenObligation(
                obligation=obligation,
                last_episode_date=episode_date,
                source_revision=revision,
            )
            key_to_id[key] = obligation_id

    open_items = sorted(
        open_by_id.values(),
        key=lambda item: (
            item.obligation.get("source_episode_date", ""),
            item.obligation.get("obligation_id", ""),
        ),
    )
    if len(open_items) > 3:
        raise TemporalEvidenceError(
            f"simultaneously open Validation Obligations exceed max 3: {len(open_items)}"
        )
    return open_items


def render_mandatory_temporal_carryover(repo_root: Path, *, episode_date: str) -> str:
    items = replay_open_validation_obligations(repo_root, before_episode_date=episode_date)
    lines = [
        "## Mandatory Temporal Carryover",
        "",
        "> Carry forward questions, not conclusions. Current evidence can revise memory; memory cannot revise current evidence.",
        "",
    ]
    if not items:
        lines.append("- Open validation obligations: `0`")
        return "\n".join(lines) + "\n"
    lines.append(f"- Open validation obligations: `{len(items)}`")
    for item in items:
        vo = item.obligation
        target = vo["observation_target"]
        lines.extend(
            [
                "",
                f"### {vo['obligation_id']}",
                f"- Source episode: `{vo['source_episode_date']}`",
                f"- Current revision source: `{item.last_episode_date}/{item.source_revision}`",
                f"- Hypothesis: `{vo['hypothesis_reference']}`",
                f"- Question: {vo['question']}",
                "- Observation target: "
                + " / ".join(
                    str(target[key])
                    for key in ("market", "instrument_group", "metric", "session", "precision_required")
                ),
                f"- Strengthens if: {vo['strengthen_condition']}",
                f"- Weakens if: {vo['weaken_condition']}",
                f"- Max completed observation sessions: `{vo['max_observation_sessions']}`",
            ]
        )
    return "\n".join(lines) + "\n"


def projected_watch_next(record: Mapping[str, Any]) -> list[str]:
    temporal = record.get("temporal_evidence")
    if not isinstance(temporal, Mapping):
        return []
    projected: list[str] = []
    seen: set[str] = set()
    for item in temporal.get("validation_obligations", []):
        if not isinstance(item, Mapping):
            continue
        text = _norm_text(item.get("watch_next_display_text"))
        if text and text not in seen:
            seen.add(text)
            projected.append(text)
    return projected


def validate_watch_next_projection(record: Mapping[str, Any]) -> None:
    projected = projected_watch_next(record)
    watch_next = record.get("watch_next")
    if not isinstance(watch_next, list) or any(not isinstance(item, str) for item in watch_next):
        raise TemporalEvidenceError("watch_next must be an array of strings")
    positions: list[int] = []
    for text in projected:
        try:
            positions.append(watch_next.index(text))
        except ValueError as exc:
            raise TemporalEvidenceError(
                f"watch_next is missing deterministic VO projection: {text}"
            ) from exc
    if positions != sorted(positions):
        raise TemporalEvidenceError("VO watch_next projections must preserve obligation order")


def validate_publication_temporal(record: Mapping[str, Any], repo_root: Path) -> None:
    version = record.get("contract_version")
    temporal = record.get("temporal_evidence")
    if version == "1.0.0":
        if temporal is not None:
            raise TemporalEvidenceError("publication_record 1.0.0 must not contain temporal_evidence")
        return
    if version != "1.1.0":
        raise TemporalEvidenceError(f"unsupported publication_record contract_version: {version}")
    if not isinstance(temporal, Mapping):
        raise TemporalEvidenceError("publication_record 1.1.0 requires temporal_evidence")

    obligations = temporal.get("validation_obligations", [])
    results = temporal.get("carryover_results", [])
    if not isinstance(obligations, list) or not isinstance(results, list):
        raise TemporalEvidenceError("temporal_evidence arrays are invalid")
    if len(obligations) > 2:
        raise TemporalEvidenceError("new Validation Obligations must be 0..2 per episode")

    ids: set[str] = set()
    keys: set[str] = set()
    for index, obligation in enumerate(obligations):
        if not isinstance(obligation, Mapping):
            raise TemporalEvidenceError(f"validation_obligations[{index}] must be an object")
        validate_obligation(obligation, label=f"validation_obligations[{index}]")
        if obligation["source_episode_date"] != record.get("episode_date"):
            raise TemporalEvidenceError(
                f"validation_obligations[{index}].source_episode_date must equal publication episode_date"
            )
        if obligation["obligation_id"] in ids:
            raise TemporalEvidenceError(f"duplicate obligation_id: {obligation['obligation_id']}")
        ids.add(obligation["obligation_id"])
        key = obligation_key(obligation)
        if key in keys:
            raise TemporalEvidenceError("duplicate Validation Obligation semantics within episode")
        keys.add(key)
    for index, result in enumerate(results):
        if not isinstance(result, Mapping):
            raise TemporalEvidenceError(f"carryover_results[{index}] must be an object")
        validate_result(result, label=f"carryover_results[{index}]")

    validate_watch_next_projection(record)

    # Prevent semantic duplicate IDs against still-open history and enforce max-open=3.
    prior = replay_open_validation_obligations(
        repo_root, before_episode_date=str(record["episode_date"])
    )
    open_by_id = {item.obligation["obligation_id"]: item.obligation for item in prior}
    open_keys = {obligation_key(item.obligation): item.obligation["obligation_id"] for item in prior}
    for result in results:
        obligation_id = result.get("obligation_id")
        prior_obligation = open_by_id.get(obligation_id)
        if prior_obligation is not None and result.get("status") == "expired":
            observed = result.get("completed_observation_sessions")
            maximum = prior_obligation.get("max_observation_sessions")
            if not isinstance(observed, int) or isinstance(observed, bool):
                raise TemporalEvidenceError(
                    f"expired VO {obligation_id} requires completed_observation_sessions"
                )
            if isinstance(maximum, int) and observed < maximum:
                raise TemporalEvidenceError(
                    f"VO {obligation_id} cannot expire before max_observation_sessions={maximum}"
                )
        if obligation_id in open_by_id and result.get("status") in CLOSING_RESULT_STATUSES:
            old = open_by_id.pop(obligation_id)
            open_keys.pop(obligation_key(old), None)
    for obligation in obligations:
        key = obligation_key(obligation)
        obligation_id = obligation["obligation_id"]
        existing_by_id = open_by_id.get(obligation_id)
        if existing_by_id is not None and obligation_key(existing_by_id) != key:
            raise TemporalEvidenceError(
                f"VO {obligation_id} cannot be reused with changed semantics"
            )
        existing = open_keys.get(key)
        if existing and existing != obligation_id:
            raise TemporalEvidenceError(
                f"duplicate VO must continue existing id {existing}, not create {obligation_id}"
            )
        open_by_id.setdefault(obligation_id, dict(obligation))
        open_keys[key] = obligation_id
    if len(open_by_id) > 3:
        raise TemporalEvidenceError(
            f"publication would exceed simultaneously open VO max 3: {len(open_by_id)}"
        )


def project_publication_temporal(
    record: Mapping[str, Any],
    *,
    dossier: Mapping[str, Any],
    story_plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Project the structured Temporal source of truth into a publication record.

    Causal Research owns carryover results. Editorial/Story owns the selected 0-2
    final Validation Obligations. ``watch_next`` remains only a human-readable
    projection plus any pre-existing general monitoring points.
    """
    if dossier.get("contract_version") != "0.3.0":
        raise TemporalEvidenceError("Temporal publication projection requires causal dossier 0.3.0")
    usage = story_plan.get("temporal_usage")
    if not isinstance(usage, Mapping):
        raise TemporalEvidenceError("Temporal publication projection requires story_plan.temporal_usage")

    episode_date = _norm_text(record.get("episode_date"))
    if not episode_date or episode_date != _norm_text(story_plan.get("episode_date")):
        raise TemporalEvidenceError("publication/story episode_date mismatch")
    if episode_date != _norm_text(dossier.get("episode_date")):
        raise TemporalEvidenceError("publication/dossier episode_date mismatch")

    output = json.loads(json.dumps(record, ensure_ascii=False))
    old_projected = set(projected_watch_next(output))
    general_watch = [
        item
        for item in output.get("watch_next", [])
        if isinstance(item, str) and item not in old_projected
    ]

    publication_obligations: list[dict[str, Any]] = []
    for index, row in enumerate(usage.get("validation_obligations", [])):
        if not isinstance(row, Mapping):
            raise TemporalEvidenceError(
                f"temporal_usage.validation_obligations[{index}] must be an object"
            )
        obligation = {
            key: row[key]
            for key in (
                "obligation_id",
                "source_episode_date",
                "hypothesis_reference",
                "question",
                "observation_target",
                "strengthen_condition",
                "weaken_condition",
                "max_observation_sessions",
                "importance",
                "status",
                "watch_next_display_text",
            )
        }
        validate_obligation(
            obligation,
            label=f"temporal_usage.validation_obligations[{index}]",
        )
        publication_obligations.append(obligation)

    carryover_results: list[dict[str, Any]] = []
    for index, row in enumerate(dossier.get("carryover_results", [])):
        if not isinstance(row, Mapping):
            raise TemporalEvidenceError(f"carryover_results[{index}] must be an object")
        result = dict(row)
        validate_result(result, label=f"carryover_results[{index}]")
        carryover_results.append(result)

    output["contract_version"] = "1.1.0"
    output["temporal_evidence"] = {
        "carryover_results": carryover_results,
        "validation_obligations": publication_obligations,
    }
    projected = [item["watch_next_display_text"] for item in publication_obligations]
    output["watch_next"] = [*general_watch, *projected]
    return output


def validate_temporal_visual_intents(
    repo_root: Path,
    *,
    episode_date: str,
    visual_sources: Mapping[str, Any],
) -> None:
    """Fail closed when an adopted Temporal visual need has no Visual Source intent.

    This function does not choose a surface. Story/Visual Planning explicitly binds
    already-defined TVE need IDs to existing Visual Source intents. Old dossiers and
    tiny visual-unit fixtures remain backward compatible.
    """
    root = repo_root.resolve()
    dossier_path = root / "research" / episode_date / f"causal_research_dossier_{episode_date}.json"
    if not dossier_path.is_file():
        return
    dossier = _load_json(dossier_path)
    if dossier.get("contract_version") != "0.3.0":
        return

    story_path = root / "working" / episode_date / "story-engine" / "story_plan.json"
    if not story_path.is_file():
        raise TemporalEvidenceError(
            "E_TEMPORAL_VISUAL_EVIDENCE_MISSING: Temporal dossier 0.3 requires the reviewed Story Plan before Visual Evidence Planning"
        )
    story = _load_json(story_path)
    usage = story.get("temporal_usage")
    if not isinstance(usage, Mapping):
        raise TemporalEvidenceError(
            "E_TEMPORAL_VISUAL_EVIDENCE_MISSING: story_plan.temporal_usage is required"
        )

    known_need_ids = {
        item.get("need_id")
        for item in dossier.get("visual_evidence_needs", [])
        if isinstance(item, Mapping) and isinstance(item.get("need_id"), str)
    }
    required_need_ids: set[str] = set()

    def collect(row: Mapping[str, Any], label: str) -> None:
        if row.get("mode") != "spoken":
            return
        ids = row.get("visual_need_ids", [])
        if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids):
            raise TemporalEvidenceError(
                f"E_TEMPORAL_VISUAL_EVIDENCE_MISSING: {label}.visual_need_ids must be an array"
            )
        unknown = set(ids) - known_need_ids
        if unknown:
            raise TemporalEvidenceError(
                f"E_TEMPORAL_VISUAL_EVIDENCE_MISSING: {label} references unknown visual need ids {sorted(unknown)}"
            )
        required_need_ids.update(ids)

    for index, row in enumerate(usage.get("carryover_results", [])):
        if isinstance(row, Mapping):
            collect(row, f"temporal_usage.carryover_results[{index}]")
    cross = usage.get("cross_market")
    if isinstance(cross, Mapping):
        collect(cross, "temporal_usage.cross_market")
    for index, row in enumerate(usage.get("validation_obligations", [])):
        if isinstance(row, Mapping):
            collect(row, f"temporal_usage.validation_obligations[{index}]")

    planned_need_ids: set[str] = set()
    intents = visual_sources.get("intents", [])
    if not isinstance(intents, list):
        raise TemporalEvidenceError("E_TEMPORAL_VISUAL_EVIDENCE_MISSING: Visual Source intents must be an array")
    for index, intent in enumerate(intents):
        if not isinstance(intent, Mapping):
            continue
        values = intent.get("temporalEvidenceNeedIds", [])
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            raise TemporalEvidenceError(
                f"E_TEMPORAL_VISUAL_EVIDENCE_MISSING: intents[{index}].temporalEvidenceNeedIds must be an array"
            )
        unknown = set(values) - known_need_ids
        if unknown:
            raise TemporalEvidenceError(
                f"E_TEMPORAL_VISUAL_EVIDENCE_MISSING: Visual Source intent references unknown Temporal need ids {sorted(unknown)}"
            )
        planned_need_ids.update(values)

    missing = required_need_ids - planned_need_ids
    if missing:
        raise TemporalEvidenceError(
            "E_TEMPORAL_VISUAL_EVIDENCE_MISSING: spoken/material Temporal visual needs have no Visual Source plan: "
            + ", ".join(sorted(missing))
        )
