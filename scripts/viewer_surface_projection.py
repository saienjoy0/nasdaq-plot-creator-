#!/usr/bin/env python3
"""Project approved NASDAQ Cafe authoring into viewer-facing display text.

This module never changes speech meaning. It only converts deterministic numeric
surface forms for captions/telops and fails closed when numeric Japanese remains
ambiguous. Speech/TTS text is intentionally kept byte-identical.
"""
from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

KANJI_DIGITS = {"〇": 0, "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
SMALL_UNITS = {"十": 10, "百": 100, "千": 1000}
BIG_UNITS = {"万": 10_000, "億": 100_000_000, "兆": 1_000_000_000_000}
NUM_CHARS = "〇零一二三四五六七八九十百千万億兆"
KANJI_DIGIT_CHARS = "〇零一二三四五六七八九"
COEFF_CHARS = "〇零一二三四五六七八九十百千"
NUM_TOKEN = rf"[{NUM_CHARS}]+(?:・[{NUM_CHARS}]+)?"
COEFF_TOKEN = rf"[{COEFF_CHARS}]+(?:・[{KANJI_DIGIT_CHARS}]+)?"
PERCENT_RE = re.compile(rf"({NUM_TOKEN})パーセント")
TIME_RE = re.compile(rf"({NUM_TOKEN})時({NUM_TOKEN})分")
PREFIX_RE = re.compile(rf"第({NUM_TOKEN})")
FINANCIAL_MAGNITUDE_RE = re.compile(rf"({COEFF_TOKEN})(億|万)(ドル|円)")
UNIT_RE = re.compile(
    rf"(?<![0-9,.])({NUM_TOKEN})(ドル|円|分足|番目|年|月|日|回|件|社|人|位|段|つ)"
)
# Bare 分 is lexically ambiguous in Japanese (for example 十分な), so duration
# conversion requires a following duration boundary. 時間 and 秒 share this rule to
# keep the detector and converter intentionally narrow and deterministic.
DURATION_RE = re.compile(
    rf"(?<![0-9,.])({NUM_TOKEN})(時間|分|秒)"
    rf"(?=(?:から|まで|間|前|後|以内|以上|以下|未満|程度|ほど|くらい|ぐらい|ごと|おき|の|で|を|に|、|。|\s|$))"
)
# The middle dot is an explicit decimal marker in the TTS surface. Once unit-specific
# rules have run, convert it regardless of whether Japanese prose follows immediately
# (for example "二万六千...・四五でした"). Boundaries only exclude adjacent numeral
# characters, so ordinary Japanese words such as 一方 / 四半期 remain untouched.
STANDALONE_DECIMAL_RE = re.compile(
    rf"(?<![{NUM_CHARS}])([{NUM_CHARS}]+・[{KANJI_DIGIT_CHARS}]+)(?![{NUM_CHARS}])"
)


class ViewerSurfaceError(ValueError):
    pass


@dataclass(frozen=True)
class Conversion:
    path: str
    before: str
    after: str
    rule_id: str


def _digit_string(token: str) -> str | None:
    if token and all(char in KANJI_DIGITS for char in token):
        return "".join(str(KANJI_DIGITS[char]) for char in token)
    return None


def _integer_value(token: str) -> int:
    direct = _digit_string(token)
    if direct is not None:
        return int(direct or "0")
    total = 0
    section = 0
    current = 0
    for char in token:
        if char in KANJI_DIGITS:
            current = KANJI_DIGITS[char]
        elif char in SMALL_UNITS:
            unit = SMALL_UNITS[char]
            section += (current or 1) * unit
            current = 0
        elif char in BIG_UNITS:
            section += current
            current = 0
            total += (section or 1) * BIG_UNITS[char]
            section = 0
        else:
            raise ViewerSurfaceError(f"unsupported numeric token: {token}")
    return total + section + current


def _format_integer(value: int) -> str:
    return f"{value:,}"


def normalize_numeric_token(token: str) -> str:
    if "・" not in token:
        return _format_integer(_integer_value(token))
    left, right = token.split("・", 1)
    right_digits = _digit_string(right)
    if right_digits is None:
        raise ViewerSurfaceError(f"ambiguous decimal token: {token}")
    return f"{_format_integer(_integer_value(left))}.{right_digits}"


def _apply_regex(text: str, pattern: re.Pattern[str], repl, rule_id: str, path: str,
                 conversions: list[Conversion]) -> str:
    def wrapped(match: re.Match[str]) -> str:
        before = match.group(0)
        after = repl(match)
        if before != after:
            conversions.append(Conversion(path=path, before=before, after=after, rule_id=rule_id))
        return after
    return pattern.sub(wrapped, text)


def normalize_viewer_text(value: str, *, path: str, conversions: list[Conversion]) -> str:
    text = value
    text = _apply_regex(
        text, PERCENT_RE,
        lambda match: f"{normalize_numeric_token(match.group(1))}%",
        "percent", path, conversions,
    )
    text = _apply_regex(
        text, TIME_RE,
        lambda match: f"{_integer_value(match.group(1))}:{_integer_value(match.group(2)):02d}",
        "clock-time", path, conversions,
    )
    text = _apply_regex(
        text, PREFIX_RE,
        lambda match: f"第{normalize_numeric_token(match.group(1))}",
        "ordinal-prefix", path, conversions,
    )
    # Preserve Japanese market-friendly magnitude units. "五千億ドル" means
    # "5,000億ドル" on screen, not "500,000,000,000ドル".
    text = _apply_regex(
        text, FINANCIAL_MAGNITUDE_RE,
        lambda match: f"{normalize_numeric_token(match.group(1))}{match.group(2)}{match.group(3)}",
        "financial-magnitude", path, conversions,
    )
    text = _apply_regex(
        text, UNIT_RE,
        lambda match: f"{normalize_numeric_token(match.group(1))}{match.group(2)}",
        "numeric-unit", path, conversions,
    )
    text = _apply_regex(
        text, DURATION_RE,
        lambda match: f"{normalize_numeric_token(match.group(1))}{match.group(2)}",
        "duration-unit", path, conversions,
    )
    text = _apply_regex(
        text,
        STANDALONE_DECIMAL_RE,
        lambda match: normalize_numeric_token(match.group(1)),
        "standalone-decimal",
        path,
        conversions,
    )
    return text


def assert_viewer_text_safe(value: str, path: str) -> None:
    # Use the same narrowly-scoped recognizers as projection. This prevents the
    # fail-closed detector from treating ordinary words such as 十分な or 一分野 as
    # numeric display text while still stopping any convertible Japanese number that
    # escaped projection.
    remaining_patterns = (
        PERCENT_RE,
        TIME_RE,
        PREFIX_RE,
        FINANCIAL_MAGNITUDE_RE,
        UNIT_RE,
        DURATION_RE,
    )
    if any(pattern.search(value) for pattern in remaining_patterns):
        raise ViewerSurfaceError(f"E_VIEWER_NUMERIC_KANJI_REMAINS:{path}:{value}")
    if re.search(rf"[{NUM_CHARS}]+・[{NUM_CHARS}]+", value):
        raise ViewerSurfaceError(f"E_VIEWER_NUMERIC_AMBIGUOUS:{path}:{value}")
    if re.match(r"^(?:EXPECTED|ACTUAL|GAP)(?:$|｜)", value):
        raise ViewerSurfaceError(f"E_VIEWER_FIXED_UI_ENGLISH:{path}:{value}")


def project_caption_text(value: str, *, path: str = "captionText") -> tuple[str, list[Conversion]]:
    conversions: list[Conversion] = []
    projected = normalize_viewer_text(value, path=path, conversions=conversions)
    assert_viewer_text_safe(projected, path)
    return projected, conversions


def _project_string(container: dict[str, Any], key: str, path: str, conversions: list[Conversion]) -> None:
    value = container.get(key)
    if not isinstance(value, str):
        return
    projected = normalize_viewer_text(value, path=path, conversions=conversions)
    assert_viewer_text_safe(projected, path)
    container[key] = projected


def _project_string_list(container: dict[str, Any], key: str, path: str,
                         conversions: list[Conversion]) -> None:
    values = container.get(key)
    if not isinstance(values, list):
        return
    projected_values: list[Any] = []
    for index, value in enumerate(values):
        if not isinstance(value, str):
            projected_values.append(value)
            continue
        item_path = f"{path}[{index}]"
        projected = normalize_viewer_text(value, path=item_path, conversions=conversions)
        assert_viewer_text_safe(projected, item_path)
        projected_values.append(projected)
    container[key] = projected_values


def project_authoring_viewer_surfaces(authoring: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    projected = copy.deepcopy(authoring)
    conversions: list[Conversion] = []
    for scene_index, scene in enumerate(projected.get("scenes", [])):
        base = f"$.scenes[{scene_index}]"
        _project_string(scene, "headline", f"{base}.headline", conversions)
        _project_string_list(scene, "supportingTexts", f"{base}.supportingTexts", conversions)
        for beat_index, beat in enumerate(scene.get("beats", [])):
            beat_base = f"{base}.beats[{beat_index}]"
            _project_string(beat, "screenQuestion", f"{beat_base}.screenQuestion", conversions)
            _project_string(beat, "primaryElement", f"{beat_base}.primaryElement", conversions)
            _project_string_list(beat, "viewerTexts", f"{beat_base}.viewerTexts", conversions)
            for metric_index, metric in enumerate(beat.get("metrics", [])):
                if not isinstance(metric, dict):
                    continue
                _project_string(metric, "label", f"{beat_base}.metrics[{metric_index}].label", conversions)
                _project_string(metric, "value", f"{beat_base}.metrics[{metric_index}].value", conversions)
                _project_string(metric, "comparison", f"{beat_base}.metrics[{metric_index}].comparison", conversions)
            for node_index, node in enumerate(beat.get("nodes", [])):
                if isinstance(node, dict):
                    _project_string(node, "label", f"{beat_base}.nodes[{node_index}].label", conversions)
        # chunk['text'] is speech/TTS source and MUST remain untouched.
    publishing = projected.get("publishing")
    if isinstance(publishing, dict):
        _project_string_list(publishing, "titleCandidates", "$.publishing.titleCandidates", conversions)
        _project_string_list(publishing, "thumbnailTextCandidates", "$.publishing.thumbnailTextCandidates", conversions)
        _project_string(publishing, "description", "$.publishing.description", conversions)
    report = {
        "contractVersion": "1.0.0",
        "episodeDate": projected.get("episodeDate"),
        "speechTextChanged": False,
        "conversions": [conversion.__dict__ for conversion in conversions],
        "ambiguousCount": 0,
        "viewerKanjiNumericCount": 0,
        "fixedUiViolations": 0,
        "status": "PASS",
    }
    return projected, report


def write_projection_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
