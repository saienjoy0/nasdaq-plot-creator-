#!/usr/bin/env python3
"""Validate Story Engine sidecars against frozen ChatGPT production semantics.

Historical versions of this entry point projected Story Script narration, visual-copy
bindings, review metadata, and reaction bindings back into ``render_spec.json`` and the
public episode package. That made the Story Engine a second semantic writer after
ChatGPT authoring.

Production now treats Story Engine output as a validation-only sidecar. The authoritative
meaning is the assembled ``daily-authoring/<date>.json`` already materialized into the
producer RenderSpec and public episode package. This gate verifies identity and writes
only a report. It never changes narration, telops, Scene order, Visual Candidates,
assets, sources, causal wording, Primary/Fallback selection, or reaction bindings.

Two legacy helper APIs remain for read-only diagnostics: ``segment`` and
``apply_visual_overrides``. They operate only on caller-owned in-memory values and are
not called by this module's production ``main``. Existing Pre-TTS validation uses them
on a deep copy so historical compatibility checks can still reason about old bindings
without restoring any production writeback authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SENTENCE_RE = re.compile(r".*?(?:[。！？!?](?:[」』】）)]*)|$)")


class StoryProjectionIdentityError(ValueError):
    pass


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StoryProjectionIdentityError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise StoryProjectionIdentityError(f"{label} root must be an object")
    return value


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text)


def sentences(text: str) -> list[str]:
    """Compatibility helper for read-only historical diagnostics."""
    out = [match.group(0) for match in SENTENCE_RE.finditer(text) if match.group(0)]
    return out or [text]


def segment(text: str, count: int) -> list[str]:
    """Split text deterministically without changing bytes when rejoined.

    This helper is retained only for diagnostic/test compatibility. Production Story
    validation never re-segments frozen ChatGPT narration.
    """
    if count <= 0:
        raise ValueError("chunk count must be positive")
    if count == 1:
        return [text]
    parts = sentences(text)
    if len(parts) < count:
        joined = "".join(parts)
        cuts = [round(len(joined) * i / count) for i in range(count + 1)]
        return [joined[cuts[i]:cuts[i + 1]] for i in range(count)]
    target = len(text) / count
    result: list[str] = []
    current = ""
    remaining_groups = count
    for index, part in enumerate(parts):
        remaining_parts = len(parts) - index
        if current and len(result) < count - 1 and (
            len(current) >= target or remaining_parts == remaining_groups - 1
        ):
            result.append(current)
            current = ""
            remaining_groups -= 1
        current += part
    result.append(current)
    while len(result) < count:
        result.append("")
    if len(result) > count:
        result[count - 1] = "".join(result[count - 1:])
        result = result[:count]
    if "".join(result) != text:
        raise ValueError("narration segmentation changed authored text")
    return result


def apply_visual_overrides(render: dict[str, Any], bindings: dict[str, Any]) -> None:
    """Apply historical Story overrides to an in-memory diagnostic copy only.

    The production ``main`` never calls this helper. It exists because Pre-TTS legacy
    compatibility checks intentionally deep-copy a historical RenderSpec and ask what
    those historical bindings *would* have produced. New production is forbidden from
    carrying non-empty Story overrides after semantic freeze.
    """
    scene_map = {
        scene["sceneId"]: scene
        for scene in render.get("scenes", [])
        if isinstance(scene, dict) and isinstance(scene.get("sceneId"), str)
    }
    for scene_id, override in bindings.get("scene_overrides", {}).items():
        scene = scene_map.get(scene_id)
        if scene is None:
            raise ValueError(f"unknown scene override: {scene_id}")
        if not isinstance(override, dict):
            raise ValueError(f"invalid scene override: {scene_id}")
        for key in ("headline", "supportingTexts", "purpose", "performanceIntent"):
            if key in override:
                scene[key] = override[key]

    beat_map = {
        beat["beatId"]: beat
        for scene in render.get("scenes", [])
        if isinstance(scene, dict)
        for beat in scene.get("visualBeats", [])
        if isinstance(beat, dict) and isinstance(beat.get("beatId"), str)
    }
    for beat_id, override in bindings.get("beat_overrides", {}).items():
        beat = beat_map.get(beat_id)
        if beat is None:
            raise ValueError(f"unknown beat override: {beat_id}")
        if not isinstance(override, dict):
            raise ValueError(f"invalid beat override: {beat_id}")
        for key in (
            "screenQuestion",
            "primaryElement",
            "viewerTexts",
            "changeCue",
            "contentType",
            "visualTemplate",
            "visualMode",
            "screenState",
        ):
            if key in override:
                beat[key] = override[key]
        if "templateVariant" in override:
            config = beat.get("templateConfig")
            if not isinstance(config, dict):
                raise ValueError(f"{beat_id}: templateConfig required for templateVariant")
            config["variant"] = override["templateVariant"]
            beat["templateVariant"] = override["templateVariant"]
        if "visualGrammarId" in override or "transitionRole" in override:
            grammar = beat.get("visualGrammar")
            if not isinstance(grammar, dict):
                raise ValueError(f"{beat_id}: visualGrammar required for grammar override")
            if "visualGrammarId" in override:
                grammar["grammarId"] = override["visualGrammarId"]
            if "transitionRole" in override:
                grammar["transitionRole"] = override["transitionRole"]


def _repo_root_from_render(render_path: Path) -> Path:
    resolved = render_path.resolve()
    # <root>/render-specs/<date>/render_spec.json
    if len(resolved.parents) < 3 or resolved.parents[1].name != "render-specs":
        raise StoryProjectionIdentityError(
            "render spec must be <repo>/render-specs/<date>/render_spec.json"
        )
    return resolved.parents[2]


def _episode_date(script: dict[str, Any], render: dict[str, Any]) -> str:
    date = script.get("episode_date")
    if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise StoryProjectionIdentityError("story script episode_date is invalid")
    if render.get("episode", {}).get("targetDate") != date:
        raise StoryProjectionIdentityError("render/story episode date mismatch")
    return date


def _authored_scene_narration(scene: dict[str, Any], scene_id: str) -> str:
    chunks = scene.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise StoryProjectionIdentityError(f"{scene_id}: authored chunks missing")
    texts: list[str] = []
    for index, chunk in enumerate(chunks, 1):
        if not isinstance(chunk, dict) or not isinstance(chunk.get("text"), str):
            raise StoryProjectionIdentityError(
                f"{scene_id}: invalid authored chunk {index}"
            )
        texts.append(chunk["text"])
    return "".join(texts)


def _public_scene_narration(md: str, scene_number: int) -> str:
    pattern = re.compile(
        rf"(?ms)^##\s+(?:B{scene_number}\.\s+)?Scene\s+{scene_number}(?:｜|\|).*?"
        rf"^### 完成ナレーション\s*\n(.*?)"
        rf"(?=\n- ナレーションで示す出典主体・媒体：|\n- 根拠と不確実性：)"
    )
    match = pattern.search(md)
    if not match:
        raise StoryProjectionIdentityError(
            f"episode package Scene {scene_number} 完成ナレーション block not found"
        )
    return match.group(1).strip()


def _require_no_post_freeze_overrides(bindings: dict[str, Any], date: str) -> None:
    if bindings.get("contract_version") != "1.0.0" or bindings.get("episode_date") != date:
        raise StoryProjectionIdentityError("story production bindings contract/date mismatch")
    scene_overrides = bindings.get("scene_overrides", {})
    beat_overrides = bindings.get("beat_overrides", {})
    if scene_overrides not in ({}, None):
        raise StoryProjectionIdentityError(
            "E_STORY_SEMANTIC_WRITER_FORBIDDEN: scene_overrides must be authored upstream before semantic freeze"
        )
    if beat_overrides not in ({}, None):
        raise StoryProjectionIdentityError(
            "E_STORY_SEMANTIC_WRITER_FORBIDDEN: beat_overrides must be authored upstream before semantic freeze"
        )


def _validate_plan_identity(
    plan: dict[str, Any], authoring: dict[str, Any], date: str
) -> None:
    if plan.get("episode_date") != date:
        raise StoryProjectionIdentityError("story plan episode_date mismatch")
    editorial = authoring.get("editorial")
    if not isinstance(editorial, dict):
        raise StoryProjectionIdentityError("daily authoring editorial missing")
    comparisons = {
        "central_contradiction": authoring.get("centralContradiction"),
        "headline_beyond_discovery": authoring.get("headlineBeyondDiscovery"),
        "selected_angle_id": authoring.get("selectedAngleId"),
        "central_question": authoring.get("centralQuestion"),
        "story_spine": editorial.get("storySpine"),
        "opening_promise": authoring.get("openingPromise"),
        "midpoint_turn": authoring.get("midpointTurn"),
        "closing_reframe": authoring.get("closingReframe"),
    }
    for key, expected in comparisons.items():
        if plan.get(key) != expected:
            raise StoryProjectionIdentityError(
                f"E_STORY_SEMANTIC_DRIFT: story plan {key} differs from frozen ChatGPT authoring"
            )

    authored_scenes = authoring.get("scenes")
    plan_scenes = plan.get("scenes")
    if not isinstance(authored_scenes, list) or len(authored_scenes) != 9:
        raise StoryProjectionIdentityError("daily authoring must contain nine Scenes")
    if not isinstance(plan_scenes, list) or len(plan_scenes) != 9:
        raise StoryProjectionIdentityError("story plan must contain nine Scenes")
    for index, (authored, planned) in enumerate(
        zip(authored_scenes, plan_scenes, strict=True), 1
    ):
        if not isinstance(authored, dict) or not isinstance(planned, dict):
            raise StoryProjectionIdentityError(f"scene-{index:02d}: invalid plan/authoring Scene")
        expected = {
            "scene_id": f"scene-{index:02d}",
            "new_evidence_ids": authored.get("newEvidenceIds", []),
            "new_meaning": authored.get("newMeaning", ""),
            "continuation_reason": authored.get("continuationReason", ""),
            "connector": authored.get("connector", "therefore"),
        }
        for key, value in expected.items():
            if planned.get(key) != value:
                raise StoryProjectionIdentityError(
                    f"E_STORY_SEMANTIC_DRIFT: scene-{index:02d} plan {key} differs from frozen ChatGPT authoring"
                )


def _validate_script_identity(
    script: dict[str, Any],
    authoring: dict[str, Any],
    render: dict[str, Any],
    md: str,
    date: str,
) -> None:
    authored_scenes = authoring.get("scenes")
    script_scenes = script.get("scenes")
    render_scenes = render.get("scenes")
    if not isinstance(authored_scenes, list) or len(authored_scenes) != 9:
        raise StoryProjectionIdentityError("daily authoring must contain nine Scenes")
    if not isinstance(script_scenes, list) or len(script_scenes) != 9:
        raise StoryProjectionIdentityError("story script must contain nine Scenes")
    if not isinstance(render_scenes, list) or len(render_scenes) != 9:
        raise StoryProjectionIdentityError("render spec must contain nine Scenes")

    for index, (authored, scripted, rendered) in enumerate(
        zip(authored_scenes, script_scenes, render_scenes, strict=True), 1
    ):
        scene_id = f"scene-{index:02d}"
        if not all(isinstance(item, dict) for item in (authored, scripted, rendered)):
            raise StoryProjectionIdentityError(f"{scene_id}: invalid Scene object")
        if scripted.get("scene_id") != scene_id or rendered.get("sceneId") != scene_id:
            raise StoryProjectionIdentityError(f"{scene_id}: Scene identity mismatch")

        authoritative = _authored_scene_narration(authored, scene_id)
        story_narration = scripted.get("narration")
        if not isinstance(story_narration, str) or normalize(story_narration) != normalize(authoritative):
            raise StoryProjectionIdentityError(
                f"E_STORY_SEMANTIC_DRIFT: {scene_id} Story Script narration differs from frozen ChatGPT authoring"
            )

        if scripted.get("connection_to_previous") != authored.get("connector", "therefore"):
            raise StoryProjectionIdentityError(
                f"E_STORY_SEMANTIC_DRIFT: {scene_id} connector differs from frozen ChatGPT authoring"
            )
        if scripted.get("evidence_ids", []) != authored.get("newEvidenceIds", []):
            raise StoryProjectionIdentityError(
                f"E_STORY_SEMANTIC_DRIFT: {scene_id} evidence IDs differ from frozen ChatGPT authoring"
            )
        if scripted.get("causal_claims", []) != authored.get("causalClaims", []):
            raise StoryProjectionIdentityError(
                f"E_STORY_SEMANTIC_DRIFT: {scene_id} causal claims differ from frozen ChatGPT authoring"
            )

        chunks = rendered.get("narrationChunks")
        if not isinstance(chunks, list) or not chunks:
            raise StoryProjectionIdentityError(f"{scene_id}: render narrationChunks missing")
        render_narration = "".join(
            str(chunk.get("speechText", "")) for chunk in chunks if isinstance(chunk, dict)
        )
        if normalize(render_narration) != normalize(authoritative):
            raise StoryProjectionIdentityError(
                f"E_STORY_SEMANTIC_DRIFT: {scene_id} render narration differs from frozen ChatGPT authoring"
            )

        public_narration = _public_scene_narration(md, index)
        if normalize(public_narration) != normalize(authoritative):
            raise StoryProjectionIdentityError(
                f"E_STORY_SEMANTIC_DRIFT: {scene_id} public narration differs from frozen ChatGPT authoring"
            )

        chunk_by_id = {
            chunk.get("chunkId"): chunk.get("speechText", "")
            for chunk in chunks
            if isinstance(chunk, dict) and isinstance(chunk.get("chunkId"), str)
        }
        for beat in rendered.get("visualBeats", []):
            if not isinstance(beat, dict):
                raise StoryProjectionIdentityError(f"{scene_id}: invalid Visual Beat")
            start_text = chunk_by_id.get(beat.get("startChunkId"))
            end_text = chunk_by_id.get(beat.get("endChunkId"))
            if not isinstance(start_text, str) or not isinstance(end_text, str):
                raise StoryProjectionIdentityError(
                    f"{beat.get('beatId', scene_id)}: narration chunk reference missing"
                )
            start_cue = beat.get("narrationStartCue")
            end_cue = beat.get("narrationEndCue")
            if not isinstance(start_cue, str) or not normalize(start_text).startswith(normalize(start_cue)):
                raise StoryProjectionIdentityError(
                    f"{beat.get('beatId', scene_id)}: narrationStartCue is stale"
                )
            if not isinstance(end_cue, str) or not normalize(end_text).endswith(normalize(end_cue)):
                raise StoryProjectionIdentityError(
                    f"{beat.get('beatId', scene_id)}: narrationEndCue is stale"
                )

    if script.get("retained_counterevidence_ids", []) != authoring.get(
        "retainedCounterevidenceIds", []
    ):
        raise StoryProjectionIdentityError(
            "E_STORY_SEMANTIC_DRIFT: retained counterevidence differs from frozen ChatGPT authoring"
        )
    if script.get("unresolved_points", []) != authoring.get("unresolvedPoints", []):
        raise StoryProjectionIdentityError(
            "E_STORY_SEMANTIC_DRIFT: unresolved points differ from frozen ChatGPT authoring"
        )


def validate_read_only(
    *,
    story_script_path: Path,
    creative_review_path: Path,
    render_spec_path: Path,
    episode_package_public_path: Path,
    bindings_path: Path,
) -> dict[str, Any]:
    before = {
        "render_spec": sha(render_spec_path),
        "episode_package_public": sha(episode_package_public_path),
    }
    script = load_json(story_script_path, "story script")
    review = load_json(creative_review_path, "creative review")
    render = load_json(render_spec_path, "render spec")
    bindings = load_json(bindings_path, "story production bindings")
    md = episode_package_public_path.read_text(encoding="utf-8")
    date = _episode_date(script, render)
    root = _repo_root_from_render(render_spec_path)
    authoring_path = root / "daily-authoring" / f"{date}.json"
    story_plan_path = story_script_path.parent / "story_plan.json"
    authoring = load_json(authoring_path, "daily authoring")
    plan = load_json(story_plan_path, "story plan")

    if authoring.get("episodeDate") != date:
        raise StoryProjectionIdentityError("daily authoring episodeDate mismatch")
    if review.get("verdict") != "pass":
        raise StoryProjectionIdentityError("Story Engine review must be PASS")
    _require_no_post_freeze_overrides(bindings, date)
    _validate_plan_identity(plan, authoring, date)
    _validate_script_identity(script, authoring, render, md, date)

    after = {
        "render_spec": sha(render_spec_path),
        "episode_package_public": sha(episode_package_public_path),
    }
    if after != before:
        raise StoryProjectionIdentityError(
            "E_STORY_SEMANTIC_WRITER_FORBIDDEN: read-only Story gate changed production inputs"
        )
    return {
        "contract_version": "2.0.0",
        "episode_date": date,
        "status": "pass",
        "mode": "read-only-semantic-identity",
        "authority": "chatgpt-daily-authoring",
        "story_engine_role": "validation-only",
        "semantic_writer": False,
        "source_story_plan_sha256": sha(story_plan_path),
        "source_story_script_sha256": sha(story_script_path),
        "source_creative_review_sha256": sha(creative_review_path),
        "source_daily_authoring_sha256": sha(authoring_path),
        "before": before,
        "after": after,
        "scene_count": 9,
        "visual_override_count": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--story-script", type=Path, required=True)
    ap.add_argument("--creative-review", type=Path, required=True)
    ap.add_argument("--render-spec", type=Path, required=True)
    ap.add_argument("--episode-package-public", type=Path, required=True)
    ap.add_argument("--bindings", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    try:
        report = validate_read_only(
            story_script_path=args.story_script,
            creative_review_path=args.creative_review,
            render_spec_path=args.render_spec,
            episode_package_public_path=args.episode_package_public,
            bindings_path=args.bindings,
        )
        code = 0
    except (OSError, json.JSONDecodeError, StoryProjectionIdentityError) as exc:
        report = {
            "contract_version": "2.0.0",
            "status": "fail",
            "mode": "read-only-semantic-identity",
            "semantic_writer": False,
            "errors": [str(exc)],
        }
        code = 2
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(canonical(report), encoding="utf-8")
    print(canonical(report), end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
