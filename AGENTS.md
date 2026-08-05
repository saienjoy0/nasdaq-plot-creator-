# AGENTS.md

## Repository role

This repository is the editorial research, long-term memory, and script-contract workspace for 朝のNASDAQカフェ.

It does not render video and it does not delegate editorial judgment to GitHub Actions, Codex, Remotion, external research frameworks, or the memory layer.

## Source-of-truth order

When instructions conflict, apply this order:

1. Current ChatGPT project instructions
2. `source-of-truth/02_editorial_bible.md`
3. `source-of-truth/01_fox_character_bible.md`
4. Materialized `03_episode_production_spec.md`
5. Materialized `04_entertainment_inquisitor.md`
6. Current primary evidence and market data
7. Daily input
8. Editorial memory
9. Examples

External projects are references only. They may improve research and memory mechanics, but they may not override market causality, uncertainty, the fox character, the nine-scene contract, or the no-investment-advice rule.

## Required production flow

```text
daily_source_package
→ memory query plan
→ selective editorial-memory retrieval
→ deterministic retrieval replay
→ research input manifest
→ causal research dossier with memory revalidation
→ editorial decision under 02
→ fox narration under 01
→ nine-scene episode package under 03
→ entertainment inquisition under 04
→ image path resolution
→ guarded final production generation
→ hardened renderer handoff
→ preview
→ hardened real-day acceptance
→ user visual review
→ final only after explicit request
→ approved publication record
→ durable-memory promotion
```

Never skip the causal research dossier when the daily input contains more than a simple confirmed single-cause event.

The research input manifest is an immutable intake record for the current production attempt. It freezes the daily package, memory query plan, memory context, retrieval report, their episode date, and their SHA-256 values. The builder and dossier validator must replay deterministic retrieval and verify that Query Plan, Context, and Report are one result. It does not choose the lead or certify any remembered claim as current truth.

## Editorial-memory behavior

Before causal research:

- Read `editorial-memory/active_context.md`.
- Read yesterday's daily record and the current ISO-week record when present.
- Select at most five relevant topic threads using today's lead candidates, entities, policies, technologies, and indicators.
- Select related claim-ledger entries.
- Build `working/memory_context_YYYY-MM-DD.md` with the authoritative retrieval script.
- Replay retrieval and require byte-identical Context and Report before creating the research input manifest.
- Build `research/YYYY-MM-DD/research_input_manifest.json` with `scripts/build_research_input_manifest.py`.
- Store and accept only repository-relative paths that remain inside the workspace root.
- Treat memory as a list of past observations and research leads, not as current evidence.
- Classify every selected non-core memory as used, not used, unresolved, weakened, invalidated, or historical context in the causal research dossier.
- Require current tier-1 or tier-2 fact or reported-interpretation evidence before a remembered claim can be marked supported, partially supported, weakened, or invalidated.
- Never register a memory ID, memory path, memory context, or retrieval report as an `E-###` evidence item.

After final approval:

- Build a structured `publication_record_YYYY-MM-DD.json` from the final episode package, render spec, and validator report.
- Promote memory only when approval status is `approved_preview` or `published`.
- Use `scripts/promote_episode_memory.py` to update the daily record, topic threads, and claim ledger.
- Never promote drafts, rejected causal explanations, unused image paths, or pre-inquisition narration.

The fox may refer to a previous episode only when a corresponding daily/thread/claim record exists and the current episode records how that memory was revalidated or restricted to historical context. Never invent remembered trades, holdings, losses, university incidents, or personal experiences.

## Research behavior

- Treat the daily package as a starting set of evidence, not as a finished explanation.
- Generate multiple research perspectives before drafting.
- Ask follow-up questions from newly discovered evidence.
- Search historical context, company relationships, supply chain, macro transmission, timeline, and counter-hypotheses.
- Attach a source, evidence class, timestamp, and confidence to every material causal edge.
- Separate fact, reported interpretation, grounded inference, and unknown.
- Preserve important contrary evidence.
- Do not create an Expected value after the fact.
- Do not elevate a single-company event into a NASDAQ-wide cause without index, sector, timing, and alternative-explanation checks.
- Revalidate any remembered claim against current evidence before using it as a factual premise.
- Do not use editorial memory as the sole basis for Expected, Actual, a causal edge, or a NASDAQ-wide conclusion.
- Actual with a non-empty statement requires current Evidence IDs.
- Every Evidence ID referenced from questions, alternatives, timeline, causal edges, Expected / Actual, contrary evidence, or memory revalidation must exist in the dossier.
- Record `difference_from_previous` when a past claim is used for comparison or current revalidation.
- `reason_unknown`, `unresolved`, and `not_used` are valid outcomes.

## Mandatory execution gates

Production-facing execution must use the guarded entrypoints:

```text
validate_episode_package_memory.py
→ validate_episode_package_memory_hardening.py
→ build_final_production_package_hardened.py
→ build_renderer_handoff_hardened.py
→ run_real_day_acceptance_hardened.py
```

Do not use the base Final Production, Renderer Handoff, or Real-Day Acceptance scripts as production entrypoints.

The guarded chain must prove:

- Scene 1–9 exactly once and in order;
- one integrated 04 result;
- canonical Memory Annex and Final Production Source Annex ordering;
- PR #8 and PR #6 replay PASS;
- no MEMREF or memory internal metadata in public artifacts;
- persisted hardening PASS in `official_execution_preflight.json`;
- the immutable handoff bundle retains the hardened preflight;
- Real-Day Acceptance reads that bundled evidence before counting the preview path.

A failed post-build or post-copy hardening check must remove newly generated outputs and must not leave an authorized preflight or newly created bundle.

## External project adoption

The repository may adopt useful patterns from other projects aggressively, but only as isolated mechanics:

- STORM / Co-STORM: perspective-guided questions, simulated follow-up dialogue, dynamic concept map
- Open Deep Research: supervisor/researcher separation, parallel research, compression before synthesis, evaluation
- OpenClaw-style memory: daily logs, durable promotion, selective retrieval, topic-specific memory
- GraphRAG / Graphiti: entity-relation and temporal evidence retrieval when justified by scale
- Financial multi-agent projects: specialist role separation only

Do not import trading recommendations, target prices, autonomous portfolio decisions, unsupported sentiment-to-price causality, or a memory mechanism that silently rewrites past records.

## Output contract

The causal research skill produces evidence, explicit memory revalidation results, and candidate explanations. It does not make the final editorial decision and does not write the final narration.

The memory skill retrieves past context and promotes approved conclusions. It does not certify current truth and does not change 01–04.

The research input manifest and dossier validator provide structural, lineage, path, and provenance safety. A passing validator does not prove that the market interpretation is correct.

The final decision remains governed by 02, then converted by 01 and 03, then reviewed by 04.
