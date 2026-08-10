from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    path = ROOT / "scripts/story-engine/display_text.py"
    spec = importlib.util.spec_from_file_location("display_text", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_finance_style_spoken_numbers_become_display_numbers() -> None:
    module = load_module()
    text = (
        "Nasdaqは一・三〇パーセント上昇、SOXXは二・〇二パーセント高。"
        "予想はプラス八万人、実際はマイナス二・三万人。"
        "売上十四・八五億ドル、EPS〇・七六ドル。"
    )
    assert module.to_display_text(text) == (
        "Nasdaqは1.30%上昇、SOXXは2.02%高。"
        "予想は+8万人、実際は-2.3万人。"
        "売上14.85億ドル、EPS0.76ドル。"
    )


def test_non_financial_japanese_prose_is_unchanged() -> None:
    module = load_module()
    text = "ここで一度、この説明を壊しにいきます。次の四半期も確認します。"
    assert module.to_display_text(text) == text
