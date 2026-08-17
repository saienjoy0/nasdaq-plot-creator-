from __future__ import annotations

import hashlib
import json
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
    def _write_sources(
        self,
        root: Path,
        date: str,
        *,
        narration: str = "NASDAQの矛盾を確認します。",
    ) -> None:
        parts = root / "daily-authoring-parts" / date
        parts.mkdir(parents=True, exist_ok=True)
        (parts / "00_meta.json").write_text(
            json.dumps({"episodeDate": date, "editorial": {"storySpine": "A→B"}}, ensure_ascii=False),
            encoding="utf-8",
        )
        (parts / "06_scenes.json").write_text(
            json.dumps({"scenePatches": [{"sceneNumber": 1, "set": {"narration": narration}}]}, ensure_ascii=False),
            encoding="utf-8",
        )
        daily = root / "daily-inputs" / date / f"daily_source_package_{date}.md"
        daily.parent.mkdir(parents=True, exist_ok=True)
        daily.write_text("# verified daily evidence\n", encoding="utf-8")

    def test_manifest_is_deterministic_and_schema_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            date = "2026-08-17"
            self._write_sources(root, date)
            first = freeze.build_manifest(root, date)
            second = freeze.build_manifest(root, date)
            self.assertEqual(first, second)
            schema = json.loads(
                (REPO_ROOT / "contracts" / "chatgpt_semantic_freeze.schema.json").read_text(
                    encoding="utf-8"
                )
            )
            Draft202012Validator(schema).validate(first)

    def test_semantic_change_invalidates_committed_freeze(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            date = "2026-08-17"
            self._write_sources(root, date)
            manifest_path = root / "semantic-freezes" / f"{date}.json"
            original = freeze.write_manifest(root, date, manifest_path)
            self._write_sources(root, date, narration="NASDAQの意味を別の因果へ変更します。")
            changed = freeze.build_manifest(root, date)
            self.assertNotEqual(
                original["sourceSetDigestSha256"], changed["sourceSetDigestSha256"]
            )
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
            self.assertEqual(
                original["sourceSetDigestSha256"], changed["sourceSetDigestSha256"]
            )
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
            self.assertTrue(all("2026-08-17" in item["path"] for item in a["parts"]))
            self.assertTrue(all("2026-08-18" in item["path"] for item in b["parts"]))

    def test_ai_b_artifacts_must_bind_same_manifest_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            date = "2026-08-17"
            vi = root / "working" / date / "visual-intelligence"
            vi.mkdir(parents=True, exist_ok=True)
            expected = "a" * 64
            (vi / "visual_requirements.json").write_text(
                json.dumps({"semanticFreezeSha256": "b" * 64}), encoding="utf-8"
            )
            pause = frozen_closure.semantic_binding_pause(
                root, date, phase="compile", semantic_freeze_sha256=expected
            )
            self.assertEqual(pause[0], "AUTHOR_VISUAL_REQUIREMENTS")

            (vi / "visual_requirements.json").write_text(
                json.dumps({"semanticFreezeSha256": expected}), encoding="utf-8"
            )
            pause = frozen_closure.semantic_binding_pause(
                root, date, phase="compile", semantic_freeze_sha256=expected
            )
            self.assertEqual(pause[0], "AUTHOR_VISUAL_INTELLIGENCE_DECISION")

            (vi / "visual_intelligence_decision.json").write_text(
                json.dumps({"semanticFreezeSha256": "c" * 64}), encoding="utf-8"
            )
            pause = frozen_closure.semantic_binding_pause(
                root, date, phase="compile", semantic_freeze_sha256=expected
            )
            self.assertEqual(pause[0], "RESELECT_VISUAL_CANDIDATES")

            (vi / "visual_intelligence_decision.json").write_text(
                json.dumps({"semanticFreezeSha256": expected}), encoding="utf-8"
            )
            self.assertIsNone(
                frozen_closure.semantic_binding_pause(
                    root, date, phase="compile", semantic_freeze_sha256=expected
                )
            )

    def test_canonical_workflow_requires_freeze_and_wrapper(self) -> None:
        workflow = (
            REPO_ROOT / ".github" / "workflows" / "chatgpt-daily-preview-production.yml"
        ).read_text(encoding="utf-8")
        self.assertIn('["semanticFreeze"]["path"]', workflow)
        self.assertIn('["semanticFreeze"]["sha256"]', workflow)
        self.assertIn("scripts/chatgpt_semantic_freeze.py", workflow)
        self.assertIn("scripts/run_semantic_frozen_renderer_closure_v12.py", workflow)
        self.assertNotIn(
            "python3 scripts/run_daily_renderer_closure_v12.py \\\n            --phase compile",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
