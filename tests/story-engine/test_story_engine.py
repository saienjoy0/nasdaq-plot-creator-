from __future__ import annotations
import copy, hashlib, importlib.util, json, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).parents[2]
V=ROOT/"skills/nasdaq-cafe-story-engine/validators/validate_story_engine_package.py"
S=ROOT/"skills/nasdaq-cafe-story-engine/contracts/story_engine_package.schema.json"
spec=importlib.util.spec_from_file_location("sev",V);sev=importlib.util.module_from_spec(spec);assert spec and spec.loader;sys.modules[spec.name]=sev;spec.loader.exec_module(sev)
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
class Harness:
 def __init__(self,kind="single",blocked=False):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.kind=kind
  for name in ["dossier.json","01.md","02.md","03.md","04.md"]:(self.root/name).write_text(name)
  self.draft=self.root/"draft.md";self.final=self.root/"final.md";text="# Episode\n僕が整理します。";self.draft.write_text(text);self.final.write_text(text)
  refs={n:{"path":n,"sha256":h(self.root/n)} for n in ["dossier.json","01.md","02.md","03.md","04.md"]}
  scenes=[];roles=["hook","setup","proof","complication","reveal","counterevidence","implication","callback","button"]
  for i in range(1,10):scenes.append({"scene_id":f"scene-{i:02d}","official_role":str(i),"story_roles":[roles[i-1]],"viewer_belief_before":"before","new_evidence_ids":["E-001"] if i<5 else [],"new_meaning":"meaning" if i>=5 else "","viewer_belief_after":"after","connector":"therefore","open_loop_ids_opened":["OL-01"] if i==1 else [],"open_loop_ids_closed":["OL-01"] if i==8 else [],"deletion_consequence":"lost"})
  finding={"finding_id":"CR-001","code":"REPEATED_CONCLUSION","severity":"critical","scene_ids":["scene-03"],"field_paths":["scene-03.narration"],"anchor_text":"anchor","viewer_effect":"effect","required_fix":"fix","must_preserve":{"claim_ids":["CL-001"],"evidence_ids":["E-001"],"causal_scope":"company","confidence":"medium"},"status":"pending" if blocked else "fixed"}
  findings=[finding] if blocked else []
  self.pkg={"contract_version":"1.1.0","episode_date":"2026-08-06","mode":"shadow","source_binding":{"story_engine_skill_version":"1.1.0","author_invocation_id":"author","critic_invocation_id":"critic","critic_isolation_mode":"logical_shadow","files":refs},"editorial_baseline":{"lead":"lead","lead_type":"reason_unknown" if kind=="unknown" else ("composite" if kind=="multi" else "news"),"central_hypothesis":"hypothesis","story_spine":"spine","expected_actual_gap":{},"primary_driver":None if kind=="unknown" else "driver","amplifiers":["amp"] if kind=="multi" else [],"offsets":["off"] if kind=="multi" else [],"unresolved_factors":["unknown"] if kind=="unknown" else [],"causality_scope":"reason_unknown" if kind=="unknown" else ("nasdaq_support" if kind=="multi" else "company"),"confidence":"unknown" if kind=="unknown" else "medium","evidence_ids":["E-001","E-002"],"counterevidence_ids":["E-003"],"timeline":["A before B"]},"claim_ledger":[{"claim_id":"CL-001","claim_type":"unknown" if kind=="unknown" else "inference","causal_scope":"reason_unknown" if kind=="unknown" else "company","confidence":"unknown" if kind=="unknown" else "medium","evidence_ids":["E-001"],"counterevidence_ids":["E-003"],"required_modality":"limited"}],"story_discovery":{"obvious_headline":"headline","before_context":["context"],"central_contradiction":"contradiction","naive_explanations":[{}],"headline_beyond_discovery":"discovery","after_implications":["condition"],"angle_candidates":[{"angle_id":"A-001","angle_type":"reason_unknown" if kind=="unknown" else "contradiction","central_question":"q","story_spine":"spine","supported_claim_ids":["CL-001"],"eligible":True}],"angle_generation_note":"one supported angle"},"selected_angle":{"angle_id":"A-001","central_question":"q","story_spine":"spine","opening_promise":"promise","closing_reframe":"reframe","why_selected":"fit","rejected_angle_ids":[]},"narrative_arc":{"central_question":"q","opening_promise":"promise","closing_reframe":"reframe","open_loops":[{"loop_id":"OL-01","opened_scene":1,"close_status":"evidence_backed_unresolved" if kind=="unknown" else "closed","closed_scene":8}],"scenes":scenes},"author_draft":{"episode_package":{"path":"draft.md","sha256":h(self.draft)},"story_spine":"spine","scene_count":9,"surfaces_complete":{"narration":True,"visuals":True}},"review_rounds":[{"round":1,"critic_invocation_id":"critic","input_episode_package_sha256":h(self.draft),"decision":"blocked" if blocked else "pass","findings":findings,"patches":[],"output_episode_package":{"path":"final.md","sha256":h(self.final)}}],"causality_diff":{"status":"not_run" if blocked else "pass","compared_from_sha256":h(self.draft),"compared_to_sha256":h(self.final),"preserved_claim_ids":["CL-001"],"violation_codes":[],"notes":""},"final":{"episode_package":{"path":"final.md","sha256":h(self.final)},"review_status":"blocked" if blocked else "pass","final_review_round":1},"final_gate":{"status":"blocked" if blocked else "pass","blocking_codes":["REPEATED_CONCLUSION"] if blocked else [],"production_eligible":False}}
  self.path=self.root/"package.json";self.save()
 def save(self):self.path.write_text(json.dumps(self.pkg))
 def validate(self):self.save();return sev.validate(self.path,S,self.root)
 def close(self):self.t.cleanup()
