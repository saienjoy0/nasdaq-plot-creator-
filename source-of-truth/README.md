# Source-of-truth canon

`source-of-truth/canon_manifest.json` is the single machine-readable authority for the four semantic rulebooks used by 朝のNASDAQカフェ.

- `01_fox_character_bible.md` and `02_editorial_bible.md` are stored directly.
- Large 03/04 rulebooks are stored as deterministic gzip+base64 transport under `source-of-truth/packed/` and materialized when needed.
- For every document, the manifest fixes the logical path, exact logical SHA-256, raw byte length, storage mode, and physical parts.
- Workflow checks, validators, materialization, and ChatGPT semantic freeze must consume this same manifest. They must not maintain separate document SHA constants.

Verify without writing:

```bash
python scripts/canon_manifest.py verify
python scripts/materialize_sources.py --check-only
```

Materialize 03/04:

```bash
python scripts/materialize_sources.py
```

A packed transport repair is allowed only when reconstructed logical bytes still match the existing manifest SHA-256 and raw byte length exactly. A logical content change requires an intentional update to the Canon Manifest and therefore invalidates any daily semantic freeze that was bound to the previous manifest bytes.
