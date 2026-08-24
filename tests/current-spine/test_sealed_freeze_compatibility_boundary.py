from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import chatgpt_semantic_freeze as dynamic_freeze  # noqa: E402
import verify_sealed_semantic_freeze_v12 as sealed_freeze  # noqa: E402


class SealedFreezeCompatibilityBoundaryTests(unittest.TestCase):
    def test_real_2026_08_17_freeze_remains_valid_as_sealed_editorial_identity(self) -> None:
        path = REPO_ROOT / "semantic-freezes/2026-08-17.json"
        manifest = sealed_freeze.verify_manifest(REPO_ROOT, "2026-08-17", path)
        self.assertEqual(manifest["contractVersion"], "1.2.0")
        self.assertEqual(manifest["episodeDate"], "2026-08-17")

    def test_old_dynamic_verifier_exposes_the_contract_evolution_coupling(self) -> None:
        path = REPO_ROOT / "semantic-freezes/2026-08-17.json"
        with self.assertRaises(dynamic_freeze.SemanticFreezeError):
            dynamic_freeze.verify_manifest(REPO_ROOT, "2026-08-17", path)

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
