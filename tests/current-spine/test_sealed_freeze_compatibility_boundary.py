from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import verify_sealed_semantic_freeze_v12 as sealed_freeze  # noqa: E402


class SealedFreezeCompatibilityBoundaryTests(unittest.TestCase):
    def _real_manifest(self) -> Path:
        return REPO_ROOT / "semantic-freezes/2026-08-17.json"

    def test_real_2026_08_17_freeze_remains_valid_as_sealed_editorial_identity(self) -> None:
        manifest = sealed_freeze.verify_manifest(REPO_ROOT, "2026-08-17", self._real_manifest())
        self.assertEqual(manifest["contractVersion"], "1.2.0")
        self.assertEqual(manifest["episodeDate"], "2026-08-17")

    def test_sealed_verifier_is_path_stable_when_loaded_from_story_engine_context(self) -> None:
        code = f"""
import importlib.util
import sys
from pathlib import Path
root = Path({str(REPO_ROOT)!r})
path = root / 'scripts/verify_sealed_semantic_freeze_v12.py'
spec = importlib.util.spec_from_file_location('sealed_freeze_dynamic_context', path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
manifest = module.verify_manifest(root, '2026-08-17', root / 'semantic-freezes/2026-08-17.json')
assert manifest['episodeDate'] == '2026-08-17'
"""
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=REPO_ROOT / "scripts/story-engine",
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_current_contract_byte_change_does_not_retroactively_invalidate_seal(self) -> None:
        schema = REPO_ROOT / "contracts/chatgpt_daily_authoring_v2.schema.json"
        original = schema.read_bytes()
        try:
            schema.write_bytes(original + b"\n")
            manifest = sealed_freeze.verify_manifest(
                REPO_ROOT, "2026-08-17", self._real_manifest()
            )
            self.assertEqual(manifest["episodeDate"], "2026-08-17")
        finally:
            schema.write_bytes(original)

    def test_frozen_authoring_byte_change_invalidates_seal(self) -> None:
        authoring = REPO_ROOT / "daily-authoring/2026-08-17.json"
        original = authoring.read_bytes()
        try:
            authoring.write_bytes(original + b"\n")
            with self.assertRaises(sealed_freeze.SealedSemanticFreezeError):
                sealed_freeze.verify_manifest(REPO_ROOT, "2026-08-17", self._real_manifest())
        finally:
            authoring.write_bytes(original)

    def test_production_wrapper_uses_sealed_verifier_not_dynamic_rebuild(self) -> None:
        wrapper = (REPO_ROOT / "scripts/run_semantic_frozen_renderer_closure_v12.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("verify_sealed_semantic_freeze_v12.verify_manifest", wrapper)
        self.assertNotIn("chatgpt_semantic_freeze.verify_manifest", wrapper)

    def test_current_compatibility_remains_owned_by_current_renderer_closure(self) -> None:
        closure = (REPO_ROOT / "scripts/run_daily_renderer_closure_v12.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("scripts/validate_chatgpt_daily_authoring_closure.py", closure)
        self.assertIn("scripts/materialize_chatgpt_daily_authoring.py", closure)


if __name__ == "__main__":
    unittest.main()
