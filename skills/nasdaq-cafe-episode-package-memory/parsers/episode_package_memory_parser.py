#!/usr/bin/env python3
"""Deterministic parser for the episode-package memory annex and MEMREF markers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

ANNEX_BEGIN = "<!--BEGIN_EPISODE_MEMORY_ANNEX-->"
ANNEX_END = "<!--END_EPISODE_MEMORY_ANNEX-->"
MARKER_RE = re.compile(r"<!--MEMREF:(MR-[0-9]{3}):(U-[0-9]{3})-->")
SCENE_HEADING_RE = re.compile(r"(?im)^#{2,4}\s*(?:B\.\s*)?(?:Scene|SCENE)[\s\-]*(0?[1-9])(?:\b|｜|\|)")
H2_RE = re.compile(r"(?m)^##\s+(.+?)\s*$")
H3_RE = re.compile(r"(?m)^###\s+(.+?)\s*$")
JSON_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


@dataclass(frozen=True)
class MarkerLocation:
    marker: str
    reference_id: str
    usage_id: str
    start: int
    end: int
    scene_id: str | None
    surface: str | None


@dataclass
class ParsedEpisodePackage:
    public_text: str
    annex: dict[str, Any]
    markers: list[MarkerLocation]
    annex_start: int
    annex_end: int


class EpisodePackageParseError(ValueError):
    pass


def _surface_from_heading(heading: str) -> str | None:
    normalized = heading.strip().lower()
    if "ナレーション" in heading and "出典" not in heading:
        return "scene_narration"
    if "接続文" in heading:
        return "scene_connection"
    if "大テロップ" in heading:
        return "main_telop"
    if "補助テロップ" in heading:
        return "support_telop"
    if "画面で伝える" in heading or "画面内容" in heading or "visual text" in normalized:
        return "visual_text"
    return None


def _global_surface_from_h2(heading: str) -> str | None:
    lowered = heading.lower()
    if "タイトル" in heading:
        return "title"
    if "サムネイル" in heading:
        return "thumbnail"
    if "概要欄" in heading or "description" in lowered:
        return "description"
    return None


def _preceding(matches: list[re.Match[str]], position: int) -> re.Match[str] | None:
    result = None
    for match in matches:
        if match.start() >= position:
            break
        result = match
    return result


def locate_marker(markdown: str, match: re.Match[str]) -> MarkerLocation:
    scene_matches = list(SCENE_HEADING_RE.finditer(markdown))
    h2_matches = list(H2_RE.finditer(markdown))
    h3_matches = list(H3_RE.finditer(markdown))
    scene_match = _preceding(scene_matches, match.start())
    h2_match = _preceding(h2_matches, match.start())
    h3_match = _preceding(h3_matches, match.start())
    scene_id = None
    surface = None
    if h2_match:
        global_surface = _global_surface_from_h2(h2_match.group(1))
        if global_surface and (not scene_match or scene_match.start() < h2_match.start()):
            surface = global_surface
    if surface is None and scene_match:
        scene_id = f"SCENE-{int(scene_match.group(1)):02d}"
        if h3_match and h3_match.start() > scene_match.start():
            surface = _surface_from_heading(h3_match.group(1))
        if surface is None:
            surface = "scene_narration"
    return MarkerLocation(match.group(0), match.group(1), match.group(2), match.start(), match.end(), scene_id, surface)


def parse_episode_package(markdown: str) -> ParsedEpisodePackage:
    begin_count = markdown.count(ANNEX_BEGIN)
    end_count = markdown.count(ANNEX_END)
    if begin_count != 1 or end_count != 1:
        raise EpisodePackageParseError(f"episode memory annex markers must appear exactly once: begin={begin_count} end={end_count}")
    annex_start = markdown.index(ANNEX_BEGIN)
    annex_end_marker = markdown.index(ANNEX_END)
    if annex_end_marker <= annex_start:
        raise EpisodePackageParseError("episode memory annex end marker appears before begin marker")
    annex_end = annex_end_marker + len(ANNEX_END)
    annex_block = markdown[annex_start:annex_end]
    fences = list(JSON_FENCE_RE.finditer(annex_block))
    if len(fences) != 1:
        raise EpisodePackageParseError(f"episode memory annex must contain exactly one JSON fence: found={len(fences)}")
    try:
        annex = json.loads(fences[0].group(1))
    except json.JSONDecodeError as exc:
        raise EpisodePackageParseError(f"invalid episode memory annex JSON: {exc}") from exc
    if not isinstance(annex, dict):
        raise EpisodePackageParseError("episode memory annex JSON must be an object")
    public_text = markdown[:annex_start] + markdown[annex_end:]
    markers = [locate_marker(public_text, match) for match in MARKER_RE.finditer(public_text)]
    return ParsedEpisodePackage(public_text, annex, markers, annex_start, annex_end)
