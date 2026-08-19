#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

closure = root / "scripts/run_daily_renderer_closure_v12.py"
replace_once(
    closure,
    '''from current_renderer_closure_mechanisms_v12 import (\n    ensure_renderer,\n    evidence_if_exists,\n    load,\n    run,\n)\n''',
    '''from current_renderer_closure_mechanisms_v12 import (\n    CurrentRendererClosureMechanismError,\n    ensure_renderer,\n    evidence_if_exists,\n    load,\n    run,\n)\n''',
    "closure mechanism exception import",
)
replace_once(
    closure,
    "    except VisualIntelligenceClosureError as exc:\n",
    "    except (VisualIntelligenceClosureError, CurrentRendererClosureMechanismError) as exc:\n",
    "closure mechanism exception catch",
)

freeze_test = root / "tests/chatgpt-semantic-freeze/test_chatgpt_semantic_freeze.py"
old = '''    def test_ai_b_artifacts_must_bind_same_manifest_sha(self) -> None:\n        with tempfile.TemporaryDirectory() as tmp:\n            root = Path(tmp)\n            date = "2026-08-17"\n            vi = root / "working" / date / "visual-intelligence"\n            vi.mkdir(parents=True, exist_ok=True)\n            expected = "a" * 64\n            (vi / "visual_requirements.json").write_text(json.dumps({"semanticFreezeSha256": "b" * 64}), encoding="utf-8")\n            self.assertEqual(frozen_closure.semantic_binding_pause(root, date, phase="compile", semantic_freeze_sha256=expected)[0], "AUTHOR_VISUAL_REQUIREMENTS")\n            (vi / "visual_requirements.json").write_text(json.dumps({"semanticFreezeSha256": expected}), encoding="utf-8")\n            self.assertEqual(frozen_closure.semantic_binding_pause(root, date, phase="compile", semantic_freeze_sha256=expected)[0], "AUTHOR_VISUAL_INTELLIGENCE_DECISION")\n            (vi / "visual_intelligence_decision.json").write_text(json.dumps({"semanticFreezeSha256": expected}), encoding="utf-8")\n            self.assertIsNone(frozen_closure.semantic_binding_pause(root, date, phase="compile", semantic_freeze_sha256=expected))\n'''
new = '''    def test_ai_b_semantic_payloads_do_not_duplicate_manifest_sha(self) -> None:\n        with tempfile.TemporaryDirectory() as tmp:\n            root = Path(tmp)\n            date = "2026-08-17"\n            vi = root / "working" / date / "visual-intelligence"\n            vi.mkdir(parents=True, exist_ok=True)\n            expected = "a" * 64\n            requirements = {\n                "semanticPayloadVersion": "1.0.0",\n                "episodeDate": date,\n                "intent": {"beats": []},\n                "provisionalDirection": {"requirements": []},\n            }\n            (vi / "visual_requirements.semantic.json").write_text(\n                json.dumps(requirements), encoding="utf-8"\n            )\n            self.assertNotIn("semanticFreezeSha256", requirements)\n            self.assertIsNone(\n                frozen_closure.semantic_binding_pause(\n                    root, date, phase="compile", semantic_freeze_sha256=expected\n                )\n            )\n            wrapper = (REPO_ROOT / "scripts/run_semantic_frozen_renderer_closure_v12.py").read_text(encoding="utf-8")\n            self.assertNotIn('decision.get("semanticFreezeSha256")', wrapper)\n            self.assertNotIn('requirements.get("semanticFreezeSha256")', wrapper)\n'''
replace_once(freeze_test, old, new, "Semantic Freeze duplicate-binding regression")
print("PR-2 contract tests aligned")
