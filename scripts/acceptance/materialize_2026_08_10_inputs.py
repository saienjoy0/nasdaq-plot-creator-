#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, io, json, zipfile
from pathlib import Path
PAYLOAD_SHA256='b1d9ed94c50843c3b75c6d35e2d25f177a5669c9768e52afd6ef68706badab5d'
CORRECTED_SUPPLEMENT_SHA256='151f5e124cdd7fda2b17e909387b63ce7b4465f4b7dddbbc205dbd98af5d7270'
CORRECTED_DOSSIER_SHA256='78c66e20521b0299b2b845a1b0990b7ad938fbb6b9b60849a32415dab60cc44d'
CORRECTED_STORY_PLAN_SHA256='05c5e79cba26e98180dc4d46ab4470686ef6775eb89fcfd9808fa6a21dc00b09'
PART_SHA256={
 'part-01.b64':'509e05dc694585aaabc12675228074009ca7791d7b76281c118d20fe396c9a75',
 'part-02.b64':'377a99ae4888f2cb10dba3f075781817015c34a4d3ce216d06ce9f543c6e46cb',
 'part-03.b64':'59d23f493f628804251610a1012f2b083038de0dcb60b0c1e6a787eaed59fd9a',
 'part-04.b64':'434653c7074c1cb60b974e2b48deaf4fd2b6bb8e41e84c2945dee6d37cc4c926',
 'part-05.b64':'4fd5ffb318250c810c60b71dd4f671eb2cf0b6b5f16f78c519f3a60cb543299c',
 'part-06.b64':'3592013be3b004d35abe1c409de99bc4e68121eaddaa437ab202c38fc190488f',
 'part-07.b64':'23c33ede87007b16fd15b14d940f7b93a56f3773bb07a4c606b97c7471b4443b',
 'part-08.b64':'65bedb26188ac654d7b7b3b4e6582dd33d04a24f0fe0b9f33ee2d470b381be8c',
 'part-09.b64':'db33d83398fe4138c8135f89e7bfff99431d6d6cc3d2a3e4f193bebe3a68220a',
}
PART08_OFFSET=2000
PART08_CANONICAL_CHUNK='uIbxfpjUge0ID94SHoSn34g44M3kPw8PzC3VQvKBeg2DSIwes3KIh2ErVF8NAxw3AWhhU0HJhDXpRmi7HawkNpIcn3zBJyf45DpugufJwmzKhu2grrb4H/A5KgLOBtYItnUjAXf4AZ1FxVYfgi1t0aQ4yAzsmBuNXm8NuNahw7XaDgrXqjT3wV+ADX10CBxz76A+5ZPMPJC6QGz0Xk5dIVptB4VoqW0d5t93l5niyJowPlt4AmJ1TVElR8cyB1MK9enzZkXxnCIIVWdtSE9b/SBUbaceQtVlh97OutH7C4dQtTUgVLbp1CjxZINQfrZip2qpVHlDA2VmG2XWboYya/+s3m65OfB5aQBJLpmNZbgLH1PFT9kqrd7y2y/xNDWY4JNL4q+bfHIbLArMwCXG4LP4bquQwfN+wvOHwibGloT55TIKjJyWqlH7qd8fvKY6yW4MN8vntnHgxAzP7ZB84SzPPcFST6NPham3xRd3CrsZzP2tjJAm'
def canonical_part_bytes(path:Path)->bytes:
    raw=path.read_bytes()
    if path.name!='part-08.b64': return raw
    text=raw.decode('ascii')
    if len(text)!=8000: raise SystemExit(f'part-08 length drift: {len(text)}')
    repaired=text[:PART08_OFFSET]+PART08_CANONICAL_CHUNK+text[PART08_OFFSET+500:]
    repaired_raw=repaired.encode('ascii')
    repaired_sha=hashlib.sha256(repaired_raw).hexdigest()
    if repaired_sha!=PART_SHA256['part-08.b64']: raise SystemExit(f'part-08 canonical repair failed: {repaired_sha}')
    return repaired_raw

def write_checked(path:Path,doc:dict,expected_sha:str,label:str)->None:
    text=json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    actual=hashlib.sha256(text.encode('utf-8')).hexdigest()
    if actual!=expected_sha: raise SystemExit(f'{label} SHA mismatch: {actual}')
    path.write_text(text,encoding='utf-8')
    print(f'PASS corrected {label} {actual}')

