#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, io, zipfile
from pathlib import Path
PAYLOAD_SHA256='b1d9ed94c50843c3b75c6d35e2d25f177a5669c9768e52afd6ef68706badab5d'
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
def main():
    root=Path.cwd().resolve()
    parts=sorted((root/'acceptance-inputs/2026-08-10').glob('part-*.b64'))
    if len(parts)!=9: raise SystemExit(f'expected 9 input parts, found {len(parts)}')
    failures=[]
    for p in parts:
        raw=p.read_bytes()
        actual=hashlib.sha256(raw).hexdigest()
        expected=PART_SHA256.get(p.name)
        if expected is None or actual!=expected:
            failures.append(f'{p.name}: bytes={len(raw)} actual={actual} expected={expected}')
    if failures:
        raise SystemExit('acceptance input part SHA mismatch\n'+'\n'.join(failures))
    data=base64.b64decode(''.join(p.read_text(encoding='ascii').strip() for p in parts))
    actual_payload=hashlib.sha256(data).hexdigest()
    if actual_payload!=PAYLOAD_SHA256:
        raise SystemExit(f'acceptance input payload SHA mismatch actual={actual_payload} expected={PAYLOAD_SHA256}')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos=z.infolist()
        for info in infos:
            target=(root/info.filename).resolve()
            if target == root or root not in target.parents: raise SystemExit(f'unsafe payload path: {info.filename}')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(z.read(info.filename))
    print(f'PASS materialized {len(infos)} acceptance inputs payload={PAYLOAD_SHA256}')
if __name__=='__main__': main()
