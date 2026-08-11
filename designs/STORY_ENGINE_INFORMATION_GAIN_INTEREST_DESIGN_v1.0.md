# Story Engine Information Gain / Interest Design v1.0

## Status

Experimental Story Engine layer. This document does **not** modify the authority of `01`–`04` source-of-truth files.

The purpose is to improve interestingness while preserving the frozen causal contract.

## Problem

The current Story Engine can reject front-loaded episodes with no late payoff, but a script can still be causally correct, structurally valid, and pass the hard gates while feeling like a lecture in the middle.

Typical failure pattern:

```text
Scene 1: strong contradiction
Scene 2: more facts
Scene 3: more facts
Scene 4: provisional answer
Scene 5: another supporting factor
Scene 6: finally a meaningful test
```

The problem is not lack of information. It is low **Information Gain**: too much runtime is spent adding support without materially changing the viewer's explanatory model.

## Four-expert synthesis

### 1. Cognitive / curiosity perspective

Use Information Gap and Bayesian Surprise as editorial concepts.

- Give the viewer a truthful provisional model early.
- Make the unresolved mismatch concrete.
- Do not hide evidence required to make the provisional model truthful.
- Prefer evidence that changes the viewer's prediction or explanation over evidence that merely adds support.

Interestingness is not measured by shock. It is the value of the model update.

### 2. Documentary / science communication perspective

Prefer an investigation arc:

```text
Contradiction
→ Provisional Model
→ Test
→ Anomaly / Boundary
→ Model Update
→ Scope / Counterevidence
→ Synthesis
```

Use ABT (And / But / Therefore) as a compression diagnostic. Do not force literal ABT language into every Scene.

### 3. Market-causality perspective

Interest may never change:

- facts or numbers
- Expected / Actual / Gap
- chronology
- causal scope
- confidence
- material counterevidence
- unresolved uncertainty

High Information Gain does not mean high causal importance. A company-specific anomaly can be interesting because it limits a broad explanation without becoming the primary cause of NASDAQ.

### 4. Story Engine / QA perspective

Do not make Python judge semantic interestingness.

Python remains responsible for structure and causal safety. The Entertainment Critic judges whether a model update is meaningful enough to matter to a viewer.

## Internal Understanding Gain types

Story Plan should classify the main gain of each Scene internally during planning. This is not yet a required JSON schema field.

```text
support
narrow
branch
disproof
mechanism_reveal
verification
uncertainty_reduction
synthesis
```

`support` is valid but generally low-gain. It should be concise when it does not materially alter the explanatory model.

## Information Gap boundary

Allowed:

```text
金利がまず鍵です。
ただ、半導体を全部この説明に入れると、一銘柄だけ発表時刻と値動きが合いません。
```

This gives:
- early value,
- a provisional model,
- a concrete unresolved mismatch.

Not allowed:

```text
答えは知っているけれど、後半まで隠します。
```

Information Gap organizes disclosure. It does not manufacture ignorance.

## Authoring rule: ABT / fact-stacking compression

When two or more adjacent Scenes mainly stack support:

```text
fact
AND fact
AND fact
```

ask whether the spoken surface can expose the meaning more directly:

```text
known fact
BUT mismatch / boundary
THEREFORE updated interpretation
```

The fixed nine formal Scenes remain. Compression changes spoken surface and compatible content placement, not the formal skeleton.

## Critic diagnostics

### FACT_STACKING

Adjacent Scenes mainly add facts/support while the explanatory model remains unchanged.

### LOW_INFORMATION_GAIN

A Scene receives disproportionate runtime/emphasis but changes little beyond adding support.

### PAYOFF_DROUGHT

A multi-Scene stretch goes too long without a meaningful understanding reward: model update, narrowing, direct test, mechanism reveal, or consequential counterevidence.

### WEAK_SURPRISE

The nominated Understanding Upgrade technically exists but has little explanatory consequence. Removing it would barely change the final model.

"Surprise" means model update, not theatrical twist.

These findings may be minor when localized and compressible, or major when they materially damage progression. They do not replace the stronger hard findings `NO_UNDERSTANDING_UPGRADE` and `NO_LATE_PAYOFF`.

## 2026-08-10 benchmark

The benchmark story is:

```text
Contradiction:
July payrolls missed badly, yet NASDAQ and SOXX rose.

Provisional model:
Weak jobs reduced rate-hike expectations and eased the rate headwind for tech.

Supporting context:
Oil / yields also moved in a supportive direction.

High-gain verification:
QQQ / SOXX / NVDA moved higher at 8:30 ET, but MCHP did not.

Model update:
The semiconductor-up session contained at least two different engines: macro rate reaction and company-specific MCHP earnings.

Boundary:
AMD and Alphabet weakness prevents a blanket "all tech rose for the same reason" explanation.

Synthesis:
Different causal engines aligned in the same index direction.
```

Expected gain profile:

```text
Scene 1: narrow / provisional model
Scene 2: narrow
Scene 3: disproof of simple risk-off expectation
Scene 4: mechanism_reveal
Scene 5: support (keep concise)
Scene 6: branch + verification (highest gain)
Scene 7: branch + narrow
Scene 8: synthesis
```

The regression objective is not to force every day into this exact curve. It is to prove that the Engine can distinguish a support-heavy middle from a genuine evidence-backed model update.

## Rollout

1. Implement in Story Plan / Authoring / Entertainment Critic skills.
2. Extend creative-review finding vocabulary and external Critic adapter.
3. Add 2026-08-10 interest benchmark regression.
4. Validate existing Story Engine tests still pass.
5. Compare the old and revised 2026-08-10 scripts for causal equivalence and interest diagnostics.
6. Only after the behavior is proven should the principle be promoted into `02` / packed `03` / packed `04` source-of-truth documents.