def correct_supplement(root:Path)->None:
    path=root/'research/2026-08-10/research_evidence_supplement_manifest.json'; doc=json.loads(path.read_text(encoding='utf-8'))
    waves=doc.get('waves')
    if not isinstance(waves,list) or len(waves)!=2 or waves[1].get('wave')!=2: raise SystemExit('unexpected wave-2 supplement shape')
    files=waves[1].get('evidenceFiles')
    if not isinstance(files,list) or len(files)!=1: raise SystemExit('unexpected wave-2 evidenceFiles shape')
    item=files[0]
    if item.get('path')!='research/2026-08-10/evidence/RA-W2-005_exact_url_archive.json': raise SystemExit('unexpected wave-2 evidence path')
    if item.get('sha256')!='53d8d5717cff293a652c3fcba0145a98ded7de21a87ed3db546d933b7819bc06': raise SystemExit('unexpected wave-2 evidence SHA')
    if item.get('requestId') not in (None,'RA-W2-005'): raise SystemExit('unexpected wave-2 requestId before correction')
    item['requestId']='RA-W2-005'; write_checked(path,doc,CORRECTED_SUPPLEMENT_SHA256,'supplement')

def correct_dossier(root:Path)->dict:
    path=root/'research/2026-08-10/causal_research_dossier_2026-08-10.json'; doc=json.loads(path.read_text(encoding='utf-8'))
    if doc.get('episode_date')!='2026-08-10': raise SystemExit('unexpected dossier episode date')
    doc['session']={'information_cutoff':'2026-08-10T12:15:00+09:00','market_date':'2026-08-07','timezone':'Asia/Tokyo'}
    matched=0
    for item in doc.get('input_provenance',[]):
        if item.get('path_or_reference')=='research/2026-08-10/research_evidence_supplement_manifest.json':
            item['version_or_hash']=CORRECTED_SUPPLEMENT_SHA256; matched+=1
    if matched!=1: raise SystemExit(f'unexpected supplement provenance count: {matched}')
    write_checked(path,doc,CORRECTED_DOSSIER_SHA256,'causal dossier'); return doc

def correct_story_plan(root:Path,dossier:dict)->None:
    path=root/'working/2026-08-10/story-engine/templates/story_plan.template.json'; doc=json.loads(path.read_text(encoding='utf-8'))
    contradiction=next(x for x in dossier['contradictions'] if x['id']==doc['central_contradiction_id'])
    doc['central_contradiction']=contradiction['statement']
    doc['headline_beyond_discovery']=dossier['editorial_handoff']['headline_beyond_discovery']
    selected=next((x for x in doc['angle_candidates'] if x['id']==doc['selected_angle_id']),None)
    if selected is None or selected['id']!='angle-02': raise SystemExit('unexpected selected story angle')
    selected['central_question']=doc['central_question']; selected['story_spine']=doc['story_spine']; selected['opening_promise']=doc['opening_promise']
    selected['midpoint_turn_claim']=doc['midpoint_turn']['claim']; selected['closing_reframe']=doc['closing_reframe']['text']
    selected['counterevidence_ids']=sorted(set(selected['counterevidence_ids']+['E-002']))
    write_checked(path,doc,CORRECTED_STORY_PLAN_SHA256,'story plan')

def main():
    root=Path.cwd().resolve(); parts=sorted((root/'acceptance-inputs/2026-08-10').glob('part-*.b64'))
    if len(parts)!=9: raise SystemExit(f'expected 9 input parts, found {len(parts)}')
    canonical=[]
    for p in parts:
        raw=canonical_part_bytes(p); actual=hashlib.sha256(raw).hexdigest(); expected=PART_SHA256.get(p.name)
        if expected is None or actual!=expected: raise SystemExit(f'{p.name}: canonical SHA mismatch bytes={len(raw)} actual={actual} expected={expected}')
        canonical.append(raw.decode('ascii'))
    data=base64.b64decode(''.join(canonical)); actual_payload=hashlib.sha256(data).hexdigest()
    if actual_payload!=PAYLOAD_SHA256: raise SystemExit(f'acceptance input payload SHA mismatch actual={actual_payload} expected={PAYLOAD_SHA256}')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos=z.infolist()
        for info in infos:
            target=(root/info.filename).resolve()
            if target == root or root not in target.parents: raise SystemExit(f'unsafe payload path: {info.filename}')
            target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(z.read(info.filename))
    correct_supplement(root); dossier=correct_dossier(root); correct_story_plan(root,dossier)
    print(f'PASS materialized {len(infos)} acceptance inputs payload={PAYLOAD_SHA256}')
if __name__=='__main__': main()
