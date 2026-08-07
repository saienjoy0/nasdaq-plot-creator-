# Doza Assist external source record

- Project: Doza Assist
- Repository: `DozaVisuals/doza-assist`
- Pinned commit: `b93e6b912ca17a85c8ceaca93983c23695063679`
- Original asset: `docs/storytelling-foundation-oss.md`
- Reference helper: `editorial_dna/storytelling.py`
- License: MIT
- Fetched / reviewed: 2026-08-07
- Adoption mode: `direct-vendor` for the foundation document; NASDAQ-specific adapter for runtime use

## Why this asset is imported

The foundation contains compact operational storytelling rules that directly address the current NASDAQ Cafe script failure modes: adjacent redundancy, absence of a midpoint turn, information-only sequencing, weak hooks, unclear story roles, and lack of a final self-check.

## Runtime policy

The vendored document is a pinned external reference, not a higher-priority source of truth.

Priority remains:

```text
Project Instructions
→ 02_editorial_bible.md
→ 01_fox_character_bible.md
→ 03_episode_production_spec.md
→ 04_entertainment_inquisitor.md
→ external storytelling references
```

Do not inject the complete document blindly into every LLM call.
A NASDAQ adapter must select only rules compatible with 01–04.

## Rules intentionally excluded from NASDAQ runtime

- breath-gap based clip cutting
- filler-density interpretation
- tense-shift based documentary clip selection
- documentary protagonist emotional transformation requirements
- Final Cut / Premiere / interview-specific in/out point logic

## License handling

The original MIT LICENSE from the pinned repository is stored alongside this record.
The vendored document is kept unmodified; NASDAQ-specific transformations are documented separately in `MODIFICATIONS.md` and implemented outside the vendor snapshot.