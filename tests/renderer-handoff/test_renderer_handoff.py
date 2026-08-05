from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "scripts/build_renderer_handoff.py"
spec = importlib.util.spec_from_file_location("handoff", SCRIPT)
handoff = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(handoff)

DATE = "2026-08-06"
PLOT = "a" * 40
RENDERER = "b" * 40


class Harness:
    def __init__(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = Path(self.t.name)
        self.src = self.root / "src"
        self.bundles = self.root / "bundles"
        self.write_valid()
    def close(self): self.t.cleanup()
    def put(self, rel, data):
        path = self.src / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, (dict, list)):
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        elif isinstance(data, bytes):
            path.write_bytes(data)
        else:
            path.write_text(data, encoding="utf-8")
        return path
    def write_valid(self):
        asset_bytes = b"asset-data"
        asset_sha = hashlib.sha256(asset_bytes).hexdigest()
        self.put("public/mainBackground.png", asset_bytes)
        self.put(f"episodes/{DATE}/episode_package_{DATE}.md", "# package")
        self.put(f"episodes/{DATE}/spoken_script_{DATE}.md", "# spoken")
        self.put(f"episodes/{DATE}/asset_manifest.json", {
            "contract_version": "1.0.0", "episode_date": DATE, "selected_path": "not-required",
            "assets": [{"asset_id": "mainBackground", "path": "public/mainBackground.png", "media_type": "image", "status": "ready", "sha256": asset_sha, "used_by": []}]
        })
        self.put(f"render-specs/{DATE}/render_spec.json", {"schemaVersion": "2.2.0", "episode": {"targetDate": DATE}, "scenes": []})
        self.put(f"verification/{DATE}/production_consistency_report.json", {"status": "pass", "unresolved_states": 0})
        self.put(f"verification/{DATE}/official_execution_preflight.json", {"status": "pass", "episode_date": DATE, "unresolved_states": 0, "preview_authorized": True, "final_authorized": False})
    def build(self, **kwargs):
        params = {"source_root": self.src, "bundle_root": self.bundles, "date": DATE, "mode": "preview", "plot_commit": PLOT, "renderer_commit": RENDERER, "renderer_contract_version": "2.2.0", "approval_path": None}
        params.update(kwargs)
        return handoff.build_handoff(**params)
    def mutate_json(self, rel, fn):
        path = self.src / rel
        value = json.loads(path.read_text())
        fn(value)
        path.write_text(json.dumps(value))
    def approval(self, **overrides):
        value = {"episode_date": DATE, "approval_status": "approved_preview", "final_requested": True, "preview_manifest_sha256": "c" * 64}
        value.update(overrides)
        return self.put("approval.json", value)


