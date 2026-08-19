#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "scripts/run_daily_renderer_closure_v12.py"
text = path.read_text(encoding="utf-8")
old = "import renderer_binding\nimport renderer_contract_sync_v12\n"
new = (
    "import renderer_binding\n"
    "import renderer_contract_sync_v12\n"
    "from current_renderer_closure_mechanisms_v12 import (\n"
    "    ensure_renderer,\n"
    "    evidence_if_exists,\n"
    "    load,\n"
    "    run,\n"
    ")\n"
)
if text.count(old) != 1:
    raise SystemExit(f"closure import marker drift: {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("PR-2 closure helpers restored through explicit mechanism module")
