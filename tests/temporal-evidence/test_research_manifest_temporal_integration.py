from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "scripts" / "build_research_input_manifest.py"
if not BUILDER_PATH.is_file():
    pytest.skip("integration test runs after bundle is applied to nasdaq-plot-creator-", allow_module_level=True)

spec = importlib.util.spec_from_file_location("build_research_input_manifest", BUILDER_PATH)
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_optional_collector_source_pack_is_sha_bound_without_becoming_required(tmp_path: Path):
    contracts = tmp_path / "skills/nasdaq-cafe-causal-research/contracts"
    contracts.mkdir(parents=True)
    shutil.copy2(
        ROOT / "skills/nasdaq-cafe-causal-research/contracts/research_input_manifest.schema.json",
        contracts / "research_input_manifest.schema.json",
    )
    editorial = tmp_path / "skills/nasdaq-cafe-editorial-memory/contracts"
    editorial.mkdir(parents=True)
    permissive = {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}
    write_json(editorial / "memory_query_plan.schema.json", permissive)
    write_json(editorial / "memory_retrieval_report.schema.json", permissive)

    date = "2026-08-12"
    daily = tmp_path / f"daily_source_package_{date}.md"
    daily.write_text("# daily\n", encoding="utf-8")
    source_pack = tmp_path / "collector" / "source_pack.json"
    write_json(source_pack, {"cross_market_snapshot": {}})
    query = tmp_path / f"memory_query_plan_{date}.json"
    write_json(query, {"episode_date": date})
    context = tmp_path / f"memory_context_{date}.md"
    context.write_text("# memory\n", encoding="utf-8")
    report = tmp_path / f"memory_retrieval_report_{date}.json"
    write_json(
        report,
        {
            "episode_date": date,
            "query_plan_path": query.relative_to(tmp_path).as_posix(),
            "selected": [],
            "rejected": [],
        },
    )

    def replay(_query, context_out, report_out, **_kwargs):
        context_out.write_bytes(context.read_bytes())
        report_out.write_bytes(report.read_bytes())
        return json.loads(report.read_text(encoding="utf-8"))

    output = tmp_path / "research" / date / "research_input_manifest.json"
    result = builder.build_manifest(
        episode_date=date,
        market_date=date,
        timezone="America/New_York",
        information_cutoff="2026-08-12T08:00:00Z",
        daily_source_package=daily,
        collector_source_pack=source_pack,
        memory_query_plan=query,
        memory_context=context,
        memory_retrieval_report=report,
        output=output,
        contracts_dir=contracts,
        repo_root=tmp_path,
        retrieval_runner=replay,
    )
    assert result["contract_version"] == "1.1.0"
    assert result["inputs"]["collector_source_pack"] == {
        "path": "collector/source_pack.json",
        "sha256": sha(source_pack),
    }

    schema = json.loads((contracts / "research_input_manifest.schema.json").read_text(encoding="utf-8"))
    legacy = json.loads(json.dumps(result))
    legacy["contract_version"] = "1.0.0"
    legacy["inputs"].pop("collector_source_pack")
    assert not list(Draft202012Validator(schema).iter_errors(legacy))
