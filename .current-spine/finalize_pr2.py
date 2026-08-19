#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_between(path: Path, start: str, end: str, replacement: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    a = text.find(start)
    b = text.find(end, a if a >= 0 else 0)
    if a < 0 or b < 0 or text.find(start, a + 1) >= 0:
        raise SystemExit(f"{label}: marker drift")
    path.write_text(text[:a] + replacement + text[b:], encoding="utf-8")

# Daily Authoring delegates the checkpoint to a dedicated single writer.
materializer = root / "scripts/materialize_chatgpt_daily_authoring.py"
replace_once(
    materializer,
    "from pathlib import Path\n",
    "from pathlib import Path\n\nimport visual_source_checkpoint_v12\n",
    "Visual Source checkpoint import",
)
replace_once(
    materializer,
    '''    requirements_sealed = work / "visual-intelligence" / "visual_requirements.json"\n    visual_source_intents = work / "visual_source_intents.json"\n    if not requirements_sealed.is_file():\n        dump(visual_source_intents, {"contractVersion":"1.0.0","episodeDate":date,"intents":projected.get("visualSourceIntents",[])})\n        if projected.get("visualSourceSelection") is not None:\n            dump(work / "visual_source_selection.json", projected["visualSourceSelection"])\n    elif not visual_source_intents.is_file():\n        raise SystemExit(\n            "sealed Visual Requirements require the existing ChatGPT Visual Source checkpoint"\n        )\n''',
    '''    visual_source_checkpoint_v12.materialize(\n        work=work,\n        date=date,\n        projected=projected,\n    )\n''',
    "Visual Source checkpoint delegation",
)

# Remove the last current-path evidence rebind compatibility repair. The hardened
# handoff already restores the exact original preflight bytes in finally.
mechanisms = root / "scripts/current_daily_mechanisms_v12.py"
replace_between(
    mechanisms,
    "def _refresh_handoff_preflight_evidence(",
    "def build_handoff(",
    "",
    "handoff preflight rebind helper removal",
)
replace_once(
    mechanisms,
    '''    # Existing handoff hardening may persist one verified preflight update. Keep\n    # this compatibility repair isolated here until PR-2 removes the multi-writer.\n    _refresh_handoff_preflight_evidence(workspace=workspace, date=date)\n''',
    "",
    "handoff preflight rebind invocation removal",
)

