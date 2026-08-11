from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


attachment = load_module(
    "intraday_series_attachment_test",
    ROOT / "scripts/remotion_intraday_series.py",
)


class IntradaySeriesAttachmentTests(unittest.TestCase):
    def _series(self) -> dict:
        return {
            "source": "Longbridge",
            "kind": "intraday",
            "fetched_by": "longbridge-cli",
            "generated_at": "2026-08-10T05:15:44+00:00",
            "symbol": "QQQ.US",
            "marketDate": "2026-08-07",
            "timezone": "UTC",
            "session": "all",
            "resolution": "1m",
            "precision": "verified-intraday-series",
            "providerSurface": "kline-history-fallback",
            "priceBasis": "minute-close",
            "rawSha256": "a" * 64,
            "points": [
                {
                    "timestamp": "2026-08-07T12:29:00Z",
                    "price": 719.16,
                    "open": 719.302,
                    "high": 719.44,
                    "low": 718.06,
                    "close": 719.16,
                    "volume": 13132,
                    "turnover": 9441861.769,
                    "session": "Pre",
                },
                {
                    "timestamp": "2026-08-07T12:30:00Z",
                    "price": 720.23,
                    "open": 719.32,
                    "high": 721.52,
                    "low": 719.307,
                    "close": 720.23,
                    "volume": 41807,
                    "turnover": 30122415.08,
                    "session": "Pre",
                },
                {
                    "timestamp": "2026-08-07T12:31:00Z",
                    "price": 720.531,
                    "open": 720.29,
                    "high": 720.83,
                    "low": 720.14,
                    "close": 720.531,
                    "volume": 15554,
                    "turnover": 11207190.212,
                    "session": "Pre",
                },
            ],
        }

    def _render(self) -> dict:
        return {
            "scenes": [
                {
                    "sceneId": "scene-08",
                    "visualBeats": [
                        {
                            "beatId": "vb-08-01",
                            "visualTemplate": "event-reaction-timeline",
                            "templateConfig": {
                                "variant": "verified-series",
                                "reactionTimeline": {
                                    "precision": "verified-intraday-series",
                                    "eventOrderIds": ["n1", "n2", "n3"],
                                    "seriesObjectIds": ["n1", "n2", "n3"],
                                },
                            },
                        }
                    ],
                }
            ]
        }

    def test_full_series_is_attached_before_renderer_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            series_path = root / "research/2026-08-10/evidence/RA-W2-001_intraday_series.json"
            series_path.parent.mkdir(parents=True)
            series_path.write_text(json.dumps(self._series()), encoding="utf-8")
            bindings_path = root / "working/2026-08-10/reaction_timeline_bindings.json"
            bindings_path.parent.mkdir(parents=True)
            bindings_path.write_text(
                json.dumps(
                    {
                        "contractVersion": "1.0.0",
                        "episodeDate": "2026-08-10",
                        "bindings": [
                            {
                                "visualBeatId": "vb-08-01",
                                "visualTemplate": "event-reaction-timeline",
                                "templateVariant": "verified-series",
                                "precision": "verified-intraday-series",
                                "eventOrderIds": ["n1", "n2", "n3"],
                                "seriesObjectIds": ["n1", "n2", "n3"],
                                "evidenceBasis": "timing evidence only",
                                "intradaySeriesPath": "research/2026-08-10/evidence/RA-W2-001_intraday_series.json",
                                "eventMarker": {
                                    "timestamp": "2026-08-07T12:30:00Z",
                                    "label": "雇用統計",
                                    "sourceLabel": "BLS",
                                },
                                "displayTimezone": "America/New_York",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            render = self._render()
            result = attachment.attach_bound_intraday_series(
                render,
                output_root=root,
                episode_date="2026-08-10",
                reaction_bindings_path=bindings_path,
            )

            reaction = render["scenes"][0]["visualBeats"][0]["templateConfig"]["reactionTimeline"]
            self.assertEqual(1, result["attachmentCount"])
            self.assertEqual("QQQ.US", reaction["intradaySeries"]["symbol"])
            self.assertEqual(3, len(reaction["intradaySeries"]["points"]))
            self.assertEqual("雇用統計", reaction["eventMarker"]["label"])
            self.assertEqual("America/New_York", reaction["displayTimezone"])
            self.assertEqual(["n1", "n2", "n3"], reaction["seriesObjectIds"])

    def test_legacy_binding_without_path_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bindings_path = root / "reaction_timeline_bindings.json"
            bindings_path.write_text(
                json.dumps(
                    {
                        "contractVersion": "1.0.0",
                        "episodeDate": "2026-08-10",
                        "bindings": [
                            {
                                "visualBeatId": "vb-08-01",
                                "precision": "verified-intraday-series",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            render = self._render()
            result = attachment.attach_bound_intraday_series(
                render,
                output_root=root,
                episode_date="2026-08-10",
                reaction_bindings_path=bindings_path,
            )
            self.assertEqual(0, result["attachmentCount"])
            reaction = render["scenes"][0]["visualBeats"][0]["templateConfig"]["reactionTimeline"]
            self.assertNotIn("intradaySeries", reaction)

    def test_series_path_cannot_escape_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bindings_path = root / "reaction_timeline_bindings.json"
            bindings_path.write_text(
                json.dumps(
                    {
                        "contractVersion": "1.0.0",
                        "episodeDate": "2026-08-10",
                        "bindings": [
                            {
                                "visualBeatId": "vb-08-01",
                                "precision": "verified-intraday-series",
                                "intradaySeriesPath": "../outside.json",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                attachment.IntradaySeriesAttachmentError,
                "escapes output root",
            ):
                attachment.attach_bound_intraday_series(
                    self._render(),
                    output_root=root,
                    episode_date="2026-08-10",
                    reaction_bindings_path=bindings_path,
                )


if __name__ == "__main__":
    unittest.main()
