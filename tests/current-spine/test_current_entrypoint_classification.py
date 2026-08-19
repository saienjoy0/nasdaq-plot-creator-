#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
doc=(ROOT/'docs/current-spine/CURRENT_ENTRYPOINTS.md').read_text(encoding='utf-8')
workflow=(ROOT/'.github/workflows/chatgpt-daily-preview-production.yml').read_text(encoding='utf-8')
facade=(ROOT/'scripts/current_production_facade_v12.py').read_text(encoding='utf-8')

for heading in ('CURRENT PRODUCTION','LEGACY READ-ONLY / COMPATIBILITY','TEST / HISTORICAL ONLY'):
    if heading not in doc: raise AssertionError(f'missing entrypoint class: {heading}')
for current in ('scripts/current_production_facade_v12.py','scripts/build_current_preview_request_v4.py','scripts/build_current_final_request_v2.py'):
    if current not in doc: raise AssertionError(f'current entry not documented: {current}')
for legacy in ('scripts/run_daily_production.py','scripts/run_daily_production_hardened.py','scripts/run_daily_renderer_closure.py'):
    if legacy not in doc: raise AssertionError(f'legacy entry not documented: {legacy}')
if 'scripts/current_production_facade_v12.py' not in workflow:
    raise AssertionError('current production workflow bypasses canonical facade')
for lower in ('scripts/run_semantic_frozen_renderer_closure_v12.py','scripts/run_daily_renderer_closure_v12.py'):
    if lower in workflow: raise AssertionError(f'workflow exposes internal current stage directly: {lower}')
if 'scripts/run_semantic_frozen_renderer_closure_v12.py' not in facade:
    raise AssertionError('facade no longer delegates to semantic-frozen current executor')
print('Plot current entrypoint classification PASS')
