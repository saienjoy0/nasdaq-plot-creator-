from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import assemble_chatgpt_daily_authoring_parts as assembler  # noqa: E402
import materialize_renderer_sources as renderer_sources  # noqa: E402
import viewer_surface_projection as viewer  # noqa: E402


@pytest.mark.parametrize(
    ("speech", "expected"),
    [
        ("NASDAQは〇・六パーセント下落", "NASDAQは0.6%下落"),
        ("NVIDIAは二・〇五パーセント下落", "NVIDIAは2.05%下落"),
        ("十五時五十九分まで確認", "15:59まで確認"),
        ("実際の一分足です", "実際の1分足です"),
        ("五千億ドル規模", "5,000億ドル規模"),
        ("千四十億ドル", "1,040億ドル"),
        ("二十五・八億ドル", "25.8億ドル"),
        ("二万六千四百四十五・四五。", "26,445.45。"),
    ],
)
def test_caption_numeric_projection(speech: str, expected: str) -> None:
    caption, _ = viewer.project_caption_text(speech)
    assert caption == expected


@pytest.mark.parametrize("text", ["一方で四半期売上は増加", "唯一の反対材料", "三菱を確認"])
def test_non_numeric_japanese_is_unchanged(text: str) -> None:
    caption, _ = viewer.project_caption_text(text)
    assert caption == text


def test_authoring_projection_never_changes_speech_source() -> None:
    authoring = {
        "episodeDate": "2026-08-12",
        "scenes": [
            {
                "headline": "七月CPIを確認",
                "supportingTexts": ["一分足"],
                "chunks": [{"text": "NVIDIAは二・〇五パーセント下落"}],
                "beats": [
                    {
                        "screenQuestion": "十五時五十九分までどう動いたか",
                        "primaryElement": "三つの資産",
                        "viewerTexts": ["二十一時三十分 CPI"],
                    }
                ],
            }
        ],
    }
    original = copy.deepcopy(authoring)
    projected, report = viewer.project_authoring_viewer_surfaces(authoring)
    assert projected["scenes"][0]["chunks"][0]["text"] == original["scenes"][0]["chunks"][0]["text"]
    assert projected["scenes"][0]["headline"] == "7月CPIを確認"
    assert projected["scenes"][0]["supportingTexts"] == ["1分足"]
    assert projected["scenes"][0]["beats"][0]["screenQuestion"] == "15:59までどう動いたか"
    assert projected["scenes"][0]["beats"][0]["primaryElement"] == "3つの資産"
    assert projected["scenes"][0]["beats"][0]["viewerTexts"] == ["21:30 CPI"]
    assert report["speechTextChanged"] is False


def test_qualitative_financial_metric_projects_to_card() -> None:
    scene = {"numbers": [], "cards": []}
    renderer_sources._project_metric_objects(
        scene,
        [
            {
                "metricId": "metric.reuters.condition",
                "label": "Reuters",
                "valueText": "再開には米国側の条件履行が必要",
                "numericValue": None,
                "tone": "neutral",
            }
        ],
        "scene-02-beat-001",
    )
    assert scene["numbers"] == []
    assert scene["cards"] == [
        {
            "cardId": "metric.reuters.condition",
            "role": None,
            "title": "Reuters",
            "lines": [
                {
                    "label": "確認",
                    "value": "再開には米国側の条件履行が必要",
                    "tone": "neutral",
                }
            ],
        }
    ]


def test_numeric_financial_metric_projects_to_number() -> None:
    scene = {"numbers": [], "cards": []}
    renderer_sources._project_metric_objects(
        scene,
        [
            {
                "metricId": "metric.nasdaq.close",
                "label": "NASDAQ",
                "valueText": "-0.60",
                "numericValue": -0.6,
                "precision": 2,
                "unit": "%",
                "tone": "negative",
            }
        ],
        "scene-03-beat-001",
    )
    assert scene["cards"] == []
    assert scene["numbers"][0]["numberId"] == "metric.nasdaq.close"
    assert scene["numbers"][0]["numericValue"] == -0.6


def test_renderer_financial_scope_is_verified_without_rewriting_source(tmp_path: Path) -> None:
    materializer = tmp_path / "scripts" / "materialize_renderer_sources.py"
    materializer.parent.mkdir(parents=True)
    materializer.write_text(
        "FINANCIAL_TEMPLATES = {\n"
        '    "market-pulse-grid", "earnings-surprise", "dual-asset-split",\n'
        '    "macro-pressure", "source-receipt",\n'
        "}\n",
        encoding="utf-8",
    )
    before = materializer.read_bytes()
    assembler.assert_renderer_240_financial_scope(tmp_path)
    assert materializer.read_bytes() == before


def test_renderer_financial_scope_mismatch_fails_closed(tmp_path: Path) -> None:
    materializer = tmp_path / "scripts" / "materialize_renderer_sources.py"
    materializer.parent.mkdir(parents=True)
    materializer.write_text(
        'FINANCIAL_TEMPLATES = {"market-pulse-grid", "dual-asset-split"}\n',
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="Renderer 2.4 financial template scope mismatch"):
        assembler.assert_renderer_240_financial_scope(tmp_path)
