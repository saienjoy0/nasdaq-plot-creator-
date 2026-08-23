#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
doc=(ROOT/'docs/current-spine/CURRENT_ENTRYPOINTS.md').read_text(encoding='utf-8')
workflow=(ROOT/'.github/workflows/chatgpt-daily-preview-production.yml').read_text(encoding='utf-8')
facade=(ROOT/'scripts/current_production_facade_v12.py').read_text(encoding='utf-8')
agents=(ROOT/'AGENTS.md').read_text(encoding='utf-8')
readme=(ROOT/'README.md').read_text(encoding='utf-8')
runbook=(ROOT/'docs/DAILY_PRODUCTION_RUNBOOK.md').read_text(encoding='utf-8')

for heading in ('CURRENT PRODUCTION','CURRENT QUALIFICATION BOUNDARIES','LEGACY READ-ONLY / COMPATIBILITY','TEST / HISTORICAL ONLY'):
    if heading not in doc: raise AssertionError(f'missing entrypoint class: {heading}')
for current in ('scripts/current_production_facade_v12.py','scripts/build_current_preview_request_v4.py','scripts/build_current_final_request_v2.py'):
    if current not in doc: raise AssertionError(f'current entry not documented: {current}')
for boundary in ('tests/current-spine/run_exact_cross_repo_current_e2e.py','tests/remotion-compat/test_visual_director_handoff.py','tests/current-spine/test_current_preview_final_request_builders.py'):
    if boundary not in doc: raise AssertionError(f'current qualification boundary not documented: {boundary}')
for legacy in ('scripts/run_daily_production.py','scripts/run_daily_production_hardened.py','scripts/run_daily_renderer_closure.py'):
    if legacy not in doc: raise AssertionError(f'legacy entry not documented: {legacy}')
if 'must not create another full production/Renderer fixture' not in doc:
    raise AssertionError('duplicate full Current production fixture is not explicitly forbidden')
if 'Never fix Current contract drift by growing a second full synthetic production/Renderer fixture' not in doc:
    raise AssertionError('root-cause regression rule for Current fixtures is missing')
if 'scripts/current_production_facade_v12.py' not in workflow:
    raise AssertionError('current production workflow bypasses canonical facade')
for lower in ('scripts/run_semantic_frozen_renderer_closure_v12.py','scripts/run_daily_renderer_closure_v12.py'):
    if lower in workflow: raise AssertionError(f'workflow exposes internal current stage directly: {lower}')
if 'scripts/run_semantic_frozen_renderer_closure_v12.py' not in facade:
    raise AssertionError('facade no longer delegates to semantic-frozen current executor')
for label, text in (('AGENTS.md', agents), ('README.md', readme), ('daily runbook', runbook)):
    if 'scripts/current_production_facade_v12.py' not in text:
        raise AssertionError(f'{label} does not identify the canonical Current facade')
if 'Production-facing execution begins with:\n\n```text\nrun_daily_production_hardened.py' in agents:
    raise AssertionError('AGENTS.md still instructs agents to enter production through Legacy hardening')
if '本番運用では必ずhardening wrapperを使います' in runbook:
    raise AssertionError('daily runbook still promotes the Legacy hardening wrapper')
if 'scripts/build_current_preview_publication.py' not in runbook:
    raise AssertionError('daily runbook omits deterministic Renderer request publication')
print('Plot current entrypoint and qualification classification PASS')
