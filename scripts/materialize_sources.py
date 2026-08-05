#!/usr/bin/env python3
"""Materialize packed 03/04 source-of-truth Markdown files and verify hashes."""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "source-of-truth" / "packed_sources.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    failures: list[str] = []

    for source in manifest["sources"]:
        logical_path = ROOT / source["logical_path"]
        chunks: list[str] = []
        for relative_part in source["parts"]:
            part = ROOT / relative_part
            if not part.exists():
                failures.append(f"missing packed part: {relative_part}")
                continue
            chunks.append(part.read_text(encoding="ascii").strip())

        if len(chunks) != len(source["parts"]):
            continue

        try:
            packed = base64.b64decode("".join(chunks), validate=True)
            raw = gzip.decompress(packed)
        except Exception as exc:  # malformed source must fail loudly
            failures.append(f"cannot decode {source['source_name']}: {exc}")
            continue

        actual_hash = sha256(raw)
        expected_hash = source["sha256"]
        if actual_hash != expected_hash:
            failures.append(
                f"hash mismatch for {source['source_name']}: "
                f"expected {expected_hash}, got {actual_hash}"
            )
            continue

        if len(raw) != source["raw_bytes"]:
            failures.append(
                f"size mismatch for {source['source_name']}: "
                f"expected {source['raw_bytes']}, got {len(raw)}"
            )
            continue

        if not args.check_only:
            logical_path.parent.mkdir(parents=True, exist_ok=True)
            logical_path.write_bytes(raw)
            print(f"WROTE {logical_path.relative_to(ROOT)} {actual_hash}")
        else:
            print(f"PASS {source['source_name']} {actual_hash}")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
