# PR #11｜Real-Day End-to-End Acceptance

## Purpose

Verify that one new real daily source package reaches a validated preview MP4 through the completed memory, research, episode, final-production, and renderer-handoff contracts.

## Evidence chain

```text
daily source
→ preview handoff manifest and verified files
→ pinned renderer technical report
→ render-spec SHA match
→ preview MP4 SHA and size
→ user visual review
```

## Rules

- the 2026-07-31 seed cannot be reused as the MVP proof;
- handoff mode must be preview and `final_authorized=false`;
- all handoff files must still match SHA and size;
- renderer commit and render-spec SHA must match the handoff;
- technical checks must pass;
- preview must exist and be non-empty;
- any indication that final rendering ran fails acceptance;
- technical success remains pending until user visual review;
- no AI visual review replaces the user.

## Output

`verification/real-day-acceptance/YYYY-MM-DD/acceptance_report.{json,md}` records daily-source SHA, bundle manifest SHA, renderer commit, technical-report SHA, preview SHA, user-review status, and final-not-run status.

Thirty deterministic tests cover pending/approved/rejected outcomes, seed reuse, stale and tampered handoff data, renderer mismatches, preview failures, review identity, and report integrity.
