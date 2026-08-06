# Remotion 2.4.0 Handoff Compatibility Fix

## Four-reviewer decision

1. **Editorial preservation** — narration, market causality, Scene order, titles and captions remain unchanged.
2. **Contract compiler** — producer-only JSON is projected through an explicit allow-list into the strict Remotion public schema.
3. **Financial lineage** — approved financial bindings are compiled by the existing Recipe compiler and applied by the existing cross-artifact integrator; no SHA or selected path is invented.
4. **Execution boundary** — the pinned Remotion commit runs the official `spec-cli validate` before production evidence is sealed and before immutable handoff.

## Correct order

```text
approved episode package
→ explicit Financial Visual bindings
→ Final Episode Contract
→ deterministic Financial Recipe Plan
→ financial_visual_cross_artifact
→ Visual Grammar 2.4 projection
→ pinned Remotion official validator
→ renderer_validation_report.json
→ production_package_valid
→ immutable preview handoff
```

TTS audio, `production_data.json`, post-TTS Visual Grammar timing report and preview MP4 remain renderer-stage outputs. Final rendering is not authorized by this change.
