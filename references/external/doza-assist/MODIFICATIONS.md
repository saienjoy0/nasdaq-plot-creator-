# Doza Assist vendor modifications

## Vendored snapshot

`storytelling-foundation-oss.md` is stored as an unmodified snapshot of:

- Repository: `DozaVisuals/doza-assist`
- Commit: `b93e6b912ca17a85c8ceaca93983c23695063679`
- Original path: `docs/storytelling-foundation-oss.md`

The vendor copy itself is not rewritten to sound like NASDAQ Cafe.

## NASDAQ-specific adaptation

Adaptation happens outside the vendor snapshot.

Only the following families of rules may be mapped into Story Engine runtime:

- hook as question / counterintuitive gap
- explicit story roles
- adjacent redundancy rejection
- information-only rejection
- topic vs theme/claim distinction
- midpoint turn requirement
- self-check before finalization

The following rules are excluded because they are documentary/interview specific and would distort the NASDAQ Cafe contract:

- breath based in/out points
- filler density as reveal signal
- tense changes as emotional signal
- emotional-valence requirements
- protagonist transformation requirements
- clip editing/export workflow

## Source-of-truth boundary

External rules may never override:

1. Project Instructions
2. `02_editorial_bible.md`
3. `01_fox_character_bible.md`
4. `03_episode_production_spec.md`
5. `04_entertainment_inquisitor.md`

In particular, external storytelling rules may not:

- invent or modify Expected / Actual / Gap
- change timeline order
- strengthen confidence
- remove counterevidence
- promote a company-specific cause to NASDAQ-wide primary cause
- delete/reorder the formal 9-scene skeleton
- place a new argument in Scene 9

## Runtime integration target

A small NASDAQ-owned adapter should translate selected external rules into project-native checks, for example:

```text
external: A sequence without a turn is a list.
NASDAQ: Scene 4–6 must contain an evidence-backed explanatory turn.
Guard: the turn cannot be manufactured by changing evidence or timeline.
```

No runtime import from the external repository is permitted. The pinned vendor snapshot is sufficient for provenance and review.