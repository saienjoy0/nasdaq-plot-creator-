#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))

import build_current_final_authorization_bundle_v1 as auth_bundle  # noqa: E402
import build_current_final_request_v2 as final_builder  # noqa: E402
import build_current_preview_request_v4 as preview_builder  # noqa: E402

DATE='2099-07-01'
SHA='a'*64


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
          'contractVersion':'1.0.0','episodeDate':DATE,'rendererCommit':'b'*40,'rendererContractVersion':'2.4.0','registrySnapshotSha256':'c'*64,
          'inputSpecSha256':'d'*64,'ttsInputSha256':'e'*64,'ttsBlockAudioSha256':{'scenes-01-04':'f'*64,'scenes-05-09':'1'*64}
        },sort_keys=True,indent=2)+'\n',encoding='utf-8')
        preview_sha='2'*64
        try:
            auth_bundle.build(
                date=DATE,
                preview_run_id=456,
                approved_preview_sha256=preview_sha,
                preview_identity=identity,
                explicit_user_approval=False,
                output_root=root/'authorization-bundle',
            )
        except auth_bundle.FinalAuthorizationBundleError:
            pass
        else:
            raise AssertionError('Final authorization bundle built without explicit user approval')

        bundle=auth_bundle.build(
            date=DATE,
            preview_run_id=456,
            approved_preview_sha256=preview_sha,
            preview_identity=identity,
            explicit_user_approval=True,
            output_root=root/'authorization-bundle',
        )
        review=Path(bundle['human_review_path'])
        auth=Path(bundle['final_authorization_path'])
        authorization_manifest=Path(bundle['manifest_path'])
        review_value=json.loads(review.read_text(encoding='utf-8'))
        auth_value=json.loads(auth.read_text(encoding='utf-8'))
        manifest_value=json.loads(authorization_manifest.read_text(encoding='utf-8'))
        expected_identity_sha=sha256(identity)
        if set(review_value)!={'contractVersion','status','episodeDate','previewRunId','approvedPreviewSha256','previewIdentitySha256'}: raise AssertionError('Human review fields drifted')
        if set(auth_value)!={'contractVersion','status','episodeDate','previewRunId','approvedPreviewSha256','previewIdentitySha256','humanPreviewReviewSha256','finalAuthorized'}: raise AssertionError('Final authorization fields drifted')
        if set(manifest_value)!={'contractVersion','episodeDate','previewRunId','approvedPreviewSha256','previewIdentitySha256','humanPreviewReviewSha256','plotFinalAuthorizationSha256'}: raise AssertionError('Authorization manifest fields drifted')
        if review_value['previewIdentitySha256']!=expected_identity_sha or auth_value['previewIdentitySha256']!=expected_identity_sha: raise AssertionError('Preview identity SHA not preserved')
        if auth_value['humanPreviewReviewSha256']!=sha256(review): raise AssertionError('Final authorization does not bind human review')
        if manifest_value['humanPreviewReviewSha256']!=sha256(review) or manifest_value['plotFinalAuthorizationSha256']!=sha256(auth): raise AssertionError('Manifest lineage mismatch')

        try:
            final_builder.build(
                date=DATE,preview_run_id=456,approved_preview_sha256=preview_sha,
                preview_identity=identity,human_review=review,final_authorization=auth,
                authorization_manifest=authorization_manifest,plot_authorization_run_id=789,
                plot_authorization_artifact_name=f'nasdaq-cafe-final-authorization-{DATE}-789',
                explicit_final=False,
            )
        except final_builder.FinalRequestError:
            pass
        else:
            raise AssertionError('Final request built without explicit final')
        final=final_builder.build(
            date=DATE,preview_run_id=456,approved_preview_sha256=preview_sha,
            preview_identity=identity,human_review=review,final_authorization=auth,
            authorization_manifest=authorization_manifest,plot_authorization_run_id=789,
            plot_authorization_artifact_name=f'nasdaq-cafe-final-authorization-{DATE}-789',
            explicit_final=True,
        )
        if final['requestVersion']!='2.1.0' or final['confirmation']!='FINAL_RENDER': raise AssertionError('Final request version/confirmation mismatch')
        if final['rendererCommit']!='b'*40 or final['ttsBlockAudioSha256']['scenes-01-04']!='f'*64: raise AssertionError('Final identity projection mismatch')
        if final['plotAuthorizationRunId']!=789 or final['plotAuthorizationArtifactName']!=f'nasdaq-cafe-final-authorization-{DATE}-789': raise AssertionError('Plot authorization artifact identity missing')
        if final['plotAuthorizationManifestSha256']!=sha256(authorization_manifest): raise AssertionError('Authorization manifest SHA missing')
        if final['humanPreviewReviewSha256']!=sha256(review) or final['plotFinalAuthorizationSha256']!=sha256(auth): raise AssertionError('Final request approval lineage mismatch')
        fingerprint='\n'.join((sha256(identity),preview_sha,sha256(auth),'b'*40)).encode('utf-8')
        if final['finalFingerprint']!=hashlib.sha256(fingerprint).hexdigest(): raise AssertionError('Final fingerprint mismatch')
    print('current Preview/Final request builders PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
