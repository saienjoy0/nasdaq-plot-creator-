from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
import subprocess
from pathlib import Path

REPO_SOURCE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_SOURCE / "scripts"))

from memory_promotion_lib import (  # noqa: E402
    ConflictError,
    PreflightError,
    PromotionError,
    StalePlanError,
    apply_plan,
    build_plan,
)


class MemoryPromotionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(REPO_SOURCE / "scripts", self.root / "scripts")
        shutil.copytree(
            REPO_SOURCE / "skills" / "nasdaq-cafe-editorial-memory" / "contracts",
            self.root / "skills" / "nasdaq-cafe-editorial-memory" / "contracts",
        )
        (self.root / "editorial-memory" / "threads").mkdir(parents=True)
        (self.root / "editorial-memory" / "daily").mkdir(parents=True)
        self.write_json("editorial-memory/claim_ledger.json", {"contract_version": "1.0.0", "claims": []})
        self.write_json("editorial-memory/threads/index.json", {"contract_version": "1.0.0", "threads": []})
        self.write_json("editorial-memory/entity_aliases.json", {"contract_version": "1.0.0", "entities": []})
        self.write_text("editorial-memory/production-lessons.md", "# Production Lessons\n")
        self.contracts = self.root / "skills" / "nasdaq-cafe-editorial-memory" / "contracts"
        self.record_path = self.make_sources_and_record()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_json(self, relative: str, value: object) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def write_text(self, relative: str, text: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def make_sources_and_record(self, *, status: str = "approved_preview") -> Path:
        self.write_text("production/episode_package_2026-08-05.md", "# 2026-08-05\n完成回\n")
        self.write_json("render-specs/2026-08-05/render_spec.json", {"episode_date": "2026-08-05", "scenes": []})
        self.write_json("production/validator_report_2026-08-05.json", {"status": "pass"})
        record = {
            "contract_version": "1.0.0",
            "episode_date": "2026-08-05",
            "title": "AI投資の回収速度",
            "main_story": "大型テックのAI投資評価",
            "story_spine": "投資額より回収経路が評価を分けた",
            "central_hypothesis": {"text": "回収速度への評価が主役", "confidence": "medium"},
            "contrary_evidence": ["金利も動いた"],
            "watch_next": ["次回決算"],
            "topics": ["AI設備投資"],
            "entities": ["ExampleCo"],
            "thread_updates": [
                {
                    "thread_id": "ai-capex-payback",
                    "title": "AI投資の回収",
                    "question": "AI設備投資はどの速度で回収されるか",
                    "summary": "回収経路の説明が評価差につながった。",
                    "triggers": ["capex"],
                    "entities": ["ExampleCo"],
                    "topics": ["AI設備投資"],
                    "claim_ids": ["claim.ai.payback"],
                    "status": "active",
                }
            ],
            "claim_updates": [
                {
                    "claim_id": "claim.ai.payback",
                    "subject": "AI設備投資",
                    "claim": "市場は投資額だけでなく回収経路を評価する",
                    "status": "active",
                    "confidence": "medium",
                    "reason": "承認済み完成回で確認",
                    "evidence_paths": ["production/episode_package_2026-08-05.md"],
                    "thread_ids": ["ai-capex-payback"],
                    "entities": ["ExampleCo"],
                    "topics": ["AI設備投資"],
                }
            ],
            "alias_updates": [
                {
                    "canonical_id": "exampleco",
                    "display_name": "ExampleCo",
                    "aliases": ["Example Co"],
                    "entity_type": "company",
                }
            ],
            "production_lessons": ["因果の接続文を短くする"],
            "source_paths": {
                "episode_package": "production/episode_package_2026-08-05.md",
                "render_spec": "render-specs/2026-08-05/render_spec.json",
                "validator_report": "production/validator_report_2026-08-05.json",
            },
            "approval": {"status": status, "approved_at": "2026-08-05T08:00:00Z"},
        }
        return self.write_json("production/publication_record_2026-08-05.json", record)

    def plan(self, run: str = "run1") -> dict:
        return build_plan(
            self.record_path,
            self.root / "working" / "memory-promotion" / run,
            self.root,
            self.contracts,
        )

    def apply(self, run: str = "run1", **kwargs: object) -> dict:
        return apply_plan(
            self.root / "working" / "memory-promotion" / run / "promotion_plan.json",
            self.root,
            self.contracts,
            commit=False,
            **kwargs,
        )

    def memory_snapshot(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for path in sorted((self.root / "editorial-memory").rglob("*")):
            if path.is_file():
                result[path.relative_to(self.root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        return result

    def test_initial_v001_and_provenance(self) -> None:
        plan = self.plan()
        self.assertTrue(plan["safe_to_apply"])
        self.assertEqual("v001", plan["revision"])
        self.apply()
        archive = self.root / "editorial-memory/episodes/2026-08-05/revisions/v001"
        self.assertTrue((archive / "publication_record.json").is_file())
        self.assertTrue((archive / "episode_package.md").is_file())
        provenance = json.loads((archive / "provenance.json").read_text())
        self.assertEqual(["claim.ai.payback"], provenance["generated_memory_ids"]["claims"])
        self.assertEqual(64, len(provenance["source_artifacts"]["render_spec"]["sha256"]))

    def test_dry_run_never_changes_memory(self) -> None:
        before = self.memory_snapshot()
        self.plan()
        self.assertEqual(before, self.memory_snapshot())

    def test_same_input_is_noop(self) -> None:
        self.plan("first")
        self.apply("first")
        plan = self.plan("second")
        self.assertTrue(plan["noop"])
        self.assertEqual([], plan["operations"])
        report = self.apply("second")
        self.assertEqual("noop", report["status"])

    def test_correction_creates_v002_without_overwriting_v001(self) -> None:
        self.plan("first")
        self.apply("first")
        old_provenance = (self.root / "editorial-memory/episodes/2026-08-05/revisions/v001/provenance.json").read_bytes()
        record = json.loads(self.record_path.read_text())
        record.update({"revision": "v002", "supersedes_revision": "v001", "correction_reason": "反対材料を追加"})
        record["claim_updates"][0]["status"] = "strengthened"
        record["claim_updates"][0]["reason"] = "訂正版で根拠を追加"
        self.record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        self.write_text("production/episode_package_2026-08-05.md", "# 2026-08-05\n完成回・訂正版\n")
        plan = self.plan("revision")
        self.assertEqual("v002", plan["revision"])
        self.apply("revision")
        self.assertEqual(old_provenance, (self.root / "editorial-memory/episodes/2026-08-05/revisions/v001/provenance.json").read_bytes())
        self.assertTrue((self.root / "editorial-memory/episodes/2026-08-05/revisions/v002/provenance.json").is_file())

    def test_changed_same_date_without_revision_is_blocked(self) -> None:
        self.plan("first")
        self.apply("first")
        self.write_text("production/episode_package_2026-08-05.md", "# 2026-08-05\n内容変更\n")
        plan = self.plan("changed")
        self.assertFalse(plan["safe_to_apply"])
        self.assertTrue(plan["conflicts"])

    def test_unapproved_record_is_rejected(self) -> None:
        record = json.loads(self.record_path.read_text())
        record["approval"]["status"] = "draft"
        self.record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        with self.assertRaises(PreflightError):
            self.plan()

    def test_validator_non_pass_is_rejected(self) -> None:
        self.write_json("production/validator_report_2026-08-05.json", {"status": "fail"})
        with self.assertRaises(PreflightError):
            self.plan()

    def test_declared_source_hash_mismatch_is_rejected(self) -> None:
        record = json.loads(self.record_path.read_text())
        record["source_hashes"] = {"episode_package": "0" * 64}
        self.record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        with self.assertRaises(PreflightError):
            self.plan()

    def test_claim_identity_collision_blocks(self) -> None:
        ledger = {
            "contract_version": "1.0.0",
            "claims": [{"claim_id": "claim.ai.payback", "subject": "別テーマ", "claim": "別の主張", "status": "active", "confidence": "medium"}],
        }
        self.write_json("editorial-memory/claim_ledger.json", ledger)
        plan = self.plan()
        self.assertFalse(plan["safe_to_apply"])
        self.assertEqual("claim_identity_collision", plan["conflicts"][0]["type"])

    def test_invalidated_claim_cannot_return_active(self) -> None:
        record = json.loads(self.record_path.read_text())
        update = record["claim_updates"][0]
        ledger = {"contract_version": "1.0.0", "claims": [{**copy.deepcopy(update), "status": "invalidated"}]}
        self.write_json("editorial-memory/claim_ledger.json", ledger)
        plan = self.plan()
        self.assertFalse(plan["safe_to_apply"])
        self.assertTrue(any(item["type"] == "status_regression" for item in plan["conflicts"]))

    def test_alias_collision_blocks(self) -> None:
        self.write_json(
            "editorial-memory/entity_aliases.json",
            {
                "contract_version": "1.0.0",
                "entities": [{
                    "entity_id": "otherco",
                    "canonical_name": "Other",
                    "entity_type": "company",
                    "aliases": ["Example Co"],
                    "tickers": [],
                    "identifiers": {},
                    "status": "active",
                    "superseded_by": None,
                    "updated_at": "2026-08-04",
                    "source_paths": ["editorial-memory/episodes/2026-08-04/revisions/v001/provenance.json"],
                }],
            },
        )
        plan = self.plan()
        self.assertFalse(plan["safe_to_apply"])
        self.assertTrue(any(item["type"] == "alias_collision" for item in plan["conflicts"]))

    def test_thread_identity_collision_blocks(self) -> None:
        self.write_json(
            "editorial-memory/threads/index.json",
            {
                "contract_version": "1.0.0",
                "threads": [{
                    "id": "ai-capex-payback",
                    "title": "AI投資の回収",
                    "path": "threads/ai-capex-payback.md",
                    "triggers": [],
                    "entities": [],
                    "topics": [],
                    "status": "active",
                    "updated_at": "2026-08-04",
                }],
            },
        )
        self.write_text(
            "editorial-memory/threads/ai-capex-payback.md",
            "# AI投資の回収\n\n## このthreadが答える問い\n\n別の問い\n\n## 更新履歴\n",
        )
        plan = self.plan()
        self.assertFalse(plan["safe_to_apply"])
        self.assertTrue(any(item["type"] == "thread_identity_collision" for item in plan["conflicts"]))

    def test_explicit_revision_without_correction_reason_is_blocked(self) -> None:
        self.plan("first")
        self.apply("first")
        record = json.loads(self.record_path.read_text())
        record.update({"revision": "v002", "supersedes_revision": "v001"})
        self.record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        self.write_text("production/episode_package_2026-08-05.md", "# 2026-08-05\n変更\n")
        plan = self.plan("bad-revision")
        self.assertFalse(plan["safe_to_apply"])
        self.assertTrue(any("correction_reason" in item["detail"] for item in plan["conflicts"]))

    def test_tampered_staged_file_is_rejected(self) -> None:
        self.plan()
        staged = self.root / "working/memory-promotion/run1/staged/editorial-memory/claim_ledger.json"
        staged.write_text("{}\n", encoding="utf-8")
        with self.assertRaises(StalePlanError):
            self.apply()

    def test_missing_dry_run_report_is_rejected(self) -> None:
        self.plan()
        (self.root / "working/memory-promotion/run1/dry_run_report.md").unlink()
        with self.assertRaises(StalePlanError):
            self.apply()

    def test_existing_lock_rejects_apply(self) -> None:
        self.plan()
        lock = self.root / "working/memory-promotion/.apply.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("held\n", encoding="utf-8")
        with self.assertRaises(PromotionError):
            self.apply()

    def test_stale_plan_is_rejected(self) -> None:
        self.plan()
        self.write_json("editorial-memory/claim_ledger.json", {"contract_version": "1.0.0", "claims": [{"claim_id": "other"}]})
        with self.assertRaises(StalePlanError):
            self.apply()

    def test_double_apply_is_rejected(self) -> None:
        self.plan()
        self.apply()
        with self.assertRaises(PromotionError):
            self.apply()

    def test_apply_failure_rolls_back_all_memory(self) -> None:
        self.plan()
        before = self.memory_snapshot()
        with self.assertRaises(RuntimeError):
            self.apply(fail_after=2)
        self.assertEqual(before, self.memory_snapshot())
        self.assertFalse((self.root / "working/memory-promotion/.apply.lock").exists())

    def test_missing_source_is_rejected(self) -> None:
        (self.root / "production/episode_package_2026-08-05.md").unlink()
        with self.assertRaises(PreflightError):
            self.plan()

    def test_apply_with_git_creates_one_commit(self) -> None:
        subprocess.run(["git", "init", str(self.root)], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "CI"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "ci@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "--", "editorial-memory", "production", "render-specs", "skills", "scripts"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-m", "baseline"], check=True, stdout=subprocess.DEVNULL)
        self.plan("git")
        report = apply_plan(
            self.root / "working/memory-promotion/git/promotion_plan.json",
            self.root,
            self.contracts,
            commit=True,
        )
        self.assertRegex(report["git_commit"], r"^[a-f0-9]{40}$")
        count = subprocess.check_output(["git", "-C", str(self.root), "rev-list", "--count", "HEAD"], text=True).strip()
        self.assertEqual("2", count)

    def test_path_traversal_is_rejected(self) -> None:
        record = json.loads(self.record_path.read_text())
        record["source_paths"]["episode_package"] = "../outside.md"
        self.record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        with self.assertRaises(PreflightError):
            self.plan()


if __name__ == "__main__":
    unittest.main()
