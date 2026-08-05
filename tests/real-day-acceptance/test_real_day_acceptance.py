from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "scripts/run_real_day_acceptance.py"
spec = importlib.util.spec_from_file_location("accept", SCRIPT)
accept = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(accept)

DATE = "2026-08-06"
RENDERER = "b" * 40


class Harness:
    def __init__(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = Path(self.t.name)
        self.daily = self.root / "daily"
        self.bundle = self.root / "bundle"
        self.artifacts = self.root / "artifacts"
        self.daily.mkdir(); self.bundle.mkdir(); self.artifacts.mkdir()
        self.daily_file = self.daily / f"daily_source_package_{DATE}.md"
        self.daily_file.write_text("# real data")
        self.files = {}
        for role, name, data in [
            ("episode_package", "production/episode.md", b"episode"),
            ("render_spec", f"render-specs/{DATE}/render_spec.json", json.dumps({"episode": {"targetDate": DATE}}).encode()),
            ("preflight", "production/preflight.json", b"{}"),
            ("consistency_report", "production/consistency.json", b"{}"),
        ]:
            path = self.bundle / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            self.files[role] = {"role": role, "destination_path": name, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
        core = {
            "contract_version": "1.0.0", "episode_date": DATE, "mode": "preview",
            "plot_creator": {"repository": "saienjoy0/nasdaq-plot-creator-", "commit": "a" * 40},
            "renderer": {"repository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion", "expected_contract_version": "2.2.0", "expected_base_commit": RENDERER},
            "files": list(self.files.values()), "validation": {"production_package": "pass", "unresolved_states": 0},
            "final_authorized": False,
        }
        bundle_id = hashlib.sha256((json.dumps(core, sort_keys=True) + "\n").encode()).hexdigest()
        self.manifest = {**core, "bundle_id": bundle_id}
        self.manifest_path = self.bundle / "handoff_manifest.json"
        self.manifest_path.write_text(json.dumps(self.manifest))
        self.preview = self.artifacts / "preview.mp4"
        self.preview.write_bytes(b"video")
        self.tech = {
            "status": "pass", "episode_date": DATE, "renderer_commit": RENDERER,
            "final_render_executed": False, "render_spec_sha256": self.files["render_spec"]["sha256"],
            "technical_checks": "pass", "preview_artifact": "preview.mp4",
            "preview_sha256": hashlib.sha256(b"video").hexdigest(),
        }
        self.tech_path = self.artifacts / "technical_report.json"
        self.tech_path.write_text(json.dumps(self.tech))
    def close(self): self.t.cleanup()
    def save_manifest(self): self.manifest_path.write_text(json.dumps(self.manifest))
    def save_tech(self): self.tech_path.write_text(json.dumps(self.tech))
    def review(self, status="pending", **overrides):
        value = {
            "episode_date": DATE, "bundle_id": self.manifest["bundle_id"], "status": status,
            "reviewed_at": None if status == "pending" else "2026-08-06T12:00:00+09:00", "notes": "",
        }
        value.update(overrides)
        path = self.artifacts / "user_review.json"
        path.write_text(json.dumps(value))
        return path
    def run(self, **kwargs):
        params = {
            "episode_date": DATE, "daily_source_root": self.daily, "daily_source_path": self.daily_file,
            "bundle_root": self.bundle, "handoff_manifest_path": self.manifest_path,
            "renderer_artifact_root": self.artifacts, "technical_report_path": self.tech_path,
            "user_review_path": None,
        }
        params.update(kwargs)
        return accept.validate_acceptance(**params)


class Tests(unittest.TestCase):
    def setUp(self): self.h = Harness()
    def tearDown(self): self.h.close()
    def fail(self, needle, **kwargs):
        with self.assertRaises(accept.AcceptanceError) as cm:
            self.h.run(**kwargs)
        self.assertIn(needle, str(cm.exception))

    def test_01_pending_preview(self): self.assertEqual("preview_ready_user_review_pending", self.h.run()["mvp_status"])
    def test_02_approved_preview(self): self.assertEqual("passed", self.h.run(user_review_path=self.h.review("approved"))["mvp_status"])
    def test_03_rejected_preview(self): self.assertEqual("failed", self.h.run(user_review_path=self.h.review("rejected"))["mvp_status"])
    def test_04_final_always_false(self): self.assertFalse(self.h.run()["final_render_executed"])
    def test_05_seed_date_forbidden(self): self.fail("may not reuse", episode_date="2026-07-31")
    def test_06_daily_filename_date(self):
        path = self.h.daily / "daily.md"; path.write_text("x"); self.fail("filename", daily_source_path=path)
    def test_07_empty_daily_source(self): self.h.daily_file.write_text(""); self.fail("non-empty")
    def test_08_handoff_date_mismatch(self): self.h.manifest["episode_date"] = "2026-08-07"; self.h.save_manifest(); self.fail("episode_date mismatch")
    def test_09_handoff_mode_final(self): self.h.manifest["mode"] = "final"; self.h.save_manifest(); self.fail("preview handoff")
    def test_10_handoff_final_authorized(self): self.h.manifest["final_authorized"] = True; self.h.save_manifest(); self.fail("final_authorized=false")
    def test_11_handoff_validation_fail(self): self.h.manifest["validation"]["production_package"] = "fail"; self.h.save_manifest(); self.fail("must pass")
    def test_12_handoff_unresolved(self): self.h.manifest["validation"]["unresolved_states"] = 1; self.h.save_manifest(); self.fail("unresolved")
    def test_13_bundle_file_missing(self): (self.h.bundle / "production/episode.md").unlink(); self.fail("file does not exist")
    def test_14_bundle_file_sha(self): (self.h.bundle / "production/episode.md").write_bytes(b"bad"); self.fail("SHA mismatch")
    def test_15_bundle_file_size(self): self.h.manifest["files"][0]["size"] += 1; self.h.save_manifest(); self.fail("size mismatch")
    def test_16_missing_required_role(self): self.h.manifest["files"] = [x for x in self.h.manifest["files"] if x["role"] != "render_spec"]; self.h.save_manifest(); self.fail("lacks required")
    def test_17_technical_status_fail(self): self.h.tech["status"] = "fail"; self.h.save_tech(); self.fail("status must be pass")
    def test_18_technical_date_mismatch(self): self.h.tech["episode_date"] = "2026-08-07"; self.h.save_tech(); self.fail("episode_date mismatch")
    def test_19_renderer_commit_mismatch(self): self.h.tech["renderer_commit"] = "c" * 40; self.h.save_tech(); self.fail("commit mismatch")
    def test_20_final_render_detected(self): self.h.tech["final_render_executed"] = True; self.h.save_tech(); self.fail("forbids final")
    def test_21_render_spec_sha_mismatch(self): self.h.tech["render_spec_sha256"] = "d" * 64; self.h.save_tech(); self.fail("render_spec SHA")
    def test_22_technical_checks_fail(self): self.h.tech["technical_checks"] = "fail"; self.h.save_tech(); self.fail("technical checks")
    def test_23_preview_missing(self): self.h.preview.unlink(); self.fail("file does not exist")
    def test_24_preview_sha_mismatch(self): self.h.tech["preview_sha256"] = "e" * 64; self.h.save_tech(); self.fail("preview artifact SHA")
    def test_25_review_date_mismatch(self): self.fail("user review episode_date", user_review_path=self.h.review("approved", episode_date="2026-08-07"))
    def test_26_review_bundle_mismatch(self): self.fail("bundle_id mismatch", user_review_path=self.h.review("approved", bundle_id="f" * 64))
    def test_27_review_status_invalid(self): self.fail("status must", user_review_path=self.h.review("other"))
    def test_28_reviewed_at_required(self): self.fail("requires reviewed_at", user_review_path=self.h.review("approved", reviewed_at=None))
    def test_29_report_files_written(self):
        report = self.h.run(); paths = accept.write_report(report, self.h.root / "report"); self.assertTrue(Path(paths["json"]).is_file()); self.assertTrue(Path(paths["markdown"]).is_file())
    def test_30_report_records_hashes(self):
        report = self.h.run(); self.assertEqual(hashlib.sha256(b"video").hexdigest(), report["preview"]["sha256"]); self.assertEqual(accept.sha256_file(self.h.daily_file), report["daily_source"]["sha256"])


if __name__ == "__main__":
    unittest.main()
