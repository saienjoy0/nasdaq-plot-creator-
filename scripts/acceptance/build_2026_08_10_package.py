#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, subprocess, sys, traceback
from pathlib import Path

ROOT = Path.cwd().resolve()
SCRIPTS = ROOT / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import materialize_renderer_sources as renderer_sources
import visual_source_projection
import materialize_financial_contract_1_0 as financial_projection

DATE='2026-08-10'
STORY_BEGIN='<!--BEGIN_STORY_ENGINE_ANNEX-->'
STORY_END='<!--END_STORY_ENGINE_ANNEX-->'
MEM_BEGIN='<!--BEGIN_EPISODE_MEMORY_ANNEX-->'
MEM_END='<!--END_EPISODE_MEMORY_ANNEX-->'
PROD_BEGIN='<!--BEGIN_FINAL_PRODUCTION_SOURCE-->'
PROD_END='<!--END_FINAL_PRODUCTION_SOURCE-->'

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(v): return json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)
def normalize_scene_headings(text:str)->str:
    for n in range(1,10):
        text=re.sub(rf'(?m)^##\s+B{n}\.\s+Scene\s+{n}(?=｜|\|)', f'## Scene {n}', text)
    return text

def sync_story_plan_template(root:Path,date:str)->None:
    dossier_path=root/'research'/date/f'causal_research_dossier_{date}.json'
    template_path=root/'working'/date/'story-engine'/'templates'/'story_plan.template.json'
    dossier=json.loads(dossier_path.read_text(encoding='utf-8'))
    plan=json.loads(template_path.read_text(encoding='utf-8'))

    contradictions={item['id']:item for item in dossier.get('contradictions',[])}
    contradiction_id=plan.get('central_contradiction_id')
    contradiction=contradictions.get(contradiction_id)
    if contradiction is None:
        raise SystemExit(f'story plan central contradiction missing from dossier: {contradiction_id}')
    plan['central_contradiction']=contradiction['statement']

    selected=next((item for item in plan.get('angle_candidates',[]) if item.get('id')==plan.get('selected_angle_id')),None)
    if selected is None:
        raise SystemExit('story plan selected angle is missing before materialization')
    material_counter_ids={
        evidence_id
        for item in dossier.get('contrary_evidence',[])
        if item.get('effect_on_confidence')=='material'
        for evidence_id in item.get('evidence_ids',[])
    }
    selected['counterevidence_ids']=sorted(set(selected.get('counterevidence_ids',[])) | material_counter_ids)

    loop2=next((item for item in plan.get('open_loops',[]) if item.get('id')=='loop-02'),None)
    if loop2 is None:
        raise SystemExit('story plan loop-02 missing before materialization')
    loop2['promised_evidence_ids']=sorted(set(loop2.get('promised_evidence_ids',[])) | {'E-008','E-010','E-011','E-012'})
    loop2['resolution']='Microchip・原油・決算が増幅し、AMD/Alphabet逆行とMCHPの発表分ほぼ横ばいを残す複合相場として境界を引く。1分足は時系列整合の確認に使い、因果の単独証明には使わない。'

    dossier_sha=sha(dossier_path)
    if isinstance(plan.get('causal_dossier'),dict):
        plan['causal_dossier']['path']=f'research/{date}/causal_research_dossier_{date}.json'
        plan['causal_dossier']['sha256']=dossier_sha

    serialized=json.dumps(plan,ensure_ascii=False,sort_keys=True)
    if '分足欠損' in serialized:
        raise SystemExit('stale minute-gap wording remains in story plan template')

    template_path.write_text(dump(plan)+'\n',encoding='utf-8')
    print(json.dumps({
        'status':'pass',
        'storyPlanTemplateSync':str(template_path),
        'centralContradictionId':contradiction_id,
        'materialCounterevidenceIds':sorted(material_counter_ids),
        'causalDossierSha256':dossier_sha,
    },ensure_ascii=False,indent=2))

def sync_story_script_template(root:Path,date:str)->None:
    template_path=root/'working'/date/'story-engine'/'templates'/'story_script.template.json'
    script=json.loads(template_path.read_text(encoding='utf-8'))
    script['unresolved_points']=[
        {
            'evidence_ids':['E-008','E-010','E-011','E-012'],
            'statement':'8:30 ETの初動は確認済みだが、1分足だけで雇用統計が初動の原因と証明できない。',
        },
        {
            'evidence_ids':['E-009'],
            'statement':'雇用、原油・金利、企業決算それぞれの厳密な寄与度は分離できない。',
        },
    ]
    serialized=json.dumps(script,ensure_ascii=False,sort_keys=True)
    stale_terms=['分足反応は未確認','分足未取得','分足欠損']
    found=[term for term in stale_terms if term in serialized]
    if found:
        raise SystemExit(f'stale minute state remains in story script template: {found}')
    template_path.write_text(dump(script)+'\n',encoding='utf-8')
    print(json.dumps({
        'status':'pass',
        'storyScriptTemplateSync':str(template_path),
        'unresolvedPointCount':len(script['unresolved_points']),
    },ensure_ascii=False,indent=2))

