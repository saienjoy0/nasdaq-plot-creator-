#!/usr/bin/env python3
"""Hardening gate for the merged PR #8 episode-package memory validator.

This gate layers final-production structural requirements on top of the
canonical PR #8 validator. It does not make editorial decisions. It verifies
that the package is the final nine-scene, post-inquisition human source of
truth and that PR #8 production metadata cannot leak into public artifacts.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

ANNEX_BEGIN = "<!--BEGIN_EPISODE_MEMORY_ANNEX-->"
ANNEX_END = "<!--END_EPISODE_MEMORY_ANNEX-->"
FINAL_BEGIN = "<!--BEGIN_FINAL_PRODUCTION_SOURCE-->"
FINAL_END = "<!--END_FINAL_PRODUCTION_SOURCE-->"
SCENE_HEADING_RE = re.compile(
    r"(?im)^#{2,4}\s*(?:B\.\s*)?(?:Scene|SCENE)[\s\-]*(0?[1-9])(?:\b|｜|\|)"
)
INQUISITION_HEADING_RE = re.compile(
    r"(?im)^#{1,3}\s*(?:H\.\s*)?04(?:\s|　)+興味深さ・わかりやすさ審問結果\s*$"
)
JSON_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
PUBLIC_METADATA_TOKENS = (
    "<!--MEMREF:",
    ANNEX_BEGIN,
    ANNEX_END,
    "memory_reference_id",
    "dossier_current_evidence_ids",
    "difference_from_previous",
    "validation_intent",
)


@dataclass
class HardeningResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "pass" if self.ok else "fail",
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _load_base_validator(repo_root: Path):
    path = (
        repo_root
        / "skills/nasdaq-cafe-episode-package-memory/validators/validate_episode_package_memory.py"
    )
    spec = importlib.util.spec_from_file_location("pr8_base_episode_memory_validator", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import merged PR8 validator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_base_validator(repo_root: Path, episode_package: Path):
    module = _load_base_validator(repo_root)
    if hasattr(module, "validate_episode_package_memory"):
        return module.validate_episode_package_memory(
            repo_root=repo_root,
            episode_package_path=episode_package,
        )
    if hasattr(module, "validate_episode_package"):
        return module.validate_episode_package(
            episode_package,
            repo_root=repo_root,
        )
    raise RuntimeError("merged PR8 validator exposes no supported validation function")


def _result_lists(result: Any) -> tuple[list[str], list[str]]:
    if result is None:
        return ["base PR8 validator returned no result"], []
    errors = getattr(result, "errors", None)
    warnings = getattr(result, "warnings", None)
    if errors is None and isinstance(result, tuple) and len(result) == 2:
        errors, warnings = result
    if not isinstance(errors, list) or not isinstance(warnings, list):
        return ["base PR8 validator returned an unsupported result shape"], []
    return list(errors), list(warnings)


def _safe_repo_file(repo_root: Path, path: Path, label: str, errors: list[str]) -> Path | None:
    root = repo_root.resolve()
    resolved = path.resolve()
    if resolved != root and root not in resolved.parents:
        errors.append(f"{label} escapes repository root: {path}")
        return None
    if not resolved.is_file():
        errors.append(f"{label} does not exist: {path}")
        return None
    return resolved


def _extract_annex(text: str, errors: list[str]) -> tuple[dict[str, Any] | None, int, int]:
    begin_count = text.count(ANNEX_BEGIN)
    end_count = text.count(ANNEX_END)
    if begin_count != 1 or end_count != 1:
        errors.append(
            "episode memory annex markers must appear exactly once: "
            f"begin={begin_count} end={end_count}"
        )
        return None, -1, -1
    start = text.index(ANNEX_BEGIN)
    end_marker_start = text.index(ANNEX_END)
    if end_marker_start <= start:
        errors.append("episode memory annex end marker appears before begin marker")
        return None, start, end_marker_start
    end = end_marker_start + len(ANNEX_END)
    block = text[start:end]
    fences = list(JSON_FENCE_RE.finditer(block))
    if len(fences) != 1:
        errors.append(
            f"episode memory annex must contain exactly one JSON fence: found={len(fences)}"
        )
        return None, start, end
    try:
        annex = json.loads(fences[0].group(1))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid episode memory annex JSON: {exc}")
        return None, start, end
    if not isinstance(annex, dict):
        errors.append("episode memory annex JSON must be an object")
        return None, start, end
    return annex, start, end


def _scan_public_artifacts(paths: Iterable[Path], repo_root: Path, errors: list[str]) -> None:
    for raw_path in paths:
        path = _safe_repo_file(repo_root, raw_path, "public artifact", errors)
        if path is None:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"cannot read public artifact {path}: {exc}")
            continue
        for token in PUBLIC_METADATA_TOKENS:
            if token in text:
                errors.append(
                    f"public artifact contains internal episode-memory metadata token {token!r}: {path}"
                )


def validate_hardening(
    *,
    repo_root: Path,
    episode_package: Path,
    public_artifacts: Iterable[Path] = (),
    base_runner: Callable[[Path, Path], Any] | None = None,
) -> HardeningResult:
    errors: list[str] = []
    warnings: list[str] = []
    repo_root = repo_root.resolve()
    package = _safe_repo_file(repo_root, episode_package, "episode package", errors)
    if package is None:
        return HardeningResult(errors, warnings)

    try:
        text = package.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return HardeningResult([f"cannot read episode package: {exc}"], warnings)

    annex, annex_start, annex_end = _extract_annex(text, errors)
    if annex is not None:
        tail = text[annex_end:]
        if tail.strip():
            final_begin_count = tail.count(FINAL_BEGIN)
            final_end_count = tail.count(FINAL_END)
            if final_begin_count != 1 or final_end_count != 1:
                errors.append(
                    "only one Final Production Source annex may follow the episode memory annex: "
                    f"begin={final_begin_count} end={final_end_count}"
                )
            else:
                final_start = tail.index(FINAL_BEGIN)
                final_end_start = tail.index(FINAL_END)
                final_end = final_end_start + len(FINAL_END)
                if tail[:final_start].strip():
                    errors.append(
                        "no content may appear between memory annex and Final Production Source annex"
                    )
                if final_end_start <= final_start:
                    errors.append("Final Production Source annex end appears before begin")
                if tail[final_end:].strip():
                    errors.append("Final Production Source annex must be the final section")
        episode_date = annex.get("episode_date")
        if isinstance(episode_date, str) and episode_date not in package.name:
            errors.append(
                f"episode package filename must contain annex episode_date: {episode_date}"
            )

    scene_numbers = [
        int(value)
        for value in SCENE_HEADING_RE.findall(
            text[:annex_start] if annex_start >= 0 else text
        )
    ]
    expected = list(range(1, 10))
    if scene_numbers != expected:
        errors.append(
            "final episode package must contain Scene 1 through Scene 9 exactly once and in order: "
            f"actual={scene_numbers}"
        )

    inquisition_matches = list(INQUISITION_HEADING_RE.finditer(text))
    if len(inquisition_matches) != 1:
        errors.append(
            "final episode package must contain exactly one integrated "
            f"'04 興味深さ・わかりやすさ審問結果' section: found={len(inquisition_matches)}"
        )
    elif annex_start >= 0 and inquisition_matches[0].start() >= annex_start:
        errors.append("04 inquisition result must appear before the episode memory annex")

    if annex is not None:
        intent = annex.get("validation_intent")
        if not isinstance(intent, dict) or intent.get("post_inquisition_final") is not True:
            errors.append("annex.validation_intent.post_inquisition_final must be true")

    runner = base_runner or _run_base_validator
    try:
        base_result = runner(repo_root, package)
        base_errors, base_warnings = _result_lists(base_result)
        errors.extend(f"base PR8 validator: {item}" for item in base_errors)
        warnings.extend(f"base PR8 validator: {item}" for item in base_warnings)
    except Exception as exc:
        errors.append(f"base PR8 validator could not run: {exc}")

    _scan_public_artifacts(public_artifacts, repo_root, errors)
    return HardeningResult(errors, warnings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-package", required=True, type=Path)
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    parser.add_argument("--public-artifact", action="append", default=[], type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = validate_hardening(
        repo_root=args.repo_root,
        episode_package=args.episode_package,
        public_artifacts=args.public_artifact,
    )
    output = json.dumps(result.as_dict(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
