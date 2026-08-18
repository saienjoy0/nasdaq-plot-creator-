from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import materialize_chatgpt_daily_authoring as mat

projection_path = ROOT / 'scripts' / 'story-engine' / 'project_story_script_to_production.py'
spec = importlib.util.spec_from_file_location('story_projection_module', projection_path)
assert spec is not None and spec.loader is not None
projection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(projection)


def test_v2_public_package_uses_real_newlines_and_is_ws4_parseable() -> None:
    root_authoring = {
        'episodeDate': '2099-01-07',
        'marketDate': '2099-01-06',
        'informationCutoff': '2099-01-07T05:00:00Z',
        'storyPlan': {'story_spine': 'synthetic spine'},
        'creativeReview': {
            'verdict': 'pass',
            'total_score': 30,
            'scores': {'opening': 5},
        },
        'storyScript': {
            'scenes': [{'narration': '一段落目です。\n\n二段落目です。'}],
        },
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
            'formalName': 'Synthetic',
            'purpose': 'purpose',
            'performanceIntent': 'intent',
            'initialExpression': '分析',
            'visualMode': 'text-focus',
            'headline': 'headline',
            'supportingTexts': ['support'],
            'uncertainty': 'none',
            'beats': [beat],
        }],
        'publishing': {
            'titleCandidates': ['title'],
            'thumbnailTextCandidates': ['thumb'],
            'description': 'description',
        },
    }
    md = mat.build_episode_markdown_v2(root_authoring, projected)
    assert '# 朝のNASDAQカフェ｜2099-01-07 制作パッケージ\n\n## エピソード概要\n' in md
    assert '\\n\\n## エピソード概要' not in md
    assert projection._public_scene_narration(md, 1) == '一段落目です。\n\n二段落目です。'
