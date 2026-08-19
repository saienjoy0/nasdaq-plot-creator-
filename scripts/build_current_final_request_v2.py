#!/usr/bin/env python3
"""Build Current Final Request V2 from approved Preview evidence.

This builder never renders. It is fail-closed and requires --explicit-final, a human
Preview approval, the Plot Final authorization, and the exact Renderer Preview
identity receipt produced by the approved Preview Artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


class FinalRequestError(ValueError):
    pass


def sha256(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path: Path, label: str) -> dict[str, Any]:
    try: value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise FinalRequestError(f"{label} invalid: {exc}") from exc
    if not isinstance(value,dict): raise FinalRequestError(f"{label} must be an object")
    return value

def approved(value: dict[str, Any]) -> bool:
    return value.get("status") in {"approved","APPROVED","pass","PASS"} or value.get("verdict") in {"approved","APPROVED","pass","PASS"}

def optional_match(value: dict[str, Any], keys: tuple[str,...], expected: Any, label: str) -> None:
    for key in keys:
        if key in value and str(value[key]) != str(expected):
            raise FinalRequestError(f"{label} mismatch at {key}")


def build(*, date: str, preview_run_id: int, approved_preview_sha256: str,
          preview_identity: Path, human_review: Path, final_authorization: Path,
          explicit_final: bool) -> dict[str, Any]:
    if not explicit_final: raise FinalRequestError("--explicit-final is required")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",date): raise FinalRequestError("episode date must be YYYY-MM-DD")
    if preview_run_id <= 0: raise FinalRequestError("preview_run_id must be positive")
    if not re.fullmatch(r"[0-9a-f]{64}",approved_preview_sha256): raise FinalRequestError("approved Preview SHA must be SHA-256")
    identity=load(preview_identity,"Preview identity"); review=load(human_review,"Human Preview review"); auth=load(final_authorization,"Final authorization")
    if identity.get("episodeDate") != date: raise FinalRequestError("Preview identity date mismatch")
    if not approved(review): raise FinalRequestError("Human Preview review is not approved")
    if not approved(auth) and auth.get("finalAuthorized") is not True and auth.get("final_authorized") is not True:
        raise FinalRequestError("Plot Final authorization is not approved")
    optional_match(review,("episodeDate","episode_date"),date,"Human review date")
    optional_match(auth,("episodeDate","episode_date"),date,"Final authorization date")
    optional_match(review,("previewRunId","preview_run_id"),preview_run_id,"Human review Preview run")
    optional_match(auth,("previewRunId","preview_run_id"),preview_run_id,"Final authorization Preview run")
    optional_match(review,("approvedPreviewSha256","approved_preview_sha256"),approved_preview_sha256,"Human review Preview SHA")
    optional_match(auth,("approvedPreviewSha256","approved_preview_sha256"),approved_preview_sha256,"Final authorization Preview SHA")
    audio=identity.get("ttsBlockAudioSha256")
    if not isinstance(audio,dict) or set(audio)!={"scenes-01-04","scenes-05-09"}: raise FinalRequestError("Preview identity TTS audio map invalid")
    required_sha=("registrySnapshotSha256","inputSpecSha256","ttsInputSha256")
    for key in required_sha:
        if not isinstance(identity.get(key),str) or not re.fullmatch(r"[0-9a-f]{64}",identity[key]): raise FinalRequestError(f"Preview identity {key} invalid")
    for block, digest in audio.items():
        if not isinstance(digest,str) or not re.fullmatch(r"[0-9a-f]{64}",digest): raise FinalRequestError(f"Preview audio SHA invalid: {block}")
    renderer_commit=identity.get("rendererCommit"); renderer_contract=identity.get("rendererContractVersion")
    if not isinstance(renderer_commit,str) or not re.fullmatch(r"[0-9a-f]{40}",renderer_commit): raise FinalRequestError("Preview Renderer commit invalid")
    if not isinstance(renderer_contract,str) or not renderer_contract: raise FinalRequestError("Preview Renderer contract invalid")
    return {
        "requestVersion":"2.0.0",
        "episodeDate":date,
        "previewRunId":preview_run_id,
        "approvedPreviewSha256":approved_preview_sha256,
        "previewIdentitySha256":sha256(preview_identity),
        "rendererCommit":renderer_commit,
        "rendererContractVersion":renderer_contract,
        "registrySnapshotSha256":identity["registrySnapshotSha256"],
        "renderSpecSha256":identity["inputSpecSha256"],
        "ttsInputSha256":identity["ttsInputSha256"],
        "ttsBlockAudioSha256":audio,
        "confirmation":"FINAL_RENDER",
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--date",required=True); p.add_argument("--preview-run-id",type=int,required=True); p.add_argument("--approved-preview-sha256",required=True)
    p.add_argument("--preview-identity",type=Path,required=True); p.add_argument("--human-review",type=Path,required=True); p.add_argument("--final-authorization",type=Path,required=True)
    p.add_argument("--explicit-final",action="store_true"); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    try:
        value=build(date=a.date,preview_run_id=a.preview_run_id,approved_preview_sha256=a.approved_preview_sha256,preview_identity=a.preview_identity, human_review=a.human_review,final_authorization=a.final_authorization,explicit_final=a.explicit_final)
        a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps({"status":"PASS","path":str(a.output),"sha256":sha256(a.output)},sort_keys=True)); return 0
    except (OSError,FinalRequestError) as exc:
        print(json.dumps({"status":"FAIL","errors":[str(exc)]},ensure_ascii=False)); return 2
if __name__=="__main__": raise SystemExit(main())
