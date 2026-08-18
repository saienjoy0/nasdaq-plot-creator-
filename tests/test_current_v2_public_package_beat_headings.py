from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import materialize_chatgpt_daily_authoring as mat

BEAT_HEADING_RE = re.compile(r'(?m)^- \*\*(scene-0[1-9]-beat-[0-9]{3})\*\*$')


def test_v2_public_package_exposes_renderer_beat_headings() -> None:
    root_authoring = {
        'episodeDate': '2099-01-07',
        'marketDate': '2099-01-06',
        'informationCutoff': '2099-01-07T05:00:00Z',
        'storyPlan': {'story_spine': 'synthetic spine'},
        'creativeReview': {'verdict': 'pass', 'total_score': 30, 'scores': {'opening': 5}},
        'storyScript': {'scenes': [{'narration': 'synthetic narration'}]},
    }
    beat = {
        'screenState': 'synthetic-state',
        'grammarId': 'synthetic-grammar',
        'transitionRole': 'continuation',
        'visualTemplate': 'conclusion-card',
        'screenQuestion': 'question',
        'primaryElement': 'element',
        'viewerTexts': ['viewer'],
        'evidenceSourceIds': ['SRC-1'],
    }
    projected = {
        'scenes': [{
            'formalName': 'Synthetic', 'purpose': 'purpose', 'performanceIntent': 'intent',
            'initialExpression': '分析', 'visualMode': 'text-focus', 'headline': 'headline',
            'supportingTexts': ['support'], 'uncertainty': 'none', 'beats': [beat, dict(beat)],
        }],
        'publishing': {'titleCandidates': ['title'], 'thumbnailTextCandidates': ['thumb'], 'description': 'description'},
    }
    md = mat.build_episode_markdown_v2(root_authoring, projected)
    headings = BEAT_HEADING_RE.findall(md)
    assert headings == ['scene-01-beat-001', 'scene-01-beat-002']
    assert '### Visual Beats' in md
    assert '### 完成ナレーション' in md
