---
name: nasdaq-cafe-daily-production-hardening
version: 1.0.0
description: Run the daily production state machine with hardened final-production, handoff, and real-day acceptance dependencies.
---

# Hardened Daily Production Entry

## Production command

Use:

```bash
python scripts/run_daily_production_hardened.py <command> ...
```

Do not use `scripts/run_daily_production.py` as the production entrypoint.

The wrapper preserves the existing SHA-bound, forward-only daily state machine and replaces only its three execution dependencies:

```text
build-production
→ build_final_production_package_hardened.py

build-handoff
→ build_renderer_handoff_hardened.py

record-preview
→ run_real_day_acceptance_hardened.py
```

The state machine still performs no editorial research, lead selection, causality decision, narration writing, 04 inquisition, image generation, Primary/Fallback selection, preview rendering, final rendering, or visual approval.

## Resulting evidence chain

```text
post-inquisition episode package
→ PR #8 and PR #6 replay
→ leak-free final production artifacts
→ hardened preflight
→ immutable hardened handoff
→ renderer preview
→ hardened real-day acceptance
→ user visual review
```

Final remains gated by the existing `request-final --explicit-final` contract and user approval. This wrapper does not execute final rendering.
