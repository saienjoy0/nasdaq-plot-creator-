# AGENTS.md

## Scope

This directory validates editorial-memory usage in the final episode package.

## Authoritative validation order

Run both validators in this order:

1. `validators/validate_episode_package_memory.py`
2. `validators/validate_episode_package_memory_hardening.py`

The hardening gate invokes the base PR #8 validator and fails if the base validator fails or cannot run. Do not call production with a success stub.

## Non-negotiable boundaries

- Do not modify 01–04.
- Do not choose the lead, market causality, confidence, narration, title, thumbnail, or image path.
- Do not infer memory usage from prose with an LLM.
- Require one JSON memory annex and explicit invisible MEMREF markers.
- Require Scene 1 through Scene 9 exactly once and in order.
- Require exactly one integrated `04 興味深さ・わかりやすさ審問結果` section before the memory annex.
- After the memory annex, allow either whitespace only or exactly one Final Production Source annex. When present, it must be the final section.
- Re-run the PR #6 validation chain; never trust self-declared PASS fields alone.
- Keep annex, MEMREF markers, and internal memory fields out of all viewer-facing artifacts.
- Scan supplied spoken script, captions, telops, asset manifest, and render spec artifacts for metadata leakage.
- Episodes with no memory usage may pass with `references: []` only when all final-package requirements are met.
- Fail closed on path traversal, stale SHA, date mismatch, unknown memory, status/evidence tampering, marker mismatch, missing scenes, missing inquisition, forbidden title use, metadata leakage, or unrecorded fox personal history.
