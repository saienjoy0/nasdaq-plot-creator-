# PR #12｜Daily Operational Entry Point

## Purpose

Give daily 朝のNASDAQカフェ production one deterministic operational entry after the user supplies the daily source package.

This is a state and evidence controller, not an editorial AI.

## Inputs

- episode date
- `daily_source_package_YYYY-MM-DD.md`
- requested scope: package or preview
- pinned renderer commit and contract version

## Outputs

```text
working/YYYY-MM-DD/production_request.json
working/YYYY-MM-DD/production_state.json
```

The request fixes the original input SHA and renderer target. The state records forward-only transitions and SHA-bound evidence.

## Lifecycle

```text
intake_ready
→ research_inputs_bound
→ causal_dossier_valid
→ episode_package_final
→ memory_usage_valid
→ assets_resolved
→ production_package_valid
→ handoff_ready
→ preview_dispatched
→ preview_ready
→ user_review_pending
→ user_preview_approved
→ final_requested
→ final_completed
→ publication_approved
→ memory_promoted
```

## Commands

- `init`: bind source, date, renderer, and scope
- `status`: rehash request, source, and all transition evidence
- `advance`: move exactly one state with evidence
- `build-production`: invoke the deterministic Final Production builder
- `build-handoff`: create a preview-only immutable Renderer Handoff bundle
- `record-preview`: invoke Real-Day Acceptance and record pending/approved user review
- `request-final`: require approved preview, an approval record, and `--explicit-final`; record authorization only

## Safety boundaries

The CLI never:

- searches or researches current news;
- chooses the lead or market causality;
- writes or edits fox narration;
- performs 04 inquisition;
- generates images or chooses Primary/Fallback;
- dispatches final automatically;
- approves publication or memory promotion automatically.

Any changed source, request, or transition evidence invalidates state. Skipped or regressed states fail. Paths cannot escape the workspace. Initial requests cannot ask for final.

## Verification

Thirty-five positive and adversarial tests cover input binding, no-op replay, stale source/request/evidence, state order, explicit final gating, mocked production/handoff/preview integration, and path safety. Permanent CI also runs the PR #11, PR #10, PR #9, and PR #8 regression suites.

## Completion meaning

After this PR, the control-plane implementation for the approved PR #8–#12 roadmap is complete. Actual MVP proof still requires the next new real daily source package to be researched, scripted, rendered to preview, and visually reviewed by the user. The 2026-07-31 seed is not accepted as that proof.
