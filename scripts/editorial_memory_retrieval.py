#!/usr/bin/env python3
"""Deterministic, auditable retrieval for 朝のNASDAQカフェ editorial memory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover
    raise SystemExit("jsonschema is required: python -m pip install jsonschema") from exc


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
TYPE_ORDER = {"thread": 0, "claim": 1, "episode": 2, "lesson": 3}
HISTORICAL_ONLY_STATUSES = {"resolved", "invalidated"}
REJECT_REASONS = {
    "low_relevance",
    "invalidated_current_use",
    "resolved_not_needed",
    "missing_provenance",
    "duplicate",
    "diversity_limit",
    "count_limit",
    "character_limit",
    "archived",
    "outside_time_window",
}


@dataclass
class Candidate:
    item_type: str
    item_id: str
    path: str
    content: str
    score: int
    reasons: list[str]
    provenance_paths: list[str]
    status: str
    use_mode: str
    requires_current_revalidation: bool
    historical_confidence: str = "unknown"
    episode_ids: list[str] = field(default_factory=list)
    thread_ids: list[str] = field(default_factory=list)
    updated_at: str = ""
    title: str = ""
    duplicate_key: str = ""

    def __post_init__(self) -> None:
        if not self.duplicate_key:
            normalized = normalize(self.content)
            self.duplicate_key = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def report_item(self) -> dict[str, Any]:
        return {
            "item_type": self.item_type,
            "item_id": self.item_id,
            "path": self.path,
            "score": self.score,
            "reasons": sorted(set(self.reasons)),
            "provenance_paths": sorted(set(self.provenance_paths)),
            "status": self.status,
            "use_mode": self.use_mode,
            "requires_current_revalidation": self.requires_current_revalidation,
            "historical_confidence": self.historical_confidence,
            "episode_ids": sorted(set(self.episode_ids)),
        }


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip().casefold())


def unique_strings(values: Iterable[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        if not isinstance(raw, str):
            continue
        value = raw.strip()
        key = normalize(value)
        if value and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_document(document: Any, schema_path: Path) -> None:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    if errors:
        messages = []
        for error in errors[:20]:
            location = ".".join(str(part) for part in error.path) or "<root>"
            messages.append(f"{location}: {error.message}")
        raise ValueError(f"{schema_path.name} validation failed: " + "; ".join(messages))


def repo_relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def safe_repo_path(repo_root: Path, relative: str) -> Path:
    root = repo_root.resolve()
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"path escapes repository: {relative}")
    return candidate


def phrase_match(needle: str, haystack: str) -> bool:
    left = normalize(needle)
    right = normalize(haystack)
    if not left or not right:
        return False
    if left == right:
        return True
    if min(len(left), len(right)) < 3:
        return False
    return left in right or right in left


def parse_day(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def recency_points(updated_at: str, episode_date: str) -> tuple[int, str | None]:
    updated = parse_day(updated_at)
    target = parse_day(episode_date)
    if not updated or not target:
        return 0, None
    delta = (target - updated).days
    if 0 <= delta <= 30:
        return 3, "within_30_days"
    if 0 <= delta <= 90:
        return 2, "within_90_days"
    return 0, None


def query_phrases(plan: dict[str, Any]) -> list[str]:
    values: list[Any] = []
    for key in (
        "lead_candidates",
        "topics",
        "technologies",
        "policies",
        "indicators",
        "comparison_questions",
    ):
        values.extend(plan.get(key, []))
    for relation in plan.get("relations", []):
        if isinstance(relation, dict):
            values.extend([relation.get("source"), relation.get("relation"), relation.get("target")])
    for entity in plan.get("entities", []):
        if isinstance(entity, dict):
            values.extend([entity.get("raw"), entity.get("canonical"), entity.get("entity_id")])
    return unique_strings(values)


def build_alias_maps(alias_doc: dict[str, Any]) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    alias_to_id: dict[str, str] = {}
    by_id: dict[str, dict[str, Any]] = {}
    for entity in alias_doc.get("entities", []):
        if not isinstance(entity, dict):
            continue
        entity_id = str(entity.get("entity_id", "")).strip()
        if not entity_id:
            continue
        by_id[entity_id] = entity
        names = [entity_id, entity.get("canonical_name", ""), *entity.get("aliases", [])]
        for name in names:
            if isinstance(name, str) and normalize(name):
                alias_to_id[normalize(name)] = entity_id
    return alias_to_id, by_id


def resolve_entities(
    plan: dict[str, Any],
    alias_to_id: dict[str, str],
    aliases_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    resolved: list[dict[str, Any]] = []
    warnings: list[str] = []
    for item in plan.get("entities", []):
        if not isinstance(item, dict):
            continue
        raw = str(item.get("raw", "")).strip()
        canonical = str(item.get("canonical", raw)).strip() or raw
        declared_id = item.get("entity_id")
        entity_id: str | None = None
        resolution = "unresolved"

        if isinstance(declared_id, str) and declared_id in aliases_by_id:
            entity_id = declared_id
            resolution = "exact"
        else:
            raw_id = alias_to_id.get(normalize(raw))
            canonical_id = alias_to_id.get(normalize(canonical))
            entity_id = raw_id or canonical_id
            if entity_id:
                canonical_name = str(aliases_by_id[entity_id].get("canonical_name", entity_id))
                exact_terms = {normalize(entity_id), normalize(canonical_name)}
                resolution = "exact" if normalize(raw) in exact_terms or normalize(canonical) in exact_terms else "alias"

        if entity_id:
            canonical = str(aliases_by_id[entity_id].get("canonical_name", canonical))
        else:
            warnings.append(f"unresolved entity alias: {raw or canonical}")

        resolved.append(
            {
                "raw": raw or canonical,
                "canonical": canonical,
                "entity_id": entity_id,
                "resolution": resolution,
            }
        )
    return resolved, warnings


def entity_match_points(
    values: Iterable[str],
    resolved_entities: list[dict[str, Any]],
    alias_to_id: dict[str, str],
) -> tuple[int, list[str]]:
    points = 0
    reasons: list[str] = []
    normalized_values = [normalize(value) for value in values if normalize(value)]
    value_ids = {alias_to_id.get(value) for value in normalized_values if alias_to_id.get(value)}
    for entity in resolved_entities:
        entity_id = entity.get("entity_id")
        raw = normalize(entity.get("raw", ""))
        canonical = normalize(entity.get("canonical", ""))
        if entity_id and entity_id in value_ids:
            if entity.get("resolution") == "alias" and raw not in normalized_values:
                points += 7
                reasons.append("entity_alias_match")
            elif raw in normalized_values or canonical in normalized_values or normalize(entity_id) in normalized_values:
                points += 8
                reasons.append("exact_entity_match")
            else:
                points += 7
                reasons.append("entity_alias_match")
        elif any(phrase_match(raw, value) or phrase_match(canonical, value) for value in normalized_values):
            points += 5
            reasons.append("unresolved_entity_text_match")
    return points, reasons


def text_match_once(phrases: Iterable[str], fields: Iterable[str], points: int, reason: str) -> tuple[int, list[str]]:
    for phrase in phrases:
        if any(phrase_match(phrase, field) for field in fields):
            return points, [reason]
    return 0, []


def provenance_for_episode(episode_ref: str) -> str | None:
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})/(v\d{3})", episode_ref)
    if not match:
        return None
    return f"editorial-memory/episodes/{match.group(1)}/revisions/{match.group(2)}/provenance.json"


def episode_summary_path(episode_ref: str) -> str | None:
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})/(v\d{3})", episode_ref)
    if not match:
        return None
    return f"editorial-memory/episodes/{match.group(1)}/revisions/{match.group(2)}/episode_summary.md"


def has_counterevidence(repo_root: Path, episode_refs: Iterable[str]) -> bool:
    for episode_ref in episode_refs:
        relative = episode_summary_path(episode_ref)
        if not relative:
            continue
        path = safe_repo_path(repo_root, relative)
        if path.exists() and "## 重要な反対材料" in path.read_text(encoding="utf-8"):
            return True
    return False


def in_time_window(item_date: str, plan: dict[str, Any]) -> bool:
    parsed = parse_day(item_date)
    if not parsed:
        return True
    window = plan.get("time_window", {})
    lower = parse_day(window.get("from"))
    upper = parse_day(window.get("to"))
    if lower and parsed < lower:
        return False
    if upper and parsed > upper:
        return False
    return True


def rejection(item_type: str, item_id: str, reason: str, detail: str = "") -> dict[str, Any]:
    if reason not in REJECT_REASONS:
        raise ValueError(f"unsupported rejection reason: {reason}")
    item = {"item_type": item_type, "item_id": item_id, "reason": reason}
    if detail:
        item["detail"] = detail
    return item


def collect_threads(
    repo_root: Path,
    plan: dict[str, Any],
    resolved_entities: list[dict[str, Any]],
    alias_to_id: dict[str, str],
    phrases: list[str],
) -> tuple[list[Candidate], list[dict[str, Any]]]:
    memory_root = repo_root / "editorial-memory"
    index = load_json(memory_root / "threads" / "index.json", {"threads": []})
    candidates: list[Candidate] = []
    rejected: list[dict[str, Any]] = []

    for item in index.get("threads", []):
        if not isinstance(item, dict):
            continue
        thread_id = str(item.get("id", "")).strip()
        if not thread_id:
            continue
        status = str(item.get("status", "unknown"))
        if status == "archived":
            rejected.append(rejection("thread", thread_id, "archived"))
            continue

        relative = f"editorial-memory/{item.get('path', f'threads/{thread_id}.md')}"
        path = safe_repo_path(repo_root, relative)
        content = path.read_text(encoding="utf-8").strip() if path.exists() else ""
        episode_ref = str(item.get("last_episode_revision", ""))
        provenance = provenance_for_episode(episode_ref)
        if not provenance or not safe_repo_path(repo_root, provenance).exists():
            rejected.append(rejection("thread", thread_id, "missing_provenance"))
            continue
        updated_at = str(item.get("updated_at", ""))
        if not in_time_window(updated_at, plan):
            rejected.append(rejection("thread", thread_id, "outside_time_window"))
            continue

        score = 0
        reasons: list[str] = []
        added, why = entity_match_points(item.get("entities", []), resolved_entities, alias_to_id)
        score += added
        reasons += why
        added, why = text_match_once(
            phrases,
            [thread_id, str(item.get("title", "")), *item.get("triggers", [])],
            6,
            "thread_trigger_match",
        )
        score += added
        reasons += why
        added, why = text_match_once(phrases, item.get("topics", []), 4, "topic_match")
        score += added
        reasons += why
        added, why = text_match_once(phrases, [content], 3, "content_phrase_match")
        score += added
        reasons += why
        relevance_score = score
        if relevance_score == 0:
            rejected.append(rejection("thread", thread_id, "low_relevance"))
            continue
        recent, recent_reason = recency_points(updated_at, plan["episode_date"])
        score += recent
        if recent_reason:
            reasons.append(recent_reason)
        score += 2
        reasons.append("provenance_verified")
        if has_counterevidence(repo_root, [episode_ref]):
            score += 1
            reasons.append("counterevidence_preserved")
        candidates.append(
            Candidate(
                item_type="thread",
                item_id=thread_id,
                path=relative,
                content=content or f"# {item.get('title', thread_id)}\n\n記録本文なし。",
                score=score,
                reasons=reasons,
                provenance_paths=[provenance],
                status=status,
                use_mode="current_revalidation_required",
                requires_current_revalidation=True,
                episode_ids=[episode_ref.split("/")[0]] if "/" in episode_ref else [],
                thread_ids=[thread_id],
                updated_at=updated_at,
                title=str(item.get("title", thread_id)),
            )
        )
    return candidates, rejected


def collect_claims(
    repo_root: Path,
    plan: dict[str, Any],
    resolved_entities: list[dict[str, Any]],
    alias_to_id: dict[str, str],
    phrases: list[str],
    relevant_thread_ids: set[str],
) -> tuple[list[Candidate], list[dict[str, Any]]]:
    ledger = load_json(repo_root / "editorial-memory" / "claim_ledger.json", {"claims": []})
    historical_mode = bool(plan.get("comparison_questions"))
    candidates: list[Candidate] = []
    rejected: list[dict[str, Any]] = []

    for claim in ledger.get("claims", []):
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", "")).strip()
        if not claim_id:
            continue
        status = str(claim.get("status", "unknown"))
        if status == "invalidated" and not historical_mode:
            rejected.append(rejection("claim", claim_id, "invalidated_current_use"))
            continue
        if status == "resolved" and not historical_mode:
            rejected.append(rejection("claim", claim_id, "resolved_not_needed"))
            continue

        histories = [item for item in claim.get("history", []) if isinstance(item, dict)]
        provenance_paths = unique_strings(item.get("provenance_path", "") for item in histories)
        provenance_paths = [path for path in provenance_paths if safe_repo_path(repo_root, path).exists()]
        if not provenance_paths:
            rejected.append(rejection("claim", claim_id, "missing_provenance"))
            continue

        updated_at = str(claim.get("last_updated", ""))
        if not in_time_window(updated_at, plan):
            rejected.append(rejection("claim", claim_id, "outside_time_window"))
            continue

        score = 0
        reasons: list[str] = []
        added, why = entity_match_points(claim.get("entities", []), resolved_entities, alias_to_id)
        score += added
        reasons += why
        added, why = text_match_once(
            phrases,
            [str(claim.get("subject", "")), str(claim.get("claim", ""))],
            5,
            "claim_subject_match",
        )
        score += added
        reasons += why
        added, why = text_match_once(phrases, claim.get("topics", []), 4, "topic_match")
        score += added
        reasons += why
        thread_ids = {str(value) for value in claim.get("thread_ids", []) if isinstance(value, str)}
        if thread_ids & relevant_thread_ids:
            score += 6
            reasons.append("linked_relevant_thread")
        relevance_score = score
        if relevance_score == 0:
            rejected.append(rejection("claim", claim_id, "low_relevance"))
            continue
        recent, recent_reason = recency_points(updated_at, plan["episode_date"])
        score += recent
        if recent_reason:
            reasons.append(recent_reason)
        status_points = {"active": 2, "strengthened": 2, "weakened": 1}.get(status, 0)
        score += status_points
        if status_points:
            reasons.append(f"status_{status}")
        score += 2
        reasons.append("provenance_verified")
        episode_refs = unique_strings(item.get("episode_revision", "") for item in histories)
        if has_counterevidence(repo_root, episode_refs):
            score += 1
            reasons.append("counterevidence_preserved")
        historical = status in HISTORICAL_ONLY_STATUSES
        candidates.append(
            Candidate(
                item_type="claim",
                item_id=claim_id,
                path="editorial-memory/claim_ledger.json",
                content=(
                    f"## {claim.get('subject', claim_id)}\n\n"
                    f"{claim.get('claim', '')}\n\n"
                    f"- Status: `{status}`\n"
                    f"- Confidence: `{claim.get('confidence', 'unknown')}`\n"
                    f"- Last updated: `{updated_at or 'unknown'}`\n"
                    f"- Thread IDs: {', '.join(sorted(thread_ids)) or 'なし'}"
                ),
                score=score,
                reasons=reasons,
                provenance_paths=provenance_paths,
                status=status,
                use_mode="historical_context" if historical else "current_revalidation_required",
                requires_current_revalidation=not historical,
                historical_confidence=str(claim.get("confidence", "unknown")),
                episode_ids=sorted({ref.split("/")[0] for ref in episode_refs if "/" in ref}),
                thread_ids=sorted(thread_ids),
                updated_at=updated_at,
                title=str(claim.get("subject", claim_id)),
            )
        )
    return candidates, rejected


def collect_episodes(
    repo_root: Path,
    plan: dict[str, Any],
    resolved_entities: list[dict[str, Any]],
    aliases_by_id: dict[str, dict[str, Any]],
    phrases: list[str],
) -> tuple[list[Candidate], list[dict[str, Any]]]:
    episodes_root = repo_root / "editorial-memory" / "episodes"
    candidates: list[Candidate] = []
    rejected: list[dict[str, Any]] = []
    if not episodes_root.exists():
        return candidates, rejected

    for episode_dir in sorted(path for path in episodes_root.iterdir() if path.is_dir()):
        episode_id = episode_dir.name
        index_path = episode_dir / "index.json"
        if not index_path.exists():
            continue
        index = load_json(index_path)
        revision = str(index.get("current_revision", ""))
        revision_dir = episode_dir / "revisions" / revision
        summary_path = revision_dir / "episode_summary.md"
        provenance_path = revision_dir / "provenance.json"
        if not summary_path.exists() or not provenance_path.exists():
            rejected.append(rejection("episode", episode_id, "missing_provenance"))
            continue
        if not in_time_window(episode_id, plan):
            rejected.append(rejection("episode", episode_id, "outside_time_window"))
            continue

        summary = summary_path.read_text(encoding="utf-8").strip()
        provenance = load_json(provenance_path)
        status = str(provenance.get("approval_status", "unknown"))
        score = 0
        reasons: list[str] = []

        for entity in resolved_entities:
            entity_id = entity.get("entity_id")
            if not entity_id or entity_id not in aliases_by_id:
                continue
            registry = aliases_by_id[entity_id]
            exact_names = [entity.get("raw", ""), entity.get("canonical", ""), entity_id]
            alias_names = registry.get("aliases", [])
            if any(name and phrase_match(str(name), summary) for name in exact_names):
                if entity.get("resolution") == "alias":
                    score += 7
                    reasons.append("entity_alias_match")
                else:
                    score += 8
                    reasons.append("exact_entity_match")
            elif any(phrase_match(str(name), summary) for name in alias_names):
                score += 7
                reasons.append("entity_alias_match")

        added, why = text_match_once(phrases, [summary], 4, "episode_content_match")
        score += added
        reasons += why
        relevance_score = score
        if relevance_score == 0:
            rejected.append(rejection("episode", episode_id, "low_relevance"))
            continue
        recent, recent_reason = recency_points(episode_id, plan["episode_date"])
        score += recent
        if recent_reason:
            reasons.append(recent_reason)
        score += 2
        reasons.append("provenance_verified")
        if "## 重要な反対材料" in summary:
            score += 1
            reasons.append("counterevidence_preserved")
        candidates.append(
            Candidate(
                item_type="episode",
                item_id=f"{episode_id}/{revision}",
                path=repo_relative(summary_path, repo_root),
                content=summary,
                score=score,
                reasons=reasons,
                provenance_paths=[repo_relative(provenance_path, repo_root)],
                status=status,
                use_mode="historical_context",
                requires_current_revalidation=True,
                historical_confidence="unknown",
                episode_ids=[episode_id],
                updated_at=episode_id,
                title=f"{episode_id} {revision}",
            )
        )
    return candidates, rejected


LESSON_PATTERN = re.compile(r"^- `([^`]+)` \[([^\]]+)\]: (.+)$")


def collect_lessons(
    repo_root: Path,
    plan: dict[str, Any],
    phrases: list[str],
) -> tuple[list[Candidate], list[dict[str, Any]]]:
    path = repo_root / "editorial-memory" / "production-lessons.md"
    if not path.exists():
        return [], []
    candidates: list[Candidate] = []
    rejected: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = LESSON_PATTERN.match(line.strip())
        if not match:
            continue
        lesson_id, episode_ref, text = match.groups()
        provenance = provenance_for_episode(episode_ref)
        if not provenance or not safe_repo_path(repo_root, provenance).exists():
            rejected.append(rejection("lesson", lesson_id, "missing_provenance"))
            continue
        score, reasons = text_match_once(phrases, [text], 5, "lesson_content_match")
        if score == 0:
            rejected.append(rejection("lesson", lesson_id, "low_relevance"))
            continue
        candidates.append(
            Candidate(
                item_type="lesson",
                item_id=lesson_id,
                path="editorial-memory/production-lessons.md",
                content=f"- {text}",
                score=score + 2,
                reasons=[*reasons, "provenance_verified"],
                provenance_paths=[provenance],
                status="active",
                use_mode="procedural",
                requires_current_revalidation=False,
                episode_ids=[episode_ref.split("/")[0]],
                updated_at=episode_ref.split("/")[0],
                title=lesson_id,
            )
        )
    return candidates, rejected


def core_candidates(repo_root: Path) -> list[Candidate]:
    result: list[Candidate] = []
    paths = [
        ("active-context", "editorial-memory/active_context.md"),
        ("fox-editorial-state", "editorial-memory/core/fox_editorial_state.md"),
    ]
    for item_id, relative in paths:
        path = safe_repo_path(repo_root, relative)
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8").strip()
        result.append(
            Candidate(
                item_type="core",
                item_id=item_id,
                path=relative,
                content=content,
                score=100,
                reasons=["core_memory_always_attached"],
                provenance_paths=[relative],
                status="read_only",
                use_mode="procedural",
                requires_current_revalidation=False,
                title=item_id,
            )
        )
    return result


def candidate_block(candidate: Candidate) -> str:
    caution = {
        "current_revalidation_required": "現在利用には当日の一次情報で再検証が必要。",
        "historical_context": "過去時点の編集記録。現在の事実としては使用しない。",
        "procedural": "制作手順・方針として利用。",
    }[candidate.use_mode]
    heading = candidate.title or candidate.item_id
    return (
        f"## {candidate.item_type.upper()}｜{heading}\n\n"
        f"- Memory ID: `{candidate.item_id}`\n"
        f"- Source: `{candidate.path}`\n"
        f"- Status: `{candidate.status}`\n"
        f"- Score: `{candidate.score}`\n"
        f"- Use: {caution}\n"
        f"- Provenance: {', '.join(f'`{path}`' for path in candidate.provenance_paths)}\n\n"
        f"{candidate.content.strip()}\n"
    )


def select_candidates(
    core: list[Candidate],
    candidates: list[Candidate],
    rejected: list[dict[str, Any]],
    limits: dict[str, int],
    header: str,
) -> tuple[str, list[Candidate], list[dict[str, Any]], int]:
    per_type_limit = {
        "thread": int(limits["max_threads"]),
        "claim": int(limits["max_claims"]),
        "episode": int(limits["max_episodes"]),
        "lesson": int(limits["max_lessons"]),
    }
    ordered = sorted(
        candidates,
        key=lambda item: (
            TYPE_ORDER[item.item_type],
            -item.score,
            -(parse_day(item.updated_at).toordinal() if parse_day(item.updated_at) else 0),
            item.item_id,
        ),
    )

    selected_pre_budget: list[Candidate] = []
    counts = {key: 0 for key in per_type_limit}
    duplicate_keys: set[str] = set()
    duplicate_groups_removed = 0
    episode_counts: dict[str, int] = {}

    for candidate in ordered:
        if counts[candidate.item_type] >= per_type_limit[candidate.item_type]:
            rejected.append(rejection(candidate.item_type, candidate.item_id, "count_limit"))
            continue
        if candidate.duplicate_key in duplicate_keys:
            duplicate_groups_removed += 1
            rejected.append(rejection(candidate.item_type, candidate.item_id, "duplicate"))
            continue
        if any(episode_counts.get(episode_id, 0) >= 3 for episode_id in candidate.episode_ids):
            rejected.append(rejection(candidate.item_type, candidate.item_id, "diversity_limit"))
            continue
        selected_pre_budget.append(candidate)
        counts[candidate.item_type] += 1
        duplicate_keys.add(candidate.duplicate_key)
        for episode_id in candidate.episode_ids:
            episode_counts[episode_id] = episode_counts.get(episode_id, 0) + 1

    max_characters = int(limits["max_characters"])
    text = header.rstrip() + "\n"
    selected: list[Candidate] = []

    for candidate in [*core, *selected_pre_budget]:
        block = "\n" + candidate_block(candidate)
        if len(text) + len(block) <= max_characters:
            text += block
            selected.append(candidate)
            continue
        if candidate.item_type == "core":
            remaining = max_characters - len(text)
            if remaining > 160:
                shortened = block[: remaining - 40].rstrip() + "\n\n[core memory truncated]\n"
                text += shortened
                selected.append(candidate)
            continue
        rejected.append(rejection(candidate.item_type, candidate.item_id, "character_limit"))

    return text.rstrip() + "\n", selected, rejected, duplicate_groups_removed


def retrieve(
    query_plan_path: Path,
    context_output: Path,
    report_output: Path,
    *,
    repo_root: Path = DEFAULT_ROOT,
    contracts_dir: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    contracts_dir = contracts_dir or (repo_root / "skills" / "nasdaq-cafe-editorial-memory" / "contracts")
    query_plan_path = query_plan_path if query_plan_path.is_absolute() else repo_root / query_plan_path
    context_output = context_output if context_output.is_absolute() else repo_root / context_output
    report_output = report_output if report_output.is_absolute() else repo_root / report_output

    plan = load_json(query_plan_path)
    validate_document(plan, contracts_dir / "memory_query_plan.schema.json")

    alias_doc = load_json(
        repo_root / "editorial-memory" / "entity_aliases.json",
        {"contract_version": "1.0.0", "entities": []},
    )
    alias_to_id, aliases_by_id = build_alias_maps(alias_doc)
    resolved_entities, warnings = resolve_entities(plan, alias_to_id, aliases_by_id)
    phrases = query_phrases({**plan, "entities": resolved_entities})

    threads, rejected_threads = collect_threads(repo_root, plan, resolved_entities, alias_to_id, phrases)
    relevant_thread_ids = {candidate.item_id for candidate in threads}
    claims, rejected_claims = collect_claims(
        repo_root, plan, resolved_entities, alias_to_id, phrases, relevant_thread_ids
    )
    episodes, rejected_episodes = collect_episodes(
        repo_root, plan, resolved_entities, aliases_by_id, phrases
    )
    lessons, rejected_lessons = collect_lessons(repo_root, plan, phrases)

    rejected = [*rejected_threads, *rejected_claims, *rejected_episodes, *rejected_lessons]
    header = "\n".join(
        [
            "# 朝のNASDAQカフェ｜Selected Editorial Memory",
            "",
            f"Episode date: `{plan['episode_date']}`",
            f"Lead candidates: {', '.join(plan['lead_candidates'])}",
            f"Topics: {', '.join(plan['topics']) or '未指定'}",
            "Resolved entities: "
            + (
                ", ".join(
                    f"{item['raw']}→{item['entity_id'] or 'unresolved'}({item['resolution']})"
                    for item in resolved_entities
                )
                or "未指定"
            ),
            "",
            "> 過去の編集記録であり、現在の事実を証明しません。台本へ使う前に当日の一次情報と市場データで再検証してください。",
            "",
        ]
    )
    context, selected, rejected, duplicate_removed = select_candidates(
        core_candidates(repo_root),
        [*threads, *claims, *episodes, *lessons],
        rejected,
        plan["limits"],
        header,
    )
    context_output.parent.mkdir(parents=True, exist_ok=True)
    context_output.write_text(context, encoding="utf-8")

    non_core = [item for item in selected if item.item_type != "core"]
    if not non_core:
        warnings.append("no relevant durable memory selected")
    usage = {
        "threads": sum(item.item_type == "thread" for item in selected),
        "claims": sum(item.item_type == "claim" for item in selected),
        "episodes": sum(item.item_type == "episode" for item in selected),
        "lessons": sum(item.item_type == "lesson" for item in selected),
        "characters": len(context),
    }
    report = {
        "contract_version": "1.0.0",
        "episode_date": plan["episode_date"],
        "query_plan_path": repo_relative(query_plan_path, repo_root),
        "selected": [item.report_item() for item in selected],
        "rejected": sorted(
            rejected,
            key=lambda item: (TYPE_ORDER.get(item["item_type"], 99), item["item_id"], item["reason"]),
        ),
        "limits": plan["limits"],
        "usage": usage,
        "diversity": {
            "distinct_episode_ids": sorted(
                {episode_id for item in selected for episode_id in item.episode_ids}
            ),
            "distinct_thread_ids": sorted(
                {thread_id for item in selected for thread_id in item.thread_ids}
            ),
            "duplicate_groups_removed": duplicate_removed,
        },
        "warnings": sorted(set(warnings)),
    }
    validate_document(report, contracts_dir / "memory_retrieval_report.schema.json")
    write_json(report_output, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query-plan", type=Path, required=True)
    parser.add_argument("--context-output", type=Path)
    parser.add_argument("--report-output", type=Path)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    plan_path = args.query_plan if args.query_plan.is_absolute() else args.repo_root / args.query_plan
    plan = load_json(plan_path)
    episode_date = plan["episode_date"]
    context_output = args.context_output or Path(f"working/memory_context_{episode_date}.md")
    report_output = args.report_output or Path(f"working/memory_retrieval_report_{episode_date}.json")
    report = retrieve(
        args.query_plan,
        context_output,
        report_output,
        repo_root=args.repo_root,
    )
    print(f"WROTE_CONTEXT {context_output}")
    print(f"WROTE_REPORT {report_output}")
    print(f"SELECTED {len(report['selected'])}")
    print(f"REJECTED {len(report['rejected'])}")
    print(f"CHARACTERS {report['usage']['characters']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
