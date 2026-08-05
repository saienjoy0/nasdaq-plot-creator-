import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
VALIDATORS = ROOT / "skills/nasdaq-cafe-causal-research" / "validators"
for path in (SCRIPTS, VALIDATORS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_research_input_manifest import ManifestBuildError, build_manifest  # noqa: E402
from validate_causal_research_dossier import validate_dossier  # noqa: E402

CONTRACTS = ROOT / "skills/nasdaq-cafe-causal-research/contracts"
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


def fake_retrieve(query_plan, context_output, report_output, *, repo_root, contracts_dir):
    plan = read_json(query_plan)
    topic = plan["topics"][0]
    context_output.parent.mkdir(parents=True, exist_ok=True)
    context_output.write_text(
        f"# Memory context\n\nTopic: {topic}\nClaim: ai-capex-evaluation-axis\n",
        encoding="utf-8",
    )
    report = {
        "contract_version": "1.0.0",
        "episode_date": plan["episode_date"],
        "query_plan_path": query_plan.resolve().relative_to(repo_root.resolve()).as_posix(),
        "selected": [
            {
                "item_type": "core",
                "item_id": "fox-editorial-state",
                "path": "editorial-memory/core/fox_editorial_state.md",
                "score": 100,
                "reasons": ["always_include"],
                "provenance_paths": ["editorial-memory/memory_policy.md"],
                "status": "active",
                "use_mode": "procedural",
                "requires_current_revalidation": False,
                "historical_confidence": "high",
                "episode_ids": [],
            },
            {
                "item_type": "claim",
                "item_id": "ai-capex-evaluation-axis",
                "path": "editorial-memory/claim_ledger.json",
                "score": 31,
                "reasons": ["exact_entity", "topic_match", "provenance_verified"],
                "provenance_paths": [
                    "editorial-memory/episodes/2026-07-31/revisions/v001/provenance.json"
                ],
                "status": "active",
                "use_mode": "current_revalidation_required",
                "requires_current_revalidation": True,
                "historical_confidence": "medium",
                "episode_ids": ["2026-07-31/v001"],
            },
        ],
        "rejected": [],
        "limits": {
            "max_threads": 5,
            "max_claims": 10,
            "max_episodes": 3,
            "max_lessons": 3,
            "max_characters": 10000,
        },
        "usage": {
            "threads": 0,
            "claims": 1,
            "episodes": 0,
            "lessons": 0,
            "characters": len(context_output.read_text(encoding="utf-8")),
        },
        "diversity": {
            "distinct_episode_ids": ["2026-07-31/v001"],
            "distinct_thread_ids": [],
            "duplicate_groups_removed": 0,
        },
        "warnings": [],
    }
    write_json(report_output, report)
    return report


class MemoryRevalidationBridgeTest(unittest.TestCase):
    def setUp(self):
        (ROOT / "working").mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix="pr6-test-", dir=ROOT / "working"))
        self.daily = self.tmp / f"daily_source_package_{DATE}.md"
        self.query = self.tmp / f"memory_query_plan_{DATE}.json"
        self.context = self.tmp / f"memory_context_{DATE}.md"
        self.report = self.tmp / f"memory_retrieval_report_{DATE}.json"
        self.manifest = self.tmp / "research_input_manifest.json"
        self.dossier = self.tmp / f"causal_research_dossier_{DATE}.json"
        self.daily.write_text("# Daily source package\n", encoding="utf-8")
        write_json(
            self.query,
            {
                "contract_version": "1.0.0",
                "episode_date": DATE,
                "lead_candidates": ["AI設備投資"],
                "entities": [
                    {
                        "raw": "AWS",
                        "canonical": "AWS",
                        "entity_id": None,
                        "resolution": "unresolved",
                    }
                ],
                "topics": ["AI設備投資"],
                "technologies": [],
                "policies": [],
                "indicators": [],
                "relations": [],
                "time_window": {"from": None, "to": DATE},
                "comparison_questions": [],
                "limits": {
                    "max_threads": 5,
                    "max_claims": 10,
                    "max_episodes": 3,
                    "max_lessons": 3,
                    "max_characters": 10000,
                },
            },
        )
        fake_retrieve(
            self.query,
            self.context,
            self.report,
            repo_root=ROOT,
            contracts_dir=ROOT / "skills/nasdaq-cafe-editorial-memory/contracts",
        )

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
            repo_root=ROOT,
            retrieval_runner=fake_retrieve,
        )

    def base_dossier(self, status="supported", current_ids=None):
        manifest = self.build_manifest()
        current_ids = ["E-001"] if current_ids is None else current_ids
        daily_ref = manifest["inputs"]["daily_source_package"]
        dossier = {
            "contract_version": "0.2.0",
            "episode_date": DATE,
            "session": manifest["session"],
            "input_provenance": [
                {
                    "path_or_reference": daily_ref["path"],
                    "role": "daily_input",
                    "version_or_hash": daily_ref["sha256"],
                }
            ],
            "research_input_manifest": {
                "path": self.manifest.resolve().relative_to(ROOT.resolve()).as_posix(),
                "sha256": sha256(self.manifest),
            },
            "contradictions": [
                {
                    "id": "CON-01",
                    "statement": "AI投資は増えたが、株価反応は限定的だった。",
                    "rank": 1,
                    "selection_reason": "投資と市場評価のずれを説明するため。",
                }
            ],
            "research_questions": [
                {
                    "id": "Q-01",
                    "perspective": "official_evidence",
                    "question": "当日の公式資料は売上回収を示すか。",
                    "parent_question_id": None,
                    "status": "answered",
                    "answer_summary": "売上成長が確認された。",
                    "evidence_ids": ["E-001"],
                }
            ],
            "evidence": [
                {
                    "evidence_id": "E-001",
                    "claim": "公式資料でクラウド売上成長が確認された。",
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
                    "limitations": "市場解釈。",
                },
            ],
            "memory_revalidation": [
                {
                    "memory_reference_type": "claim",
                    "memory_reference_id": "ai-capex-evaluation-axis",
                    "historical_confidence": "medium",
                    "retrieval_use_mode": "current_revalidation_required",
                    "revalidation_status": status,
                    "current_evidence_ids": current_ids,
                    "difference_from_previous": "当日は現在証拠で再検証した。",
                    "editorial_use": "not_used" if status == "not_used" else "research_lead",
                    "notes": "過去仮説を現在証拠へ直接変換していない。",
                }
            ],
            "expected_actual_gap": {
                "expected": {
                    "status": "confirmed",
                    "basis_class": "prior_company_guidance",
                    "statement": "成長継続が見込まれていた。",
                    "evidence_ids": ["E-001"],
                },
                "actual": {
                    "statement": "公式資料は成長を示した。",
                    "evidence_ids": ["E-001"],
                },
                "gap": {
                    "statement": "成長確認だけでは回収懸念を消せなかった。",
                    "market_meaning": "評価軸が回収速度へ移った可能性。",
                    "confidence": "medium",
                },
            },
            "timeline": [
                {
                    "id": "T-01",
                    "timestamp_or_window": "2026-08-05 after hours",
                    "timezone": "America/New_York",
                    "event": "公式資料公表",
                    "precision": "session",
                    "evidence_ids": ["E-001"],
                }
            ],
            "causal_edges": [
                {
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
                }
            ],
            "factor_roles": {
                "primary_candidate": "投資回収への懸念",
                "amplifiers": ["金利"],
                "offsetting": ["売上成長"],
                "unresolved": [],
            },
            "alternative_hypotheses": [
                {
                    "id": "ALT-01",
                    "hypothesis": "金利だけで動いた。",
                    "supporting_evidence_ids": [],
                    "weakening_evidence_ids": ["E-001"],
                    "status": "weakened",
                }
            ],
            "contrary_evidence": [
                {
                    "statement": "売上は成長した。",
                    "evidence_ids": ["E-001"],
                    "effect_on_confidence": "material",
                }
            ],
            "editorial_handoff": {
                "provisional_lead": "AI投資回収への評価",
                "central_hypothesis": "回収速度が重視された。",
                "confidence": "medium",
                "company_direct_material": ["クラウド売上"],
                "nasdaq_wide_material": ["大型テック評価"],
                "causal_spine": "投資増加→回収懸念→大型テック評価",
                "headline_beyond_discovery": "成長より回収速度が焦点。",
                "exclude_from_narration": [],
                "unresolved_questions": [],
                "next_validation_points": ["次回ガイダンス"],
                "memory_differences": ["過去仮説を当日証拠で再検証した。"],
            },
            "validation": {"status": "pass", "errors": [], "warnings": []},
        }
        write_json(self.dossier, dossier)
        return dossier

    def rewrite_dossier(self, dossier):
        dossier["research_input_manifest"]["sha256"] = sha256(self.manifest)
        write_json(self.dossier, dossier)

    def validate(self):
        return validate_dossier(
            self.dossier,
            self.manifest,
            self.report,
            contracts_dir=CONTRACTS,
            repo_root=ROOT,
            retrieval_runner=fake_retrieve,
        )

    def test_manifest_is_deterministic_and_classifies_memory(self):
        first = self.build_manifest()
        first_bytes = self.manifest.read_bytes()
        second = self.build_manifest()
        self.assertEqual(first, second)
        self.assertEqual(first_bytes, self.manifest.read_bytes())
        self.assertEqual(first["memory_intake"]["procedural"][0]["item_type"], "core")

    def test_manifest_rejects_date_mismatch(self):
        bad = read_json(self.query)
        bad["episode_date"] = "2026-08-05"
        write_json(self.query, bad)
        with self.assertRaises(ManifestBuildError):
            self.build_manifest()

    def test_manifest_rejects_same_date_different_query_binding(self):
        other = self.tmp / f"other_memory_query_plan_{DATE}.json"
        shutil.copy2(self.query, other)
        with self.assertRaises(ManifestBuildError):
            build_manifest(
                episode_date=DATE,
                market_date="2026-08-05",
                timezone="Asia/Tokyo",
                information_cutoff="2026-08-06T07:30:00+09:00",
                daily_source_package=self.daily,
                memory_query_plan=other,
                memory_context=self.context,
                memory_retrieval_report=self.report,
                output=self.manifest,
                contracts_dir=CONTRACTS,
                repo_root=ROOT,
                retrieval_runner=fake_retrieve,
            )

    def test_manifest_rejects_context_from_other_retrieval(self):
        self.context.write_text("wrong context\n", encoding="utf-8")
        with self.assertRaises(ManifestBuildError):
            self.build_manifest()

    def test_manifest_rejects_repo_escape(self):
        outside = Path(tempfile.mkstemp(prefix="outside-")[1])
        try:
            with self.assertRaises(ManifestBuildError):
                build_manifest(
                    episode_date=DATE,
                    market_date="2026-08-05",
                    timezone="Asia/Tokyo",
                    information_cutoff="2026-08-06T07:30:00+09:00",
                    daily_source_package=outside,
                    memory_query_plan=self.query,
                    memory_context=self.context,
                    memory_retrieval_report=self.report,
                    output=self.manifest,
                    contracts_dir=CONTRACTS,
                    repo_root=ROOT,
                    retrieval_runner=fake_retrieve,
                )
        finally:
            outside.unlink(missing_ok=True)

    def test_supported_current_evidence_passes(self):
        self.base_dossier()
        result = self.validate()
        self.assertTrue(result.ok, result.errors)

    def test_weakened_with_current_quality_evidence_passes(self):
        dossier = self.base_dossier(status="weakened", current_ids=["E-002"])
        dossier["memory_revalidation"][0]["editorial_use"] = "counterevidence"
        self.rewrite_dossier(dossier)
        self.assertTrue(self.validate().ok)

    def test_supported_without_current_evidence_fails(self):
        self.base_dossier(status="supported", current_ids=[])
        self.assertTrue(any("requires current_evidence_ids" in e for e in self.validate().errors))

    def test_partially_supported_with_discovery_only_fails(self):
        dossier = self.base_dossier(status="partially_supported")
        dossier["evidence"][0]["source_tier"] = "discovery_only"
        self.rewrite_dossier(dossier)
        self.assertTrue(any("partially_supported requires" in e for e in self.validate().errors))

    def test_weakened_with_unavailable_fails(self):
        dossier = self.base_dossier(status="weakened")
        dossier["memory_revalidation"][0]["editorial_use"] = "counterevidence"
        dossier["evidence"][0]["source_tier"] = "unavailable"
        self.rewrite_dossier(dossier)
        self.assertTrue(any("weakened requires" in e for e in self.validate().errors))

    def test_invalidated_with_tier3_fails(self):
        dossier = self.base_dossier(status="invalidated")
        dossier["memory_revalidation"][0]["editorial_use"] = "counterevidence"
        dossier["evidence"][0]["source_tier"] = "tier_3"
        self.rewrite_dossier(dossier)
        self.assertTrue(any("invalidated requires" in e for e in self.validate().errors))

    def test_memory_path_cannot_be_current_evidence(self):
        dossier = self.base_dossier()
        dossier["evidence"][0]["source_reference"] = "editorial-memory/claim_ledger.json"
        self.rewrite_dossier(dossier)
        self.assertTrue(any("past memory cannot be used" in e for e in self.validate().errors))

    def test_duplicate_manifest_bucket_fails(self):
        dossier = self.base_dossier()
        manifest = read_json(self.manifest)
        duplicate = dict(manifest["memory_intake"]["current_revalidation_required"][0])
        manifest["memory_intake"]["historical_context_only"].append(duplicate)
        write_json(self.manifest, manifest)
        self.rewrite_dossier(dossier)
        self.assertTrue(any("multiple buckets" in e for e in self.validate().errors))

    def test_manifest_selected_metadata_mismatch_fails(self):
        dossier = self.base_dossier()
        manifest = read_json(self.manifest)
        manifest["memory_intake"]["current_revalidation_required"][0][
            "requires_current_revalidation"
        ] = False
        write_json(self.manifest, manifest)
        self.rewrite_dossier(dossier)
        self.assertTrue(any("metadata differs" in e for e in self.validate().errors))

    def test_manifest_wrong_bucket_fails(self):
        dossier = self.base_dossier()
        manifest = read_json(self.manifest)
        item = manifest["memory_intake"]["current_revalidation_required"].pop()
        manifest["memory_intake"]["historical_context_only"].append(item)
        write_json(self.manifest, manifest)
        self.rewrite_dossier(dossier)
        self.assertTrue(any("manifest bucket" in e for e in self.validate().errors))

    def test_input_sha_mismatch_fails(self):
        self.base_dossier()
        self.context.write_text("tampered\n", encoding="utf-8")
        self.assertTrue(any("SHA-256 mismatch" in e for e in self.validate().errors))

    def test_retrieval_lineage_is_rechecked_by_validator(self):
        dossier = self.base_dossier()
        self.context.write_text("tampered\n", encoding="utf-8")
        manifest = read_json(self.manifest)
        manifest["inputs"]["memory_context"]["sha256"] = sha256(self.context)
        write_json(self.manifest, manifest)
        self.rewrite_dossier(dossier)
        self.assertTrue(any("retrieval lineage" in e for e in self.validate().errors))

    def test_unknown_research_question_evidence_fails(self):
        dossier = self.base_dossier()
        dossier["research_questions"][0]["evidence_ids"] = ["E-999"]
        self.rewrite_dossier(dossier)
        self.assertTrue(any("research question Q-01" in e for e in self.validate().errors))

    def test_unknown_alternative_evidence_fails(self):
        dossier = self.base_dossier()
        dossier["alternative_hypotheses"][0]["supporting_evidence_ids"] = ["E-999"]
        self.rewrite_dossier(dossier)
        self.assertTrue(any("alternative hypothesis ALT-01" in e for e in self.validate().errors))

    def test_absolute_manifest_input_path_fails(self):
        dossier = self.base_dossier()
        manifest = read_json(self.manifest)
        manifest["inputs"]["memory_context"]["path"] = self.context.resolve().as_posix()
        write_json(self.manifest, manifest)
        self.rewrite_dossier(dossier)
        self.assertTrue(any("absolute paths are forbidden" in e for e in self.validate().errors))

    def test_expected_cannot_be_memory_only(self):
        dossier = self.base_dossier()
        dossier["evidence"][0]["source_reference"] = "memory:ai-capex-evaluation-axis"
        dossier["memory_revalidation"][0]["current_evidence_ids"] = ["E-002"]
        dossier["expected_actual_gap"]["actual"]["evidence_ids"] = ["E-002"]
        dossier["timeline"][0]["evidence_ids"] = ["E-002"]
        dossier["contrary_evidence"][0]["evidence_ids"] = ["E-002"]
        dossier["causal_edges"][0]["evidence_ids"] = ["E-002"]
        self.rewrite_dossier(dossier)
        self.assertTrue(any("Expected cannot be grounded only" in e for e in self.validate().errors))

    def test_nasdaq_wide_edge_requires_quality_evidence(self):
        dossier = self.base_dossier()
        for item in dossier["evidence"]:
            item["source_tier"] = "tier_3"
        dossier["memory_revalidation"][0]["revalidation_status"] = "unresolved"
        dossier["memory_revalidation"][0]["current_evidence_ids"] = []
        dossier["memory_revalidation"][0]["editorial_use"] = "not_used"
        self.rewrite_dossier(dossier)
        self.assertTrue(any("NASDAQ-wide edge requires" in e for e in self.validate().errors))


if __name__ == "__main__":
    unittest.main()
