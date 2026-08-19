#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]


def replace_between(path: Path, start: str, end: str, replacement: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    a = text.find(start)
    b = text.find(end, a if a >= 0 else 0)
    if a < 0 or b < 0 or text.find(start, a + 1) >= 0:
        raise SystemExit(f"{label}: marker drift")
    path.write_text(text[:a] + replacement + text[b:], encoding="utf-8")


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{label}: expected 1 match, found {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

production = root / ".github/workflows/chatgpt-daily-preview-production.yml"
replace_between(
    production,
    "      - name: Run semantic-frozen Visual Intelligence v1.2 production closure\n",
    "      - name: Record immutable baseline\n",
    '''      - name: Run canonical current production facade\n        id: closure\n        shell: bash\n        run: |\n          set -o pipefail\n          python3 scripts/current_production_facade_v12.py \\\n            --workspace . \\\n            --renderer-root "$NASDAQ_CAFE_RENDERER_ROOT" \\\n            closure \\\n            --episode-date "$EPISODE_DATE" \\\n            --phase compile \\\n            --semantic-freeze "$SEMANTIC_FREEZE_PATH" \\\n            --build-handoff-on-pass \\\n            --bundle-root production-bundles \\\n            --plot-commit "$GITHUB_SHA" \\\n            2>&1 | tee "verification/$EPISODE_DATE/current-facade-v12.log"\n          python3 - <<'PY' >> "$GITHUB_OUTPUT"\n          import json, os\n          from pathlib import Path\n          date=os.environ['EPISODE_DATE']\n          path=Path('verification') / date / 'current_production_facade_outcome.json'\n          if not path.is_file():\n              raise SystemExit('current production facade outcome missing')\n          value=json.loads(path.read_text(encoding='utf-8'))\n          status=value.get('status')\n          if status == 'PASS':\n              if value.get('previewHandoffReady') is not True:\n                  raise SystemExit('PASS facade outcome must include immutable handoff')\n              print('continue=true')\n          elif status in {'PREPARED', 'REVIEW_REQUIRED'}:\n              print('continue=false')\n          else:\n              raise SystemExit(f'unexpected current facade status: {status!r}')\n          print(f'status={status}')\n          PY\n\n''',
    "Production canonical facade routing",
)

canary = root / ".github/workflows/visual-intelligence-real-day-canary.yml"
replace_once(
    canary,
    '''          python scripts/run_daily_renderer_closure_v12.py \\\n            --phase "${{ inputs.phase }}" \\\n            --date "${{ inputs.episode_date }}" \\\n            --repo-root . \\\n            --renderer-root .renderer\n''',
    '''          python scripts/current_production_facade_v12.py \\\n            --workspace . \\\n            --renderer-root .renderer \\\n            closure \\\n            --phase "${{ inputs.phase }}" \\\n            --episode-date "${{ inputs.episode_date }}" \\\n            --semantic-freeze "semantic-freezes/${{ inputs.episode_date }}.json"\n''',
    "Canary canonical facade routing",
)

exact = root / ".github/workflows/current-spine-exact-cross-repo-e2e.yml"
replace_once(
    exact,
    '''      - name: Characterization remains consistent\n        run: python3 tests/current-spine/test_current_spine_characterization.py\n\n''',
    '''      - name: Characterization remains consistent\n        run: python3 tests/current-spine/test_current_spine_characterization.py\n\n      - name: Verify canonical current facade routing\n        run: |\n          python3 scripts/current_production_facade_v12.py --help >/dev/null\n          python3 tests/current-spine/test_current_production_facade_contract.py\n\n''',
    "Exact E2E facade contract",
)

daily = root / ".github/workflows/daily-production.yml"
replace_once(
    daily,
    '''            scripts/run_semantic_frozen_renderer_closure_v12.py\n''',
    '''            scripts/run_semantic_frozen_renderer_closure_v12.py \\\n            scripts/current_production_facade_v12.py\n''',
    "Daily CI facade syntax gate",
)
print("PR-4 canonical facade workflow migration applied")
