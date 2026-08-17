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

import canon_manifest as canon  # noqa: E402


EXPECTED = {
    "01": ("source-of-truth/01_fox_character_bible.md", "95c3d6adad23325b39e34477daf0628a2773cc63fdb89193e263f2a11b97a618", 19355),
    "02": ("source-of-truth/02_editorial_bible.md", "de6e6592a587e484bbce102d78ffd927ff98d58f4f195ddad734a73025631dc2", 29382),
    "03": ("source-of-truth/03_episode_production_spec.md", "c0e476f36b387961277ffa008d7b2258942e1fe44c475bebe1d79b31b9f4dc3f", 101040),
    "04": ("source-of-truth/04_entertainment_inquisitor.md", "62d7807eb01b3433fc3b3f8bce8f6bad96109f1ae2366ec417c35bac8fa47936", 45895),
}


class CanonManifestTests(unittest.TestCase):
    def test_repository_manifest_is_exact_and_verifies_all_four_documents(self) -> None:
        result = canon.verify(REPO_ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual([item["id"] for item in result["documents"]], ["01", "02", "03", "04"])
        manifest = canon.load_manifest(REPO_ROOT)
        for item in manifest["documents"]:
            path, digest, size = EXPECTED[item["id"]]
            self.assertEqual(item["logicalPath"], path)
            self.assertEqual(item["sha256"], digest)
            self.assertEqual(item["rawBytes"], size)

    def test_manifest_matches_json_schema(self) -> None:
        manifest = canon.load_manifest(REPO_ROOT)
        schema = json.loads((REPO_ROOT / "contracts/canon_manifest.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(manifest)

    def test_unsafe_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(canon.CanonManifestError):
                canon._safe_path(Path(tmp), "../outside.md", "test", must_exist=False)

    def test_materialization_reconstructs_03_and_04_without_changing_logical_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = canon.load_manifest(REPO_ROOT)
            for item in manifest["documents"]:
                for rel in item["storage"]["parts"]:
                    src = REPO_ROOT / rel
                    dst = root / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dst)
            manifest_path = root / canon.DEFAULT_MANIFEST
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / canon.DEFAULT_MANIFEST, manifest_path)
            result = canon.materialize(root)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["materialized"], [EXPECTED["03"][0], EXPECTED["04"][0]])
            for doc_id in ("03", "04"):
                path, digest, size = EXPECTED[doc_id]
                data = (root / path).read_bytes()
                self.assertEqual(canon.sha256_bytes(data), digest)
                self.assertEqual(len(data), size)

    def test_single_manifest_is_the_only_packed_source_authority(self) -> None:
        self.assertFalse((REPO_ROOT / "source-of-truth/packed_sources.json").exists())
        materializer = (REPO_ROOT / "scripts/materialize_sources.py").read_text(encoding="utf-8")
        self.assertIn("DEFAULT_MANIFEST", materializer)
        self.assertNotIn("packed_sources.json", materializer)
        workflow = (REPO_ROOT / ".github/workflows/verify-source-materialization.yml").read_text(encoding="utf-8")
        self.assertIn("scripts/canon_manifest.py verify", workflow)
        for _, digest, _ in EXPECTED.values():
            self.assertNotIn(digest, workflow)


if __name__ == "__main__":
    unittest.main()
