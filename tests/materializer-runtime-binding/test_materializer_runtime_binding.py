from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from materializer_runtime_binding import MaterializerRuntimeBinding  # noqa: E402


class MaterializerRuntimeBindingTests(unittest.TestCase):
    def _write_episode(
        self,
        root: Path,
        *,
        episode_date: str,
        market_date: str,
        cutoff: str,
        dossier_bytes: bytes,
    ) -> str:
        authoring = root / "daily-authoring" / f"{episode_date}.json"
        authoring.parent.mkdir(parents=True, exist_ok=True)
        authoring.write_text(
            json.dumps(
                {
                    "marketDate": market_date,
                    "informationCutoff": cutoff,
                }
            ),
            encoding="utf-8",
        )
        dossier = (
            root
            / "research"
            / episode_date
            / "causal_research_dossier.template.json"
        )
        dossier.parent.mkdir(parents=True, exist_ok=True)
        dossier.write_bytes(dossier_bytes)
        return hashlib.sha256(dossier_bytes).hexdigest()

    def test_two_dates_resolve_independently_without_source_mutation(self) -> None:
        materializer = REPO_ROOT / "scripts" / "materialize_daily_episode.py"
        source_before = hashlib.sha256(materializer.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sha_a = self._write_episode(
                root,
                episode_date="2026-08-17",
                market_date="2026-08-14",
                cutoff="2026-08-17T04:30:00+00:00",
                dossier_bytes=b"episode-a",
            )
            sha_b = self._write_episode(
                root,
                episode_date="2026-08-18",
                market_date="2026-08-17",
                cutoff="2026-08-18T04:31:00+00:00",
                dossier_bytes=b"episode-b",
            )

            binding_a = MaterializerRuntimeBinding.from_workspace(root, "2026-08-17")
            binding_b = MaterializerRuntimeBinding.from_workspace(root, "2026-08-18")

            self.assertEqual(binding_a.market_date, "2026-08-14")
            self.assertEqual(binding_b.market_date, "2026-08-17")
            self.assertEqual(binding_a.dossier_template_sha256, sha_a)
            self.assertEqual(binding_b.dossier_template_sha256, sha_b)
            self.assertNotEqual(binding_a.cli_args(), binding_b.cli_args())

        source_after = hashlib.sha256(materializer.read_bytes()).hexdigest()
        self.assertEqual(source_before, source_after)

    def test_cli_binding_contains_all_runtime_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dossier_sha = self._write_episode(
                root,
                episode_date="2026-08-17",
                market_date="2026-08-14",
                cutoff="2026-08-17T04:30:00+00:00",
                dossier_bytes=b"runtime-binding",
            )
            binding = MaterializerRuntimeBinding.from_workspace(root, "2026-08-17")
            self.assertEqual(
                binding.cli_args(),
                [
                    "--market-date",
                    "2026-08-14",
                    "--information-cutoff",
                    "2026-08-17T04:30:00+00:00",
                    "--dossier-template-sha",
                    dossier_sha,
                ],
            )

    def test_current_v2_routes_before_legacy_runtime_validation(self) -> None:
        materializer = (
            REPO_ROOT / "scripts" / "materialize_daily_episode.py"
        ).read_text(encoding="utf-8")
        v2_route = materializer.index("return _run_current_v2(root, args, authoring_probe)")
        legacy_market_validation = materializer.index(
            "if not isinstance(args.market_date, str) or not DATE_RE.fullmatch(args.market_date):"
        )
        legacy_cutoff_validation = materializer.index(
            "if not isinstance(args.information_cutoff, str) or not args.information_cutoff.strip():"
        )
        legacy_dossier_validation = materializer.index(
            "if not isinstance(args.dossier_template_sha, str) or not SHA256_RE.fullmatch(args.dossier_template_sha):"
        )
        self.assertLess(v2_route, legacy_market_validation)
        self.assertLess(v2_route, legacy_cutoff_validation)
        self.assertLess(v2_route, legacy_dossier_validation)

    def test_production_scripts_do_not_rewrite_materializer_source(self) -> None:
        legacy = (REPO_ROOT / "scripts" / "run_daily_renderer_closure.py").read_text(
            encoding="utf-8"
        )
        canonical = (
            REPO_ROOT / "scripts" / "run_daily_renderer_closure_v12.py"
        ).read_text(encoding="utf-8")
        materializer = (
            REPO_ROOT / "scripts" / "materialize_daily_episode.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn("bind_legacy_materializer", legacy)
        self.assertNotIn("bind_legacy_materializer", canonical)
        self.assertNotIn("re.subn(", legacy)
        self.assertNotIn('DOSSIER_TEMPLATE_SHA = "', materializer)
        self.assertNotIn('"--market-date", "2026-08-05"', materializer)
        self.assertNotIn('"--information-cutoff", "2026-08-06T04:27:46+00:00"', materializer)
        for flag in (
            "--market-date",
            "--information-cutoff",
            "--dossier-template-sha",
        ):
            self.assertIn(f'ap.add_argument("{flag}")', materializer)
            self.assertNotIn(f'ap.add_argument("{flag}", required=True)', materializer)
        self.assertNotIn("MaterializerRuntimeBinding.from_workspace", canonical)
        self.assertNotIn("*runtime_binding.cli_args()", canonical)
        self.assertIn('"scripts/materialize_daily_episode.py"', canonical)
        self.assertIn("materializer_runtime_args(root, date)", legacy)
        self.assertIn("*runtime_args", legacy)


if __name__ == "__main__":
    unittest.main()
