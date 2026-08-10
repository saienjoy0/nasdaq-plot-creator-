#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
EXPECTED_SHA256='f3d05b6cc48adc8c3c3f8c684d7f9bfbd84595c383fb5163374803ded56104d9'

def main()->int:
    path=Path('render-specs/2026-08-10/render_spec.json')
    doc=json.loads(path.read_text(encoding='utf-8'))
    if doc.get('episode',{}).get('targetDate')!='2026-08-10': raise SystemExit('render targetDate drift')
    scenes=doc.get('scenes',[])
    if len(scenes)!=9: raise SystemExit('render scene count drift')
    beat=scenes[3]['visualBeats'][0]
    if beat.get('visualBeatId')!='scene-04-beat-001': raise SystemExit('unexpected Scene 4 Beat 1')
    grammar=beat.get('visualGrammar',{})
    if grammar.get('grammarId') not in ('reaction','gap'): raise SystemExit('unexpected Scene 4 Beat 1 grammar')
    if beat.get('visualTemplate')!='expected-actual-gap-flow': raise SystemExit('Scene 4 Beat 1 template drift')
    grammar['grammarId']='gap'
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
    text=json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    actual=hashlib.sha256(text.encode('utf-8')).hexdigest()
    if actual!=EXPECTED_SHA256: raise SystemExit(f'corrected render SHA mismatch: {actual}')
    path.write_text(text,encoding='utf-8')
    print(f'PASS corrected render {actual}')
    return 0
if __name__=='__main__': raise SystemExit(main())
