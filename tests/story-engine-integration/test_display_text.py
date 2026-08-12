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
        "次四半期売上は十五・八九億から十六・一八億ドル。"
    )
    assert module.to_display_text(text) == (
        "Nasdaqは1.30%上昇、SOXXは2.02%高。"
        "予想は+8万人、実際は-2.3万人。"
        "売上14.85億ドル、EPS0.76ドル。"
        "次四半期売上は15.89億から16.18億ドル。"
    )


def test_story_projection_uses_repository_wide_viewer_surface_policy() -> None:
    module = load_module()
    text = "経路は四段です。通常取引の最初の一分から十五時五十九分まで確認します。"
    assert module.to_display_text(text) == "経路は4段です。通常取引の最初の1分から15:59まで確認します。"


def test_non_financial_japanese_prose_is_unchanged() -> None:
    module = load_module()
    text = "ここで一度、この説明を壊しにいきます。次の四半期も確認します。十分な材料を見ます。"
    assert module.to_display_text(text) == text
