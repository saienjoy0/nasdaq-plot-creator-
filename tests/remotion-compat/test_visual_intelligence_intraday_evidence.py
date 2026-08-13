#!/usr/bin/env python3
"""Regression test for lineage-verified intraday evidence binding."""
from __future__ import annotations

import base64
import hashlib
import json
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import visual_intelligence_intraday_evidence as binder  # noqa: E402


def main() -> int:
    date = "2099-05-07"
    reference = f"research/{date}/evidence/TEST_intraday_series.json"
    series = {
        "source": "Synthetic",
        "kind": "intraday",
        "symbol": "TEST.US",
        "marketDate": "2099-05-06",
        "timezone": "UTC",
        "session": "regular",
        "resolution": "1m",
        "precision": "verified-intraday-series",
        "providerSurface": "test",
        "priceBasis": "minute-close",
        "points": [
            {"timestamp": "2099-05-06T13:30:00Z", "price": 100.0, "close": 100.0, "volume": 1},
            {"timestamp": "2099-05-06T13:31:00Z", "price": 99.5, "close": 99.5, "volume": 2},
        ],
    }
    raw = json.dumps(series, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sha = hashlib.sha256(raw).hexdigest()
    render = {
        "schemaVersion": "2.4.0",
        "episode": {"targetDate": date},
        "sources": [{
            "sourceId": "source-001",
            "sourceType": "market-data",
            "reference": reference,
        }],
        "scenes": [{
            "sceneId": "scene-01",
            "narrationChunks": [{"chunkId": "scene-01-chunk-001", "speechText": "音声", "captionText": "字幕"}],
            "visualBeats": [{
                "beatId": "scene-01-beat-001",
                "evidenceSourceIds": ["source-001"],
                "objectIds": ["n1", "n2"],
                "viewerTexts": ["TEST -0.5%"],
                "templateConfig": {"variant": "zero-baseline"},
            }],
        }],
    }
    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-intraday-") as temp:
        root = Path(temp)
        packed = root / f"{reference}.zlib.b64"
        packed.parent.mkdir(parents=True)
        packed.write_text(base64.b64encode(zlib.compress(raw)).decode("ascii") + "\n", encoding="ascii")
        manifest = {
            "contractVersion": "1.0.0",
            "episodeDate": date,
            "waves": [{"evidenceFiles": [{"path": reference, "sha256": sha}]}],
        }
        manifest_path = root / "research" / date / "research_evidence_supplement_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        bound = binder.bind_verified_intraday_evidence(render, repo_root=root, date=date)
        if bound is render:
            raise AssertionError("binder must return a copy")
        beat = bound["scenes"][0]["visualBeats"][0]
        reaction = beat["templateConfig"].get("reactionTimeline")
        if reaction is None or reaction.get("precision") != "verified-intraday-series":
            raise AssertionError(reaction)
        if reaction.get("intradaySeries") != series:
            raise AssertionError("approved intraday bytes changed")
        if reaction.get("eventOrderIds") != ["n1", "n2"]:
            raise AssertionError("selected object order changed")
        if render["scenes"][0]["visualBeats"][0]["templateConfig"].get("reactionTimeline") is not None:
            raise AssertionError("source render mutated")
        if beat["viewerTexts"] != render["scenes"][0]["visualBeats"][0]["viewerTexts"]:
            raise AssertionError("viewer text changed")

        manifest["waves"][0]["evidenceFiles"][0]["sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        try:
            binder.bind_verified_intraday_evidence(render, repo_root=root, date=date)
        except binder.IntradayEvidenceBindingError as exc:
            if "SHA mismatch" not in str(exc):
                raise AssertionError(f"unexpected lineage error: {exc}") from exc
        else:
            raise AssertionError("tampered intraday evidence did not fail closed")

    print("visual intelligence intraday evidence binding test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
