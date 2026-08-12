#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, FormatChecker

EXPECTED_ROLES = [
    'direction_and_conclusion','contradiction','confirmed_facts','expected_actual_gap',
    'global_context','market_reaction','entity_divergence','validation_points','fixed_closing'
]
CONF = {'unknown':0,'low':1,'medium':2,'high':3}
FORBIDDEN_ADVICE = ('買い場','買うべき','売るべき','必ず上がる','必ず下がる','暴落確定','乗り遅れるな')
FORBIDDEN_FIRST_PERSON = re.compile(r'(^|[、。\s])(私|俺|われわれ|我々)([はがをも、。\s]|$)')
HARD_NARRATIVE_FINDINGS = {
    'HOOK_EXHAUSTS_STORY',
    'NO_UNDERSTANDING_UPGRADE',
    'FAKE_UNDERSTANDING_UPGRADE',
    'NO_LATE_PAYOFF',
    'OPENING_PROMISE_NOT_RECOVERED',
    'ENDING_NOT_BOOKENDED',
}

class Result:
    def __init__(self, errors, warnings): self.errors=errors; self.warnings=warnings
    @property
    def ok(self): return not self.errors
    def as_dict(self): return {'status':'pass' if self.ok else 'fail','errors':self.errors,'warnings':self.warnings}

def load(path:Path)->dict[str,Any]: return json.loads(path.read_text(encoding='utf-8'))
def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def schema_errors(instance:Any, schema_path:Path, label:str)->list[str]:
    schema=load(schema_path); v=Draft202012Validator(schema,format_checker=FormatChecker())
    out=[]
    for e in sorted(v.iter_errors(instance), key=lambda x:list(x.absolute_path)):
        p='.'.join(map(str,e.absolute_path)) or '<root>'; out.append(f'{label}.{p}: {e.message}')
    return out

def resolve_ref(ref:dict[str,str], repo_root:Path, label:str, errors:list[str])->Path|None:
    p=Path(ref['path'])
    if p.is_absolute(): errors.append(f'{label}: absolute path forbidden'); return None
    root=repo_root.resolve(); q=(root/p).resolve()
    if q!=root and root not in q.parents: errors.append(f'{label}: path escapes repo'); return None
    if not q.is_file(): errors.append(f'{label}: missing file {ref["path"]}'); return None
    actual=sha(q)
    if actual!=ref['sha256']: errors.append(f'{label}: sha256 mismatch')
    return q

