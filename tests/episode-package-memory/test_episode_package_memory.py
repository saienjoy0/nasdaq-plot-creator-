from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
VALIDATOR_PATH = ROOT / "skills/nasdaq-cafe-episode-package-memory/validators/validate_episode_package_memory.py"
spec = importlib.util.spec_from_file_location("episode_memory_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)

MEMORY_ENTRIES = {
    "supported": {"memory_reference_type": "claim", "memory_reference_id": "supported-claim", "historical_confidence": "medium", "retrieval_use_mode": "current_revalidation_required", "revalidation_status": "supported", "current_evidence_ids": ["E-001", "E-002"], "difference_from_previous": "Current official evidence continues to support the evaluation axis.", "editorial_use": "explanation_context", "notes": ""},
    "partially_supported": {"memory_reference_type": "thread", "memory_reference_id": "partial-thread", "historical_confidence": "medium", "retrieval_use_mode": "current_revalidation_required", "revalidation_status": "partially_supported", "current_evidence_ids": ["E-001"], "difference_from_previous": "The company-level point remains, but index-wide transmission is unconfirmed.", "editorial_use": "comparison", "notes": ""},
    "weakened": {"memory_reference_type": "claim", "memory_reference_id": "weakened-claim", "historical_confidence": "medium", "retrieval_use_mode": "current_revalidation_required", "revalidation_status": "weakened", "current_evidence_ids": ["E-002"], "difference_from_previous": "The prior relationship is weaker in the current session.", "editorial_use": "counterevidence", "notes": ""},
    "invalidated": {"memory_reference_type": "episode", "memory_reference_id": "invalidated-episode", "historical_confidence": "low", "retrieval_use_mode": "current_revalidation_required", "revalidation_status": "invalidated", "current_evidence_ids": ["E-001"], "difference_from_previous": "Current evidence no longer supports the former explanation.", "editorial_use": "counterevidence", "notes": ""},
    "unresolved": {"memory_reference_type": "thread", "memory_reference_id": "unresolved-thread", "historical_confidence": "unknown", "retrieval_use_mode": "current_revalidation_required", "revalidation_status": "unresolved", "current_evidence_ids": [], "difference_from_previous": "Current evidence is insufficient to resolve the prior question.", "editorial_use": "monitoring_point", "notes": ""},
    "historical_context_only": {"memory_reference_type": "weekly", "memory_reference_id": "historical-week", "historical_confidence": "medium", "retrieval_use_mode": "historical_context", "revalidation_status": "historical_context_only", "current_evidence_ids": [], "difference_from_previous": "Retained only as historical comparison context.", "editorial_use": "comparison", "notes": ""},
    "not_used": {"memory_reference_type": "lesson", "memory_reference_id": "unused-lesson", "historical_confidence": "low", "retrieval_use_mode": "current_revalidation_required", "revalidation_status": "not_used", "current_evidence_ids": [], "difference_from_previous": "Not used in the current episode.", "editorial_use": "not_used", "notes": ""},
}
EVIDENCE = [
    {"evidence_id": "E-001", "evidence_class": "fact", "source_tier": "tier_1", "source_reference": "https://issuer.example/filing"},
    {"evidence_id": "E-002", "evidence_class": "reported_interpretation", "source_tier": "tier_2", "source_reference": "https://wire.example/report"},
    {"evidence_id": "E-003", "evidence_class": "grounded_inference", "source_tier": "tier_3", "source_reference": "https://analysis.example/context"},
]


def replay_pass(repo_root: Path, dossier_path: Path):
    return validator.ValidationResult([], [])


def replay_fail(repo_root: Path, dossier_path: Path):
    return validator.ValidationResult(["forced dossier replay failure"], [])


def make_usage(*, reference_id="MR-001", usage_id="U-001", surface="scene_narration", scene_id="SCENE-03", anchor="Current official data still supports the evaluation axis.", claim_mode="current_fact", evidence_ids=None, wording_strength="qualified", permission="not_applicable"):
    if evidence_ids is None:
        evidence_ids = ["E-001"]
    return {"usage_id": usage_id, "surface": surface, "scene_id": scene_id, "anchor_text": anchor, "marker": f"<!--MEMREF:{reference_id}:{usage_id}-->", "claim_mode": claim_mode, "evidence_ids": evidence_ids, "requires_source_attribution": False, "wording_strength": wording_strength, "title_thumbnail_permission": permission}


def make_reference(status="supported", *, reference_id="MR-001", usage=None, public_mode=None):
    entry = MEMORY_ENTRIES[status]
    if usage is None:
        usage = make_usage(reference_id=reference_id)
    if public_mode is None:
        public_mode = {"supported": "current_supported_context", "partially_supported": "historical_comparison", "weakened": "counterevidence", "invalidated": "correction", "unresolved": "monitoring_point", "historical_context_only": "historical_comparison", "not_used": "internal_only"}[status]
    return {"reference_id": reference_id, "memory_reference_type": entry["memory_reference_type"], "memory_reference_id": entry["memory_reference_id"], "historical_confidence": entry["historical_confidence"], "current_revalidation_status": entry["revalidation_status"], "dossier_editorial_use": entry["editorial_use"], "dossier_current_evidence_ids": entry["current_evidence_ids"], "difference_from_previous": entry["difference_from_previous"], "public_usage_mode": public_mode, "scope_limit": "Company-level only; index-wide transmission remains unconfirmed." if status == "partially_supported" else "", "usages": [] if status == "not_used" else [usage]}


def surface_block(usage):
    anchor_marker = usage["anchor_text"] + usage["marker"]
    surface = usage["surface"]
    if surface == "title":
        return f"## C. タイトル\n{anchor_marker}\n"
    if surface == "thumbnail":
        return f"## D. サムネイル文言\n{anchor_marker}\n"
    if surface == "description":
        return f"## E. 概要欄\n{anchor_marker}\n"
    scene_no = int(usage["scene_id"].split("-")[1])
    heading = {"scene_narration": "ナレーション", "scene_connection": "前後の接続文", "main_telop": "大テロップ", "support_telop": "補助テロップ", "visual_text": "画面で伝える内容"}[surface]
    return f"## B. Scene {scene_no}｜Test\n### {heading}\n{anchor_marker}\n"


def build_markdown(annex, *, extra_public="", duplicate_annex=False, malformed=False):
    blocks = [surface_block(usage) for ref in annex["references"] for usage in ref["usages"]]
    blocks.append(extra_public)
    json_text = "{" if malformed else json.dumps(annex, ensure_ascii=False, indent=2)
    annex_block = "## I. Editorial Memory Usage Annex\n\n<!--BEGIN_EPISODE_MEMORY_ANNEX-->\n```json\n" + json_text + "\n```\n<!--END_EPISODE_MEMORY_ANNEX-->\n"
    if duplicate_annex:
        annex_block += annex_block
    return "\n".join(blocks) + "\n" + annex_block


class Harness:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "episodes/2026-08-06").mkdir(parents=True)
        (self.root / "research/2026-08-06").mkdir(parents=True)
        schema_src = ROOT / "skills/nasdaq-cafe-episode-package-memory/contracts/episode_package_memory_annex.schema.json"
        schema_dst = self.root / "skills/nasdaq-cafe-episode-package-memory/contracts/episode_package_memory_annex.schema.json"
        schema_dst.parent.mkdir(parents=True)
        schema_dst.write_bytes(schema_src.read_bytes())
        self.schema = schema_dst

    def close(self):
        self.tmp.cleanup()

    def dossier(self):
        return {"episode_date": "2026-08-06", "research_input_manifest": {"path": "research/2026-08-06/research_input_manifest.json", "sha256": "0" * 64}, "validation": {"status": "pass"}, "evidence": copy.deepcopy(EVIDENCE), "memory_revalidation": [copy.deepcopy(item) for item in MEMORY_ENTRIES.values()]}

    def write(self, annex, *, dossier=None, markdown=None, extra_public=""):
        dossier = dossier or self.dossier()
        dossier_path = self.root / "research/2026-08-06/causal_research_dossier_2026-08-06.json"
        dossier_path.write_text(json.dumps(dossier, ensure_ascii=False, indent=2), encoding="utf-8")
        annex["causal_dossier"] = {"path": "research/2026-08-06/causal_research_dossier_2026-08-06.json", "sha256": hashlib.sha256(dossier_path.read_bytes()).hexdigest()}
        package_path = self.root / "episodes/2026-08-06/episode_package_2026-08-06.md"
        package_path.write_text(markdown if markdown is not None else build_markdown(annex, extra_public=extra_public), encoding="utf-8")
        return package_path

    def validate(self, annex, *, dossier=None, markdown=None, replay=replay_pass, extra_public=""):
        package_path = self.write(annex, dossier=dossier, markdown=markdown, extra_public=extra_public)
        return validator.validate_episode_package_memory(repo_root=self.root, episode_package_path=package_path, schema_path=self.schema, dossier_replay=replay)


