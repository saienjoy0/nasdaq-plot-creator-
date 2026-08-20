#!/usr/bin/env python3
"""Generation-neutral mechanical helpers for the current Renderer closure."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import renderer_binding


class CurrentRendererClosureMechanismError(RuntimeError):
    pass


def run(
    root: Path,
    *args: str,
    env: dict[str, str] | None = None,
    ok_codes=(0,),
) -> int:
    command = list(args)
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=root, env=env, check=False)
    if completed.returncode not in ok_codes:
        raise CurrentRendererClosureMechanismError(
            f"command failed ({completed.returncode}): {' '.join(command)}"
        )
    return completed.returncode


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CurrentRendererClosureMechanismError(f"JSON root must be object: {path}")
    return value


def ensure_renderer(root: Path, renderer_root: Path) -> dict:
    try:
        return renderer_binding.verify_renderer_checkout(root, renderer_root)
    except renderer_binding.RendererBindingError as exc:
        raise CurrentRendererClosureMechanismError(str(exc)) from exc


def evidence_if_exists(root: Path, values: list[str]) -> list[str]:
    return [value for value in values if (root / value).is_file()]
