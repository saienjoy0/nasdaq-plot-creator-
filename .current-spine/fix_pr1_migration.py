#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).with_name("apply_pr1.py")
text = path.read_text(encoding="utf-8")
old = 'if "run_daily_production_hardened" in v12 or "_rebind_request_sha" in v12:\n'
new = 'if "import run_daily_production_hardened as hardened" in v12 or "def _rebind_request_sha(" in v12:\n'
if text.count(old) != 1:
    raise SystemExit(f"migration guard occurrence drift: {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("PR-1 migration guard repaired")
