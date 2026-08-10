from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from research_evidence_supplement import (  # noqa: E402
    SupplementError,
    append_wave,
    validate_manifest,
)

SCHEMA = ROOT / "skills/nasdaq-cafe-causal-research/contracts/research_evidence_supplement_manifest.schema.json"
DATE = "2026-08-06"


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ResearchEvidenceSupplementTest(unittest.TestCase):
    def setUp(self) -> None:
        (ROOT / "working").mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix="research-supplement-", dir=ROOT / "working"))
        self.base = self.tmp / "research_input_manifest.json"
        self.request = self.tmp / "research_acquisition_request_w01.json"
        self.result = self.tmp / "research_acquisition_result_w01.json"
        self.evidence = self.tmp / "RA-001_intraday_series.json"
        self.manifest = self.tmp / "research_evidence_supplement_manifest.json"
        write_json(self.base, {"episode_date": DATE})
        write_json(
            self.request,
            {
                "contractVersion": "1.0.0",
                "episodeDate": DATE,
                "wave": 1,
                "baseResearchInputManifestSha256": sha256(self.base),
                "researchPurpose": "timeline test",
                "requests": [
                    {
                        "requestId": "RA-001",
                        "type": "market_intraday",
                        "reason": "event timing",
                        "requiredness": "material",
                        "parameters": {
                            "symbol": "AMD.US",
                            "date": "2026-08-05",
                            "resolution": "1m",
                            "session": "all",
                        },
                    }
                ],
            },
        )
        write_json(
            self.evidence,
            {
                "source": "Longbridge",
                "symbol": "AMD.US",
                "precision": "verified-intraday-series",
                "points": [{"timestamp": "2026-08-05T20:00:00Z", "price": 100.0}],
            },
        )
        write_json(
            self.result,
            {
                "contractVersion": "1.0.0",
                "episodeDate": DATE,
                "wave": 1,
                "requestSha256": sha256(self.request),
                "status": "success",
                "results": [
                    {
                        "requestId": "RA-001",
                        "status": "success",
                        "provider": "Longbridge",
                        "outputPath": "followup/RA-001_intraday_series.json",
                        "sha256": sha256(self.evidence),
                        "recordCount": 1,
                        "reason": "",
                    }
                ],
            },
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def append(self, wave: int = 1) -> dict:
        return append_wave(
            manifest_path=self.manifest,
            repo_root=ROOT,
            episode_date=DATE,
            base_manifest_path=self.base,
            wave=wave,
            request_path=self.request,
            result_path=self.result,
            evidence_bindings=[f"RA-001={self.evidence.relative_to(ROOT)}"],
            collector_run_id=12345,
            schema_path=SCHEMA,
        )

    def test_valid_wave_is_sha_bound_and_validates(self) -> None:
        manifest = self.append()
        self.assertEqual(1, len(manifest["waves"]))
        validated = validate_manifest(self.manifest, repo_root=ROOT, schema_path=SCHEMA)
        self.assertEqual(DATE, validated["episodeDate"])
        self.assertEqual(sha256(self.base), validated["baseResearchInputManifest"]["sha256"])

    def test_tampered_evidence_is_rejected(self) -> None:
        self.append()
        self.evidence.write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(SupplementError, "SHA"):
            validate_manifest(self.manifest, repo_root=ROOT, schema_path=SCHEMA)

    def test_base_manifest_replacement_is_rejected(self) -> None:
        self.append()
        write_json(self.base, {"episode_date": DATE, "changed": True})
        with self.assertRaisesRegex(SupplementError, "baseResearchInputManifest SHA"):
            validate_manifest(self.manifest, repo_root=ROOT, schema_path=SCHEMA)

    def test_successful_result_without_evidence_copy_is_rejected(self) -> None:
        self.append()
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["waves"][0]["evidenceFiles"] = []
        write_json(self.manifest, manifest)
        with self.assertRaisesRegex(SupplementError, "exactly match successful results"):
            validate_manifest(self.manifest, repo_root=ROOT, schema_path=SCHEMA)

    def test_duplicate_wave_is_rejected(self) -> None:
        self.append()
        with self.assertRaisesRegex(SupplementError, "already exists"):
            self.append()

    def test_wave_three_is_rejected(self) -> None:
        with self.assertRaisesRegex(SupplementError, "wave must be"):
            self.append(wave=3)

    def test_result_bound_to_wrong_request_is_rejected(self) -> None:
        result = json.loads(self.result.read_text(encoding="utf-8"))
        result["requestSha256"] = "0" * 64
        write_json(self.result, result)
        with self.assertRaisesRegex(SupplementError, "requestSha256"):
            self.append()

    def test_non_success_result_cannot_claim_evidence(self) -> None:
        result = json.loads(self.result.read_text(encoding="utf-8"))
        result["status"] = "unavailable"
        result["results"][0]["status"] = "unavailable"
        result["results"][0]["sha256"] = None
        result["results"][0]["outputPath"] = None
        result["results"][0]["recordCount"] = 0
        result["results"][0]["reason"] = "unavailable"
        write_json(self.result, result)
        with self.assertRaisesRegex(SupplementError, "non-success"):
            self.append()


if __name__ == "__main__":
    unittest.main()
