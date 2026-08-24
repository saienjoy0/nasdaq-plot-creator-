from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import chatgpt_semantic_freeze as freeze  # noqa: E402
import run_semantic_frozen_renderer_closure_v12 as frozen_closure  # noqa: E402


class SemanticFreezeTests(unittest.TestCase):
    def _write_sources(self, root: Path, date: str, narration: str = "僕は確認します。") -> None:
        parts = root / "daily-authoring-parts" / date
        parts.mkdir(parents=True, exist_ok=True)
        (parts / "00_meta.json").write_text(
            json.dumps({"episodeDate": date, "narration": narration}, ensure_ascii=False),
            encoding="utf-8",
        )
        daily = root / "daily-inputs" / date
        daily.mkdir(parents=True, exist_ok=True)
        (daily / f"daily_source_package_{date}.md").write_text("daily", encoding="utf-8")
        source = root / "source-of-truth"
        source.mkdir(parents=True, exist_ok=True)
        canon = source / "canon_manifest.json"
        canon.write_text(
            json.dumps(
                {
                    "contractVersion": "1.0.0",
                    "documents": [
                        {
                            "id": "01",
                            "logicalPath": "source-of-truth/01.md",
                            "storage": "plain",
                            "sha256": "a" * 64,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (source / "01.md").write_text("x", encoding="utf-8")

    def test_legacy_build_and_verify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            date = "2026-08-17"
            self._write_sources(root, date)
            manifest_path = root / "semantic-freezes" / f"{date}.json"
            manifest = freeze.write_manifest(root, date, manifest_path)
            self.assertEqual("1.1.0", manifest["contractVersion"])
            self.assertEqual(date, manifest["episodeDate"])
            self.assertEqual(manifest, freeze.verify_manifest(root, date, manifest_path))

    def test_legacy_changed_source_invalidates_freeze(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            date = "2026-08-17"
            self._write_sources(root, date)
            manifest_path = root / "semantic-freezes" / f"{date}.json"
            freeze.write_manifest(root, date, manifest_path)
            part = root / "daily-authoring-parts" / date / "00_meta.json"
            part.write_text(json.dumps({"episodeDate": date, "narration": "changed"}), encoding="utf-8")
            with self.assertRaises(freeze.SemanticFreezeError):
                freeze.verify_manifest(root, date, manifest_path)

    def test_legacy_byte_change_invalidates_even_when_semantics_same(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            date = "2026-08-17"
            self._write_sources(root, date)
            manifest_path = root / "semantic-freezes" / f"{date}.json"
            original = freeze.write_manifest(root, date, manifest_path)
            part = root / "daily-authoring-parts" / date / "00_meta.json"
            value = json.loads(part.read_text(encoding="utf-8"))
            part.write_text(json.dumps(value, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
            changed = freeze.build_manifest(root, date)
            original_semantic = [item["semanticSha256"] for item in original["parts"]]
            changed_semantic = [item["semanticSha256"] for item in changed["parts"]]
            self.assertEqual(original_semantic, changed_semantic)
            self.assertNotEqual(original["parts"][0]["sha256"], changed["parts"][0]["sha256"])
            with self.assertRaises(freeze.SemanticFreezeError):
                freeze.verify_manifest(root, date, manifest_path)

    def test_two_dates_have_isolated_source_sets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_sources(root, "2026-08-17", narration="A")
            self._write_sources(root, "2026-08-18", narration="B")
            a = freeze.build_manifest(root, "2026-08-17")
            b = freeze.build_manifest(root, "2026-08-18")
            self.assertNotEqual(a["sourceSetDigestSha256"], b["sourceSetDigestSha256"])
            self.assertEqual(a["canonManifest"], b["canonManifest"])

    def test_ai_b_semantic_payloads_do_not_duplicate_manifest_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            date = "2026-08-17"
            vi = root / "working" / date / "visual-intelligence"
            vi.mkdir(parents=True, exist_ok=True)
            expected = "a" * 64
            requirements = {
                "semanticPayloadVersion": "1.0.0",
                "episodeDate": date,
                "intent": {"beats": []},
                "provisionalDirection": {"requirements": []},
            }
            (vi / "visual_requirements.semantic.json").write_text(
                json.dumps(requirements), encoding="utf-8"
            )
            self.assertNotIn("semanticFreezeSha256", requirements)
            self.assertIsNone(
                frozen_closure.semantic_binding_pause(
                    root, date, phase="compile", semantic_freeze_sha256=expected
                )
            )
            wrapper = (REPO_ROOT / "scripts/run_semantic_frozen_renderer_closure_v12.py").read_text(encoding="utf-8")
            self.assertNotIn('decision.get("semanticFreezeSha256")', wrapper)
            self.assertNotIn('requirements.get("semanticFreezeSha256")', wrapper)

    def test_canonical_workflow_delegates_semantic_verification_to_facade(self) -> None:
        workflow = (REPO_ROOT / ".github/workflows/chatgpt-daily-preview-production.yml").read_text(encoding="utf-8")
        facade = (REPO_ROOT / "scripts/current_production_facade_v12.py").read_text(encoding="utf-8")
        self.assertIn('["semanticFreeze"]["path"]', workflow)
        self.assertIn('["semanticFreeze"]["sha256"]', workflow)
        self.assertIn("scripts/current_production_facade_v12.py", workflow)
        self.assertNotIn("scripts/chatgpt_semantic_freeze.py", workflow)
        self.assertNotIn("scripts/verify_sealed_semantic_freeze_v12.py", workflow)
        self.assertNotIn("scripts/validate_editorial_semantic_boundary.py", workflow)
        self.assertNotIn("scripts/run_semantic_frozen_renderer_closure_v12.py", workflow)
        self.assertNotIn("python3 scripts/run_daily_renderer_closure_v12.py", workflow)
        self.assertIn('"scripts/run_semantic_frozen_renderer_closure_v12.py"', facade)


if __name__ == "__main__":
    unittest.main()
