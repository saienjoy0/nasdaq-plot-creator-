#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
EXPECTED_SHA256='f3a98dd5c42357eafd5391cece2c982a7032b004da4361c45e7e76187e3243f7'

def main()->int:
    path=Path('render-specs/2026-08-10/render_spec.json')
    doc=json.loads(path.read_text(encoding='utf-8'))
    if doc.get('episode',{}).get('targetDate')!='2026-08-10': raise SystemExit('render targetDate drift')
    scenes=doc.get('scenes',[])
    if len(scenes)!=9: raise SystemExit('render scene count drift')

    expected_scopes={2:('macro','nasdaq'),3:('macro','nasdaq'),5:('global','multiple')}
    for scene_number,(old,new) in expected_scopes.items():
        scene=scenes[scene_number-1]
        if scene.get('sceneNumber')!=scene_number: raise SystemExit(f'Scene {scene_number} numbering drift')
        if scene.get('causalScope') not in (old,new): raise SystemExit(f'Scene {scene_number} causalScope drift: {scene.get("causalScope")}')
        scene['causalScope']=new

    scene3_followup=scenes[2]['visualBeats'][1]
    if scene3_followup.get('visualBeatId')!='scene-03-beat-002' or scene3_followup.get('visualMode')!='text-focus':
        raise SystemExit('unexpected Scene 3 follow-up Beat shape')
    if scene3_followup.get('objectIds') not in (['scene-03-card-002'],[]):
        raise SystemExit(f'Scene 3 follow-up objectIds drift: {scene3_followup.get("objectIds")}')
    scene3_followup['objectIds']=[]

    # Pin templates to Renderer 2.4 grammar vocabulary, but keep bridge-text
    # bounded to two true transitional beats. Scene 2's second beat is an
    # explicit comparison (revisions vs NASDAQ close), while Scene 3's second
    # beat is evidence explaining that the two -10.3万 figures mean different
    # things. No narration, facts, timing, or causal claim changes here.
    for scene in scenes:
        for beat in scene.get('visualBeats',[]):
            template=beat.get('visualTemplate')
            grammar=beat.get('visualGrammar',{})
            beat_id=beat.get('visualBeatId')
            if template=='text-focus':
                if beat_id=='scene-02-beat-002':
                    grammar['grammarId']='comparison'
                elif beat_id=='scene-03-beat-002':
                    grammar['grammarId']='evidence'
                else:
                    grammar['grammarId']='bridge-text'
            elif template=='expected-actual-gap-flow':
                grammar['grammarId']='gap'
            elif template=='market-pulse-grid':
                grammar['grammarId']='evidence'

    text=json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    actual=hashlib.sha256(text.encode('utf-8')).hexdigest()
    if actual!=EXPECTED_SHA256: raise SystemExit(f'corrected render SHA mismatch: {actual}')
    path.write_text(text,encoding='utf-8')
    print(f'PASS corrected render {actual}')
    return 0
if __name__=='__main__': raise SystemExit(main())
