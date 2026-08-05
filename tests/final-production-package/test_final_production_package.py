from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "scripts/build_final_production_package.py"
spec = importlib.util.spec_from_file_location("builder", SCRIPT)
builder = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(builder)


def asset(asset_id):
    return {"asset_id": asset_id, "path": f"public/{asset_id}.png", "media_type": "image", "status": "ready", "sha256": "a" * 64}


def scene(n):
    sid = f"scene-{n:02d}"
    cid = f"{sid}-chunk-001"
    bid = f"{sid}-beat-001"
    speech, caption = f"Speech {n}.", f"Caption {n}"
    return {
        "sceneId": sid, "sceneNumber": n, "sceneRole": "editorial-body", "formalName": f"Scene {n}",
        "purpose": "purpose", "causalScope": "multiple", "performanceIntent": "intent",
        "evidenceSourceIds": ["source-001"], "uncertainty": "none", "timelineBasis": "session",
        "expectedBasisType": "not-applicable", "visualMode": "text-focus", "initialExpression": "通常",
        "headline": f"Headline {n}", "supportingTexts": [f"Support {n}"], "sourceLabel": "source",
        "narrationChunks": [{"chunkId": cid, "speechText": speech, "captionText": caption, "expression": "通常", "pauseAfterMs": 200}],
        "visualBeats": [{
            "beatId": bid, "startChunkId": cid, "endChunkId": cid,
            "narrationStartCue": speech, "narrationEndCue": speech,
            "primaryFunction": "Explain", "screenState": "Data", "visualMode": "text-focus",
            "visualTemplate": "text-focus", "templateConfig": {}, "sequencePolicy": "static",
            "finalHoldMs": 500, "contentType": "text", "screenQuestion": f"Question {n}",
            "primaryElement": f"Primary {n}", "viewerTexts": [f"Viewer {n}"], "changeCue": caption,
            "objectIds": [], "assetPlacementIds": [], "assetState": "not-required", "returnScreenState": None,
            "evidenceSourceIds": ["source-001"], "expressionChange": None, "fallback": None,
            "entity": None, "pictureBook": None
        }],
        "cards": [], "numbers": [], "nodes": [], "arrows": [], "visualEvents": [],
        "assetPlacements": [{
            "placementId": f"{sid}-bg", "assetId": "mainBackground", "role": "background",
            "region": "full-canvas", "fit": "cover", "opacity": 1,
            "startChunkId": None, "endChunkId": None
        }],
        "transition": {"type": "cut", "durationMs": 0}
    }


def render_spec():
    return {
        "schemaVersion": "2.2.0",
        "episode": {"id": "2026-08-06", "targetDate": "2026-08-06", "marketSession": "US", "informationCutoff": "2026-08-06T07:00:00+09:00", "episodeType": "single-news", "durationMode": "standard", "shortenedReason": None, "fps": 30, "width": 1920, "height": 1080},
        "editorial": {"storySpine": "Spine", "centralHypothesis": "Hypothesis"},
        "publishing": {"recommendedTitle": "Title", "recommendedThumbnailText": "Thumb", "description": "Description"},
        "sources": [{"sourceId": "source-001", "title": "Source"}],
        "review": {"verdict": "approved", "requiredChanges": [], "changesApplied": [], "approvedForCodex": True},
        "scenes": [scene(i) for i in range(1, 10)]
    }


def annex():
    return {
        "contract_version": "1.0.0", "episode_date": "2026-08-06",
        "post_inquisition": {"status": "pass", "required_changes_applied": True, "unresolved_required_changes": 0},
        "image_resolution": {
            "status": "resolved", "selected_path": "not-required", "unresolved_count": 0,
            "routes": [{"beat_id": f"scene-{i:02d}-beat-001", "selected_path": "not-required", "selected_asset_id": None, "primary_asset_id": None, "fallback_asset_id": None} for i in range(1, 10)]
        },
        "renderer_contract": {"repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion", "schema_version": "2.2.0"},
        "asset_catalog": [asset("mainBackground")], "render_spec": render_spec()
    }