# Replace obsolete capture/restore tests with the new single-writer contract.
state_test = root / "tests/remotion-compat/test_visual_intelligence_v12_state.py"
replace_once(
    state_test,
    "import run_daily_renderer_closure_v12 as closure_v12  # noqa: E402\n",
    "import run_daily_renderer_closure_v12 as closure_v12  # noqa: E402\nimport visual_source_checkpoint_v12  # noqa: E402\n",
    "state test checkpoint import",
)
old_tests = '''def test_post_pass_b_visual_source_authoring_is_preserved() -> None:\n    date = "2099-03-04"\n    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-source-authoring-") as temp:\n        root = Path(temp)\n        work = root / "working" / date\n        vi = work / "visual-intelligence"\n        write(\n            vi / "visual_requirements.json",\n            {\n                "contractVersion": "1.0.0",\n                "episodeDate": date,\n                "intent": {"beats": []},\n                "provisionalDirection": {"requirements": []},\n            },\n        )\n        intent_path = write(\n            work / "visual_source_intents.json",\n            {\n                "contractVersion": "1.0.0",\n                "episodeDate": date,\n                "intents": [{"intentId": "chatgpt-authored-source-plan"}],\n            },\n        )\n        selection_path = write(\n            work / "visual_source_selection.json",\n            {\n                "contractVersion": "1.0.0",\n                "episodeDate": date,\n                "selectedPath": "primary",\n            },\n        )\n        expected_intents = intent_path.read_bytes()\n        expected_selection = selection_path.read_bytes()\n\n        captured = closure_v12._capture_visual_source_authoring(root, date)\n        write(\n            intent_path,\n            {\n                "contractVersion": "1.0.0",\n                "episodeDate": date,\n                "intents": [],\n            },\n        )\n        selection_path.unlink()\n        closure_v12._restore_visual_source_authoring(root, date, captured)\n\n        if intent_path.read_bytes() != expected_intents:\n            raise AssertionError("post-Pass-B Visual Source intents were not preserved byte-for-byte")\n        if selection_path.read_bytes() != expected_selection:\n            raise AssertionError("post-Pass-B Visual Source selection was not preserved byte-for-byte")\n\n\ndef test_pre_pass_b_materialization_remains_authoritative() -> None:\n    date = "2099-03-05"\n    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-source-seed-") as temp:\n        root = Path(temp)\n        work = root / "working" / date\n        write(\n            work / "visual_source_intents.json",\n            {\n                "contractVersion": "1.0.0",\n                "episodeDate": date,\n                "intents": [{"intentId": "pre-pass-b-seed"}],\n            },\n        )\n        captured = closure_v12._capture_visual_source_authoring(root, date)\n        if captured:\n            raise AssertionError("Visual Source authoring must not be preserved before Visual Requirements exist")\n\n\n'''
new_tests = '''def test_post_pass_b_visual_source_authoring_is_preserved() -> None:\n    date = "2099-03-04"\n    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-source-authoring-") as temp:\n        root = Path(temp)\n        work = root / "working" / date\n        vi = work / "visual-intelligence"\n        write(\n            vi / "visual_requirements.json",\n            {\n                "contractVersion": "1.0.0",\n                "episodeDate": date,\n                "intent": {"beats": []},\n                "provisionalDirection": {"requirements": []},\n            },\n        )\n        intent_path = write(\n            work / "visual_source_intents.json",\n            {\n                "contractVersion": "1.0.0",\n                "episodeDate": date,\n                "intents": [{"intentId": "chatgpt-authored-source-plan"}],\n            },\n        )\n        selection_path = write(\n            work / "visual_source_selection.json",\n            {\n                "contractVersion": "1.0.0",\n                "episodeDate": date,\n                "selectedPath": "primary",\n            },\n        )\n        expected_intents = intent_path.read_bytes()\n        expected_selection = selection_path.read_bytes()\n        result = visual_source_checkpoint_v12.materialize(\n            work=work,\n            date=date,\n            projected={\n                "visualSourceIntents": [],\n                "visualSourceSelection": {\n                    "contractVersion": "1.0.0",\n                    "episodeDate": date,\n                    "selectedPath": "fallback",\n                },\n            },\n        )\n        if result != "preserved":\n            raise AssertionError("sealed Visual Source checkpoint was not preserved")\n        if intent_path.read_bytes() != expected_intents:\n            raise AssertionError("sealed Visual Source intents changed")\n        if selection_path.read_bytes() != expected_selection:\n            raise AssertionError("sealed Visual Source selection changed")\n\n\ndef test_pre_pass_b_materialization_remains_authoritative() -> None:\n    date = "2099-03-05"\n    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-source-seed-") as temp:\n        root = Path(temp)\n        work = root / "working" / date\n        result = visual_source_checkpoint_v12.materialize(\n            work=work,\n            date=date,\n            projected={\n                "visualSourceIntents": [{"intentId": "pre-pass-b-seed"}],\n                "visualSourceSelection": None,\n            },\n        )\n        if result != "seeded":\n            raise AssertionError("pre-Requirements Visual Source was not seeded")\n        value = json.loads((work / "visual_source_intents.json").read_text(encoding="utf-8"))\n        if value.get("intents") != [{"intentId": "pre-pass-b-seed"}]:\n            raise AssertionError("pre-Requirements Visual Source seed drifted")\n\n\n'''
replace_once(state_test, old_tests, new_tests, "Visual Source state regressions")

# Characterization also forbids any current evidence rebind repair.
character = root / "tests/current-spine/test_current_spine_characterization.py"
replace_once(
    character,
    '''    require(mechanisms, "def request_final(", "current Final authorization mechanism")\n''',
    '''    require(mechanisms, "def request_final(", "current Final authorization mechanism")\n    forbid(mechanisms, "evidence_rebindings", "current evidence SHA rebind repair")\n    forbid(mechanisms, "_refresh_handoff_preflight_evidence", "current preflight rebind helper")\n''',
    "characterize no current evidence rebind",
)
print("PR-2 single-writer finalization applied")
