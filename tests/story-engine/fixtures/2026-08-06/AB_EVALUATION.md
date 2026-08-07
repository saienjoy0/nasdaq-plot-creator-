# 2026-08-06 Story Engine A/B fixture evaluation

This fixture uses the confirmed AMD/NVIDIA causal structure from the 2026-08-06 episode as a regression case. It is a test fixture, not a new production episode package.

## Old-script failure being targeted

The legacy episode revealed the core answer in Scene 1: the market was already described as judging who could secure the next giant AI demand. That made later Expected / Actual / Gap and market-reaction Scenes feel like supporting appendices rather than a discovery path.

Expected legacy findings:
- `ANSWER_REVEALED_TOO_EARLY`
- `REPEATED_CONCLUSION`
- `NO_LATE_PAYOFF`
- `PROCEDURAL_NARRATION`

## New Story Plan

The new plan preserves the same market causality but changes the order of understanding:

1. Scene 1 gives direction + contradiction + question, but withholds the full mechanism.
2. Scene 2 establishes that the numbers and stock direction conflict.
3. Scene 3 fixes timing and confirmed facts before interpretation.
4. Scene 4 separates ordinary consensus from the higher AI-competition expectation gap.
5. Scene 5 introduces SpaceX/NVIDIA as the concrete comparison evidence.
6. Scene 6 tests the hypothesis against actual market divergence and becomes the midpoint turn.
7. Scene 7 limits the claim: AMD is the lead contradiction, not the sole cause of Nasdaq weakness.
8. Scene 8 keeps missing macro/intraday data visible and delivers the closing reframe.
9. Scene 9 is fixed closing only.

## Independent Critic trace

Round 1 score: **24/30 — conditional**.

Single finding: Scene 5 opened with procedural wording equivalent to “next, check SpaceX.” The critic requested only a connector rewrite. No evidence, confidence, scope, timing, counterevidence, or Scene role was changed.

Applied patch:

- Before: `次にSpaceXを確認します。`
- After: `その別の採点欄を具体化する材料が、同じ夜にNVIDIA側へ出ました。`

Round 2 score: **27/30 — pass**.

- opening: 4/5
- progression: 5/5
- discovery: 5/5
- clarity: 4/5
- fox_voice: 4/5
- late_payoff: 5/5

The final fixture retains all material counterevidence used by the test dossier, keeps unresolved rates/VIX/intraday limitations explicit, and does not promote AMD to a Nasdaq-primary cause.