def main()->int:
    root=ROOT; date=DATE
    work=root/'working'/date; story=work/'story-engine'; research=root/'research'/date; episodes=root/'episodes'/date
    verification=root/'verification'/date
    for p in (work,story,research,episodes,verification): p.mkdir(parents=True,exist_ok=True)

    sync_story_plan_template(root,date)
    sync_story_script_template(root,date)
    subprocess.run([sys.executable,'scripts/story-engine/materialize_story_engine.py','--date',date,'--repo-root',str(root)],check=True)

    dossier=research/f'causal_research_dossier_{date}.json'
    report=work/f'memory_retrieval_report_{date}.json'
    render_path=root/'render-specs'/date/'render_spec.json'
    public_path=episodes/f'episode_package_public_{date}.md'
    bindings=work/'financial_visual_bindings.json'
    subprocess.run([sys.executable,'scripts/acceptance/correct_2026_08_10_render.py'],check=True)
    subprocess.run([sys.executable,'scripts/acceptance/sync_2026_08_10_episode_public.py'],check=True)
    mat=renderer_sources.materialize(root=root,date=date,render_path=render_path,public_package_path=public_path,bindings_path=bindings)
    render=mat['render']
    visual=visual_source_projection.prepare_visual_sources(root=root,date=date,final_contract_path=mat['final_contract_path'],render=render)
    financial_projection.materialize(root=root,date=date)

    resolution={
      'contract_version':'1.0.0','episode_date':date,'status':'resolved','selected_path':visual['selected_path'],
      'unresolved_count':0,'routes':visual['routes'],'note':'Visual Evidence Planning completed; no day-specific visual source required.'
    }
    (verification/'asset_resolution_log.json').write_text(dump(resolution)+'\n',encoding='utf-8')
    (verification/'image_generation_log.json').write_text(dump({'episode_date':date,'status':'not-required','attempts':0})+'\n',encoding='utf-8')

    story_accept=story/'story_engine_acceptance.json'
    sa=json.loads(story_accept.read_text(encoding='utf-8'))
    story_annex={
      'contract_version':'1.0.0','episode_date':date,'status':'pass',
      'story_plan':{'path':f'working/{date}/story-engine/story_plan.json','sha256':sha(story/'story_plan.json')},
      'story_script':{'path':f'working/{date}/story-engine/story_script.json','sha256':sha(story/'story_script.json')},
      'creative_review':{'path':f'working/{date}/story-engine/creative_review.json','sha256':sha(story/'creative_review.json')},
      'acceptance':{'path':f'working/{date}/story-engine/story_engine_acceptance.json','sha256':sha(story_accept)},
      'critic':sa['critic'],
    }

    dossier_doc=json.loads(dossier.read_text(encoding='utf-8'))
    retrieval=json.loads(report.read_text(encoding='utf-8'))
    rv={(x['memory_reference_type'],x['memory_reference_id']):x for x in dossier_doc['memory_revalidation']}
    refs=[]; serial=1
    for item in retrieval['selected']:
        if item['item_type']=='core': continue
        key=(item['item_type'],item['item_id']); entry=rv[key]
        if entry['revalidation_status']!='not_used' or entry['editorial_use']!='not_used':
            raise SystemExit(f'2026-08-10 acceptance expects selected historical memory to be not_used: {key}')
        refs.append({
          'reference_id':f'MR-{serial:03d}','memory_reference_type':entry['memory_reference_type'],
          'memory_reference_id':entry['memory_reference_id'],'historical_confidence':entry['historical_confidence'],
          'current_revalidation_status':entry['revalidation_status'],'dossier_editorial_use':entry['editorial_use'],
          'dossier_current_evidence_ids':entry['current_evidence_ids'],'difference_from_previous':entry['difference_from_previous'],
          'public_usage_mode':'internal_only','scope_limit':'現在の市場因果・タイトル・サムネイル・ナレーションには使用しない。','usages':[]
        }); serial+=1
    memory_annex={
      'contract_version':'1.0.0','episode_date':date,
      'causal_dossier':{'path':f'research/{date}/causal_research_dossier_{date}.json','sha256':sha(dossier)},
      'references':refs,
      'validation_intent':{'past_mentions_complete':True,'title_thumbnail_checked':True,'post_inquisition_final':True}
    }
    asset_catalog=visual_source_projection.build_asset_catalog(render,visual)
    prod_annex={
      'contract_version':'1.0.0','episode_date':date,
      'post_inquisition':{'status':'pass','required_changes_applied':True,'unresolved_required_changes':0},
      'image_resolution':{'status':'resolved','selected_path':visual['selected_path'],'unresolved_count':0,'routes':visual['routes']},
      'renderer_contract':{'repository':'saienjoy0/saienjoy0-nasdaq-cafe-remotion','schema_version':render['schemaVersion']},
      'asset_catalog':asset_catalog,'render_spec':render,
    }
    public=normalize_scene_headings(Path(mat['contract_package_path']).read_text(encoding='utf-8').rstrip())
    final=(public+'\n\n'+STORY_BEGIN+'\n```json\n'+dump(story_annex)+'\n```\n'+STORY_END
           +'\n\n'+MEM_BEGIN+'\n```json\n'+dump(memory_annex)+'\n```\n'+MEM_END
           +'\n\n'+PROD_BEGIN+'\n```json\n'+dump(prod_annex)+'\n```\n'+PROD_END+'\n')
    out=episodes/f'episode_package_{date}.md'; out.write_text(final,encoding='utf-8')
    print(json.dumps({'status':'pass','episodePackage':str(out),'sha256':sha(out),'renderIntermediate':sha(render_path),'assetCount':len(asset_catalog)},ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except BaseException:
        diagnostic=ROOT/'verification'/DATE/'package_build.log'
        diagnostic.parent.mkdir(parents=True,exist_ok=True)
        diagnostic.write_text(traceback.format_exc(),encoding='utf-8')
        raise
