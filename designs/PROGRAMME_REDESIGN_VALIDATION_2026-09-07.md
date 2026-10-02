# Programme remediation implementation receipt

## Actual changes

- Current Visual Intelligence validates explicit causal nodes/arrows/config only. No card-order inference, event fan-out or outcome selection. Invalid input returns precise JSON paths and RETURN_TO_STORY. Explicit disconnected company/macro graphs are preserved. Legacy compatibility helper remains only for legacy replay; Current final production suppresses legacy materialization.
- Causal Research, Story Plan, Story Authoring, Visual Intelligence and Entertainment Critic strengthened in place. No new standalone Skill. Structural East Asia screening is independent from chronological cross-market transmission. Image generation remains a conceptual production capability with Primary/Fallback and source boundaries.
- Canon02 updated to 2.6.0 with manifest SHA/rawBytes and snapshot test. Historical freezes are not rewritten. Existing 03/04 remain unchanged, and variable scene production is not claimed.

## Initial validation before coordinated runtime adoption

- `python scripts/canon_manifest.py verify`: PASS.
- `python -m pytest -q tests/canon-manifest/test_canon_manifest.py`: 5 passed.
- `python tests/remotion-compat/test_visual_intelligence_causal_inventory.py`: PASS.
- `python tests/remotion-compat/test_visual_intelligence_object_references.py`: PASS.
- `python -m unittest discover -s tests/current-spine -p 'test_*.py'`: 19 passed.
- `python -m unittest tests/remotion-compat/test_remotion_compat.py`: 8 passed.
- Related Visual Intelligence compatibility scripts: PASS; scripts requiring local module imports ran with `PYTHONPATH=scripts`.
- Independent causal review: no blocking findings. Independent editorial review found the old Section8 NASDAQ-path rule conflicted with structural context; the rule was scoped to market-causation claims and canon integrity rechecked.
- Generic skill-creator quick_validate is incompatible with the repository's pre-existing top-level `version` metadata and rejects all five Skills for that field. This patch retains the repository convention and does not claim generic validation success.

## Not completed / rollout boundaries

This change does not reauthor the historical 2026-08-17 producer package or render a replacement MP4. Its card-only causal Beat now returns to editorial authoring if replayed through Current. Reauthor explicit supported graph objects in a new attempt; do not mutate an old approved bundle or label an inferred graph approved. New Story/Visual freezes must bind the updated canon; old approvals do not authorize new semantics or pixels.

The coordinated 5–12-scene migration is designed in PROGRAMME_REDESIGN_2026-09-07.md but not enabled. No TTS or Current Preview/Final request is published by this code PR. No audience retention or continuous audio/motion approval is claimed. Broader quality improvement still requires a newly authored episode, actual preview review and real audience feedback.

Renderer companion: https://github.com/saienjoy0/saienjoy0-nasdaq-cafe-remotion/pull/224 . It fixes subtitle token breaks, with 26 test entrypoints plus typecheck/build passing. Whole Renderer lint has the same pre-existing 30 errors/3warnings at baseline and patched tree.

## GitHub verification and ownership split (2026-09-19)

Renderer PR224 passes its three GitHub checks. Plot PR198's functional checks, including the synthetic Current Visual Intelligence cross-repository acceptance, passed on its first CI run. Two integration controls rejected the PR: unregistered `source-of-truth/**` / `designs/**` ownership in the trusted-base merge policy, and the prohibition on changing the AI-B-owned Visual Intelligence Skill in an architecture PR.

The Visual Intelligence Skill change is now isolated in editorial-only PR199: https://github.com/saienjoy0/nasdaq-plot-creator-/pull/199 . PR198 retains the other four Skill changes. The ownership check itself is unchanged. The code/Skill design describes the combined change, not files all owned by a single PR.

A separate prerequisite policy change will register canon changes against both the existing canon verifier and daily-production validation, with matching workflow triggers. It must pass the existing trusted-base gate and be reviewed/adopted normally before refreshing PR198's base. PR198 cannot authorize its own policy change. No gate status is manually overridden, no force merge is used, and unclassified changes remain failures.

## Coordinated runtime requalification (2026-10-02)

- Prerequisite Plot PR200 was independently reviewed and merged through the normal trusted-base gates at `022e9e27d7d8c9326275ff245a37006456978924`. Editorial-only PR199 was independently reviewed and merged after its exact-head checks succeeded at `fde3eb23310cb00fb94c5cbb79d4a003dc7a6475`. PR198 now includes both adopted bases; its own final remote checks remain required before merge.
- Renderer subtitle PR224 and authored-causal-authority PR227 were independently reviewed and merged after their exact-head required gates succeeded. The coordinated canonical binding pins the resulting merged Renderer `536fbe8a139b2fa9f89cd9c76e9db71fa889c02e`, rather than an unmerged branch. Contract `2.4.0`, bridge `visual-intelligence-bridge/1.2.0`, frozen-interface SHA and registry SHA `24dac243a8d4492a14fcac537f728d4e204de95510936111e582ce6cc147c9d0` remain unchanged.
- Current graph validation also applies to every `causal-build` shot, including one carried by a non-causal template. Its card-only bypass regression failed before the guard was added and passes after the repair. Legacy graph materialization remains outside Current production.
- The exact-pinned cross-repository test passed both the existing Current Renderer fixture and one variation of that same fixture with four explicitly authored nodes and two independent arrows. Inventory order deliberately differs from `nodeOrder`, and `outcomeNodeId` is explicitly null. Identity Candidate selection, compiled/source equality and Visual Intelligence package lineage validation preserve graph objects, authored order and the absence of an outcome. The old bound Renderer `83db1e9e204269c941f743e71c6d3ed34d8f334e` failed this graph acceptance; the new pinned checkout passed. This adds a mechanical regression case, not another daily producer or an approved production fixture.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=scripts python3 tests/current-spine/run_exact_cross_repo_current_e2e.py --renderer-root <exact-pinned-checkout>`: PASS. Exact checkout and registry verification, Director/Critic pauses, illegal or stale selections, compiled identity, sealed immutability, Visual Intelligence package lineage validation and Preview V4 request-schema acceptance all passed. Request validation does not publish a preview.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=scripts python3 -m pytest -q tests/current-spine tests/canon-manifest tests/editorial-semantic-boundary tests/remotion-compat/test_visual_director_handoff.py`: 99 passed, 25 subtests passed. Current VI state, preflight binding and final-authorization contract scripts also passed.
- Independent coordination review found no unresolved Critical, Important or Minor issue. It separately reran the exact-pinned cross-repository test and 19 focused tests, checked binding/registry consistency and reviewed the mechanical-only receipt wording.
- The merged Renderer tree equals the locally qualified combined tree. Its 27 underlying spec/public-screen/handoff test entrypoints, typecheck and build passed. The local `tsx` CLI cannot bind its IPC socket, so those entrypoints ran with `node --import tsx`; no source or assertions were bypassed. Whole-repository lint still reports the baseline 30 errors and 3 warnings, with no added diagnostic.

These are code and mechanical-contract results. No live TTS, rendered episode, continuous audio/motion review, publication, audience response or whole-production quality PASS is claimed. Historical bundles remain immutable, and the scene-count migration remains design only.
