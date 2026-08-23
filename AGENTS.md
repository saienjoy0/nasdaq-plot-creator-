# AGENTS.md

## Repository role

This repository is the editorial research, long-term memory, and script-contract workspace for 朝のNASDAQカフェ.

It does not render video and it does not delegate editorial judgment to GitHub Actions, Codex, Remotion, external research frameworks, the Collector, or the memory layer.

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
→ causal research
→ optional bounded Research Acquisition Bridge
→ research evidence supplement lineage when acquisition is used
→ causal research dossier with memory revalidation
→ editorial decision under 02
→ fox narration under 01
→ nine-scene episode package under 03
→ entertainment inquisition under 04
→ image path resolution
→ hardened daily control plane
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

Targeted acquisition never rewrites the research input manifest. When Causal Research identifies a material evidence gap, ChatGPT may author at most two bounded acquisition waves for explicit read-only market data or exact-URL archive retrieval. The Collector executes those requests mechanically. It does not choose the lead, Expected / Actual / Gap, related entities, causal scope, or story meaning.

Any acquired file used as current dossier evidence must be copied into `research/YYYY-MM-DD/evidence/` and bound through the append-only `research_evidence_supplement_manifest.json`. The unified causal validator must verify the base manifest, request/result SHA lineage, copied evidence SHA, dossier input provenance, and acquired-evidence references. Missing or unavailable follow-up evidence remains unresolved rather than being invented.

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
- Use the Research Acquisition Bridge only for a material evidence gap, never merely to collect more links or visual素材.
- Use one acquisition wave by default; allow a second only when wave-1 evidence materially changes the necessary test; never use a third wave.
- Keep dynamic symbol choice and comparison-set choice in ChatGPT/Causal Research, not in the Collector.
- Treat minute/intraday series as timing evidence; timing alone does not prove causal attribution.
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

## Temporal Evidence Loop v1.2

Before using Memory or Cross-Market interpretation, construct the current overnight contradiction candidates from Current Evidence only. Then reconcile approved open Validation Obligations and run the cross-market materiality screen.

- `source_pack.json` remains the Collector machine source of truth; `collector_source_pack` is an optional SHA-bound manifest input.
- Candidate Pool / Discovery Coverage never become Evidence merely because they were collected.
- Carryover is replayed from approved `current_revision` publication history; production gaps do not close an open VO.
- Structured Validation Obligations are authoritative; `watch_next` is only their human-readable projection plus optional general monitoring points.
- Earlier market is chronology evidence, not automatic causality.
- No Temporal DB, new Daily Production state, new Scene system, or second Research Engine is introduced.

## Mandatory execution gates

Production-facing execution begins with:

```text
scripts/current_production_facade_v12.py
```

The facade is the sole Current production entry. It normalizes one immutable
semantic-freeze request and delegates to the Current v1.2 control plane and
stage executors. The lower-level Current scripts are internal; the hardened and
base scripts are Legacy/compatibility only.

```text
scripts/current_production_facade_v12.py
→ scripts/run_semantic_frozen_renderer_closure_v12.py
→ scripts/run_daily_renderer_closure_v12.py
→ scripts/run_daily_production_v12.py
```

Do not use `run_daily_production.py`, `run_daily_production_hardened.py`, the
base Final Production/Renderer Handoff/Real-Day Acceptance scripts, or an
internal Current executor as a public production entrypoint.

After a PASS closure, build the Current Preview V4 request and the deterministic
publication receipt. The publication target is append-only and keyed by episode
date, Plot run ID, and exact request SHA. Publish it through a request-only PR in
the Renderer repository; retrying the same bytes must reuse the same target and
must not create a second logical request.

Before advancing `causal_dossier_valid`, use the unified causal validator when acquired research evidence is present:

```text
validate_causal_research_with_supplement.py
```

The guarded chain must prove:

- Scene 1–9 exactly once and in order;
- one integrated 04 result;
- canonical Memory Annex and Final Production Source Annex ordering;
- PR #8 and PR #6 replay PASS;
- acquired research evidence is SHA-bound when used;
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

The Research Acquisition Bridge provides additional source material only. A successful Collector result is not itself a causal conclusion, and unavailable acquisition is not repaired by inference.

The memory skill retrieves past context and promotes approved conclusions. It does not certify current truth and does not change 01–04.

The research input manifest, optional supplement manifest, and dossier validators provide structural, lineage, path, and provenance safety. A passing validator does not prove that the market interpretation is correct.

The final decision remains governed by 02, then converted by 01 and 03, then reviewed by 04.
