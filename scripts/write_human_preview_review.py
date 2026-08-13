#!/usr/bin/env python3
"""Write human_preview_review.json only from an explicit user approval action."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--date", required=True)
    parser.add_argument("--preview", required=True, type=Path)
    parser.add_argument("--explicit-user-approval", action="store_true")
    args = parser.parse_args()
    if not args.explicit_user_approval:
        raise SystemExit("human preview approval requires --explicit-user-approval")
    root = args.root.resolve()
    preview = args.preview.resolve()
    if not preview.is_file():
        raise SystemExit(f"preview missing: {preview}")
    value = {
        "contractVersion": "1.0.0",
        "episodeDate": args.date,
        "previewSha256": hashlib.sha256(preview.read_bytes()).hexdigest(),
        "status": "approved",
        "reviewedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    output = root / "verification" / args.date / "human_preview_review.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(output), **value}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
