from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import chatgpt_semantic_freeze as freeze  # noqa: E402
import run_semantic_frozen_renderer_closure_v12 as frozen_closure  # noqa: E402


class ChatGPTSemanticFreezeTests(unittest.TestCase):
    def _copy_canon(self, root: Path) -> None:
        manifest = json.loads((REPO_ROOT / "source-of-truth/canon_manifest.json").read_text(encoding="utf-8"))
        for item in manifest["documents"]:
            for rel in item["storage"]["parts"]:
                src = REPO_ROOT / rel
                dst = root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
        target = root / "source-of-truth/canon_manifest.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / "source-of-truth/canon_manifest.json", target)

    def _write_sources(self, root: Path, date: str, *, narration: str = "NASDAQの矛盾を確認します。") -> None:
        self._copy_canon(root)
        parts = root / "daily-authoring-parts" / date
        parts.mkdir(parents=True, exist_ok=True)
        (parts / "00_meta.json").write_text(json.dumps({"episodeDate": date, "editorial": {"storySpine": "A→B"}}, ensure_ascii=False), encoding="utf-8")
        (parts / "06_scenes.json").write_text(json.dumps({"scenePatches": [{"sceneNumber": 1, "set": {"narration": narration}}]}, ensure_ascii=False), encoding="utf-8")
        daily = root / "daily-inputs" / date / f"daily_source_package_{date}.md"
        daily.parent.mkdir(parents=True, exist_ok=True)
        daily.write_text("# verified daily evidence\n", encoding="utf-8")

    def test_manifest_is_deterministic_schema_valid_and_binds_canon(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            date = "2026-08-17"
            self._write_sources(root, date)
            first = freeze.build_manifest(root, date)
            second = freeze.build_manifest(root, date)
            self.assertEqual(first, second)
            self.assertEqual(first["contractVersion"], "1.1.0")
            self.assertEqual(first["canonManifest"]["path"], "source-of-truth/canon_manifest.json")
            self.assertEqual(len(first["canonManifest"]["sha256"]), 64)
            schema = json.loads((REPO_ROOT / "contracts/chatgpt_semantic_freeze.schema.json").read_text(encoding="utf-8"))
            Draft202012Validator(schema).validate(first)

    def test_real_day_2026_08_12_source_set_is_freezable(self) -> None:
        manifest = freeze.build_manifest(REPO_ROOT, "2026-08-12")
        self.assertEqual(manifest["episodeDate"], "2026-08-12")
        self.assertGreater(len(manifest["parts"]), 5)
        self.assertEqual(manifest["canonManifest"]["path"], "source-of-truth/canon_manifest.json")
        self.assertEqual(len(manifest["sourceSetDigestSha256"]), 64)

    def test_semantic_change_invalidates_committed_freeze(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            date = "2026-08-17"
            self._write_sources(root, date)
            manifest_path = root / "semantic-freezes" / f"{date}.json"
            original = freeze.write_manifest(root, date, manifest_path)
            self._write_sources(root, date, narration="NASDAQの意味を別の因果へ変更します。")
            changed = freeze.build_manifest(root, date)
            self.assertNotEqual(original["sourceSetDigestSha256"], changed["sourceSetDigestSha256"])
            with self.assertRaises(freeze.SemanticFreezeError):
                freeze.verify_manifest(root, date, manifest_path)

    def test_canon_manifest_change_invalidates_committed_freeze(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            date = "2026-08-17"
            self._write_sources(root, date)
            manifest_path = root / "semantic-freezes" / f"{date}.json"
            freeze.write_manifest(root, date, manifest_path)
            canon_path = root / "source-of-truth/canon_manifest.json"
            value = json.loads(canon_path.read_text(encoding="utf-8"))
            value["documents"][0]["rawBytes"] += 1
            canon_path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(freeze.SemanticFreezeError):
                freeze.verify_manifest(root, date, manifest_path)

    def test_format_only_change_keeps_semantic_digest_but_breaks_exact_source_lineage(self) -> None:
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

    def test_canonical_workflow_requires_freeze_and_facade(self) -> None:
        workflow = (REPO_ROOT / ".github/workflows/chatgpt-daily-preview-production.yml").read_text(encoding="utf-8")
        facade = (REPO_ROOT / "scripts/current_production_facade_v12.py").read_text(encoding="utf-8")
        self.assertIn('["semanticFreeze"]["path"]', workflow)
        self.assertIn('["semanticFreeze"]["sha256"]', workflow)
        self.assertIn("scripts/chatgpt_semantic_freeze.py", workflow)
        self.assertIn("scripts/current_production_facade_v12.py", workflow)
        self.assertNotIn("scripts/run_semantic_frozen_renderer_closure_v12.py", workflow)
        self.assertNotIn("python3 scripts/run_daily_renderer_closure_v12.py", workflow)
        self.assertIn('"scripts/run_semantic_frozen_renderer_closure_v12.py"', facade)


if __name__ == "__main__":
    unittest.main()
