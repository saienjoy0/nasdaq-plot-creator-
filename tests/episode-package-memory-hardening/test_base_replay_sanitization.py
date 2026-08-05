from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "skills/nasdaq-cafe-episode-package-memory/validators/validate_episode_package_memory_hardening.py"
spec = importlib.util.spec_from_file_location("episode_memory_hardening_sanitize", VALIDATOR)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class Result:
    errors = []
    warnings = []


class Tests(unittest.TestCase):
    def test_final_production_annex_is_removed_only_for_base_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "episode_package_2026-08-06.md"
            package.write_text(
                "public\n"
                "<!--BEGIN_EPISODE_MEMORY_ANNEX-->\n"
                "```json\n{}\n```\n"
                "<!--END_EPISODE_MEMORY_ANNEX-->\n"
                "<!--BEGIN_FINAL_PRODUCTION_SOURCE-->\n"
                "```json\n{\"private\":true}\n```\n"
                "<!--END_FINAL_PRODUCTION_SOURCE-->\n",
                encoding="utf-8",
            )
            seen = {}

            def validate_episode_package_memory(*, repo_root, episode_package_path):
                seen["path"] = episode_package_path
                seen["text"] = episode_package_path.read_text(encoding="utf-8")
                self.assertNotEqual(package, episode_package_path)
                self.assertNotIn(module.FINAL_BEGIN, seen["text"])
                self.assertTrue(seen["text"].rstrip().endswith(module.ANNEX_END))
                return Result()

            original = module._load_base_validator
            module._load_base_validator = lambda repo_root: SimpleNamespace(
                validate_episode_package_memory=validate_episode_package_memory
            )
            try:
                result = module._run_base_validator(root, package)
            finally:
                module._load_base_validator = original

            self.assertEqual([], result.errors)
            self.assertTrue(package.exists())
            self.assertFalse(seen["path"].exists())
            self.assertIn(module.FINAL_BEGIN, package.read_text(encoding="utf-8"))

    def test_malformed_final_annex_fails_before_validation_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "episode_package_2026-08-06.md"
            package.write_text(
                "<!--BEGIN_EPISODE_MEMORY_ANNEX-->\n"
                "```json\n{}\n```\n"
                "<!--END_EPISODE_MEMORY_ANNEX-->\n"
                "<!--BEGIN_FINAL_PRODUCTION_SOURCE-->\n",
                encoding="utf-8",
            )
            validation_called = False

            def validate_episode_package_memory(*, repo_root, episode_package_path):
                nonlocal validation_called
                validation_called = True
                return Result()

            original = module._load_base_validator
            module._load_base_validator = lambda repo_root: SimpleNamespace(
                validate_episode_package_memory=validate_episode_package_memory
            )
            try:
                with self.assertRaises(RuntimeError):
                    module._run_base_validator(root, package)
            finally:
                module._load_base_validator = original

            self.assertFalse(validation_called)


if __name__ == "__main__":
    unittest.main()
