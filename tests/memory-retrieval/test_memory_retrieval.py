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

from editorial_memory_retrieval import retrieve  # noqa: E402

CONTRACTS = ROOT / "skills" / "nasdaq-cafe-editorial-memory" / "contracts"


def write(path: Path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, (dict, list)):
        path.write_text(
            json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    else:
        path.write_text(content, encoding="utf-8")


class RetrievalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        write(self.tmp / "editorial-memory/active_context.md", "# active\n")
        write(self.tmp / "editorial-memory/core/fox_editorial_state.md", "# fox\n")
        write(
            self.tmp / "editorial-memory/entity_aliases.json",
            {
                "contract_version": "1.0.0",
                "entities": [
                    {
                        "entity_id": "amazon-web-services",
                        "canonical_name": "AWS",
                        "aliases": [
                            "AWS",
                            "Amazon Web Services",
                            "アマゾンウェブサービス",
                        ],
                    }
                ],
            },
        )
        write(
            self.tmp / "editorial-memory/threads/index.json",
            {
                "threads": [
                    {
                        "id": "ai-capex-payback",
                        "title": "AI設備投資の回収",
                        "path": "threads/ai-capex-payback.md",
                        "triggers": ["AI設備投資"],
                        "entities": ["AWS"],
                        "topics": ["クラウド"],
                        "status": "active",
                        "updated_at": "2026-07-31",
                        "last_episode_revision": "2026-07-31/v001",
                    }
                ]
            },
        )
        write(
            self.tmp / "editorial-memory/threads/ai-capex-payback.md",
            "# AI設備投資の回収\n\nAWSの回収証拠。\n",
        )
        provenance = "editorial-memory/episodes/2026-07-31/revisions/v001/provenance.json"
        active_history = {
            "date": "2026-07-31",
            "status": "active",
            "confidence": "medium",
            "episode_revision": "2026-07-31/v001",
            "provenance_path": provenance,
        }
        invalid_history = {
            "date": "2026-07-31",
            "status": "invalidated",
            "confidence": "low",
            "episode_revision": "2026-07-31/v001",
            "provenance_path": provenance,
        }
        write(
            self.tmp / "editorial-memory/claim_ledger.json",
            {
                "claims": [
                    {
                        "claim_id": "ai-capex-evaluation-axis",
                        "subject": "AI設備投資の評価軸",
                        "claim": "市場はAWS売上による回収を評価する",
                        "status": "active",
                        "confidence": "medium",
                        "last_updated": "2026-07-31",
                        "thread_ids": ["ai-capex-payback"],
                        "entities": ["AWS"],
                        "topics": ["AI設備投資"],
                        "history": [active_history],
                    },
                    {
                        "claim_id": "old-invalid",
                        "subject": "古いAI仮説",
                        "claim": "古いAI仮説は否定された",
                        "status": "invalidated",
                        "confidence": "low",
                        "last_updated": "2026-07-31",
                        "thread_ids": [],
                        "entities": ["AWS"],
                        "topics": ["AI設備投資"],
                        "history": [invalid_history],
                    },
                    {
                        "claim_id": "missing-prov",
                        "subject": "AI設備投資の別仮説",
                        "claim": "出典なし",
                        "status": "active",
                        "confidence": "low",
                        "last_updated": "2026-07-31",
                        "thread_ids": [],
                        "entities": ["AWS"],
                        "topics": ["AI設備投資"],
                        "history": [],
                    },
                ]
            },
        )
        write(self.tmp / provenance, {"approval_status": "approved_preview"})
        write(
            self.tmp / "editorial-memory/episodes/2026-07-31/index.json",
            {"current_revision": "v001"},
        )
        write(
            self.tmp
            / "editorial-memory/episodes/2026-07-31/revisions/v001/episode_summary.md",
            "# 回\n\n## 主役\nAWSとAI設備投資\n\n"
            "## 重要な反対材料\n半導体への波及は限定的。\n",
        )
        write(self.tmp / "editorial-memory/production-lessons.md", "# Production Lessons\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def plan(
        self,
        *,
        entity="アマゾンウェブサービス",
        topic="AI設備投資",
        comparisons=None,
        characters=10000,
    ) -> Path:
        plan = {
            "contract_version": "1.0.0",
            "episode_date": "2026-08-01",
            "lead_candidates": [topic],
            "entities": [
                {
                    "raw": entity,
                    "canonical": entity,
                    "entity_id": None,
                    "resolution": "unresolved",
                }
            ],
            "topics": [topic],
            "technologies": [],
            "policies": [],
            "indicators": [],
            "relations": [],
            "time_window": {"from": None, "to": "2026-08-01"},
            "comparison_questions": comparisons or [],
            "limits": {
                "max_threads": 5,
                "max_claims": 10,
                "max_episodes": 3,
                "max_lessons": 3,
                "max_characters": characters,
            },
        }
        path = self.tmp / "working/query.json"
        write(path, plan)
        return path

    def run_retrieve(self, **kwargs):
        query = self.plan(**kwargs)
        return retrieve(
            query,
            self.tmp / "working/context.md",
            self.tmp / "working/report.json",
            repo_root=self.tmp,
            contracts_dir=CONTRACTS,
        )

    def test_alias_selects_grounded_memory(self):
        report = self.run_retrieve()
        ids = {item["item_id"] for item in report["selected"]}
        self.assertIn("ai-capex-payback", ids)
        self.assertIn("ai-capex-evaluation-axis", ids)
        self.assertIn("2026-07-31/v001", ids)
        claim = next(
            item
            for item in report["selected"]
            if item["item_id"] == "ai-capex-evaluation-axis"
        )
        self.assertTrue(claim["requires_current_revalidation"])
        self.assertIn("provenance_verified", claim["reasons"])

    def test_invalidated_is_excluded_from_current_use(self):
        report = self.run_retrieve()
        self.assertNotIn(
            "old-invalid", {item["item_id"] for item in report["selected"]}
        )
        self.assertIn(
            ("old-invalid", "invalidated_current_use"),
            {(item["item_id"], item["reason"]) for item in report["rejected"]},
        )

    def test_invalidated_is_historical_only_when_comparison_is_requested(self):
        report = self.run_retrieve(
            comparisons=["以前のAI設備投資仮説はどう変わったか"]
        )
        item = next(
            value for value in report["selected"] if value["item_id"] == "old-invalid"
        )
        self.assertEqual(item["use_mode"], "historical_context")
        self.assertFalse(item["requires_current_revalidation"])

    def test_unrelated_query_returns_no_durable_memory(self):
        report = self.run_retrieve(entity="Tesla", topic="自動運転")
        durable = [
            item for item in report["selected"] if item["item_type"] != "core"
        ]
        self.assertEqual(durable, [])
        self.assertIn("no relevant durable memory selected", report["warnings"])

    def test_missing_provenance_is_rejected(self):
        report = self.run_retrieve()
        self.assertIn(
            ("missing-prov", "missing_provenance"),
            {(item["item_id"], item["reason"]) for item in report["rejected"]},
        )

    def test_character_budget_is_enforced(self):
        report = self.run_retrieve(characters=1000)
        context = (self.tmp / "working/context.md").read_text(encoding="utf-8")
        self.assertLessEqual(report["usage"]["characters"], 1000)
        self.assertEqual(report["usage"]["characters"], len(context))


if __name__ == "__main__":
    unittest.main()
