#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))

import build_current_final_request_v2 as final_builder  # noqa: E402
import build_current_preview_request_v4 as preview_builder  # noqa: E402

DATE='2099-07-01'
SHA='a'*64


def main()->int:
    with tempfile.TemporaryDirectory(prefix='nasdaq-current-request-builders-') as temp:
        root=Path(temp); (root/'contracts').mkdir(parents=True)
        shutil.copyfile(ROOT/'contracts/renderer_binding.json',root/'contracts/renderer_binding.json')
        binding=json.loads((root/'contracts/renderer_binding.json').read_text(encoding='utf-8'))
        manifest=root/'handoff_manifest.json'; manifest.write_text(json.dumps({'episodeDate':DATE,'bundleId':SHA})+'\n',encoding='utf-8')
        preview=preview_builder.build(root=root,date=DATE,manifest=manifest,plot_run_id=123,artifact_name='handoff-artifact')
        if preview['expectedRendererCommit']!=binding['renderer']['commit']: raise AssertionError('Preview request did not use canonical Renderer binding')
        if preview['expectedRendererContractVersion']!=binding['renderer']['contractVersion']: raise AssertionError('Preview Renderer contract mismatch')
        if preview['expectedRegistrySnapshotSha256']!=binding['renderer']['registrySnapshotSha256']: raise AssertionError('Preview Registry binding mismatch')
        if preview['confirmation']!='PREVIEW': raise AssertionError('Preview confirmation mismatch')

        identity=root/'preview_identity.json'; identity.write_text(json.dumps({
          'episodeDate':DATE,'rendererCommit':'b'*40,'rendererContractVersion':'2.4.0','registrySnapshotSha256':'c'*64,
          'inputSpecSha256':'d'*64,'ttsInputSha256':'e'*64,'ttsBlockAudioSha256':{'scenes-01-04':'f'*64,'scenes-05-09':'1'*64}
        })+'\n',encoding='utf-8')
        review=root/'human_preview_review.json'; review.write_text(json.dumps({'status':'approved','episodeDate':DATE,'previewRunId':456,'approvedPreviewSha256':'2'*64})+'\n',encoding='utf-8')
        auth=root/'final_render_authorization.json'; auth.write_text(json.dumps({'status':'approved','episodeDate':DATE,'previewRunId':456,'approvedPreviewSha256':'2'*64})+'\n',encoding='utf-8')
        try:
            final_builder.build(date=DATE,preview_run_id=456,approved_preview_sha256='2'*64,preview_identity=identity,human_review=review,final_authorization=auth,explicit_final=False)
        except final_builder.FinalRequestError:
            pass
        else:
            raise AssertionError('Final request built without explicit final')
        final=final_builder.build(date=DATE,preview_run_id=456,approved_preview_sha256='2'*64,preview_identity=identity,human_review=review,final_authorization=auth,explicit_final=True)
        if final['confirmation']!='FINAL_RENDER': raise AssertionError('Final confirmation mismatch')
        if final['rendererCommit']!='b'*40 or final['ttsBlockAudioSha256']['scenes-01-04']!='f'*64: raise AssertionError('Final identity projection mismatch')
    print('current Preview/Final request builders PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
