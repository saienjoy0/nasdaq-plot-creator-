from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from canon_manifest import document_bytes, load_manifest
from run_exact_cross_repo_current_e2e import verify_authoring_runtime_policy


class AuthoringRuntimePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        document = next(item for item in load_manifest(ROOT)["documents"] if item["id"] == "03")
        cls.text = document_bytes(ROOT, document).decode("utf-8")
        cls.model = re.search(r"Gemini TTS `([^`]+)`", cls.text).group(1)
        bounds = re.search(r"\*\*実音声(\d+)〜(\d+)秒\*\*", cls.text)
        cls.lower, cls.upper = (int(value) for value in bounds.groups())

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.renderer = Path(temporary.name)
        (self.renderer / "config").mkdir()
        (self.renderer / "scripts").mkdir()
        profile = {"provider": "gemini", "model": self.model, "voice": "Charon", "provisional": False}
        (self.renderer / "config/voice-profiles.json").write_text(
            json.dumps({"profiles": {"fox-main": profile, "gemini-charon": profile}}), encoding="utf-8"
        )
        (self.renderer / "scripts/duration-policy.ts").write_text(
            f"export const STANDARD_DURATION_MIN_MS = {self.lower * 1000};\n"
            f"export const STANDARD_DURATION_MAX_MS = {self.upper * 1000};\n",
            encoding="utf-8",
        )

    def verify_text(self, text: str) -> dict:
        with patch("canon_manifest.document_bytes", return_value=text.encode("utf-8")):
            return verify_authoring_runtime_policy(self.renderer)

    def assert_rejected(self, original: str, replacement: str, message: str) -> None:
        self.assertIn(original, self.text)
        changed = self.text.replace(original, replacement)
        self.assertNotEqual(changed, self.text)
        with self.assertRaisesRegex(AssertionError, message):
            self.verify_text(changed)

    def test_current_canon_is_consistent_with_its_runtime_policy(self) -> None:
        result = self.verify_text(self.text)
        self.assertEqual(result["authoringRuntimePolicy"], "PASS")
        self.assertEqual(result["standardDurationSeconds"], [self.lower, self.upper])

    def test_changing_every_authoring_voice_is_rejected(self) -> None:
        self.assert_rejected("Charon", "Puck", "voice policy mismatch")

    def test_one_contradictory_quoted_voice_is_rejected(self) -> None:
        self.assert_rejected("音声`Charon`", "音声`Puck`", "voice policy mismatch")

    def test_model_followed_by_japanese_is_checked(self) -> None:
        self.assert_rejected(
            f"Gemini TTS {self.model}のCharon", "Gemini TTS gemini-99.0-flash-ttsのCharon", "TTS policy mismatch"
        )

    def test_final_directive_voice_is_checked(self) -> None:
        self.assert_rejected(f"{self.model}のCharon", f"{self.model}のPuck", "voice policy mismatch")

    def test_stale_checklist_range_is_rejected(self) -> None:
        self.assert_rejected(
            f"通常回はCharon実音声{self.lower}〜{self.upper}秒", "通常回はCharon実音声480〜540秒", "duration policy mismatch"
        )

    def test_contradictory_shortened_boundary_is_rejected(self) -> None:
        self.assert_rejected(f"実音声が{self.lower}秒未満で", f"実音声が{self.lower - 1}秒未満で", "shortened boundary")

    def test_contradictory_upper_boundary_is_rejected(self) -> None:
        self.assert_rejected(f"実音声が{self.upper}秒を超えた", f"実音声が{self.upper + 1}秒を超えた", "upper boundary")

    def test_incorrect_scene_budget_total_is_rejected(self) -> None:
        ranges = re.findall(r"^\| [1-9] \| (\d+)〜(\d+)秒 \|", self.text, re.MULTILINE)
        lower = sum(int(low) for low, _ in ranges)
        upper = sum(int(high) for _, high in ranges)
        self.assert_rejected(f"合計{lower}〜{upper}秒", f"合計{lower}〜{upper + 1}秒", "writing-budget total mismatch")


if __name__ == "__main__":
    unittest.main()
