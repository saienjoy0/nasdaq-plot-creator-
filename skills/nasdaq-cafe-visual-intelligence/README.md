# NASDAQ Cafe Visual Intelligence

Editorial-only Visual Intelligence for 朝のNASDAQカフェ.

This directory implements the AI-B side of Visual Intelligence under frozen bridge `visual-intelligence-bridge/1.2.0`.

It deliberately contains no renderer implementation, schema, CI workflow, Hard Validator, Registry, or Candidate Builder logic.

## Role

```text
Story / 04 reviewed editorial snapshot
→ Visual Intent
→ Provisional Direction
→ Architecture-owned asset resolution + legal Candidate Catalog
→ LLM Visual Director selection
→ Architecture-owned compile
→ Independent Visual Plan Critic
→ targeted candidate-only patch / re-review
→ PASS or explicit upstream return
```

## Phase 1

Required now:

- Visual Intent
- Provisional Direction
- candidate selection with strongest alternative
- independent Visual Plan Critic
- candidate-only patch
- re-review, maximum two rounds

## Phase 2

May be connected after fresh real-day Preview succeeds:

- Recent Approved Visual Pattern retrieval
- Production Lessons retrieval
- cross-episode staleness judgment

Only exact-SHA human-approved previews may become Visual memory.

## Frozen boundary

Do not change the shared bridge from this directory. Frozen Interface SHA-256:

`a9c54f2115f1d5a73251be64edcd5ff3f84c0940613ff7a6d7718f755581977f`
