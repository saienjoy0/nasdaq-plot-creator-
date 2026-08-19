#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "scripts/run_visual_intelligence_v12.py"
text = path.read_text(encoding="utf-8")
old = "        stale = visual_intelligence_read_set_v12.verify(root, direct_read_sets)\n"
new = "        stale = visual_intelligence_read_set_v12.verify(\n            root, direct_read_sets, renderer_root=renderer_root\n        )\n"
if text.count(old) != 1:
    raise SystemExit(f"read-set verifier call drift: {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("PR-3 read-set verifier bound to exact Renderer checkout")
