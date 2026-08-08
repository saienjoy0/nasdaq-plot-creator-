#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
from validate_story_engine_package import validate
import json

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path,default=Path.cwd());p.add_argument("--package",type=Path,required=True);p.add_argument("--output",type=Path);a=p.parse_args()
    root=a.repo_root.resolve(); schema=(root/"skills/nasdaq-cafe-story-engine/contracts/story_engine_package.schema.json").resolve(); package=a.package if a.package.is_absolute() else root/a.package
    result=validate(package,schema,root); payload=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    if a.output:
        out=a.output if a.output.is_absolute() else root/a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(payload,encoding="utf-8")
    print(payload,end="");return 0 if result["status"]=="pass" else 1
if __name__=="__main__": raise SystemExit(main())