class Tests(unittest.TestCase):
    def setUp(self): self.h = Harness()
    def tearDown(self): self.h.close()
    def fail(self, needle, **kwargs):
        with self.assertRaises(handoff.HandoffError) as cm:
            self.h.build(**kwargs)
        self.assertIn(needle, str(cm.exception))

    def test_01_preview_bundle_created(self):
        result = self.h.build(); self.assertEqual("created", result["status"]); self.assertTrue(Path(result["manifest_path"]).is_file())
    def test_02_idempotent_noop(self):
        first = self.h.build(); second = self.h.build(); self.assertEqual(first["bundle_id"], second["bundle_id"]); self.assertEqual("noop", second["status"])
    def test_03_manifest_has_required_roles(self):
        result = self.h.build(); manifest = json.loads(Path(result["manifest_path"]).read_text()); self.assertTrue(set(handoff.REQUIRED_ROLES).issubset({item["role"] for item in manifest["files"]}))
    def test_04_preview_never_final_authorized(self):
        result = self.h.build(); manifest = json.loads(Path(result["manifest_path"]).read_text()); self.assertFalse(manifest["final_authorized"])
    def test_05_missing_required_file(self):
        (self.h.src / f"episodes/{DATE}/spoken_script_{DATE}.md").unlink(); self.fail("file does not exist")
    def test_06_preflight_fail(self):
        self.h.mutate_json(f"verification/{DATE}/official_execution_preflight.json", lambda d: d.update(status="fail")); self.fail("status must be pass")
    def test_07_preflight_date_mismatch(self):
        self.h.mutate_json(f"verification/{DATE}/official_execution_preflight.json", lambda d: d.update(episode_date="2026-08-07")); self.fail("episode_date mismatch")
    def test_08_unresolved_preflight(self):
        self.h.mutate_json(f"verification/{DATE}/official_execution_preflight.json", lambda d: d.update(unresolved_states=1)); self.fail("unresolved_states")
    def test_09_preview_not_authorized(self):
        self.h.mutate_json(f"verification/{DATE}/official_execution_preflight.json", lambda d: d.update(preview_authorized=False)); self.fail("preview_authorized")
    def test_10_consistency_fail(self):
        self.h.mutate_json(f"verification/{DATE}/production_consistency_report.json", lambda d: d.update(status="fail")); self.fail("consistency")
    def test_11_render_date_mismatch(self):
        self.h.mutate_json(f"render-specs/{DATE}/render_spec.json", lambda d: d["episode"].update(targetDate="2026-08-07")); self.fail("targetDate mismatch")
    def test_12_renderer_schema_mismatch(self): self.fail("schemaVersion", renderer_contract_version="2.1.0")
    def test_13_asset_manifest_date_mismatch(self):
        self.h.mutate_json(f"episodes/{DATE}/asset_manifest.json", lambda d: d.update(episode_date="2026-08-07")); self.fail("asset manifest episode_date")
    def test_14_unresolved_selected_path(self):
        self.h.mutate_json(f"episodes/{DATE}/asset_manifest.json", lambda d: d.update(selected_path="pending")); self.fail("selected_path")
    def test_15_missing_asset(self):
        (self.h.src / "public/mainBackground.png").unlink(); self.fail("file does not exist")
    def test_16_asset_sha_mismatch(self):
        self.h.mutate_json(f"episodes/{DATE}/asset_manifest.json", lambda d: d["assets"][0].update(sha256="d" * 64)); self.fail("SHA mismatch")
    def test_17_unsafe_asset_path(self):
        self.h.mutate_json(f"episodes/{DATE}/asset_manifest.json", lambda d: d["assets"][0].update(path="../secret")); self.fail("escapes root")
    def test_18_invalid_plot_commit(self): self.fail("plot_commit", plot_commit="short")
    def test_19_invalid_renderer_commit(self): self.fail("renderer_commit", renderer_commit="z" * 40)
    def test_20_preview_rejects_approval_record(self): self.fail("must not include", approval_path=self.h.approval())
    def test_21_final_requires_preflight_authorization(self): self.fail("final_authorized", mode="final", approval_path=self.h.approval())
    def test_22_final_requires_approval_record(self):
        self.h.mutate_json(f"verification/{DATE}/official_execution_preflight.json", lambda d: d.update(final_authorized=True)); self.fail("explicit approval", mode="final")
    def test_23_final_approval_date_mismatch(self):
        self.h.mutate_json(f"verification/{DATE}/official_execution_preflight.json", lambda d: d.update(final_authorized=True)); self.fail("approval_record.episode_date", mode="final", approval_path=self.h.approval(episode_date="2026-08-07"))
    def test_24_final_approval_status(self):
        self.h.mutate_json(f"verification/{DATE}/official_execution_preflight.json", lambda d: d.update(final_authorized=True)); self.fail("approval_record.approval_status", mode="final", approval_path=self.h.approval(approval_status="pending"))
    def test_25_final_requested_true(self):
        self.h.mutate_json(f"verification/{DATE}/official_execution_preflight.json", lambda d: d.update(final_authorized=True)); self.fail("approval_record.final_requested", mode="final", approval_path=self.h.approval(final_requested=False))
    def test_26_valid_final_bundle(self):
        self.h.mutate_json(f"verification/{DATE}/official_execution_preflight.json", lambda d: d.update(final_authorized=True)); result = self.h.build(mode="final", approval_path=self.h.approval()); manifest = json.loads(Path(result["manifest_path"]).read_text()); self.assertTrue(manifest["final_authorized"])
    def test_27_existing_bundle_tamper_detected(self):
        result = self.h.build(); manifest = json.loads(Path(result["manifest_path"]).read_text()); target = Path(result["bundle_path"]) / manifest["files"][0]["destination_path"]; target.write_text("tampered"); self.fail("missing or modified")
    def test_28_bundle_id_changes_with_renderer_commit(self):
        first = self.h.build(); second = self.h.build(renderer_commit="e" * 40); self.assertNotEqual(first["bundle_id"], second["bundle_id"])
    def test_29_bundle_id_changes_with_source(self):
        first = self.h.build(); (self.h.src / f"episodes/{DATE}/spoken_script_{DATE}.md").write_text("changed"); second = self.h.build(); self.assertNotEqual(first["bundle_id"], second["bundle_id"])
    def test_30_asset_copied_and_verified(self):
        result = self.h.build(); manifest = json.loads(Path(result["manifest_path"]).read_text()); item = next(x for x in manifest["files"] if x["role"] == "asset"); copied = Path(result["bundle_path"]) / item["destination_path"]; self.assertEqual(item["sha256"], handoff.sha256_file(copied))


if __name__ == "__main__":
    unittest.main()
