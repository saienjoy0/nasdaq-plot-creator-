#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, io, zipfile
from pathlib import Path
PAYLOAD_SHA256='b1d9ed94c50843c3b75c6d35e2d25f177a5669c9768e52afd6ef68706badab5d'
def main():
    root=Path.cwd().resolve()
    parts=sorted((root/'acceptance-inputs/2026-08-10').glob('part-*.b64'))
    if len(parts)!=9: raise SystemExit(f'expected 9 input parts, found {len(parts)}')
    data=base64.b64decode(''.join(p.read_text(encoding='ascii').strip() for p in parts))
    if hashlib.sha256(data).hexdigest()!=PAYLOAD_SHA256: raise SystemExit('acceptance input payload SHA mismatch')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos=z.infolist()
        for info in infos:
            target=(root/info.filename).resolve()
            if target == root or root not in target.parents: raise SystemExit(f'unsafe payload path: {info.filename}')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(z.read(info.filename))
    print(f'PASS materialized {len(infos)} acceptance inputs payload={PAYLOAD_SHA256}')
if __name__=='__main__': main()
