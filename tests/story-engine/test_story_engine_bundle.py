import copy, hashlib, json, importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
VALIDATOR=ROOT/'scripts'/'story-engine'/'validate_story_engine_bundle.py'
spec=importlib.util.spec_from_file_location('story_engine_validator', VALIDATOR)
v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
STORY_CONTRACTS=ROOT/'skills'/'nasdaq-cafe-story-authoring'/'contracts'
CRITIC_CONTRACTS=ROOT/'skills'/'nasdaq-cafe-entertainment-critic'/'contracts'

def dump(root,name,obj):
    p=root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8'); return p

def ref(p,root): return {'path':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def passing_scene_checks():
    checks=[]
    for i in range(1,8):
        checks.append({'scene_id':f'scene-{i:02d}','mode':'continue','payoff_delivered':True,'belief_changed':True,'continuation_reason_natural':True,'closure_effective':None,'opening_promise_recovered':None,'procedural_language_dominant':False})
    checks.append({'scene_id':'scene-08','mode':'close','payoff_delivered':True,'belief_changed':True,'continuation_reason_natural':None,'closure_effective':True,'opening_promise_recovered':True,'procedural_language_dominant':False})
    return checks

def base(tmp_path):
    root=tmp_path
    dossier={
      'episode_date':'2026-08-06','editorial_handoff':{'confidence':'medium'},
      'evidence':[{'evidence_id':'E-001','evidence_class':'fact'},{'evidence_id':'E-004','evidence_class':'fact'},{'evidence_id':'E-005','evidence_class':'reported_interpretation'},{'evidence_id':'E-008','evidence_class':'reported_interpretation'},{'evidence_id':'E-009','evidence_class':'fact'}],
      'contrary_evidence':[{'effect_on_confidence':'material','evidence_ids':['E-004']},{'effect_on_confidence':'material','evidence_ids':['E-001']},{'effect_on_confidence':'minor','evidence_ids':['E-008']}],
      'factor_roles':{'unresolved':['金利・VIXの寄与']},
      'causal_edges':[{'scope':'nasdaq_wide','evidence_ids':['E-001','E-008']}]
    }
    dp=dump(root,'research/dossier.json',dossier)
    roles=v.EXPECTED_ROLES
    plan={'episode_date':'2026-08-06','scenes':[{'scene_id':f'scene-{i:02d}','formal_role':r} for i,r in enumerate(roles,1)]}
    pp=dump(root,'working/story_plan.json',plan)
    scenes=[]
    for i,r in enumerate(roles,1):
      scenes.append({'scene_id':f'scene-{i:02d}','formal_role':r,'narration':f'Scene {i}。僕が確認します。','connection_to_previous':'','evidence_ids':['E-001'] if i<9 else [],'causal_claims':[]})
    scenes[3]['evidence_ids']=['E-004','E-005']; scenes[3]['causal_claims']=[{'claim_id':'claim-01','statement':'通常予想超過だけでは説明しきれないとの市場解釈です。','claim_type':'reported_interpretation','evidence_ids':['E-005'],'confidence':'medium','scope':'company'}]
    scenes[5]['evidence_ids']=['E-001','E-008']; scenes[5]['causal_claims']=[{'claim_id':'claim-02','statement':'複数の大型テック安がNASDAQ下落を支えました。','claim_type':'reported_interpretation','evidence_ids':['E-001','E-008'],'confidence':'medium','scope':'nasdaq_support'}]
    scenes[-1]['narration']='以上、朝のNASDAQカフェでした。今日も気をつけて、いってらっしゃい。こちらはそろそろ、おやすみなさい。'
    script={'contract_version':'1.0.0','episode_date':'2026-08-06','producer':'chatgpt','story_plan':ref(pp,root),'causal_dossier':ref(dp,root),'scenes':scenes,'retained_counterevidence_ids':['E-001','E-004'],'unresolved_points':[{'statement':'金利・VIXの寄与は未確認です。','evidence_ids':['E-009']}]}
    sp=dump(root,'working/script.json',script)
    review={'contract_version':'1.1.0','episode_date':'2026-08-06','reviewer':'editorial_critic','round':1,'scores':{'opening':5,'progression':4,'discovery':4,'clarity':4,'fox_voice':4,'late_payoff':4},'total_score':25,'scene_checks':passing_scene_checks(),'immediate_failures':[],'findings':[],'verdict':'pass'}
    rp=dump(root,'working/review.json',review)
    return root,dp,pp,sp,rp,script,review

def run(root,dp,pp,sp,rp=None,patch=None,before=None):
    return v.validate_bundle(sp,pp,dp,story_contracts_dir=STORY_CONTRACTS,critic_contracts_dir=CRITIC_CONTRACTS,repo_root=root,review_path=rp,patch_path=patch,before_script_path=before)

def test_valid_bundle_passes(tmp_path):
    x=base(tmp_path); assert run(*x[:5]).ok

def test_confidence_strengthening_fails(tmp_path):
    root,dp,pp,sp,rp,script,_=base(tmp_path); script['scenes'][3]['causal_claims'][0]['confidence']='high'; sp=dump(root,'working/script2.json',script); assert any('confidence strengthened' in e for e in run(root,dp,pp,sp).errors)

def test_material_counterevidence_removal_fails(tmp_path):
    root,dp,pp,sp,rp,script,_=base(tmp_path); script['retained_counterevidence_ids']=['E-001']; sp=dump(root,'working/script2.json',script); assert any('counterevidence' in e for e in run(root,dp,pp,sp).errors)

def test_scene9_new_evidence_fails(tmp_path):
    root,dp,pp,sp,rp,script,_=base(tmp_path); script['scenes'][-1]['evidence_ids']=['E-001']; sp=dump(root,'working/script2.json',script); assert any('scene-09' in e for e in run(root,dp,pp,sp).errors)

def test_wrong_fox_first_person_fails(tmp_path):
    root,dp,pp,sp,rp,script,_=base(tmp_path); script['scenes'][0]['narration']='私は確認します。'; sp=dump(root,'working/script2.json',script); assert any('first-person' in e for e in run(root,dp,pp,sp).errors)

def test_review_score_contract_fails(tmp_path):
    root,dp,pp,sp,rp,script,review=base(tmp_path); review['scores']['fox_voice']=2; review['total_score']=23; review['verdict']='pass'; rp=dump(root,'working/review2.json',review); assert any('verdict' in e for e in run(root,dp,pp,sp,rp).errors)

def test_patch_cannot_touch_scene9(tmp_path):
    root,dp,pp,sp,rp,script,review=base(tmp_path); review['scores']['opening']=4; review['total_score']=24; review['verdict']='conditional'; review['findings']=[{'finding_id':'finding-01','severity':'minor','issue_type':'ABSTRACT_EDITORIAL_LANGUAGE','scene_ids':['scene-08'],'problem':'表現が抽象的','viewer_impact':'回収が伝わりにくい','minimal_fix':'Scene 8の表現を具体化'}]; rp=dump(root,'working/review2.json',review)
    patch={'contract_version':'1.0.0','episode_date':'2026-08-06','round':1,'source_review_round':1,'operations':[{'operation_id':'patch-01','operation':'rewrite_scene','target_scene_ids':['scene-09'],'finding_ids':['finding-01'],'purpose':'回収','instruction':'書き換える'}]}; xp=dump(root,'working/patch.json',patch)
    assert any('Scene 9' in e for e in run(root,dp,pp,sp,rp,xp).errors)

def test_rewrite_cannot_change_causal_metadata(tmp_path):
    root,dp,pp,sp,rp,script,_=base(tmp_path); before=dump(root,'working/before.json',copy.deepcopy(script)); script['scenes'][3]['causal_claims'][0]['scope']='sector'; sp=dump(root,'working/after.json',script); assert any('guarded causal metadata' in e for e in run(root,dp,pp,sp,before=before).errors)
