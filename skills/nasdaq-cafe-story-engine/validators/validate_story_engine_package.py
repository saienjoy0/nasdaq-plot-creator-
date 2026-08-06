#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, FormatChecker

UPDATE_ROLES={"turn","complication","boundary","counterevidence","disproof","reveal"}
FORBIDDEN=("今すぐ買うべき","今すぐ売るべき","買い場","必ず上がる","必ず下がる","乗り遅れるな","暴落確定")
PROCEDURAL=("三点確認します","順番に見ます","次は市場反応です","ここで整理します","仮説を検証します","確認できた数字を置きます","三つだけ並べます")

@dataclass
class Item:
    code:str
    message:str
    path:str=""
    def dict(self)->dict[str,str]: return {"code":self.code,"message":self.message,"path":self.path}

def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError("JSON root must be object")
    return value

def safe(root:Path,ref:dict[str,Any],label:str,errors:list[Item])->Path|None:
    p=Path(str(ref.get("path","")))
    if p.is_absolute(): errors.append(Item("E_PATH","absolute path forbidden",label)); return None
    q=(root/p).resolve()
    if q!=root and root not in q.parents: errors.append(Item("E_PATH","path escapes root",label)); return None
    if not q.is_file(): errors.append(Item("E_PATH",f"missing file: {p}",label)); return None
    actual=sha(q)
    if actual!=ref.get("sha256"): errors.append(Item("E_HASH",f"hash mismatch declared={ref.get('sha256')} actual={actual}",label))
    return q

