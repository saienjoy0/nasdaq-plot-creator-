from __future__ import annotations
import importlib.util, json, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).parents[2]
SCRIPT=ROOT/"scripts/run_daily_production.py"
spec=importlib.util.spec_from_file_location("daily",SCRIPT)
daily=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(daily)

DATE="2026-08-06"; RENDERER="b"*40

class Harness:
  def __init__(self):
    self.t=tempfile.TemporaryDirectory(); self.root=Path(self.t.name)
    self.source=self.root/f"daily_source_package_{DATE}.md"; self.source.write_text("# source")
  def close(self):self.t.cleanup()
  def init(self,**kw):
    p={"workspace":self.root,"date":DATE,"daily_source":self.source,"requested_scope":"preview","renderer_commit":RENDERER,"renderer_contract_version":"2.2.0"};p.update(kw)
    return daily.init_request(**p)
  def evidence(self,name="evidence.json",data=None):
    p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
    if data is None:data={"status":"pass"}
    p.write_text(json.dumps(data));return p
  def advance_to(self,target):
    if not daily.request_path(self.root,DATE).exists():self.init()
    current=daily.status(workspace=self.root,date=DATE)["current_state"]
    while current!=target:
      nxt=daily.STATES[daily.STATES.index(current)+1]
      daily.add_transition(workspace=self.root,date=DATE,new_state=nxt,evidence_paths=[self.evidence(f"evidence/{nxt}.json")])
      current=nxt
  def approval(self,**kw):
    d={"episode_date":DATE,"status":"approved","final_requested":True};d.update(kw)
    return self.evidence("approval.json",d)