class Tests(unittest.TestCase):
 def test_three_valid_modes(self):
  for kind in ["single","multi","unknown"]:
   harn=Harness(kind);self.addCleanup(harn.close);self.assertEqual("pass",harn.validate()["status"])
 def test_boring_fixture_blocks(self):
  harn=Harness(blocked=True);self.addCleanup(harn.close);codes={e["code"] for e in harn.validate()["errors"]};self.assertTrue({"E_CRITICAL_FINDING","E_CAUSALITY_DIFF","E_FINAL_REVIEW","E_FINAL_GATE"}<=codes)
 def test_independent_critic(self):
  harn=Harness();self.addCleanup(harn.close);harn.pkg["source_binding"]["critic_invocation_id"]="author";self.assertIn("E_INVOCATION_NOT_INDEPENDENT",{e["code"] for e in harn.validate()["errors"]})
 def test_production_requires_real_critic_isolation(self):
  harn=Harness();self.addCleanup(harn.close);harn.pkg["mode"]="production";harn.pkg["final_gate"]["production_eligible"]=True;self.assertIn("E_CRITIC_ISOLATION",{e["code"] for e in harn.validate()["errors"]})
 def test_shadow_cannot_claim_production_eligibility(self):
  harn=Harness();self.addCleanup(harn.close);harn.pkg["final_gate"]["production_eligible"]=True;self.assertIn("E_SHADOW_PRODUCTION_ELIGIBILITY",{e["code"] for e in harn.validate()["errors"]})
 def test_scene_order(self):
  harn=Harness();self.addCleanup(harn.close);harn.pkg["narrative_arc"]["scenes"].reverse();self.assertIn("E_SCENE_SEQUENCE",{e["code"] for e in harn.validate()["errors"]})
 def test_hash_binding(self):
  harn=Harness();self.addCleanup(harn.close);harn.pkg["final"]["episode_package"]["sha256"]="0"*64;self.assertIn("E_HASH",{e["code"] for e in harn.validate()["errors"]})
 def test_committed_shadow_package_passes(self):
  package=ROOT/"working/2026-08-06/story-engine-shadow/story_engine_package_2026-08-06.json";result=sev.validate(package,S,ROOT);self.assertEqual("pass",result["status"],result)
 def test_committed_shadow_expected_findings(self):
  path=ROOT/"skills/nasdaq-cafe-story-engine/fixtures/boring_2026-08-06/critic_review_round1.json";codes={x["code"] for x in json.loads(path.read_text())["findings"]};self.assertEqual({"HOOK_EXHAUSTS_THE_STORY","REPEATED_CONCLUSION","NO_BELIEF_CHANGE","PROCEDURAL_NARRATION","NO_LATE_PAYOFF","FOX_VOICE_ABSENT"},codes)
 def test_committed_shadow_causality_preserved(self):
  package=json.loads((ROOT/"working/2026-08-06/story-engine-shadow/story_engine_package_2026-08-06.json").read_text());self.assertEqual("pass",package["causality_diff"]["status"]);self.assertEqual({x["claim_id"] for x in package["claim_ledger"]},set(package["causality_diff"]["preserved_claim_ids"]))
if __name__=="__main__":unittest.main()
