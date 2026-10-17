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
- Canon03 now uses the adopted model, 180–420-second standard acceptance, a 200–400-second writing target and sub-180-second shortened mode. The illustrative Scene budget table sums to 200–340 seconds. Those flexible ranges can be redistributed toward the global writing target; they are not mandatory per-Scene duration limits.
- Exact-pinned E2E derives voice/model from the two real production profiles and duration bounds from the real Renderer policy. It compares all explicit model/voice and measured-duration directives in the decoded canon03, checks the Scene-table total, and adds the result to the existing receipt. Canon changes both trigger that workflow and require its success through the existing merge-gate policy.
- Renderer lint repairs use existing structural types and preserve validation/render behavior. CSS-animation warnings were false positives on Scene timing fixture properties; those assignments now stay outside object literals, without disabling the lint rule or changing fixture values.
- Visual Story CI runs ESLint with `--max-warnings=0`.
- README and the current-state roadmap describe the actual Current path and separate mechanical qualification, real media, user review and audience evidence.

## Fresh local evidence

| Verification | Result |
|---|---|
| Existing official mounted-skill preflight | PASS for the installed 2.5.0 skill only; not represented as approval of newer repository canon |
| Repository `scripts/canon_manifest.py verify` | PASS after intentional canon03 update |
| Major Plot affected suite: Current Spine, canon manifest, editorial semantic boundary, Renderer handoff | 109 test cases and 28 subtests PASS; JUnit reports 137 results, zero failures/errors/skips |
| Existing exact-pinned Current Cross-Repo E2E against clean Renderer worktree | PASS, including authored independent graph paths, nullable outcome, Preview V4 acceptance and authoring/runtime policy |
| Focused policy/gate regressions | 30 cases and 28 subtests PASS, including contradictory voice, Japanese-adjacent model token, stale checklist range, shortened/upper bounds, incorrect table total and failed required E2E |
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

Fresh independent review found no critical issue, two important verification gaps and one minor arithmetic error. The important gaps were a missing required-gate classification for canon-only changes and permissive prose checks that accepted contradictory voice/duration directives or missed a model followed by Japanese text. The minor error described a 200–340-second table as totaling 200–400 seconds.

The follow-up regression run reproduced the two gaps before repair (16 failed results including subtests). The existing gate now requires the same E2E for canon changes; ASCII model-token boundaries and explicit voice/range/bound checks reject the contradictions. The table prose now states its actual sum. The focused suite, full affected suite and clean exact-bound E2E all passed after that fix pass. The reviewer also confirmed identical emitted JavaScript for the typed Final adapter and migration changes.

No repair branch has been pushed and no repair PR, remote checks or merge exists at the time of this receipt. Exact-head GitHub checks remain required before adoption. This file describes verified local branch changes and does not claim main has been updated.