def base_annex(reference=None):
    return {"contract_version": "1.0.0", "episode_date": "2026-08-06", "causal_dossier": {"path": "placeholder", "sha256": "0" * 64}, "references": [] if reference is None else [reference], "validation_intent": {"past_mentions_complete": True, "title_thumbnail_checked": True, "post_inquisition_final": True}}


class EpisodePackageMemoryTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
    def tearDown(self):
        self.h.close()
    def assertPass(self, annex, **kwargs):
        result = self.h.validate(annex, **kwargs); self.assertEqual([], result.errors, result.errors)
    def assertFail(self, annex, needle, **kwargs):
        result = self.h.validate(annex, **kwargs); self.assertTrue(any(needle in item for item in result.errors), result.errors)

    def test_01_memory_free_episode(self): self.assertPass(base_annex())
    def test_02_supported_current_context(self): self.assertPass(base_annex(make_reference("supported")))
    def test_03_supported_historical_comparison(self): self.assertPass(base_annex(make_reference("supported", usage=make_usage(claim_mode="historical", wording_strength="historical"), public_mode="historical_comparison")))
    def test_04_partially_supported_qualified_comparison(self): self.assertPass(base_annex(make_reference("partially_supported", usage=make_usage(claim_mode="historical", wording_strength="qualified"))))
    def test_05_weakened_counterevidence(self): self.assertPass(base_annex(make_reference("weakened", usage=make_usage(scene_id="SCENE-07", claim_mode="counterevidence", evidence_ids=["E-002"]))))
    def test_06_invalidated_correction(self): self.assertPass(base_annex(make_reference("invalidated", usage=make_usage(scene_id="SCENE-07", claim_mode="correction", evidence_ids=["E-001"], wording_strength="corrective"))))
    def test_07_unresolved_scene8_monitoring(self): self.assertPass(base_annex(make_reference("unresolved", usage=make_usage(scene_id="SCENE-08", claim_mode="monitoring", evidence_ids=[], wording_strength="uncertain"))))
    def test_08_historical_only_background(self): self.assertPass(base_annex(make_reference("historical_context_only", usage=make_usage(scene_id="SCENE-02", claim_mode="historical", evidence_ids=[], wording_strength="historical"))))
    def test_09_supported_description_reference(self): self.assertPass(base_annex(make_reference("supported", usage=make_usage(surface="description", scene_id=None, claim_mode="historical", wording_strength="historical"), public_mode="historical_comparison")))
    def test_10_multiple_memories(self):
        ref1 = make_reference("supported", reference_id="MR-001")
        ref2 = make_reference("weakened", reference_id="MR-002", usage=make_usage(reference_id="MR-002", usage_id="U-002", scene_id="SCENE-07", anchor="The earlier relationship is weaker today.", claim_mode="counterevidence", evidence_ids=["E-002"]))
        annex = base_annex(); annex["references"] = [ref1, ref2]; self.assertPass(annex)
    def test_11_missing_annex(self):
        annex=base_annex(); package=self.h.write(annex); package.write_text("## B. Scene 1\nNo annex\n"); result=validator.validate_episode_package_memory(repo_root=self.h.root, episode_package_path=package, schema_path=self.h.schema, dossier_replay=replay_pass); self.assertTrue(any("annex markers" in e for e in result.errors))
    def test_12_duplicate_annex(self):
        annex=base_annex(); package=self.h.write(annex); package.write_text(build_markdown(annex, duplicate_annex=True)); result=validator.validate_episode_package_memory(repo_root=self.h.root, episode_package_path=package, schema_path=self.h.schema, dossier_replay=replay_pass); self.assertTrue(any("annex markers" in e for e in result.errors))
    def test_13_malformed_annex_json(self):
        annex=base_annex(); package=self.h.write(annex); package.write_text(build_markdown(annex, malformed=True)); result=validator.validate_episode_package_memory(repo_root=self.h.root, episode_package_path=package, schema_path=self.h.schema, dossier_replay=replay_pass); self.assertTrue(any("JSON" in e for e in result.errors))
    def test_14_schema_missing_post_inquisition(self):
        annex=base_annex(); del annex["validation_intent"]["post_inquisition_final"]; self.assertFail(annex,"post_inquisition_final")
    def test_15_dossier_path_traversal(self):
        annex=base_annex(); package=self.h.write(annex); annex["causal_dossier"]={"path":"../../outside.json","sha256":"0"*64}; package.write_text(build_markdown(annex)); result=validator.validate_episode_package_memory(repo_root=self.h.root, episode_package_path=package, schema_path=self.h.schema, dossier_replay=replay_pass); self.assertTrue(any("escapes repository root" in e for e in result.errors))
    def test_16_stale_dossier_sha(self):
        annex=base_annex(); package=self.h.write(annex); package.write_text(package.read_text().replace(annex["causal_dossier"]["sha256"],"f"*64)); result=validator.validate_episode_package_memory(repo_root=self.h.root, episode_package_path=package, schema_path=self.h.schema, dossier_replay=replay_pass); self.assertTrue(any("SHA-256 mismatch" in e for e in result.errors))
    def test_17_episode_date_mismatch(self):
        annex=base_annex(); annex["episode_date"]="2026-08-07"; self.assertFail(annex,"episode date mismatch")
    def test_18_pr6_replay_failure(self): self.assertFail(base_annex(),"PR6 dossier replay",replay=replay_fail)
    def test_19_unknown_memory(self):
        ref=make_reference("supported"); ref["memory_reference_id"]="missing"; self.assertFail(base_annex(ref),"not present in dossier")
    def test_20_status_tamper(self):
        ref=make_reference("supported"); ref["current_revalidation_status"]="weakened"; self.assertFail(base_annex(ref),"differs from dossier")
    def test_21_confidence_tamper(self):
        ref=make_reference("supported"); ref["historical_confidence"]="high"; self.assertFail(base_annex(ref),"historical_confidence differs")
    def test_22_editorial_use_tamper(self):
        ref=make_reference("supported"); ref["dossier_editorial_use"]="comparison"; self.assertFail(base_annex(ref),"dossier_editorial_use differs")
    def test_23_current_evidence_tamper(self):
        ref=make_reference("supported"); ref["dossier_current_evidence_ids"]=["E-001"]; self.assertFail(base_annex(ref),"dossier_current_evidence_ids differs")
    def test_24_difference_tamper(self):
        ref=make_reference("supported"); ref["difference_from_previous"]="rewritten"; self.assertFail(base_annex(ref),"difference_from_previous differs")
    def test_25_duplicate_reference_id(self):
        ref1=make_reference("supported",reference_id="MR-001"); ref2=make_reference("weakened",reference_id="MR-001",usage=make_usage(reference_id="MR-001",usage_id="U-002",scene_id="SCENE-07",claim_mode="counterevidence",evidence_ids=["E-002"])); annex=base_annex(); annex["references"]=[ref1,ref2]; self.assertFail(annex,"duplicate reference_id")
    def test_26_same_memory_twice(self):
        ref1=make_reference("supported"); ref2=copy.deepcopy(ref1); ref2["reference_id"]="MR-002"; ref2["usages"][0]["usage_id"]="U-002"; ref2["usages"][0]["marker"]="<!--MEMREF:MR-002:U-002-->"; annex=base_annex(); annex["references"]=[ref1,ref2]; self.assertFail(annex,"same memory appears more than once")
    def test_27_duplicate_usage_id(self):
        ref1=make_reference("supported"); ref2=make_reference("weakened",reference_id="MR-002",usage=make_usage(reference_id="MR-002",usage_id="U-001",scene_id="SCENE-07",claim_mode="counterevidence",evidence_ids=["E-002"])); annex=base_annex(); annex["references"]=[ref1,ref2]; self.assertFail(annex,"duplicate usage_id")
    def test_28_missing_marker(self):
        ref=make_reference("supported"); annex=base_annex(ref); package=self.h.write(annex); package.write_text(package.read_text().replace(ref["usages"][0]["marker"],"",1)); result=validator.validate_episode_package_memory(repo_root=self.h.root, episode_package_path=package, schema_path=self.h.schema, dossier_replay=replay_pass); self.assertTrue(result.errors)
    def test_29_orphan_marker(self): self.assertFail(base_annex(),"orphan MEMREF",extra_public="## B. Scene 2｜Test\n### ナレーション\nPast.<!--MEMREF:MR-999:U-999-->")
    def test_30_duplicate_marker(self):
        ref=make_reference("supported"); self.assertFail(base_annex(ref),"marker must appear exactly once",extra_public=ref["usages"][0]["marker"])
    def test_31_missing_anchor(self):
        ref=make_reference("supported"); annex=base_annex(ref); package=self.h.write(annex); package.write_text(package.read_text().replace(ref["usages"][0]["anchor_text"],"Different text",1)); result=validator.validate_episode_package_memory(repo_root=self.h.root, episode_package_path=package, schema_path=self.h.schema, dossier_replay=replay_pass); self.assertTrue(any("anchor_text" in e for e in result.errors))
    def test_32_duplicate_anchor(self):
        ref=make_reference("supported"); self.assertFail(base_annex(ref),"anchor_text must appear exactly once",extra_public=ref["usages"][0]["anchor_text"])
    def test_33_wrong_scene(self):
        ref=make_reference("supported"); annex=base_annex(ref); package=self.h.write(annex); mutated=copy.deepcopy(annex); mutated["references"][0]["usages"][0]["scene_id"]="SCENE-04"; public=package.read_text().split("## I. Editorial Memory Usage Annex",1)[0]; annex_part=build_markdown(mutated).split("## I. Editorial Memory Usage Annex",1)[1]; package.write_text(public+"## I. Editorial Memory Usage Annex"+annex_part); result=validator.validate_episode_package_memory(repo_root=self.h.root,episode_package_path=package,schema_path=self.h.schema,dossier_replay=replay_pass); self.assertTrue(any("scene mismatch" in e for e in result.errors))
    def test_34_wrong_surface(self):
        ref=make_reference("supported"); annex=base_annex(ref); package=self.h.write(annex); mutated=copy.deepcopy(annex); mutated["references"][0]["usages"][0]["surface"]="main_telop"; public=package.read_text().split("## I. Editorial Memory Usage Annex",1)[0]; annex_part=build_markdown(mutated).split("## I. Editorial Memory Usage Annex",1)[1]; package.write_text(public+"## I. Editorial Memory Usage Annex"+annex_part); result=validator.validate_episode_package_memory(repo_root=self.h.root,episode_package_path=package,schema_path=self.h.schema,dossier_replay=replay_pass); self.assertTrue(any("surface mismatch" in e for e in result.errors))
    def test_35_marker_not_immediate(self):
        ref=make_reference("supported"); annex=base_annex(ref); package=self.h.write(annex); package.write_text(package.read_text().replace(ref["usages"][0]["anchor_text"]+ref["usages"][0]["marker"],ref["usages"][0]["anchor_text"]+" extra "+ref["usages"][0]["marker"])); result=validator.validate_episode_package_memory(repo_root=self.h.root,episode_package_path=package,schema_path=self.h.schema,dossier_replay=replay_pass); self.assertTrue(any("immediately follow" in e for e in result.errors))
    def test_36_partial_current_context_forbidden(self): self.assertFail(base_annex(make_reference("partially_supported",public_mode="current_supported_context")),"forbidden for status")
    def test_37_partial_scope_required(self):
        ref=make_reference("partially_supported"); ref["scope_limit"]=""; self.assertFail(base_annex(ref),"requires scope_limit")
    def test_38_partial_current_fact_forbidden(self):
        ref=make_reference("partially_supported"); ref["usages"][0]["claim_mode"]="current_fact"; self.assertFail(base_annex(ref),"cannot be presented as a current fact")
    def test_39_weakened_direct_claim_forbidden(self):
        ref=make_reference("weakened"); ref["usages"][0]["claim_mode"]="current_fact"; ref["usages"][0]["wording_strength"]="direct"; self.assertFail(base_annex(ref),"weakened memory")
    def test_40_invalidated_noncorrective_forbidden(self):
        ref=make_reference("invalidated"); ref["usages"][0]["claim_mode"]="historical"; self.assertFail(base_annex(ref),"requires correction or counterevidence")
    def test_41_unresolved_wrong_scene(self):
        ref=make_reference("unresolved"); ref["usages"][0]["scene_id"]="SCENE-07"; self.assertFail(base_annex(ref),"limited to SCENE-08")
    def test_42_historical_only_current_fact_forbidden(self):
        ref=make_reference("historical_context_only"); ref["usages"][0]["claim_mode"]="current_fact"; self.assertFail(base_annex(ref),"must use historical claim_mode")
    def test_43_not_used_public_usage_forbidden(self):
        ref=make_reference("not_used"); ref["usages"]=[make_usage()]; self.assertFail(base_annex(ref),"not_used memory cannot have public usages")
    def test_44_internal_only_public_usage_forbidden(self): self.assertFail(base_annex(make_reference("unresolved",public_mode="internal_only")),"internal_only memory cannot have public usages")
    def test_45_usage_evidence_not_subset(self):
        ref=make_reference("supported"); ref["usages"][0]["evidence_ids"]=["E-003"]; self.assertFail(base_annex(ref),"subset of dossier current evidence")
    def test_46_current_usage_requires_evidence(self):
        ref=make_reference("supported"); ref["usages"][0]["evidence_ids"]=[]; self.assertFail(base_annex(ref),"requires current evidence")
    def test_47_low_quality_current_evidence(self):
        ref=make_reference("supported"); ref["dossier_current_evidence_ids"]=["E-003"]; ref["usages"][0]["evidence_ids"]=["E-003"]; dossier=self.h.dossier(); next(x for x in dossier["memory_revalidation"] if x["memory_reference_id"]=="supported-claim")["current_evidence_ids"]=["E-003"]; self.assertFail(base_annex(ref),"not tier-1/tier-2",dossier=dossier)
    def test_48_scene4_current_memory_forbidden(self):
        ref=make_reference("supported"); ref["usages"][0]["scene_id"]="SCENE-04"; self.assertFail(base_annex(ref),"Scene 4 Expected")
    def test_49_scene6_current_memory_forbidden(self):
        ref=make_reference("supported"); ref["usages"][0]["scene_id"]="SCENE-06"; self.assertFail(base_annex(ref),"Scene 6 price causality")
    def test_50_unresolved_scene1_forbidden(self):
        ref=make_reference("unresolved"); ref["usages"][0]["scene_id"]="SCENE-01"; self.assertFail(base_annex(ref),"limited to SCENE-08")
    def test_51_partial_title_forbidden(self): self.assertFail(base_annex(make_reference("partially_supported",usage=make_usage(surface="title",scene_id=None,claim_mode="historical",permission="allowed"))),"only supported memory may be used")
    def test_52_supported_title_requires_permission(self): self.assertFail(base_annex(make_reference("supported",usage=make_usage(surface="title",scene_id=None,claim_mode="current_fact",permission="forbidden"))),"requires permission=allowed")
    def test_53_supported_title_overclaim(self): self.assertFail(base_annex(make_reference("supported",usage=make_usage(surface="title",scene_id=None,anchor="前回予測が的中",claim_mode="current_fact",permission="allowed"))),"overclaims remembered material")
    def test_54_concrete_fox_history_forbidden(self): self.assertFail(base_annex(),"fox personal-history",extra_public="僕も履修登録で失敗しました。")
    def test_55_episode_path_outside_root(self):
        with tempfile.NamedTemporaryFile("w",suffix=".md",delete=False) as handle: outside=Path(handle.name); handle.write("x")
        try:
            result=validator.validate_episode_package_memory(repo_root=self.h.root,episode_package_path=outside,schema_path=self.h.schema,dossier_replay=replay_pass); self.assertTrue(any("escapes repository root" in e for e in result.errors))
        finally: outside.unlink(missing_ok=True)

if __name__ == "__main__": unittest.main()
