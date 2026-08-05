# PR #8｜Episode Package Memory References

## Purpose

Connect only revalidated editorial memory from a validated causal research dossier to the final episode package. The bridge is auditable by memory identity, current evidence, revalidation status, Scene use, and public-use mode.

## Boundary

This PR does not choose the lead, write narration, perform the entertainment inquisition, generate render specs, or change renderer behavior. ChatGPT remains responsible for editorial meaning. Deterministic code only verifies declared use.

## Contract

Every final episode memory reference records:

- memory type and ID
- historical confidence
- current revalidation status
- exact current Evidence IDs
- difference from the previous episode
- editorial use
- Scene IDs
- public usage mode

## Safety matrix

- `supported`: may be current context, comparison, monitoring, or internal
- `partially_supported`: may be carefully qualified current context, comparison, counterevidence, monitoring, or internal
- `historical_context_only`: comparison or internal only
- `weakened` / `invalidated`: counterevidence, comparison, or internal only
- `unresolved` / `not_used`: internal only

The validator requires exact equality with the dossier revalidation record and rejects memory-only current claims, missing Evidence IDs, untraceable references, and public use without a Scene.

## Files

- episode memory-reference JSON Schema
- cross-artifact validator
- deterministic unit and adversarial tests
- permanent CI workflow

## Done

- an episode with no memory passes
- supported memory can be used with current evidence
- historical-only memory cannot become a current fact
- weakened or invalidated memory cannot support the central current claim
- every public memory use is traceable to one or more Scenes