def validate_script(script:dict, plan:dict, dossier:dict, errors:list[str], warnings:list[str]):
    if script['episode_date']!=plan['episode_date'] or script['episode_date']!=dossier['episode_date']:
        errors.append('episode_date mismatch across script/plan/dossier')
    scenes=script['scenes']
    ids=[s['scene_id'] for s in scenes]
    wanted=[f'scene-{i:02d}' for i in range(1,10)]
    if ids!=wanted: errors.append(f'scene order must be fixed: {wanted}')
    roles=[s['formal_role'] for s in scenes]
    if roles!=EXPECTED_ROLES: errors.append('formal 9-scene roles changed')
    plan_roles=[s['formal_role'] for s in plan['scenes']]
    if roles!=plan_roles: errors.append('script formal roles differ from story plan')
    evidence={e['evidence_id']:e for e in dossier['evidence']}
    all_used=set(); claims={}
    for scene in scenes:
        for eid in scene['evidence_ids']:
            all_used.add(eid)
            if eid not in evidence: errors.append(f'{scene["scene_id"]}: unknown evidence {eid}')
        for c in scene['causal_claims']:
            cid=c['claim_id']
            if cid in claims: errors.append(f'duplicate causal claim id {cid}')
            claims[cid]=c
            if not c['evidence_ids'] and c['claim_type']!='unknown': errors.append(f'{cid}: causal claim lacks evidence')
            for eid in c['evidence_ids']:
                all_used.add(eid)
                if eid not in evidence: errors.append(f'{cid}: unknown evidence {eid}')
            if c['claim_type']!='fact':
                ceiling=dossier['editorial_handoff']['confidence']
                if CONF[c['confidence']]>CONF[ceiling]: errors.append(f'{cid}: confidence strengthened above dossier {ceiling}')
            if c['claim_type']=='unknown' and (c['confidence']!='unknown' or c['scope']!='reason_unknown'):
                errors.append(f'{cid}: unknown claim must remain unknown/reason_unknown')
            if c['scope']=='nasdaq_support':
                wide=set()
                for edge in dossier.get('causal_edges',[]):
                    if edge.get('scope')=='nasdaq_wide': wide.update(edge.get('evidence_ids',[]))
                if not wide.intersection(c['evidence_ids']): errors.append(f'{cid}: NASDAQ-support claim lacks NASDAQ-wide evidence')
    text='\n'.join(s['narration'] for s in scenes)
    if '僕' not in text: errors.append('fox narration never uses required first-person 僕')
    if FORBIDDEN_FIRST_PERSON.search(text): errors.append('forbidden first-person form detected; use 僕')
    for term in FORBIDDEN_ADVICE:
        if term in text: errors.append(f'forbidden investment-advice/hype wording: {term}')
    s9=scenes[-1]
    if s9['evidence_ids'] or s9['causal_claims']: errors.append('scene-09 cannot contain new evidence or causal claims')
    for phrase in ('以上、朝のNASDAQカフェでした','いってらっしゃい','おやすみなさい'):
        if phrase not in s9['narration']: errors.append(f'scene-09 fixed closing meaning missing phrase: {phrase}')
    material=set()
    for item in dossier.get('contrary_evidence',[]):
        if item.get('effect_on_confidence')=='material': material.update(item.get('evidence_ids',[]))
    retained=set(script['retained_counterevidence_ids'])
    missing=material-retained
    if missing: errors.append(f'material counterevidence not retained: {sorted(missing)}')
    not_used=retained-all_used
    if not_used: errors.append(f'retained_counterevidence_ids not actually used in script: {sorted(not_used)}')
    if dossier.get('factor_roles',{}).get('unresolved') and not script['unresolved_points']:
        errors.append('dossier has unresolved factors but script records none')
    for u in script['unresolved_points']:
        for eid in u['evidence_ids']:
            if eid not in evidence: errors.append(f'unresolved point uses unknown evidence {eid}')
    return claims

def _has_finding(review:dict, scene_id:str, issue_types:set[str])->bool:
    return any(scene_id in f.get('scene_ids',[]) and f.get('issue_type') in issue_types for f in review.get('findings',[]))

def validate_scene_checks(review:dict, errors:list[str]):
    checks=review['scene_checks']
    ids=[c['scene_id'] for c in checks]
    wanted=[f'scene-{i:02d}' for i in range(1,9)]
    if ids!=wanted: errors.append(f'review scene_checks must be exactly ordered {wanted}')
    for index,check in enumerate(checks, start=1):
        sid=check['scene_id']
        if index<=7:
            if check['mode']!='continue': errors.append(f'{sid}: scene check mode must be continue')
            if not isinstance(check['continuation_reason_natural'],bool): errors.append(f'{sid}: continuation_reason_natural must be boolean')
            if check['closure_effective'] is not None or check['opening_promise_recovered'] is not None:
                errors.append(f'{sid}: closure fields must be null before Scene 8')
            if not check['payoff_delivered'] and not _has_finding(review,sid,{'NO_PAYOFF','NO_NEW_EVIDENCE','NO_NEW_EVIDENCE_OR_MEANING'}):
                errors.append(f'{sid}: missing payoff requires a matching finding')
            if not check['belief_changed'] and not _has_finding(review,sid,{'NO_BELIEF_CHANGE'}):
                errors.append(f'{sid}: unchanged belief requires NO_BELIEF_CHANGE finding')
            if check['continuation_reason_natural'] is False and not _has_finding(review,sid,{'DEAD_END_SCENE','FAKE_OPEN_LOOP'}):
                errors.append(f'{sid}: unnatural continuation requires DEAD_END_SCENE or FAKE_OPEN_LOOP finding')
        else:
            if check['mode']!='close': errors.append('scene-08: scene check mode must be close')
            if check['continuation_reason_natural'] is not None: errors.append('scene-08: continuation_reason_natural must be null')
            if not isinstance(check['closure_effective'],bool): errors.append('scene-08: closure_effective must be boolean')
            if not isinstance(check['opening_promise_recovered'],bool): errors.append('scene-08: opening_promise_recovered must be boolean')
            if not check['payoff_delivered'] and not _has_finding(review,sid,{'NO_PAYOFF','NO_NEW_EVIDENCE_OR_MEANING'}):
                errors.append('scene-08: missing payoff requires a matching finding')
            if not check['belief_changed'] and not _has_finding(review,sid,{'NO_BELIEF_CHANGE'}):
                errors.append('scene-08: unchanged belief requires NO_BELIEF_CHANGE finding')
            if check['closure_effective'] is False and review['verdict']=='pass': errors.append('scene-08: ineffective closure cannot PASS')
            if check['opening_promise_recovered'] is False and review['verdict']=='pass': errors.append('scene-08: unrecovered opening promise cannot PASS')
        if check['procedural_language_dominant'] and not _has_finding(review,sid,{'PROCEDURAL_NARRATION'}):
            errors.append(f'{sid}: procedural-language dominance requires PROCEDURAL_NARRATION finding')

