# AGENTS.md

## Scope

This directory validates editorial-memory usage in the final episode package.

## Non-negotiable boundaries

- Do not modify 01–04.
- Do not choose the lead, market causality, confidence, narration, title, thumbnail, or image path.
- Do not infer memory usage from prose with an LLM.
- Require one JSON annex and explicit invisible MEMREF markers.
- Re-run the PR #6 validation chain; never trust self-declared PASS fields alone.
- Keep annex and markers out of all viewer-facing artifacts.
- Episodes with no memory usage must pass with `references: []`.
- Fail closed on path traversal, stale SHA, date mismatch, unknown memory, status/evidence tampering, marker mismatch, forbidden title use, or unrecorded fox personal history.
