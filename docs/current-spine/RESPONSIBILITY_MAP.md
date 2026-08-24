# NASDAQ Cafe Current Spine Responsibility Map

Status: architecture authority for reducing duplicate ownership without rewriting editorial meaning.

## Goal

Current production must be one directional path. A later implementation change must not retroactively invalidate an already sealed editorial episode. A component may own exactly one of these four responsibilities:

1. **EDITORIAL** — decide and seal meaning.
2. **AUTHORING** — express the sealed meaning as explicit Scene/Beat presentation intent.
3. **COMPILE** — prove current compatibility and deterministically translate authoring to current Renderer inputs.
4. **RENDER** — execute TTS/Remotion and publish Preview/Final artifacts.

If one file appears to own two responsibilities, the ownership must be split or narrowed. New files are not added merely to mirror an existing authority.

## Canonical one-way path

```text
01-04 canon + daily research
        |
        v
Daily Authoring v2 + Editorial Semantic Acceptance
        |
        v
Semantic Freeze 1.2  [sealed EDITORIAL identity]
        |
        v
Current Production Facade
        |
        +--> sealed Freeze verifier
        |       - verifies frozen source bytes/semantic digests
        |       - verifies frozen Acceptance points to the same frozen meaning
        |       - does NOT compare historical contract SHAs to today's files
        |
        +--> Current Authoring Closure
        |       - validates frozen authoring against today's Authoring/Renderer rules
        |       - compatibility failure is a Current compatibility failure, not a stale Freeze
        |
        v
Visual Intelligence / deterministic materializers
        |
        v
RenderSpec + immutable handoff
        |
        v
Renderer Current Preview request V4
        |
        v
Preview MP4 -> human review -> explicit Final only
```

## Classification

### KEEP — current authority

These remain authoritative and must not be duplicated.

| Responsibility | Authority | Why it stays |
| --- | --- | --- |
| EDITORIAL canon | `source-of-truth/canon_manifest.json` + 01-04 sources | Single editorial rule authority |
| EDITORIAL daily meaning | `daily-authoring/<date>.json` | Canonical structured episode meaning/presentation authoring |
| EDITORIAL acceptance | `verification/<date>/editorial_semantic_acceptance.json` | Records that the episode passed the editorial boundary at issuance time |
| EDITORIAL seal | `semantic-freezes/<date>.json` | Immutable episode identity after ChatGPT editorial approval |
| ENTRY | `scripts/current_production_facade_v12.py` | Sole public Plot production facade |
| CONTROL PLANE | `scripts/run_daily_production_v12.py` | Internal production state/policy owner |
| SEALED IDENTITY | `scripts/verify_sealed_semantic_freeze_v12.py` | Production-only proof that frozen episode inputs themselves have not changed |
| CURRENT COMPATIBILITY | `scripts/validate_chatgpt_daily_authoring_closure.py` | Current Authoring/Renderer compatibility gate |
| CURRENT COMPILE | `scripts/run_daily_renderer_closure_v12.py` | Current materialization + Visual Intelligence closure |
| RENDERER BINDING | `contracts/renderer_binding.json` | Single current Renderer identity |
| PREVIEW REQUEST | `scripts/build_current_preview_request_v4.py` | Deterministic immutable Preview request |
| FINAL REQUEST | `scripts/build_current_final_request_v2.py` | Explicit post-review Final request only |
| PRODUCTION WORKFLOW | `.github/workflows/chatgpt-daily-preview-production.yml` | Current mechanical GitHub Actions entry |

### INTEGRATE / NARROW — keep the file, remove overlapping responsibility

| Component | Previous overlap | Required ownership after cleanup |
| --- | --- | --- |
| `scripts/run_semantic_frozen_renderer_closure_v12.py` | Freeze identity + Current contract freshness were coupled indirectly through dynamic Freeze rebuild | Thin production wrapper: sealed identity first, then invoke Current compatibility/compile |
| `scripts/chatgpt_semantic_freeze.py` | Creation-time freeze builder and production-time current-contract freshness checker | Authoring/PR preparation only. It may create/rebuild a candidate Freeze before sealing; production runtime must not use its dynamic rebuild as the definition of historical validity |
| `contracts/chatgpt_daily_authoring_v2.schema.json` | Editorial structure plus Renderer-facing presentation requirements | Current Authoring compatibility contract. Changes here may require current compatibility work but must not invalidate a sealed historical episode by themselves |
| Visual Intelligence v1.2 modules | Candidate generation, selection validation, compile state | COMPILE only. They never reinterpret market causality, narration, Scene order, or Primary/Fallback semantics |

