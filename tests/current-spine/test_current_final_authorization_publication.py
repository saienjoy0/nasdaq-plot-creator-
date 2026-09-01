#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))

import publish_current_final_authorization_v1 as publisher  # noqa: E402

DATE='2099-07-01'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main()->int:
    with tempfile.TemporaryDirectory(prefix='nasdaq-current-final-publication-') as temp:
        root=Path(temp)
        identity_bytes=(json.dumps({
            'contractVersion':'1.0.0',
            'episodeDate':DATE,
            'rendererCommit':'b'*40,
            'rendererContractVersion':'2.4.0',
            'registrySnapshotSha256':'c'*64,
            'inputSpecSha256':'d'*64,
            'ttsInputSha256':'e'*64,
            'ttsBlockAudioSha256':{'scenes-01-04':'f'*64,'scenes-05-09':'1'*64},
        },ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')
        identity_sha=hashlib.sha256(identity_bytes).hexdigest()
        request=root/'final-authorization-request.json'
        request.write_text(json.dumps({
            'contractVersion':'1.0.0',
            'episodeDate':DATE,
            'previewRunId':456,
            'approvedPreviewSha256':'2'*64,
            'previewIdentitySha256':identity_sha,
            'previewIdentityBase64':base64.b64encode(identity_bytes).decode('ascii'),
            'confirmation':'FINAL_AUTHORIZATION',
        },ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        result=publisher.publish(request=request,plot_authorization_run_id=789,output_root=root/'out')
        bundle=Path(result['bundle_root'])
        final_request=Path(result['final_request_path'])
        receipt=Path(result['publication_receipt_path'])
        if result['artifact_name']!=f'nasdaq-cafe-final-authorization-{DATE}-789': raise AssertionError('Authorization artifact identity mismatch')
        if not all((bundle/name).is_file() for name in ('human_preview_review.json','final_render_authorization.json','final_authorization_manifest.json')): raise AssertionError('Authorization bundle incomplete')
        request_value=json.loads(final_request.read_text(encoding='utf-8'))
        if request_value['requestVersion']!='2.1.0' or request_value['plotAuthorizationRunId']!=789: raise AssertionError('Final request did not project authorization run')
        if request_value['previewIdentitySha256']!=identity_sha: raise AssertionError('Exact Preview identity SHA changed')
        receipt_value=json.loads(receipt.read_text(encoding='utf-8'))
        expected_target=f"final-render-requests-v2/{DATE}-plot-auth-789-{request_value['finalFingerprint'][:12]}.json"
        if receipt_value['state']!='FINAL_REQUEST_PUBLICATION_READY' or receipt_value['renderer']['targetPath']!=expected_target: raise AssertionError('Final publication target mismatch')
        if receipt_value['request']['sha256']!=sha256(final_request): raise AssertionError('Publication receipt does not bind Final request bytes')

    workflow=ROOT/'.github/workflows/chatgpt-daily-final-authorization.yml'
    text=workflow.read_text(encoding='utf-8')
    required=(
        'final-authorization-requests-v1/*.json',
        'publish_current_final_authorization_v1.py',
        'actions/upload-artifact@v4',
        'FINAL REQUEST PUBLICATION READY',
    )
    for needle in required:
        if needle not in text: raise AssertionError(f'Final authorization workflow missing {needle}')
    if 'final-render-requests-v2/' in text and 'targetPath' not in text:
        raise AssertionError('Plot authorization workflow must publish request metadata, not write Renderer Final requests')
    print('current Final authorization publication PASS'); return 0


if __name__=='__main__': raise SystemExit(main())