def public_text(a):
    rs = a["render_spec"]
    values = [rs["publishing"]["recommendedTitle"], rs["publishing"]["recommendedThumbnailText"], rs["publishing"]["description"]]
    for s in rs["scenes"]:
        values += [s["headline"], *s["supportingTexts"]]
        for c in s["narrationChunks"]:
            values += [c["speechText"], c["captionText"]]
        for b in s["visualBeats"]:
            values += [b["narrationStartCue"], b["narrationEndCue"], b["screenQuestion"], b["primaryElement"], b["changeCue"], *b["viewerTexts"]]
    return "\n".join(dict.fromkeys(values))


def markdown(a):
    return public_text(a) + "\n" + builder.BEGIN + "\n```json\n" + json.dumps(a, ensure_ascii=False, indent=2) + "\n```\n" + builder.END + "\n"


class Tests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = Path(self.t.name)
        self.schema = ROOT / "skills/nasdaq-cafe-final-production/contracts/final_production_source_annex.schema.json"
        self.pkg = self.root / "episode_package_2026-08-06.md"
    def tearDown(self): self.t.cleanup()
    def write(self, a=None, text=None):
        a = a or annex()
        self.pkg.write_text(text if text is not None else markdown(a), encoding="utf-8")
        return a
    def build(self, a=None, text=None):
        self.write(a, text)
        return builder.build(self.pkg, self.root / "out", self.schema)
    def fail(self, a, needle, text=None):
        self.write(a, text)
        with self.assertRaises(builder.ProductionPackageError) as cm:
            builder.build(self.pkg, self.root / "out", self.schema)
        self.assertIn(needle, str(cm.exception))

    def test_01_builds_all_artifacts(self):
        result = self.build(); self.assertEqual("pass", result["status"]); self.assertEqual(6, len(result["paths"]))
    def test_02_byte_identical_rerun(self):
        first = self.build(); second = builder.build(self.pkg, self.root / "out", self.schema); self.assertEqual(first["hashes"], second["hashes"])
    def test_03_nine_scene_order(self):
        a = annex(); a["render_spec"]["scenes"].reverse(); self.fail(a, "must be exactly")
    def test_04_missing_scene(self):
        a = annex(); a["render_spec"]["scenes"].pop(); self.fail(a, "too short")
    def test_05_date_mismatch(self):
        a = annex(); a["render_spec"]["episode"]["targetDate"] = "2026-08-07"; self.fail(a, "targetDate")
    def test_06_schema_version_mismatch(self):
        a = annex(); a["renderer_contract"]["schema_version"] = "2.1.0"; self.fail(a, "schema_version")
    def test_07_review_not_approved(self):
        a = annex(); a["render_spec"]["review"]["verdict"] = "rejected"; self.fail(a, "verdict")
    def test_08_codex_not_approved(self):
        a = annex(); a["render_spec"]["review"]["approvedForCodex"] = False; self.fail(a, "approvedForCodex")
    def test_09_duplicate_chunk(self):
        a = annex(); a["render_spec"]["scenes"][1]["narrationChunks"][0]["chunkId"] = "scene-01-chunk-001"; self.fail(a, "duplicate chunkId")
    def test_10_bad_beat_chunk_reference(self):
        a = annex(); a["render_spec"]["scenes"][0]["visualBeats"][0]["startChunkId"] = "missing"; self.fail(a, "same scene")
    def test_11_unresolved_asset_state(self):
        a = annex(); a["render_spec"]["scenes"][0]["visualBeats"][0]["assetState"] = "pending"; self.fail(a, "assetState is unresolved")
    def test_12_missing_asset_catalog_entry(self):
        a = annex(); a["asset_catalog"] = []; self.fail(a, "omits placement assets")
    def test_13_duplicate_asset_id(self):
        a = annex(); a["asset_catalog"].append(copy.deepcopy(a["asset_catalog"][0])); self.fail(a, "duplicate asset_id")
    def test_14_unsafe_asset_path(self):
        a = annex(); a["asset_catalog"][0]["path"] = "../secret"; self.fail(a, "safe and relative")
    def test_15_primary_route_mismatch(self):
        a = annex(); a["image_resolution"]["selected_path"] = "primary"; a["image_resolution"]["routes"][0].update(selected_path="primary", primary_asset_id="mainBackground", selected_asset_id="other"); self.fail(a, "primary selected path")
    def test_16_fallback_route_mismatch(self):
        a = annex(); a["image_resolution"]["selected_path"] = "fallback"; a["image_resolution"]["routes"][0].update(selected_path="fallback", fallback_asset_id="mainBackground", selected_asset_id="other"); self.fail(a, "fallback selected path")
    def test_17_not_required_has_asset(self):
        a = annex(); a["image_resolution"]["routes"][0]["selected_asset_id"] = "mainBackground"; self.fail(a, "not-required route")
    def test_18_missing_public_speech(self):
        a = annex(); self.fail(a, "speechText", markdown(a).replace("Speech 1.", "", 1))
    def test_19_memref_in_speech(self):
        a = annex(); a["render_spec"]["scenes"][0]["narrationChunks"][0]["speechText"] = "Bad<!--MEMREF:MR-001:U-001-->"; self.fail(a, "MEMREF")
    def test_20_negative_pause(self):
        a = annex(); a["render_spec"]["scenes"][0]["narrationChunks"][0]["pauseAfterMs"] = -1; self.fail(a, "pauseAfterMs")
    def test_21_missing_source_annex(self):
        self.write(text="no annex");
        with self.assertRaises(builder.ProductionPackageError): builder.build(self.pkg, self.root / "out", self.schema)
    def test_22_duplicate_source_annex(self):
        a = annex(); self.write(text=markdown(a) + markdown(a));
        with self.assertRaises(builder.ProductionPackageError): builder.build(self.pkg, self.root / "out", self.schema)
    def test_23_spoken_script_excludes_markers(self):
        result = self.build(); self.assertNotIn("MEMREF", Path(result["paths"]["spoken_script"]).read_text())
    def test_24_manifest_tracks_used_assets(self):
        result = self.build(); manifest = json.loads(Path(result["paths"]["asset_manifest"]).read_text()); self.assertEqual(9, len(manifest["assets"][0]["used_by"]))
    def test_25_preflight_blocks_final(self):
        result = self.build(); preflight = json.loads(Path(result["paths"]["preflight"]).read_text()); self.assertTrue(preflight["preview_authorized"]); self.assertFalse(preflight["final_authorized"])
    def test_26_ir_matches_scene_order(self):
        result = self.build(); ir = json.loads(Path(result["paths"]["ir"]).read_text()); self.assertEqual(builder.SCENE_IDS, [s["sceneId"] for s in ir["scenes"]])
    def test_27_malformed_json(self):
        self.write(text=builder.BEGIN + "\n```json\n{\n```\n" + builder.END)
        with self.assertRaises(builder.ProductionPackageError): builder.build(self.pkg, self.root / "out", self.schema)
    def test_28_absolute_asset_path(self):
        a = annex(); a["asset_catalog"][0]["path"] = "/tmp/x"; self.fail(a, "safe and relative")
    def test_29_selected_asset_absent(self):
        a = annex(); a["image_resolution"]["selected_path"] = "primary"; a["image_resolution"]["routes"][0].update(selected_path="primary", primary_asset_id="new", selected_asset_id="new"); self.fail(a, "absent from asset_catalog")
    def test_30_duplicate_beat(self):
        a = annex(); a["render_spec"]["scenes"][1]["visualBeats"][0]["beatId"] = "scene-01-beat-001"; self.fail(a, "duplicate beatId")


if __name__ == "__main__":
    unittest.main()
