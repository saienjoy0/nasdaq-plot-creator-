from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
VALIDATORS = ROOT / "skills/nasdaq-cafe-causal-research/validators"
for item in (SCRIPTS, VALIDATORS):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

spec = importlib.util.spec_from_file_location(
    "causal_supplement_gate",
    VALIDATORS / "validate_causal_research_with_supplement.py",
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

DATE = "2026-08-06"
CONTRACTS = ROOT / "skills/nasdaq-cafe-causal-research/contracts"


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path: Path, *, bind_supplement: bool = True, acquired_ref: bool = True):
    base = tmp_path / "research" / DATE / "research_input_manifest.json"
    request = tmp_path / "research" / DATE / "research_acquisition_request_w01.json"
    result = tmp_path / "research" / DATE / "research_acquisition_result_w01.json"
    evidence = tmp_path / "research" / DATE / "evidence" / "RA-001_intraday_series.json"
    supplement = tmp_path / "research" / DATE / "research_evidence_supplement_manifest.json"
    dossier = tmp_path / "research" / DATE / f"causal_research_dossier_{DATE}.json"
    report = tmp_path / "working" / DATE / f"memory_retrieval_report_{DATE}.json"

    write_json(base, {"episode_date": DATE})
    write_json(report, {})
    write_json(
        request,
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "wave": 1,
            "baseResearchInputManifestSha256": sha256(base),
            "researchPurpose": "timeline",
            "requests": [
                {
                    "requestId": "RA-001",
                    "type": "market_intraday",
                    "reason": "timing",
                    "requiredness": "material",
                    "parameters": {
                        "symbol": "AMD.US",
                        "date": "2026-08-05",
                        "resolution": "1m",
                        "session": "all",
                    },
                }
            ],
        },
    )
    write_json(evidence, {"precision": "verified-intraday-series", "points": []})
    write_json(
        result,
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "wave": 1,
            "requestSha256": sha256(request),
            "status": "success",
            "results": [
                {
                    "requestId": "RA-001",
                    "status": "success",
                    "provider": "Longbridge",
                    "outputPath": "followup/RA-001_intraday_series.json",
                    "sha256": sha256(evidence),
                    "recordCount": 0,
                    "reason": "",
                }
            ],
        },
    )
    write_json(
        supplement,
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "baseResearchInputManifest": {
                "path": base.relative_to(tmp_path).as_posix(),
                "sha256": sha256(base),
            },
            "waves": [
                {
                    "wave": 1,
                    "request": {
                        "path": request.relative_to(tmp_path).as_posix(),
                        "sha256": sha256(request),
                    },
                    "result": {
                        "path": result.relative_to(tmp_path).as_posix(),
                        "sha256": sha256(result),
                    },
                    "collectorRunId": 123,
                    "evidenceFiles": [
                        {
                            "requestId": "RA-001",
                            "path": evidence.relative_to(tmp_path).as_posix(),
                            "sha256": sha256(evidence),
                        }
                    ],
                }
            ],
        },
    )
    provenance = []
    if bind_supplement:
        provenance.append(
            {
                "role": "other",
                "path_or_reference": supplement.relative_to(tmp_path).as_posix(),
                "version_or_hash": sha256(supplement),
            }
        )
    source_reference = (
        evidence.relative_to(tmp_path).as_posix()
        if acquired_ref
        else "https://example.com/non-acquired-source"
    )
    write_json(
        dossier,
        {
            "episode_date": DATE,
            "input_provenance": provenance,
            "evidence": [{"evidence_id": "E-001", "source_reference": source_reference}],
        },
    )
    return dossier, base, report, supplement, evidence


def base_pass():
    return module.ValidationResult([], [])


def test_valid_supplement_is_integrated(tmp_path: Path) -> None:
    dossier, base, report, supplement, _ = fixture(tmp_path)
    with patch.object(module, "validate_dossier", return_value=base_pass()):
        result = module.validate_dossier_with_supplement(
            dossier,
            base,
            report,
            supplement_path=supplement,
            contracts_dir=CONTRACTS,
            repo_root=tmp_path,
        )
    assert result.ok


def test_dossier_must_bind_supplement_manifest_in_input_provenance(tmp_path: Path) -> None:
    dossier, base, report, supplement, _ = fixture(tmp_path, bind_supplement=False)
    with patch.object(module, "validate_dossier", return_value=base_pass()):
        result = module.validate_dossier_with_supplement(
            dossier,
            base,
            report,
            supplement_path=supplement,
            contracts_dir=CONTRACTS,
            repo_root=tmp_path,
        )
    assert not result.ok
    assert any("input_provenance" in error for error in result.errors)


def test_unbound_acquired_evidence_is_rejected(tmp_path: Path) -> None:
    dossier, base, report, supplement, evidence = fixture(tmp_path)
    supplement_doc = json.loads(supplement.read_text(encoding="utf-8"))
    supplement_doc["waves"][0]["evidenceFiles"][0]["path"] = "research/2026-08-06/evidence/different.json"
    different = tmp_path / "research" / DATE / "evidence" / "different.json"
    different.write_bytes(evidence.read_bytes())
    supplement_doc["waves"][0]["evidenceFiles"][0]["sha256"] = sha256(different)
    result_doc = json.loads((tmp_path / "research" / DATE / "research_acquisition_result_w01.json").read_text(encoding="utf-8"))
    result_doc["results"][0]["sha256"] = sha256(different)
    result_path = tmp_path / "research" / DATE / "research_acquisition_result_w01.json"
    write_json(result_path, result_doc)
    supplement_doc["waves"][0]["result"]["sha256"] = sha256(result_path)
    write_json(supplement, supplement_doc)
    dossier_doc = json.loads(dossier.read_text(encoding="utf-8"))
    dossier_doc["input_provenance"][0]["version_or_hash"] = sha256(supplement)
    write_json(dossier, dossier_doc)
    with patch.object(module, "validate_dossier", return_value=base_pass()):
        result = module.validate_dossier_with_supplement(
            dossier,
            base,
            report,
            supplement_path=supplement,
            contracts_dir=CONTRACTS,
            repo_root=tmp_path,
        )
    assert not result.ok
    assert any("not supplement-bound" in error for error in result.errors)


def test_acquired_evidence_without_supplement_is_rejected(tmp_path: Path) -> None:
    dossier, base, report, _, _ = fixture(tmp_path, bind_supplement=False)
    with patch.object(module, "validate_dossier", return_value=base_pass()):
        result = module.validate_dossier_with_supplement(
            dossier,
            base,
            report,
            supplement_path=None,
            contracts_dir=CONTRACTS,
            repo_root=tmp_path,
        )
    assert not result.ok
    assert any("no research evidence supplement" in error for error in result.errors)


def test_non_acquired_evidence_does_not_require_supplement(tmp_path: Path) -> None:
    dossier, base, report, _, _ = fixture(tmp_path, bind_supplement=False, acquired_ref=False)
    with patch.object(module, "validate_dossier", return_value=base_pass()):
        result = module.validate_dossier_with_supplement(
            dossier,
            base,
            report,
            supplement_path=None,
            contracts_dir=CONTRACTS,
            repo_root=tmp_path,
        )
    assert result.ok
