import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
VALIDATORS = ROOT / "skills" / "nasdaq-cafe-causal-research" / "validators"
for path in (SCRIPTS, VALIDATORS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_research_input_manifest import ManifestBuildError, build_manifest  # noqa: E402
from validate_causal_research_dossier import validate_dossier  # noqa: E402

CONTRACTS = ROOT / "skills" / "nasdaq-cafe-causal-research" / "contracts"
FIXTURES = ROOT / "tests" / "memory-revalidation" / "fixtures"
DATE = "2026-08-06"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MemoryRevalidationBridgeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.daily = self.tmp / f"daily/daily_source_package_{DATE}.md"
        self.query = self.tmp / f"working/memory_query_plan_{DATE}.json"
        self.context = self.tmp / f"working/memory_context_{DATE}.md"
        self.report = self.tmp / f"working/memory_retrieval_report_{DATE}.json"
        for source, target in (
            (FIXTURES / f"daily_source_package_{DATE}.md", self.daily),
            (FIXTURES / f"memory_query_plan_{DATE}.json", self.query),
            (FIXTURES / f"memory_context_{DATE}.md", self.context),
            (FIXTURES / f"memory_retrieval_report_{DATE}.json", self.report),
        ):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        self.manifest = self.tmp / f"research/{DATE}/research_input_manifest.json"
        self.dossier = self.tmp / f"research/{DATE}/causal_research_dossier_{DATE}.json"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def build_manifest(self):
        return build_manifest(
            episode_date=DATE,
            market_date="2026-08-05",
            timezone="Asia/Tokyo",
            information_cutoff="2026-08-06T07:30:00+09:00",
            daily_source_package=self.daily,
            memory_query_plan=self.query,
            memory_context=self.context,
            memory_retrieval_report=self.report,
            output=self.manifest,
            contracts_dir=CONTRACTS,
        )

    def base_dossier(self, status="supported", current_ids=None):
        self.build_manifest()
        current_ids = ["E-001"] if current_ids is None else current_ids
        dossier = {
            "contract_version": "0.2.0",
            "episode_date": DATE,
            "session": {
                "market_date": "2026-08-05",
                "timezone": "Asia/Tokyo",
                "information_cutoff": "2026-08-06T07:30:00+09:00",
            },
            "input_provenance": [{
                "path_or_reference": self.daily.as_posix(),
                "role": "daily_input",
                "version_or_hash": sha256(self.daily),
            }],
            "research_input_manifest": {
                "path": self.manifest.as_posix(),
                "sha256": sha256(self.manifest),
            },
            "contradictions": [{
                "id": "CON-01",
                "statement": "AI投資は増えたが、株価反応は限定的だった。",
                "rank": 1,
                "selection_reason": "投資と市場評価のずれを説明するため。",
            }],
            "research_questions": [{
                "id": "Q-01",
                "perspective": "official_evidence",
                "question": "当日の公式資料は売上回収を示すか。",
                "parent_question_id": None,
                "status": "answered",
                "answer_summary": "AWS売上成長が確認された。",
                "evidence_ids": ["E-001"],
            }],
            "evidence": [
                {
                    "evidence_id": "E-001",
                    "claim": "当日の公式資料でクラウド売上成長が確認された。",
                    "evidence_class": "fact",
                    "source_tier": "tier_1",
                    "source_title": "Current earnings release",
                    "source_issuer_or_publisher": "Example issuer",
                    "source_reference": "https://example.invalid/current-release",
                    "event_timestamp": "2026-08-05T16:00:00-04:00",
                    "publication_timestamp": "2026-08-05T16:00:00-04:00",
                    "timezone": "America/New_York",
                    "directness": "direct",
                    "independence_group": "issuer-release",
                    "confidence": "high",
                    "limitations": "",
                },
                {
                    "evidence_id": "E-002",
                    "claim": "市場報道は投資回収への懸念を伝えた。",
                    "evidence_class": "reported_interpretation",
                    "source_tier": "tier_2",
                    "source_title": "Current market report",
                    "source_issuer_or_publisher": "Example publisher",
                    "source_reference": "https://example.invalid/current-report",
                    "event_timestamp": None,
                    "publication_timestamp": "2026-08-05T18:00:00-04:00",
                    "timezone": "America/New_York",
                    "directness": "supporting",
                    "independence_group": "publisher-report",
                    "confidence": "medium",
                    "limitations": "市場解釈であり公式説明ではない。",
                },
            ],
            "memory_revalidation": [{
                "memory_reference_type": "claim",
                "memory_reference_id": "ai-capex-evaluation-axis",
                "historical_confidence": "medium",
                "retrieval_use_mode": "current_revalidation_required",
                "revalidation_status": status,
                "current_evidence_ids": current_ids,
                "difference_from_previous": "当日は公式売上データで再検証した。",
                "editorial_use": "not_used" if status == "not_used" else "research_lead",
                "notes": "過去仮説を現在証拠へ直接変換していない。",
            }],
            "expected_actual_gap": {
                "expected": {
                    "status": "confirmed",
                    "basis_class": "prior_company_guidance",
                    "statement": "市場はクラウド成長の継続を見込んでいた。",
                    "evidence_ids": ["E-001"],
                },
                "actual": {
                    "statement": "当日の公式資料はクラウド成長を示した。",
                    "evidence_ids": ["E-001"],
                },
                "gap": {
                    "statement": "成長確認だけでは投資回収懸念を消せなかった。",
                    "market_meaning": "評価軸が売上成長から回収速度へ移った可能性。",
                    "confidence": "medium",
                },
            },
            "timeline": [{
                "id": "T-01",
                "timestamp_or_window": "2026-08-05 after hours",
                "timezone": "America/New_York",
                "event": "公式資料公表",
                "precision": "session",
                "evidence_ids": ["E-001"],
            }],
            "causal_edges": [{
                "id": "EDGE-01",
                "from_node": "AI設備投資",
                "to_node": "NASDAQ大型テック評価",
                "mechanism": "投資回収への懸念",
                "evidence_ids": ["E-001", "E-002"],
                "timing_alignment": "partial",
                "confidence": "medium",
                "strongest_alternative": "金利要因",
                "editorially_required": True,
                "scope": "nasdaq_wide",
            }],
            "factor_roles": {
                "primary_candidate": "投資回収への懸念",
                "amplifiers": ["金利"],
                "offsetting": ["クラウド売上成長"],
                "unresolved": [],
            },
            "alternative_hypotheses": [{
                "id": "ALT-01",
                "hypothesis": "金利だけで大型テックが動いた。",
                "supporting_evidence_ids": [],
                "weakening_evidence_ids": ["E-001"],
                "status": "weakened",
            }],
            "contrary_evidence": [{
                "statement": "クラウド売上は成長した。",
                "evidence_ids": ["E-001"],
                "effect_on_confidence": "material",
            }],
            "editorial_handoff": {
                "provisional_lead": "AI投資回収への評価",
                "central_hypothesis": "売上成長より投資回収速度が重視された。",
                "confidence": "medium",
                "company_direct_material": ["クラウド売上"],
                "nasdaq_wide_material": ["大型テック評価"],
                "causal_spine": "投資増加→回収懸念→大型テック評価",
                "headline_beyond_discovery": "成長の有無ではなく回収速度が焦点。",
                "exclude_from_narration": [],
                "unresolved_questions": [],
                "next_validation_points": ["次回ガイダンス"],
                "memory_differences": ["過去仮説を当日証拠で再検証した。"],
            },
            "validation": {"status": "pass", "errors": [], "warnings": []},
        }
        write_json(self.dossier, dossier)
        return dossier

    def validate(self):
        return validate_dossier(
            self.dossier,
            self.manifest,
            self.report,
            contracts_dir=CONTRACTS,
            repo_root=self.tmp,
        )

    def rewrite_dossier(self, dossier):
        dossier["research_input_manifest"]["sha256"] = sha256(self.manifest)
        write_json(self.dossier, dossier)

    def test_manifest_is_deterministic_and_classifies_memory(self):
        first = self.build_manifest()
        first_bytes = self.manifest.read_bytes()
        second = self.build_manifest()
        self.assertEqual(first, second)
        self.assertEqual(first_bytes, self.manifest.read_bytes())
        self.assertEqual(first["memory_intake"]["current_revalidation_required"][0]["item_id"], "ai-capex-evaluation-axis")
        self.assertEqual(first["memory_intake"]["procedural"][0]["item_type"], "core")

    def test_manifest_rejects_date_mismatch(self):
        bad = read_json(self.query)
        bad["episode_date"] = "2026-08-05"
        write_json(self.query, bad)
        with self.assertRaises(ManifestBuildError):
            self.build_manifest()

    def test_supported_current_evidence_passes(self):
        self.base_dossier()
        result = self.validate()
        self.assertTrue(result.ok, result.errors)

    def test_weakened_with_current_contrary_evidence_passes(self):
        dossier = self.base_dossier(status="weakened", current_ids=["E-002"])
        dossier["memory_revalidation"][0]["editorial_use"] = "counterevidence"
        self.rewrite_dossier(dossier)
        self.assertTrue(self.validate().ok)

    def test_historical_only_passes_for_historical_retrieval(self):
        report = read_json(self.report)
        claim = next(item for item in report["selected"] if item["item_type"] == "claim")
        claim["status"] = "invalidated"
        claim["use_mode"] = "historical_context"
        claim["requires_current_revalidation"] = False
        write_json(self.report, report)
        dossier = self.base_dossier(status="historical_context_only", current_ids=[])
        entry = dossier["memory_revalidation"][0]
        entry["retrieval_use_mode"] = "historical_context"
        entry["editorial_use"] = "comparison"
        self.rewrite_dossier(dossier)
        self.assertTrue(self.validate().ok)

    def test_supported_without_current_evidence_fails(self):
        self.base_dossier(status="supported", current_ids=[])
        result = self.validate()
        self.assertFalse(result.ok)
        self.assertTrue(any("requires current_evidence_ids" in error for error in result.errors))

    def test_memory_path_cannot_be_current_evidence(self):
        dossier = self.base_dossier()
        dossier["evidence"][0]["source_reference"] = "editorial-memory/episodes/2026-07-31/revisions/v001/provenance.json"
        self.rewrite_dossier(dossier)
        self.assertTrue(any("past memory cannot be used" in error for error in self.validate().errors))

    def test_invalidated_retrieval_cannot_be_current_premise(self):
        report = read_json(self.report)
        claim = next(item for item in report["selected"] if item["item_type"] == "claim")
        claim["status"] = "invalidated"
        claim["use_mode"] = "historical_context"
        claim["requires_current_revalidation"] = False
        write_json(self.report, report)
        dossier = self.base_dossier(status="supported", current_ids=["E-001"])
        dossier["memory_revalidation"][0]["retrieval_use_mode"] = "historical_context"
        self.rewrite_dossier(dossier)
        self.assertTrue(any("cannot be a current premise" in error for error in self.validate().errors))

    def test_selected_memory_must_be_classified(self):
        dossier = self.base_dossier()
        manifest = read_json(self.manifest)
        manifest["memory_intake"]["current_revalidation_required"] = []
        write_json(self.manifest, manifest)
        self.rewrite_dossier(dossier)
        self.assertTrue(any("manifest omits selected memory" in error for error in self.validate().errors))

    def test_input_sha_mismatch_fails(self):
        self.base_dossier()
        self.context.write_text("tampered\n", encoding="utf-8")
        self.assertTrue(any("SHA-256 mismatch" in error for error in self.validate().errors))

    def test_expected_cannot_be_memory_only(self):
        dossier = self.base_dossier()
        dossier["evidence"][0]["source_reference"] = "memory:ai-capex-evaluation-axis"
        dossier["memory_revalidation"][0]["current_evidence_ids"] = ["E-002"]
        dossier["causal_edges"][0]["evidence_ids"] = ["E-002"]
        dossier["timeline"][0]["evidence_ids"] = ["E-002"]
        dossier["contrary_evidence"][0]["evidence_ids"] = ["E-002"]
        dossier["expected_actual_gap"]["actual"]["evidence_ids"] = ["E-002"]
        self.rewrite_dossier(dossier)
        self.assertTrue(any("Expected cannot be grounded only" in error for error in self.validate().errors))

    def test_nasdaq_wide_edge_requires_current_quality_evidence(self):
        dossier = self.base_dossier()
        for item in dossier["evidence"]:
            item["source_tier"] = "tier_3"
        dossier["memory_revalidation"][0]["revalidation_status"] = "partially_supported"
        self.rewrite_dossier(dossier)
        self.assertTrue(any("NASDAQ-wide edge requires" in error for error in self.validate().errors))

    def test_unknown_current_evidence_id_fails(self):
        dossier = self.base_dossier()
        dossier["memory_revalidation"][0]["current_evidence_ids"] = ["E-999"]
        self.rewrite_dossier(dossier)
        self.assertTrue(any("unknown current evidence id E-999" in error for error in self.validate().errors))


if __name__ == "__main__":
    unittest.main()
