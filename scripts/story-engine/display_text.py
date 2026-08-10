from __future__ import annotations

import re

_DIGITS = {
    "〇": 0,
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
_SMALL_UNITS = {"十": 10, "百": 100, "千": 1000}
_JP_INTEGER = r"[〇零一二三四五六七八九十百千]+"
_JP_NUMBER = rf"{_JP_INTEGER}(?:・[〇零一二三四五六七八九]+)?"


def _parse_integer(value: str) -> int:
    if all(char in _DIGITS for char in value):
        return int("".join(str(_DIGITS[char]) for char in value))
    total = 0
    pending: int | None = None
    for char in value:
        if char in _DIGITS:
            pending = _DIGITS[char]
            continue
        unit = _SMALL_UNITS.get(char)
        if unit is None:
            raise ValueError(f"unsupported Japanese numeral: {value}")
        total += (1 if pending is None else pending) * unit
        pending = None
    return total + (pending or 0)


def _number(value: str) -> str:
    if "・" not in value:
        return str(_parse_integer(value))
    integer, fraction = value.split("・", 1)
    fractional_digits = "".join(str(_DIGITS[char]) for char in fraction)
    return f"{_parse_integer(integer)}.{fractional_digits}"


def _signed(sign: str | None, value: str) -> str:
    prefix = "+" if sign == "プラス" else "-" if sign == "マイナス" else ""
    return prefix + _number(value)


def to_display_text(text: str) -> str:
    """Normalize only finance-style spoken numbers for on-screen captions.

    Ordinary Japanese prose is left untouched. Conversion is intentionally
    limited to percentages and explicit financial/population units so TTS can
    keep natural readings while captions use compact Arabic numerals.
    """
    text = re.sub(
        rf"(?:(プラス|マイナス))?({_JP_NUMBER})パーセント",
        lambda match: f"{_signed(match.group(1), match.group(2))}%",
        text,
    )
    text = re.sub(
        rf"(?:(プラス|マイナス))?({_JP_NUMBER})(億ドル|万ドル|ドル|万人|億円|万円|円)",
        lambda match: f"{_signed(match.group(1), match.group(2))}{match.group(3)}",
        text,
    )
    return text
