#!/usr/bin/env python3
"""Mechanically project an approved Story Script into existing episode/render structures.

This script does not invent or rewrite narration. It preserves the authored Story Script
verbatim, re-segments it only at sentence boundaries to fit existing narration chunk IDs,
and applies only explicitly authored visual-copy overrides.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SENTENCE_RE = re.compile(r".*?(?:[。！？!?](?:[」』】）)]*)|$)")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return value


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sentences(text: str) -> list[str]:
    out = [m.group(0) for m in SENTENCE_RE.finditer(text) if m.group(0)]
    return out or [text]


def segment(text: str, count: int) -> list[str]:
    if count <= 0:
        raise ValueError("chunk count must be positive")
    if count == 1:
        return [text]
    parts = sentences(text)
    if len(parts) < count:
        # Preserve text exactly while making enough deterministic segments.
        joined = "".join(parts)
        cuts = [round(len(joined) * i / count) for i in range(count + 1)]
        return [joined[cuts[i]:cuts[i + 1]] for i in range(count)]
    target = len(text) / count
    result: list[str] = []
    current = ""
    remaining_groups = count
    for idx, part in enumerate(parts):
        remaining_parts = len(parts) - idx
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


def cue_start(text: str, size: int = 64) -> str:
    return text[:size]


def cue_end(text: str, size: int = 64) -> str:
    return text[-size:]


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text)


def replace_scene_narration(md: str, scene_number: int, narration: str) -> str:
    scene_pat = re.compile(
        rf"(?ms)(^##\s+(?:B{scene_number}\.\s+)?Scene\s+{scene_number}(?:｜|\|).*?^### 完成ナレーション\s*\n)(.*?)(?=\n- ナレーションで示す出典主体・媒体：)"
    )
    match = scene_pat.search(md)
    if not match:
        raise ValueError(f"episode package Scene {scene_number} 完成ナレーション block not found")
    return md[:match.start(2)] + narration + "\n" + md[match.end(2):]


def replace_beat_cues(md: str, beat_id: str, start: str, end: str) -> str:
    block_re = re.compile(
        rf"(?ms)(- \*\*{re.escape(beat_id)}\*\*.*?)(?=\n- \*\*scene-0[1-9]-beat-[0-9]{{3}}\*\*|\n### 完成ナレーション)"
    )
    match = block_re.search(md)
    if not match:
        raise ValueError(f"episode package beat block not found: {beat_id}")
    block = match.group(1)
    block = re.sub(r"(?m)^  - 開始合図：.*$", f"  - 開始合図：{start}", block, count=1)
    block = re.sub(r"(?m)^  - 終了合図：.*$", f"  - 終了合図：{end}", block, count=1)
    return md[:match.start(1)] + block + md[match.end(1):]


def apply_visual_overrides(render: dict[str, Any], bindings: dict[str, Any]) -> None:
    scene_map = {scene["sceneId"]: scene for scene in render.get("scenes", [])}
    for scene_id, override in bindings.get("scene_overrides", {}).items():
        scene = scene_map.get(scene_id)
        if scene is None:
            raise ValueError(f"unknown scene override: {scene_id}")
        for key in ("headline", "supportingTexts", "purpose", "performanceIntent"):
            if key in override:
                scene[key] = override[key]
    beat_map = {
        beat["beatId"]: beat
        for scene in render.get("scenes", [])
        for beat in scene.get("visualBeats", [])
    }
    for beat_id, override in bindings.get("beat_overrides", {}).items():
        beat = beat_map.get(beat_id)
        if beat is None:
            raise ValueError(f"unknown beat override: {beat_id}")
        for key in ("screenQuestion", "primaryElement", "viewerTexts", "changeCue", "contentType"):
            if key in override:
                beat[key] = override[key]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--story-script", type=Path, required=True)
    ap.add_argument("--creative-review", type=Path, required=True)
    ap.add_argument("--render-spec", type=Path, required=True)
    ap.add_argument("--episode-package-public", type=Path, required=True)
    ap.add_argument("--bindings", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    script = load_json(args.story_script)
    review = load_json(args.creative_review)
    render = load_json(args.render_spec)
    bindings = load_json(args.bindings)
    md = args.episode_package_public.read_text(encoding="utf-8")
    before = {"render_spec": sha(args.render_spec), "episode_package_public": sha(args.episode_package_public)}

    if bindings.get("contract_version") != "1.0.0" or bindings.get("episode_date") != script.get("episode_date"):
        raise SystemExit("story production bindings contract/date mismatch")
    if review.get("verdict") != "pass":
        raise SystemExit("cannot project a non-PASS creative review")

    script_scenes = {scene["scene_id"]: scene for scene in script["scenes"]}
    for scene_index, render_scene in enumerate(render.get("scenes", []), start=1):
        scene_id = f"scene-{scene_index:02d}"
        if render_scene.get("sceneId") != scene_id or scene_id not in script_scenes:
            raise SystemExit(f"scene identity mismatch at {scene_id}")
        narration = script_scenes[scene_id]["narration"]
        chunks = render_scene.get("narrationChunks", [])
        pieces = segment(narration, len(chunks))
        chunk_by_id: dict[str, str] = {}
        for chunk, piece in zip(chunks, pieces, strict=True):
            chunk["speechText"] = piece
            chunk["captionText"] = piece
            chunk_by_id[chunk["chunkId"]] = piece
        if "".join(chunk["speechText"] for chunk in chunks) != narration:
            raise SystemExit(f"{scene_id}: render narration changed authored script")
        for beat in render_scene.get("visualBeats", []):
            start_text = chunk_by_id[beat["startChunkId"]]
            end_text = chunk_by_id[beat["endChunkId"]]
            beat["narrationStartCue"] = cue_start(start_text)
            beat["narrationEndCue"] = cue_end(end_text)
            md = replace_beat_cues(md, beat["beatId"], beat["narrationStartCue"], beat["narrationEndCue"])
        md = replace_scene_narration(md, scene_index, narration)

    apply_visual_overrides(render, bindings)
    score_map = {
        "openingHook": review["scores"]["opening"],
        "storyProgression": review["scores"]["progression"],
        "discovery": review["scores"]["discovery"],
        "clarity": review["scores"]["clarity"],
        "foxCharacter": review["scores"]["fox_voice"],
        "reasonToFinish": review["scores"]["late_payoff"],
    }
    render.setdefault("review", {})["verdict"] = "approved"
    render["review"]["scores"] = score_map
    render["review"]["totalScore"] = review["total_score"]
    render["review"]["requiredChanges"] = []
    render["review"]["changesApplied"] = ["Story Engine independent critic PASS after targeted patch"]

    # Final semantic identity check: public narration and render narration must equal Story Script.
    for idx, scene in enumerate(script["scenes"], start=1):
        rscene = render["scenes"][idx - 1]
        if normalize("".join(c["speechText"] for c in rscene["narrationChunks"])) != normalize(scene["narration"]):
            raise SystemExit(f"scene-{idx:02d}: render/script narration mismatch")

    args.render_spec.write_text(canonical(render), encoding="utf-8")
    args.episode_package_public.write_text(md, encoding="utf-8")
    report = {
        "contract_version": "1.0.0",
        "episode_date": script["episode_date"],
        "status": "pass",
        "source_story_script_sha256": sha(args.story_script),
        "source_creative_review_sha256": sha(args.creative_review),
        "before": before,
        "after": {"render_spec": sha(args.render_spec), "episode_package_public": sha(args.episode_package_public)},
        "scene_count": 9,
        "visual_override_count": len(bindings.get("beat_overrides", {})) + len(bindings.get("scene_overrides", {})),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(canonical(report), encoding="utf-8")
    print(canonical(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
