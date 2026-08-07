import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/'tests'/'story-engine'/'fixtures'/'2026-08-06'

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

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
    result=bundle_validator.validate_bundle(
        FIXTURE/'story_script_final_fixture.json',
        FIXTURE/'story_plan_fixture.json',
        FIXTURE/'causal_dossier_fixture.json',
        story_contracts_dir=ROOT/'skills'/'nasdaq-cafe-story-authoring'/'contracts',
        critic_contracts_dir=ROOT/'skills'/'nasdaq-cafe-entertainment-critic'/'contracts',
        repo_root=FIXTURE,
        review_path=FIXTURE/'creative_review_round2_fixture.json',
    )
    assert result.ok, result.errors