def validate_review(review:dict, errors:list[str]):
    vals=list(review['scores'].values()); total=sum(vals)
    if review['total_score']!=total: errors.append(f'review total_score={review["total_score"]} but sum={total}')
    validate_scene_checks(review,errors)

    for finding in review.get('findings',[]):
        if finding.get('issue_type') in HARD_NARRATIVE_FINDINGS and finding.get('severity') == 'minor':
            errors.append(f"{finding.get('finding_id')}: {finding.get('issue_type')} must be major or critical")

    for finding in review.get('findings',[]):
        if finding.get('issue_type') == 'FALSE_TEMPORAL_CAUSALITY' and finding.get('severity') != 'critical':
            errors.append(f"{finding.get('finding_id')}: FALSE_TEMPORAL_CAUSALITY must be critical")

    severe=any(f['severity']=='critical' for f in review['findings'])
    major=any(f['severity']=='major' for f in review['findings'])
    if review['immediate_failures'] or severe:
        expected='fail'
    elif total>=25 and min(vals)>=3 and not major:
        expected='pass'
    elif total>=21:
        expected='conditional'
    elif total>=16:
        expected='restructure'
    else:
        expected='fail'

    if review['verdict']=='pass':
        checks=review['scene_checks']
        for check in checks[:7]:
            sid=check['scene_id']
            if not check['payoff_delivered']:
                errors.append(f'{sid}: PASS requires payoff_delivered=true')
            if not check['belief_changed']:
                errors.append(f'{sid}: PASS requires belief_changed=true')
            if check['continuation_reason_natural'] is not True:
                errors.append(f'{sid}: PASS requires a natural continuation reason')
        scene8=checks[7]
        if not scene8['payoff_delivered']:
            errors.append('scene-08: PASS requires payoff_delivered=true')
        if not scene8['belief_changed']:
            errors.append('scene-08: PASS requires belief_changed=true')
        if not scene8['closure_effective']:
            errors.append('scene-08: PASS requires effective closure')
        if not scene8['opening_promise_recovered']:
            errors.append('scene-08: PASS requires opening-promise recovery')

    if review['verdict']!=expected: errors.append(f'review verdict must be {expected} for scores/findings')
    return {f['finding_id']:f for f in review['findings']}

