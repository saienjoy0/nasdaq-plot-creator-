#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
EXPECTED_SHA256='d4866b61e532bc90b3464457113c42cee1cfa8a5fbd782051d8e6d7208f9479e'

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
    # The renderer-source materializer intentionally removes this redundant
    # card. Keep the evidence Beat static and use its already-authored
    # viewerTexts instead of reviving an object that no longer exists.
    scene3_followup['objectIds']=[]

    # Keep bridge-text bounded to the two genuine transitional Beats. The two
    # analytical Beats switch template and grammar together using existing
    # renderer templates that do not create a new Financial Visual binding.
    # Narration, numbers, evidence ids, cues, and causal claims remain unchanged.
    for scene in scenes:
        for beat in scene.get('visualBeats',[]):
            template=beat.get('visualTemplate')
            grammar=beat.get('visualGrammar',{})
            beat_id=beat.get('visualBeatId')
            if template=='text-focus':
                if beat_id=='scene-02-beat-002':
                    beat['visualTemplate']='evidence-boundary'
                    beat['templateConfig']['variant']='confirmed-vs-unconfirmed'
                    grammar['grammarId']='evidence'
                elif beat_id=='scene-03-beat-002':
                    beat['visualTemplate']='news-media'
                    beat['templateConfig']['variant']='default'
                    beat['screenState']='News'
                    beat['visualMode']='news-media'
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
