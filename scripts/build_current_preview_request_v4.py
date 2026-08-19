#!/usr/bin/env python3
"""Build Renderer Current Preview Request V4 from one immutable Plot handoff."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import renderer_binding


class PreviewRequestError(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, label: str) -> dict[str, Any]:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:
        raise PreviewRequestError(f"{label} invalid: {exc}") from exc
    if not isinstance(value,dict): raise PreviewRequestError(f"{label} must be an object")
    return value


def first_string(value: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        item=value.get(key)
        if isinstance(item,str) and item: return item
    return None


def build(*, root: Path, date: str, manifest: Path, plot_run_id: int, artifact_name: str,
          signed_url: str="", signed_digest: str="") -> dict[str, Any]:
    root=root.resolve(); manifest=manifest.resolve()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",date): raise PreviewRequestError("episode date must be YYYY-MM-DD")
    if plot_run_id <= 0: raise PreviewRequestError("plot_run_id must be positive")
    if not re.fullmatch(r"[A-Za-z0-9._-]+",artifact_name): raise PreviewRequestError("unsafe artifact name")
    value=load(manifest,"handoff manifest")
    manifest_date=first_string(value,"episode_date","episodeDate")
    if manifest_date and manifest_date != date: raise PreviewRequestError("handoff manifest date mismatch")
    bundle_id=first_string(value,"bundle_id","bundleId")
    if not bundle_id or not re.fullmatch(r"[0-9a-f]{64}",bundle_id): raise PreviewRequestError("handoff manifest bundle id missing/invalid")
    binding=renderer_binding.load_binding(root); renderer=binding["renderer"]
    if bool(signed_url) != bool(signed_digest): raise PreviewRequestError("signed URL/digest must be supplied together")
    if signed_digest and not re.fullmatch(r"[0-9a-f]{64}",signed_digest): raise PreviewRequestError("signed digest must be SHA-256")
    return {
        "contractVersion":"2.0.0",
        "episodeDate":date,
        "plotRunId":plot_run_id,
        "handoffArtifactName":artifact_name,
        "expectedBundleId":bundle_id,
        "expectedManifestSha256":sha256(manifest),
        "expectedRendererCommit":renderer["commit"],
        "expectedRendererContractVersion":renderer["contractVersion"],
        "expectedRegistrySnapshotSha256":renderer["registrySnapshotSha256"],
        "signedArtifactUrl":signed_url,
        "signedArtifactDigestSha256":signed_digest,
        "confirmation":"PREVIEW",
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--root",type=Path,default=Path.cwd()); p.add_argument("--date",required=True)
    p.add_argument("--manifest",type=Path,required=True); p.add_argument("--plot-run-id",type=int,required=True); p.add_argument("--artifact-name",required=True)
    p.add_argument("--signed-url",default=""); p.add_argument("--signed-digest",default=""); p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    try:
        value=build(root=a.root,date=a.date,manifest=a.manifest,plot_run_id=a.plot_run_id,artifact_name=a.artifact_name,signed_url=a.signed_url,signed_digest=a.signed_digest)
        a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps({"status":"PASS","path":str(a.output),"sha256":sha256(a.output)},sort_keys=True)); return 0
    except (OSError,PreviewRequestError,renderer_binding.RendererBindingError) as exc:
        print(json.dumps({"status":"FAIL","errors":[str(exc)]},ensure_ascii=False)); return 2
if __name__=="__main__": raise SystemExit(main())