class Tests(unittest.TestCase):
  def setUp(self):self.h=Harness()
  def tearDown(self):self.h.close()
  def assertCode(self,code,fn,*a,**kw):
    with self.assertRaises(daily.DailyProductionError) as cm:fn(*a,**kw)
    self.assertEqual(code,cm.exception.code)
  def test_01_init_created(self):
    r=self.h.init();self.assertEqual("created",r["status"]);self.assertEqual("intake_ready",r["current_state"])
  def test_02_init_identical_noop(self):
    self.h.init();r=self.h.init();self.assertEqual("noop",r["status"])
  def test_03_date_filename_mismatch(self):
    p=self.h.root/"daily.md";p.write_text("x");self.assertCode(daily.ERROR_CODES["date"],daily.init_request,workspace=self.h.root,date=DATE,daily_source=p,requested_scope="preview",renderer_commit=RENDERER,renderer_contract_version="2.2.0")
  def test_04_empty_source(self):
    self.h.source.write_text("");self.assertCode(daily.ERROR_CODES["stale"],self.h.init)
  def test_05_final_scope_forbidden(self):
    self.assertCode(daily.ERROR_CODES["final"],self.h.init,requested_scope="final")
  def test_06_renderer_sha_length(self):
    self.assertCode(daily.ERROR_CODES["renderer"],self.h.init,renderer_commit="x")
  def test_07_renderer_sha_hex(self):
    self.assertCode(daily.ERROR_CODES["renderer"],self.h.init,renderer_commit="z"*40)
  def test_08_status_pass(self):
    self.h.init();self.assertEqual("pass",daily.status(workspace=self.h.root,date=DATE)["validation"]["status"])
  def test_09_source_change_stale(self):
    self.h.init();self.h.source.write_text("changed");self.assertEqual("fail",daily.status(workspace=self.h.root,date=DATE)["validation"]["status"])
  def test_10_request_change_stale(self):
    self.h.init();p=daily.request_path(self.h.root,DATE);p.write_text(p.read_text()+" ");self.assertEqual("fail",daily.status(workspace=self.h.root,date=DATE)["validation"]["status"])
  def test_11_missing_state(self):
    self.h.init();daily.state_path(self.h.root,DATE).unlink();self.assertCode(daily.ERROR_CODES["stale"],daily.status,workspace=self.h.root,date=DATE)
  def test_12_advance_one_state(self):
    self.h.init();r=daily.add_transition(workspace=self.h.root,date=DATE,new_state="research_inputs_bound",evidence_paths=[self.h.evidence()]);self.assertEqual("research_inputs_bound",r["current_state"])
  def test_13_skip_state_rejected(self):
    self.h.init();self.assertCode(daily.ERROR_CODES["stale"],daily.add_transition,workspace=self.h.root,date=DATE,new_state="causal_dossier_valid",evidence_paths=[self.h.evidence()])
  def test_14_regression_rejected(self):
    self.h.advance_to("research_inputs_bound");self.assertCode(daily.ERROR_CODES["stale"],daily.add_transition,workspace=self.h.root,date=DATE,new_state="intake_ready",evidence_paths=[self.h.evidence()])
  def test_15_no_evidence_rejected(self):
    self.h.init();self.assertCode(daily.ERROR_CODES["stale"],daily.add_transition,workspace=self.h.root,date=DATE,new_state="research_inputs_bound",evidence_paths=[])
  def test_16_missing_evidence_rejected(self):
    self.h.init();self.assertCode(daily.ERROR_CODES["stale"],daily.add_transition,workspace=self.h.root,date=DATE,new_state="research_inputs_bound",evidence_paths=[self.h.root/"missing"])
  def test_17_modified_evidence_stale(self):
    self.h.init();p=self.h.evidence();daily.add_transition(workspace=self.h.root,date=DATE,new_state="research_inputs_bound",evidence_paths=[p]);p.write_text("changed");self.assertEqual("fail",daily.status(workspace=self.h.root,date=DATE)["validation"]["status"])
  def test_18_same_state_noop(self):
    self.h.init();r=daily.add_transition(workspace=self.h.root,date=DATE,new_state="intake_ready",evidence_paths=[self.h.evidence()]);self.assertEqual("noop",r["status"])
  def test_19_package_scope_preview_false(self):
    self.h.init(requested_scope="package");q=json.loads(daily.request_path(self.h.root,DATE).read_text());self.assertFalse(q["approvals"]["preview_requested"])
  def test_20_preview_scope_true(self):
    self.h.init();q=json.loads(daily.request_path(self.h.root,DATE).read_text());self.assertTrue(q["approvals"]["preview_requested"])
  def test_21_request_final_requires_explicit(self):
    self.h.advance_to("user_preview_approved");self.assertCode(daily.ERROR_CODES["final"],daily.request_final,workspace=self.h.root,date=DATE,approval_record=self.h.approval(),explicit_final=False)
  def test_22_request_final_requires_approved_state(self):
    self.h.init();self.assertCode(daily.ERROR_CODES["final"],daily.request_final,workspace=self.h.root,date=DATE,approval_record=self.h.approval(),explicit_final=True)
  def test_23_approval_date(self):
    self.h.advance_to("user_preview_approved");self.assertCode(daily.ERROR_CODES["final"],daily.request_final,workspace=self.h.root,date=DATE,approval_record=self.h.approval(episode_date="2026-08-07"),explicit_final=True)
  def test_24_approval_status(self):
    self.h.advance_to("user_preview_approved");self.assertCode(daily.ERROR_CODES["final"],daily.request_final,workspace=self.h.root,date=DATE,approval_record=self.h.approval(status="pending"),explicit_final=True)
  def test_25_approval_final_flag(self):
    self.h.advance_to("user_preview_approved");self.assertCode(daily.ERROR_CODES["final"],daily.request_final,workspace=self.h.root,date=DATE,approval_record=self.h.approval(final_requested=False),explicit_final=True)
  def test_26_valid_final_request(self):
    self.h.advance_to("user_preview_approved");r=daily.request_final(workspace=self.h.root,date=DATE,approval_record=self.h.approval(),explicit_final=True);self.assertEqual("final_requested",r["current_state"]);self.assertEqual("pass",daily.status(workspace=self.h.root,date=DATE)["validation"]["status"])
  def test_27_build_production_wrong_state(self):
    self.h.init();self.assertCode(daily.ERROR_CODES["package"],daily.build_production,workspace=self.h.root,date=DATE,episode_package=self.h.evidence("episode.md"))
  def test_28_build_handoff_wrong_state(self):
    self.h.init();self.assertCode(daily.ERROR_CODES["handoff"],daily.build_handoff,workspace=self.h.root,date=DATE,bundle_root=self.h.root/"bundles",plot_commit="a"*40)
  def test_29_record_preview_wrong_state(self):
    self.h.init();self.assertCode(daily.ERROR_CODES["preview"],daily.record_preview,workspace=self.h.root,date=DATE,daily_source_root=self.h.root,bundle_root=self.h.root,handoff_manifest=self.h.evidence(),renderer_artifact_root=self.h.root,technical_report=self.h.evidence(),user_review=None)
  def test_30_safe_path_escape(self):
    out=Path(tempfile.gettempdir())/"outside-daily-test";out.write_text("x")
    try:self.assertCode(daily.ERROR_CODES["stale"],daily.safe_path,self.h.root,out,"outside")
    finally:out.unlink(missing_ok=True)
  def test_31_transition_count(self):
    self.h.advance_to("causal_dossier_valid");s=json.loads(daily.state_path(self.h.root,DATE).read_text());self.assertEqual(3,len(s["transitions"]))
  def test_32_build_production_success(self):
    self.h.advance_to("assets_resolved");pkg=self.h.evidence(f"episode_package_{DATE}.md")
    original=daily.final_builder.build
    def fake(package,workspace,schema):
      paths={}
      for key,rel in {"ir":f"working/{DATE}/ir.json","spoken_script":f"episodes/{DATE}/spoken.md","asset_manifest":f"episodes/{DATE}/assets.json","render_spec":f"render-specs/{DATE}/render_spec.json","consistency_report":f"verification/{DATE}/consistency.json","preflight":f"verification/{DATE}/preflight.json"}.items():
        p=self.h.evidence(rel);paths[key]=str(p)
      return {"status":"pass","paths":paths}
    daily.final_builder.build=fake
    try:r=daily.build_production(workspace=self.h.root,date=DATE,episode_package=pkg);self.assertEqual("pass",r["status"]);self.assertEqual("production_package_valid",daily.status(workspace=self.h.root,date=DATE)["current_state"])
    finally:daily.final_builder.build=original
  def test_33_build_handoff_success(self):
    self.h.advance_to("production_package_valid");m=self.h.evidence("bundle/handoff_manifest.json")
    original=daily.handoff_builder.build_handoff;daily.handoff_builder.build_handoff=lambda **kw:{"status":"created","manifest_path":str(m)}
    try:r=daily.build_handoff(workspace=self.h.root,date=DATE,bundle_root=self.h.root/"bundles",plot_commit="a"*40);self.assertEqual("created",r["status"]);self.assertEqual("handoff_ready",daily.status(workspace=self.h.root,date=DATE)["current_state"])
    finally:daily.handoff_builder.build_handoff=original
  def test_34_record_preview_pending(self):
    self.h.advance_to("handoff_ready")
    orig_v=daily.acceptance_runner.validate_acceptance;orig_w=daily.acceptance_runner.write_report
    report={"mvp_status":"preview_ready_user_review_pending","user_review":{"status":"pending"}}
    p1=self.h.evidence(f"verification/real-day-acceptance/{DATE}/report.json");p2=self.h.evidence(f"verification/real-day-acceptance/{DATE}/report.md")
    daily.acceptance_runner.validate_acceptance=lambda **kw:report;daily.acceptance_runner.write_report=lambda r,o:{"json":str(p1),"markdown":str(p2)}
    try:r=daily.record_preview(workspace=self.h.root,date=DATE,daily_source_root=self.h.root,bundle_root=self.h.root,handoff_manifest=self.h.evidence("h.json"),renderer_artifact_root=self.h.root,technical_report=self.h.evidence("t.json"),user_review=None);self.assertEqual("user_review_pending",daily.status(workspace=self.h.root,date=DATE)["current_state"])
    finally:daily.acceptance_runner.validate_acceptance=orig_v;daily.acceptance_runner.write_report=orig_w
  def test_35_record_preview_approved(self):
    self.h.advance_to("handoff_ready")
    orig_v=daily.acceptance_runner.validate_acceptance;orig_w=daily.acceptance_runner.write_report
    report={"mvp_status":"passed","user_review":{"status":"approved"}}
    p1=self.h.evidence(f"verification/real-day-acceptance/{DATE}/report.json");p2=self.h.evidence(f"verification/real-day-acceptance/{DATE}/report.md")
    daily.acceptance_runner.validate_acceptance=lambda **kw:report;daily.acceptance_runner.write_report=lambda r,o:{"json":str(p1),"markdown":str(p2)}
    try:daily.record_preview(workspace=self.h.root,date=DATE,daily_source_root=self.h.root,bundle_root=self.h.root,handoff_manifest=self.h.evidence("h.json"),renderer_artifact_root=self.h.root,technical_report=self.h.evidence("t.json"),user_review=self.h.evidence("review.json"));self.assertEqual("user_preview_approved",daily.status(workspace=self.h.root,date=DATE)["current_state"])
    finally:daily.acceptance_runner.validate_acceptance=orig_v;daily.acceptance_runner.write_report=orig_w

if __name__=="__main__":unittest.main()
