---
name: nasdaq-cafe-real-day-acceptance
version: 1.0.0
description: Verify a new real daily source package reaches a technically valid preview while final remains unexecuted.
---

# Real-Day End-to-End Acceptance

## Purpose

Prove the full daily production path on a new real episode after PR #8–#10 contracts are satisfied.

## Required evidence

- non-empty `daily_source_package_YYYY-MM-DD.md` for a date other than the 2026-07-31 seed;
- immutable preview handoff manifest and all bundle files;
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
