#!/usr/bin/env python3
"""Import compatibility shim for Story Engine auxiliary bindings.

The implementation remains authoritative at
``scripts/story-engine/apply_story_auxiliary_bindings.py``. This shim exists so tools
that import the Story projection module from the repository-level ``scripts`` path can
resolve its historical absolute import without duplicating any binding logic.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_IMPL = Path(__file__).resolve().parent / "story-engine" / "apply_story_auxiliary_bindings.py"
_SPEC = importlib.util.spec_from_file_location("story_engine_auxiliary_bindings_impl", _IMPL)
if not _SPEC or not _SPEC.loader:
    raise ImportError(f"cannot load Story Engine auxiliary bindings: {_IMPL}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)

apply_story_reaction_bindings = _MODULE.apply_story_reaction_bindings

__all__ = ["apply_story_reaction_bindings"]
