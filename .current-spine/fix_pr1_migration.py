#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).with_name("apply_pr1.py")
text = path.read_text(encoding="utf-8")
replacements = [
    (
        'if "run_daily_production_hardened" in v12 or "_rebind_request_sha" in v12:\n',
        'if "import run_daily_production_hardened as hardened" in v12 or "def _rebind_request_sha(" in v12:\n',
        "migration guard",
    ),
    (
        '        daily.write_text("# synthetic current source\\n", encoding="utf-8")\n',
        '        daily.write_text("# synthetic current source\\\\n", encoding="utf-8")\n',
        "daily-source newline escape",
    ),
    (
        '        freeze.write_text(json.dumps({"contractVersion": "1.2.0", "episodeDate": DATE}) + "\\n", encoding="utf-8")\n',
        '        freeze.write_text(json.dumps({"contractVersion": "1.2.0", "episodeDate": DATE}) + "\\\\n", encoding="utf-8")\n',
        "freeze newline escape",
    ),
]
for old, new, label in replacements:
    if text.count(old) != 1:
        raise SystemExit(f"{label} occurrence drift: {text.count(old)}")
    text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("PR-1 migration guard and generated-test escaping repaired")
