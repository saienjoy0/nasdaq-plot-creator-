---
name: nasdaq-cafe-real-day-acceptance
version: 1.1.0
description: Verify a new real daily source package reaches a technically valid preview while final remains unexecuted.
---

# Real-Day End-to-End Acceptance

## Purpose

Prove the full daily production path on a new real episode after memory, research, episode, final-production, and renderer-handoff contracts are satisfied.

## Mandatory guarded entrypoint

Use `scripts/run_real_day_acceptance_hardened.py` for MVP evidence.

Before invoking the base acceptance runner, it verifies that the immutable handoff manifest contains exactly one preflight role and that the bundled preflight still carries:

```json
{
  "episode_memory_hardening": {
    "pre_build": "pass",
    "public_artifacts": "pass"
  }
}
```

The base acceptance runner must then return validation PASS. A technically valid preview without this complete production evidence is not accepted as MVP proof.

## Required evidence

- non-empty `daily_source_package_YYYY-MM-DD.md` for a date other than the 2026-07-31 seed;
- immutable hardened preview handoff manifest and all bundle files;
- renderer technical report from the pinned renderer commit;
- non-empty preview MP4 with verified SHA;
- optional user visual-review record.

## Acceptance states

- `preview_ready_user_review_pending`: technical path passed and the preview is available, but the user has not approved it;
- `passed`: technical path passed and the user approved the preview;
- `failed`: technical path passed but the user rejected the visual result, or validation stopped earlier.

## Absolute boundary

The acceptance runner never starts final rendering. It rejects any technical report indicating that final ran and records `final_render_executed=false` in every valid report.

It does not judge the market story, rewrite narration, inspect representative frames with AI, or auto-approve visual quality. User review remains the final visual gate.
