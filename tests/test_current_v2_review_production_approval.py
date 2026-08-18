from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'scripts' / 'materialize_chatgpt_daily_authoring.py'


def _derived_review_ast() -> ast.Dict:
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == 'derived_review'
            for target in node.targets
        ):
            assert isinstance(node.value, ast.Dict)
            return node.value
    raise AssertionError('derived_review assignment not found')


def test_current_v2_review_projects_pass_into_legacy_approval_flag() -> None:
    value = _derived_review_ast()
    mapping = {
        key.value: item
        for key, item in zip(value.keys, value.values, strict=True)
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    assert 'approvedForCodex' in mapping
    expr = mapping['approvedForCodex']
    assert isinstance(expr, ast.Compare)
    assert isinstance(expr.left, ast.Subscript)
    assert isinstance(expr.ops[0], ast.Eq)
    assert isinstance(expr.comparators[0], ast.Constant)
    assert expr.comparators[0].value == 'pass'
