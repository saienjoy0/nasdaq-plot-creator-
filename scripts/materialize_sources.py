#!/usr/bin/env python3
"""Materialize packed 03/04 canon documents from the single 01-04 manifest."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from canon_manifest import DEFAULT_MANIFEST, CanonManifestError, materialize, verify

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(ROOT, args.manifest) if args.check_only else materialize(ROOT, args.manifest)
        code = 0
    except (OSError, CanonManifestError) as exc:
        result = {"status": "FAIL", "error": str(exc)}
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
