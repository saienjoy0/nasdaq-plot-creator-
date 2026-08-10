from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "visual_source_contract_planning_gate",
    SCRIPTS / "visual_source_contract.py",
)
assert spec and spec.loader
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def test_missing_intent_document_fails_at_contract_boundary(tmp_path: Path) -> None:
    with pytest.raises(contract.VisualSourceContractError, match="E_VISUAL_SOURCE_PLANNING_MISSING"):
        contract.load_intent_document(tmp_path / "missing.json", "2026-08-06")


def test_none_intent_path_fails_at_contract_boundary() -> None:
    with pytest.raises(contract.VisualSourceContractError, match="E_VISUAL_SOURCE_PLANNING_MISSING"):
        contract.load_intent_document(None, "2026-08-06")


def test_explicit_empty_intent_document_is_valid(tmp_path: Path) -> None:
    path = tmp_path / "visual_source_intents.json"
    path.write_text(
        json.dumps(
            {
                "contractVersion": "1.0.0",
                "episodeDate": "2026-08-06",
                "intents": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    value = contract.load_intent_document(path, "2026-08-06")
    assert value == {"contractVersion": "1.0.0", "intents": []}