### ISOLATE — legacy compatibility/read-only

Current production must never route through these policy owners:

- `scripts/run_daily_production.py`
- `scripts/run_daily_production_hardened.py`
- `scripts/run_daily_renderer_closure.py`
- legacy Preview request builders/shapes that do not bind exact Renderer commit + contract + Registry identity
- historical combined `visual_intelligence_decision.json` paths outside Current v1.2
- older all-in-one Final package builders when they are used only to reproduce historical bundles

Rules for isolated code:

- no Current workflow import;
- no Current policy ownership;
- no new features;
- security/mechanical helpers may be extracted into Current-neutral helpers, after which the legacy caller stays isolated.

### DELETE — generated or one-shot artifacts, after reference scan

Delete rather than maintain when no Current or historical regression path references them:

- tracked `__pycache__/` and `*.pyc` files;
- one-shot migration/bootstrap scripts whose migration is already merged and verified;
- temporary duplicate fixtures that reproduce a full Current production/Renderer stack;
- obsolete request helpers superseded by Preview V4 / Final V2 and not needed for historical reproduction.

Deletion is deliberately a separate PR after reference scanning. Architectural cleanup must not mix broad deletion with the semantic-boundary repair.

## Invalidations: the rule that prevents another stale cascade

| What changed | What must be re-run | What must NOT be invalidated automatically |
| --- | --- | --- |
| Research / causal meaning / narration / Scene order | Editorial acceptance -> Semantic Freeze -> all downstream | nothing downstream may silently preserve an old semantic seal |
| Beat presentation authoring before sealing | Editorial acceptance -> Semantic Freeze -> compile/render | research evidence that did not change |
| Current Authoring schema/validator | Current compatibility -> compile/render | existing sealed Semantic Freeze |
| Visual Intelligence/compiler | compile/render | Semantic Freeze and accepted authoring |
| Renderer/Remotion implementation | Renderer qualification -> render | Semantic Freeze, authoring, market causality |
| TTS/render settings | render only | all editorial/authoring/compile identities |

## Contract version discipline

A schema may not change behavior while keeping the same version indefinitely.

- formatting-only changes: canonical semantic digest may stay equivalent;
- backward-compatible validation additions: bump minor version when the contract meaning changes;
- breaking required-field/meaning change: bump major version or publish an explicit compatibility adapter;
- raw SHA remains useful as exact-byte evidence, but it is not a substitute for contract version or responsibility boundaries.

## Current 2026-08-17 incident

The episode was sealed on 2026-08-17. Later Current Spine work changed `contracts/chatgpt_daily_authoring_v2.schema.json` while the acceptance still recorded the issuance-time schema SHA. Production then called a dynamic Freeze verifier that rebuilt acceptance expectations against today's contract files, so the historical acceptance was classified as stale before Current compatibility could even run.

The repair is intentionally narrow:

1. production verifies the already-sealed 2026-08-17 editorial identity without dereferencing historical contract SHAs against mutable current files;
2. `run_daily_renderer_closure_v12.py` still runs `validate_chatgpt_daily_authoring_closure.py` against the current schema;
3. therefore an actually incompatible old Authoring still fails closed, but at the correct **Current compatibility** boundary;
4. no narration, market causality, Scene order, evidence, Visual meaning, or Primary/Fallback decision is changed by this architecture repair.

## Non-negotiable anti-growth rules

- One public production entry: `current_production_facade_v12.py`.
- One sealed editorial identity: Semantic Freeze.
- One Current Authoring compatibility gate.
- One canonical Renderer binding.
- One Preview request contract and one explicit Final request contract.
- Do not create a second full synthetic production pipeline to test the first.
- Do not fix stale lineage by rewriting a sealed request in place.
- Do not make GitHub Actions, Codex, Visual Intelligence, or Remotion reinterpret editorial meaning.