def validate_patch(patch:dict, review:dict, plan:dict, errors:list[str]):
    if patch['round']!=review['round'] or patch['source_review_round']!=review['round']:
        errors.append('patch round must match source review round')
    findings={f['finding_id']:f for f in review['findings']}
    roles={s['scene_id']:s['formal_role'] for s in plan['scenes']}
    for op in patch['operations']:
        for fid in op['finding_ids']:
            if fid not in findings: errors.append(f'{op["operation_id"]}: unknown finding {fid}')
        for sid in op['target_scene_ids']:
            if sid not in roles: errors.append(f'{op["operation_id"]}: unknown target scene {sid}')
            if sid=='scene-09': errors.append(f'{op["operation_id"]}: fixed Scene 9 cannot be patched')
        if op['operation']=='move_content_to_compatible_scene' and len(op['target_scene_ids'])<2:
            errors.append(f'{op["operation_id"]}: move_content requires source and destination scenes')

def compare_before_after(before:dict, after:dict, errors:list[str]):
    if before['episode_date']!=after['episode_date']: errors.append('rewrite changed episode_date')
    bsc=before['scenes']; asc=after['scenes']
    if [(s['scene_id'],s['formal_role']) for s in bsc] != [(s['scene_id'],s['formal_role']) for s in asc]:
        errors.append('rewrite changed scene order or formal roles')
    if bsc[-1]['narration']!=asc[-1]['narration']: errors.append('rewrite changed fixed Scene 9 narration')
    def cmap(doc): return {c['claim_id']:c for s in doc['scenes'] for c in s['causal_claims']}
    b=cmap(before); a=cmap(after)
    if set(a)!=set(b): errors.append('rewrite added or removed causal claim IDs')
    for cid in set(a)&set(b):
        for key in ('claim_type','evidence_ids','confidence','scope'):
            if a[cid][key]!=b[cid][key]: errors.append(f'{cid}: rewrite changed guarded causal metadata field {key}')

def validate_bundle(script_path:Path, plan_path:Path, dossier_path:Path, *, story_contracts_dir:Path, critic_contracts_dir:Path, repo_root:Path, review_path:Path|None=None, patch_path:Path|None=None, before_script_path:Path|None=None)->Result:
    errors=[]; warnings=[]
    script=load(script_path); plan=load(plan_path); dossier=load(dossier_path)
    errors += schema_errors(script, story_contracts_dir/'story_script.schema.json','script')
    if errors: return Result(errors,warnings)
    for label,ref,supplied in [('story_plan',script['story_plan'],plan_path),('causal_dossier',script['causal_dossier'],dossier_path)]:
        resolved=resolve_ref(ref,repo_root,label,errors)
        if resolved and resolved.resolve()!=supplied.resolve(): errors.append(f'{label}: ref does not resolve to supplied file')
    validate_script(script,plan,dossier,errors,warnings)
    if review_path:
        review=load(review_path); errors += schema_errors(review,critic_contracts_dir/'creative_review.schema.json','review')
        if not errors:
            validate_review(review,errors)
            if review['episode_date']!=script['episode_date']: errors.append('review episode_date mismatch')
        if patch_path:
            patch=load(patch_path); errors += schema_errors(patch,critic_contracts_dir/'rewrite_patch.schema.json','patch')
            if not errors:
                validate_patch(patch,review,plan,errors)
                if patch['episode_date']!=script['episode_date']: errors.append('patch episode_date mismatch')
    if before_script_path:
        before=load(before_script_path)
        compare_before_after(before,script,errors)
    return Result(sorted(set(errors)),warnings)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--script',type=Path,required=True); ap.add_argument('--story-plan',type=Path,required=True); ap.add_argument('--dossier',type=Path,required=True); ap.add_argument('--story-contracts-dir',type=Path,required=True); ap.add_argument('--critic-contracts-dir',type=Path,required=True); ap.add_argument('--repo-root',type=Path,default=Path('.')); ap.add_argument('--review',type=Path); ap.add_argument('--patch',type=Path); ap.add_argument('--before-script',type=Path)
    a=ap.parse_args(); r=validate_bundle(a.script,a.story_plan,a.dossier,story_contracts_dir=a.story_contracts_dir,critic_contracts_dir=a.critic_contracts_dir,repo_root=a.repo_root,review_path=a.review,patch_path=a.patch,before_script_path=a.before_script)
    print(json.dumps(r.as_dict(),ensure_ascii=False,indent=2)); sys.exit(0 if r.ok else 1)
if __name__=='__main__': main()