def validate(package:Path,schema:Path,root:Path)->dict[str,Any]:
    root=root.resolve(); errors:list[Item]=[]; warnings:list[Item]=[]
    try: pkg=load(package); sch=load(schema)
    except Exception as exc: return {"status":"fail","errors":[Item("E_JSON",str(exc),str(package)).dict()],"warnings":[]}
    validator=Draft202012Validator(sch,format_checker=FormatChecker())
    for err in sorted(validator.iter_errors(pkg),key=lambda x:list(x.absolute_path)):
        errors.append(Item("E_SCHEMA",err.message,".".join(map(str,err.absolute_path))))
    if errors: return report(pkg,package,errors,warnings)

    sb=pkg["source_binding"]
    if sb["author_invocation_id"]==sb["critic_invocation_id"]:
        errors.append(Item("E_INVOCATION_NOT_INDEPENDENT","Author and Critic IDs must differ","source_binding"))
    isolation=sb["critic_isolation_mode"]
    if pkg["mode"]=="production" and isolation!="separate_invocation":
        errors.append(Item("E_CRITIC_ISOLATION","production mode requires a separately executed Critic invocation","source_binding.critic_isolation_mode"))
    if pkg["mode"]=="shadow" and isolation=="logical_shadow":
        warnings.append(Item("W_LOGICAL_SHADOW_CRITIC","Critic input was isolated at artifact level, but separate model-process execution is not proven","source_binding.critic_isolation_mode"))
    for name,ref in sb["files"].items(): safe(root,ref,f"source_binding.files.{name}",errors)

    baseline=pkg["editorial_baseline"]
    evidence=set(baseline["evidence_ids"]); counter=set(baseline["counterevidence_ids"])
    claims={c["claim_id"]:c for c in pkg["claim_ledger"]}
    if len(claims)!=len(pkg["claim_ledger"]): errors.append(Item("E_CLAIM_LEDGER","duplicate claim ID","claim_ledger"))
    for cid,c in claims.items():
        if not set(c["evidence_ids"])<=evidence or not set(c["counterevidence_ids"])<=counter:
            errors.append(Item("E_CLAIM_LEDGER",f"{cid} references evidence outside baseline","claim_ledger"))

    angles={a["angle_id"]:a for a in pkg["story_discovery"]["angle_candidates"]}
    for aid,a in angles.items():
        if not set(a["supported_claim_ids"])<=set(claims): errors.append(Item("E_ANGLE_CLAIM",f"{aid} references unknown Claim","story_discovery.angle_candidates"))
    selected=pkg["selected_angle"]["angle_id"]
    if selected not in angles or not angles.get(selected,{}).get("eligible"):
        errors.append(Item("E_SELECTED_ANGLE","selected angle missing or ineligible","selected_angle.angle_id"))
    if pkg["selected_angle"]["story_spine"]!=baseline["story_spine"]:
        errors.append(Item("E_STORY_SPINE","selected spine differs from baseline","selected_angle.story_spine"))
    if pkg["author_draft"]["story_spine"]!=baseline["story_spine"]:
        errors.append(Item("E_STORY_SPINE","author draft spine differs from baseline","author_draft.story_spine"))

    scenes=pkg["narrative_arc"]["scenes"]; expected=[f"scene-{i:02d}" for i in range(1,10)]
    if [s["scene_id"] for s in scenes]!=expected:
        errors.append(Item("E_SCENE_SEQUENCE","Scenes must be scene-01 through scene-09 in order","narrative_arc.scenes"))
    if not any(set(s["story_roles"])&UPDATE_ROLES for s in scenes[3:7]):
        errors.append(Item("E_NO_UNDERSTANDING_UPDATE","Scenes 4–7 have no understanding update","narrative_arc.scenes"))
    for i,s in enumerate(scenes):
        if not set(s["new_evidence_ids"])<=evidence: errors.append(Item("E_SCENE_EVIDENCE","Scene references evidence outside baseline",f"narrative_arc.scenes.{i}"))
        if not s["new_evidence_ids"] and not s["new_meaning"].strip(): errors.append(Item("E_NO_EVIDENCE_OR_MEANING","Scene has no new evidence or meaning",f"narrative_arc.scenes.{i}"))
        if s["viewer_belief_before"].strip()==s["viewer_belief_after"].strip(): errors.append(Item("E_NO_BELIEF_CHANGE","Scene belief does not change",f"narrative_arc.scenes.{i}"))
    loops={x["loop_id"] for x in pkg["narrative_arc"]["open_loops"]}
    opened={x for s in scenes for x in s["open_loop_ids_opened"]}; closed={x for s in scenes for x in s["open_loop_ids_closed"]}
    if opened!=loops or closed!=loops: errors.append(Item("E_OPEN_LOOP_REFERENCE","open-loop catalog and Scene use differ","narrative_arc"))
    if scenes[-1]["open_loop_ids_opened"]: errors.append(Item("E_SCENE9_OPENS_LOOP","Scene 9 opens a loop","narrative_arc.scenes.8"))

    safe(root,pkg["author_draft"]["episode_package"],"author_draft.episode_package",errors)
    final=safe(root,pkg["final"]["episode_package"],"final.episode_package",errors)
    if not all(pkg["author_draft"]["surfaces_complete"].values()): errors.append(Item("E_DRAFT_INCOMPLETE","all production surfaces must be complete","author_draft.surfaces_complete"))

    finding_ids:set[str]=set(); critical:list[str]=[]; previous=0
    for i,r in enumerate(pkg["review_rounds"]):
        if r["round"]!=previous+1: errors.append(Item("E_REVIEW_SEQUENCE","rounds must be sequential",f"review_rounds.{i}.round"))
        previous=r["round"]
        if r["critic_invocation_id"]!=sb["critic_invocation_id"]: errors.append(Item("E_INVOCATION_NOT_INDEPENDENT","round Critic ID differs",f"review_rounds.{i}"))
        wanted=pkg["author_draft"]["episode_package"]["sha256"] if i==0 else pkg["review_rounds"][i-1]["output_episode_package"]["sha256"]
        if r["input_episode_package_sha256"]!=wanted: errors.append(Item("E_REVIEW_INPUT_HASH","review input hash breaks lineage",f"review_rounds.{i}"))
        safe(root,r["output_episode_package"],f"review_rounds.{i}.output_episode_package",errors)
        for f in r["findings"]:
            fid=f["finding_id"]
            if fid in finding_ids: errors.append(Item("E_FINDING_DUPLICATE","duplicate finding ID",f"review_rounds.{i}"))
            finding_ids.add(fid)
            preserve=f["must_preserve"]
            if not set(preserve["claim_ids"])<=set(claims) or not set(preserve["evidence_ids"])<=evidence:
                errors.append(Item("E_FINDING_PRESERVATION","finding preservation refs escape baseline",f"review_rounds.{i}.findings"))
            if f["severity"]=="critical" and f["status"]!="fixed": critical.append(fid)
        for patch in r["patches"]:
            if not set(patch["finding_ids"])<=finding_ids: errors.append(Item("E_PATCH_ORPHAN","patch references unknown finding",f"review_rounds.{i}.patches"))
            if patch["status"]=="applied" and not patch["target_paths"]: errors.append(Item("E_PATCH_TARGET","applied patch has no targets",f"review_rounds.{i}.patches"))
    if critical: errors.append(Item("E_CRITICAL_FINDING",f"unresolved Critical findings: {critical}","review_rounds"))
    if pkg["final"]["final_review_round"]!=pkg["review_rounds"][-1]["round"] or pkg["review_rounds"][-1]["decision"]!="pass":
        errors.append(Item("E_FINAL_REVIEW","final review round is not the last passing review","final"))

    diff=pkg["causality_diff"]
    if diff["status"]!="pass" or diff["violation_codes"] or set(diff["preserved_claim_ids"])!=set(claims): errors.append(Item("E_CAUSALITY_DIFF","causality preservation did not pass","causality_diff"))
    if diff["compared_from_sha256"]!=pkg["author_draft"]["episode_package"]["sha256"] or diff["compared_to_sha256"]!=pkg["final"]["episode_package"]["sha256"]: errors.append(Item("E_CAUSALITY_DIFF","diff hashes do not bind draft/final","causality_diff"))
    if pkg["final"]["review_status"]!="pass": errors.append(Item("E_FINAL_REVIEW","final review did not pass","final.review_status"))
    gate=pkg["final_gate"]
    if gate["status"]!="pass" or gate["blocking_codes"]: errors.append(Item("E_FINAL_GATE","final gate blocked","final_gate"))
    if pkg["mode"]=="shadow" and gate["production_eligible"]:
        errors.append(Item("E_SHADOW_PRODUCTION_ELIGIBILITY","shadow packages cannot be marked production eligible","final_gate.production_eligible"))
    if pkg["mode"]=="production" and not gate["production_eligible"]:
        errors.append(Item("E_PRODUCTION_ELIGIBILITY","production package must be explicitly production eligible","final_gate.production_eligible"))
    if pkg["review_rounds"][-1]["output_episode_package"]["sha256"]!=pkg["final"]["episode_package"]["sha256"]: errors.append(Item("E_FINAL_HASH","last review output differs from final","final"))
    if final:
        text=final.read_text(encoding="utf-8",errors="replace")
        for phrase in FORBIDDEN:
            if phrase in text: errors.append(Item("E_FORBIDDEN_PUBLIC_TEXT",f"forbidden phrase: {phrase}",str(final)))
        for phrase in PROCEDURAL:
            if phrase in text: warnings.append(Item("W_PROCEDURAL_LANGUAGE",f"Critic must review phrase: {phrase}",str(final)))
        if "僕" not in text: warnings.append(Item("W_FOX_FIRST_PERSON","final package does not contain 僕",str(final)))
    return report(pkg,package,errors,warnings)

def report(pkg:dict[str,Any],package:Path,errors:list[Item],warnings:list[Item])->dict[str,Any]:
    return {"contract_version":"1.0.0","episode_date":str(pkg.get("episode_date","unknown")),"status":"fail" if errors else "pass","checked_package_sha256":sha(package) if package.is_file() else "0"*64,"errors":[x.dict() for x in errors],"warnings":[x.dict() for x in warnings]}

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("--repo-root",type=Path,default=Path.cwd()); parser.add_argument("--package",type=Path,required=True); parser.add_argument("--schema",type=Path,required=True); parser.add_argument("--output",type=Path); args=parser.parse_args()
    root=args.repo_root.resolve(); package=args.package if args.package.is_absolute() else root/args.package; schema=args.schema if args.schema.is_absolute() else root/args.schema
    result=validate(package,schema,root); payload=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    if args.output:
        out=args.output if args.output.is_absolute() else root/args.output; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(payload,encoding="utf-8")
    print(payload,end=""); return 0 if result["status"]=="pass" else 1
if __name__=="__main__": raise SystemExit(main())
