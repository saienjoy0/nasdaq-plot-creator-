from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "skills/nasdaq-cafe-episode-package-memory/validators/validate_episode_package_memory_hardening.py"
spec = importlib.util.spec_from_file_location("episode_memory_hardening", VALIDATOR)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class StubResult:
    def __init__(self, errors=None, warnings=None):
        self.errors = errors or []
        self.warnings = warnings or []


def base_pass(repo_root: Path, package: Path):
    return StubResult()


def base_fail(repo_root: Path, package: Path):
    return StubResult(["forced base failure"])


def annex(date="2026-08-06"):
    return {
        "contract_version": "1.0.0",
        "episode_date": date,
        "causal_dossier": {"path": "research/x.json", "sha256": "0" * 64},
        "references": [],
        "validation_intent": {
            "past_mentions_complete": True,
            "title_thumbnail_checked": True,
            "post_inquisition_final": True,
        },
    }


def build_package(*, scenes=None, include_inquisition=True, tail="", date="2026-08-06", final_annex=False):
    scenes = list(range(1, 10)) if scenes is None else scenes
    blocks = [f"## B. Scene {number}｜Test\n### ナレーション\nScene {number}.\n" for number in scenes]
    if include_inquisition:
        blocks.append(
            "# 04 興味深さ・わかりやすさ審問結果\n"
            "## 判定\n合格\n## 必須修正\nなし\n"
        )
    blocks.append(
        "## I. Editorial Memory Usage Annex\n"
        "<!--BEGIN_EPISODE_MEMORY_ANNEX-->\n"
        "```json\n"
        + json.dumps(annex(date), ensure_ascii=False, indent=2)
        + "\n```\n"
        "<!--END_EPISODE_MEMORY_ANNEX-->"
    )
    text = "\n".join(blocks)
    if final_annex:
        text += "\n<!--BEGIN_FINAL_PRODUCTION_SOURCE-->\n```json\n{}\n```\n<!--END_FINAL_PRODUCTION_SOURCE-->"
    return text + tail


class HardeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "episodes").mkdir()
        self.package = self.root / "episodes/episode_package_2026-08-06.md"
        self.package.write_text(build_package(), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def validate(self, *, base_runner=base_pass, public_artifacts=()):
        return module.validate_hardening(
            repo_root=self.root,
            episode_package=self.package,
            public_artifacts=public_artifacts,
            base_runner=base_runner,
        )

    def assertFail(self, needle, **kwargs):
        result = self.validate(**kwargs)
        self.assertTrue(any(needle in item for item in result.errors), result.errors)

    def test_01_valid_final_package_passes(self):
        self.assertEqual([], self.validate().errors)

    def test_02_only_final_source_annex_may_follow_memory_annex(self):
        self.package.write_text(build_package(tail="\n## Extra\nnot allowed\n"), encoding="utf-8")
        self.assertFail("only one Final Production Source annex")

    def test_02b_final_source_annex_after_memory_passes(self):
        self.package.write_text(build_package(final_annex=True), encoding="utf-8")
        self.assertEqual([], self.validate().errors)

    def test_02c_final_source_annex_must_be_last(self):
        self.package.write_text(build_package(final_annex=True, tail="\nextra"), encoding="utf-8")
        self.assertFail("must be the final section")

    def test_03_all_nine_scenes_required(self):
        self.package.write_text(build_package(scenes=list(range(1, 9))), encoding="utf-8")
        self.assertFail("Scene 1 through Scene 9")

    def test_04_duplicate_scene_rejected(self):
        self.package.write_text(build_package(scenes=[1, 2, 3, 4, 5, 5, 6, 7, 8, 9]), encoding="utf-8")
        self.assertFail("exactly once and in order")

    def test_05_out_of_order_scene_rejected(self):
        self.package.write_text(build_package(scenes=[1, 2, 4, 3, 5, 6, 7, 8, 9]), encoding="utf-8")
        self.assertFail("exactly once and in order")

    def test_06_inquisition_required(self):
        self.package.write_text(build_package(include_inquisition=False), encoding="utf-8")
        self.assertFail("exactly one integrated")

    def test_07_duplicate_inquisition_rejected(self):
        text = build_package().replace(
            "# 04 興味深さ・わかりやすさ審問結果",
            "# 04 興味深さ・わかりやすさ審問結果\n# 04 興味深さ・わかりやすさ審問結果",
        )
        self.package.write_text(text, encoding="utf-8")
        self.assertFail("found=2")

    def test_08_filename_date_must_match(self):
        wrong = self.root / "episodes/episode_package_2026-08-07.md"
        wrong.write_text(build_package(), encoding="utf-8")
        self.package = wrong
        self.assertFail("filename must contain")

    def test_09_base_validator_failure_propagates(self):
        self.assertFail("forced base failure", base_runner=base_fail)

    def test_10_public_spoken_script_must_not_leak_marker(self):
        spoken = self.root / "spoken.md"
        spoken.write_text("hello <!--MEMREF:MR-001:U-001-->", encoding="utf-8")
        self.assertFail("internal episode-memory metadata", public_artifacts=[spoken])

    def test_11_public_render_spec_must_not_leak_annex(self):
        render = self.root / "render_spec.json"
        render.write_text('{"text":"<!--BEGIN_EPISODE_MEMORY_ANNEX-->"}', encoding="utf-8")
        self.assertFail("internal episode-memory metadata", public_artifacts=[render])

    def test_12_public_artifact_must_not_leak_reference_fields(self):
        artifact = self.root / "captions.json"
        artifact.write_text('{"memory_reference_id":"x"}', encoding="utf-8")
        self.assertFail("memory_reference_id", public_artifacts=[artifact])

    def test_13_clean_public_artifacts_pass(self):
        spoken = self.root / "spoken.md"
        render = self.root / "render_spec.json"
        spoken.write_text("狐の公開ナレーション", encoding="utf-8")
        render.write_text('{"text":"公開テロップ"}', encoding="utf-8")
        self.assertEqual([], self.validate(public_artifacts=[spoken, render]).errors)

    def test_14_public_artifact_outside_repo_rejected(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as handle:
            outside = Path(handle.name)
            handle.write("clean")
        try:
            self.assertFail("escapes repository root", public_artifacts=[outside])
        finally:
            outside.unlink(missing_ok=True)

    def test_15_malformed_annex_fails_closed(self):
        self.package.write_text(
            build_package().replace('"contract_version": "1.0.0"', '"contract_version":'),
            encoding="utf-8",
        )
        self.assertFail("invalid episode memory annex JSON")


if __name__ == "__main__":
    unittest.main()
