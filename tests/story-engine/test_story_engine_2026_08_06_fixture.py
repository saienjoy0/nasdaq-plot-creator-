import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/'tests'/'story-engine'/'fixtures'/'2026-08-06'

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

plan_validator=load_module('story_plan_validator',ROOT/'skills'/'nasdaq-cafe-story-plan'/'validators'/'validate_story_plan.py')
bundle_validator=load_module('story_bundle_validator',ROOT/'scripts'/'story-engine'/'validate_story_engine_bundle.py')

def test_2026_08_06_story_plan_fixture_passes():
    result=plan_validator.validate_story_plan(
        FIXTURE/'story_plan_fixture.json',
        FIXTURE/'causal_dossier_fixture.json',
        repo_root=FIXTURE,
        schema_path=ROOT/'skills'/'nasdaq-cafe-story-plan'/'contracts'/'story_plan.schema.json',
    )
    assert result.ok, result.errors

def test_2026_08_06_final_story_and_review_pass():
    # The Story Plan fixture was intentionally migrated from v1.1 to v1.2.
    # Rebind the unchanged script fixture to that migrated plan in a temporary
    # workspace so the test proves semantic/causal compatibility without
    # pretending the historical script file was authored with the new hash.
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        for name in ('causal_dossier_fixture.json','story_plan_fixture.json','story_script_final_fixture.json','creative_review_round2_fixture.json'):
            shutil.copy2(FIXTURE/name, root/name)
        script_path=root/'story_script_final_fixture.json'
        script=json.loads(script_path.read_text(encoding='utf-8'))
        script['story_plan']['sha256']=sha256(root/'story_plan_fixture.json')
        script_path.write_text(json.dumps(script,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        result=bundle_validator.validate_bundle(
            script_path,
            root/'story_plan_fixture.json',
            root/'causal_dossier_fixture.json',
            story_contracts_dir=ROOT/'skills'/'nasdaq-cafe-story-authoring'/'contracts',
            critic_contracts_dir=ROOT/'skills'/'nasdaq-cafe-entertainment-critic'/'contracts',
            repo_root=root,
            review_path=root/'creative_review_round2_fixture.json',
        )
    assert result.ok, result.errors
