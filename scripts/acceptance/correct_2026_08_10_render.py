#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
EXPECTED_SHA256='2fcd9087a83faa9e4ef99a823d2ca8aa2fcfd0553aa4cc57d868435b574ed572'

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
    text=json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    actual=hashlib.sha256(text.encode('utf-8')).hexdigest()
    if actual!=EXPECTED_SHA256: raise SystemExit(f'corrected render SHA mismatch: {actual}')
    path.write_text(text,encoding='utf-8')
    print(f'PASS corrected render {actual}')
    return 0
if __name__=='__main__': raise SystemExit(main())
