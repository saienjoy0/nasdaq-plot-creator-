#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).with_name("validate_story_engine_package.py")
spec=importlib.util.spec_from_file_location("story_engine_validator",BASE);mod=importlib.util.module_from_spec(spec);assert spec and spec.loader;sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
SCHEMA=ROOT/"skills/nasdaq-cafe-story-engine/contracts/story_engine_package.schema.json"
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path,default=ROOT);p.add_argument("--package",type=Path,required=True);p.add_argument("--output",type=Path);a=p.parse_args();root=a.repo_root.resolve()
 if root!=ROOT.resolve(): print(json.dumps({"status":"fail","error":"repo-root must be repository root"}));return 2
 package=a.package if a.package.is_absolute() else root/a.package;result=mod.validate(package,SCHEMA,root);payload=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
 out=a.output
 if out is None: out=root/f"verification/{result.get('episode_date','unknown')}/story_engine_validation_report.json"
 elif not out.is_absolute(): out=root/out
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(payload,encoding="utf-8");print(payload,end="");return 0 if result["status"]=="pass" else 1
if __name__=="__main__": raise SystemExit(main())
