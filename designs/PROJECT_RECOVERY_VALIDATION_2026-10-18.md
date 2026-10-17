# NASDAQ Cafe project recovery validation — 2026-10-18

## Scope and authority

Repair plan: `docs/reliability/plans/2026-10-18-project-recovery.md`.

Observed base Plot `9c0b51a6ed15f51094b2c89a47a101ff2442fe83`; canonical bound Renderer `536fbe8a139b2fa9f89cd9c76e9db71fa889c02e`; Collector `42908709f8044ba8d7a836d67fbe9b715f4b7790`.

Changes belong to `fix/project-recovery-20261018` in Plot and Renderer until separately adopted. No historical episode, sealed freeze, publication approval, production request, dependency, production model, TTS block or actual render settings changed. The Plot Renderer binding stays at its already-adopted commit; the Renderer patch needs its own normal merge/requalification before a later binding update.

## Reproduced boundaries

1. Canon03 required `gemini-3.1-flash-tts-preview` and 480–540 seconds. The pinned runtime profiles require `gemini-3.8-flash-tts` / Charon, and `duration-policy.ts` requires standard 180–420 seconds. A new assertion in the existing exact-pinned E2E failed on the original canon with `authoring/runtime TTS policy mismatch` before synthetic production proceeded.
2. Renderer `npm run lint` reported 30 errors and three warnings on the base tree. Its Visual Story CI had no lint step.
3. Current-state roadmap still instructed the next worker to implement PR #8 from an August 5 baseline, despite Current facade, Preview V4 / Final V2 and real August 17 media already existing.
4. Recent Renderer run `39048732981` only resolved the Motion Preview queue. Wake, render and outcome jobs were skipped. Its success is not new media evidence. Collector run `38986866992` succeeded on October 17; success does not establish source completeness.

## Changes

- Canon03 is intentionally versioned to 2.6.0 and deterministically repacked under the existing four-part transport. Only its manifest SHA/rawBytes and intentional canon snapshot change. Canon01, Canon02, Canon04 and historical freeze files remain unchanged.
- Canon03 now uses the adopted model, 180–420-second standard acceptance, a 200–400-second writing target and sub-180-second shortened mode. Its flexible Scene writing budgets sum to 200–400 seconds; they are not mandatory per-Scene duration limits.
- Exact-pinned E2E derives voice/model from the two real production profiles and duration bounds from the real Renderer policy. It compares the decoded canon03 and adds the result to the existing receipt. Canon changes trigger that same workflow.
- Renderer lint repairs use existing structural types and preserve validation/render behavior. CSS-animation warnings were false positives on Scene timing fixture properties; those assignments now stay outside object literals, without disabling the lint rule or changing fixture values.
- Visual Story CI runs ESLint with `--max-warnings=0`.
- README and the current-state roadmap describe the actual Current path and separate mechanical qualification, real media, user review and audience evidence.

## Fresh local evidence

| Verification | Result |
|---|---|
| Existing official mounted-skill preflight | PASS for the installed 2.5.0 skill only; not represented as approval of newer repository canon |
| Repository `scripts/canon_manifest.py verify` | PASS after intentional canon03 update |
| Major Plot affected suite: Current Spine, canon manifest, editorial semantic boundary, Renderer handoff | 99 test cases PASS; fresh verbose log contains all 99 PASSED results |
| Existing exact-pinned Current Cross-Repo E2E against clean Renderer worktree | PASS, including authored independent graph paths, nullable outcome, Preview V4 acceptance and authoring/runtime policy |
| Independent duration-only negative check | Changing the canonical range back to 480–540 seconds is rejected even with the correct model |
| Renderer `npm run lint` | PASS, including TypeScript |
| Renderer `npx eslint src scripts --max-warnings=0` | PASS: zero errors and zero warnings |
| Renderer required spec/public-screen/handoff/Visual Story plus workflow/TTS/key-pool/duration/text-safety checks | 38 unique existing test entrypoints PASS |
| Renderer `npm run build` | PASS |
| Legacy migration before/after on the same temporary renderable fixture | Output files byte-identical |
| Collector with its pinned requirements | 81 tests PASS |

The local `tsx` CLI cannot bind its IPC socket (`listen EPERM`), so the normal `npm run test:spec` wrapper cannot start. Its existing scripts and nested required suites were expanded, deduplicated and run with `node --import tsx`; Python entrypoints were retained unchanged. No source, assertion or gate was omitted to obtain the 38-entrypoint result. This environment limitation is not a test failure or an episode approval. CI uses its normal commands.

## Qualification limits and remaining work

These are technical repair and regression results. No live TTS request, new Preview/Final render, AI visual inspection, user appearance approval, publication or audience improvement is claimed.

Open semanticScope/schema-2.5 PRs, 5–12-scene migration and optional Skill integration remain separate unadopted proposals. They are not repaired by weakening nine-scene or protected-semantic checks. A new episode must be authored under the selected canon, pass real Current readiness, produce actual media and receive exact-output user review. Retention/CTR require real audience data.

The installed aggregate `produce-nasdaq-cafe-video` skill still embeds older runtime defaults. `AGENTS.md` explicitly makes the repository's local canon authoritative; use the Current repository route for production. Do not silently rewrite installed skills or historical freezes to disguise that version difference.

## Review and remote adoption

Fresh independent review and exact-head GitHub checks must be recorded before adoption. Until those checks and normal merge occur, this file describes verified branch changes and does not claim main has been updated.
