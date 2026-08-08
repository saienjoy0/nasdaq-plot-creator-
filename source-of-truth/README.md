# Source-of-truth packaging

`01_fox_character_bible.md` and `02_editorial_bible.md` are stored directly.

Large 03/04 rulebooks may be stored as deterministic packed transport under `source-of-truth/packed/` and described by `source-of-truth/packed_sources.json`. Their authoritative identity is the logical path plus the manifest SHA-256 and raw byte length, not the gzip byte stream itself.

Use:

```bash
python scripts/materialize_sources.py --check-only
```

before any Story Engine Critic bundling or production use. This reconstructs the logical Markdown and verifies both SHA-256 and raw byte length.

If a packed transport part is corrupted but the authoritative source document is available and its raw byte length and SHA-256 exactly match the existing manifest, it is permitted to regenerate only the gzip+base64 transport parts. Do **not** change `packed_sources.json`, the logical document identity, source filename, or neighboring rulebooks during such a transport-only repair.

A transport repair must be accepted only after `scripts/materialize_sources.py --check-only` passes for every packed source.
