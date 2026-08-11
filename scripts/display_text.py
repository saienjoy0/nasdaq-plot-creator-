#!/usr/bin/env python3
"""Compatibility shim for dynamically loaded Story Engine projection modules.

Normal Story Engine execution resolves ``display_text`` from
``scripts/story-engine`` because that directory is Python's script directory. Some
validation entrypoints load the projection module with ``importlib`` while exposing
only ``scripts`` on ``sys.path``. This shim loads the exact Story Engine helper so
those validators use the same implementation instead of maintaining a second copy.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SOURCE = Path(__file__).resolve().parent / "story-engine" / "display_text.py"
_SPEC = importlib.util.spec_from_file_location("nasdaq_cafe_story_display_text", _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load Story Engine display_text helper: {_SOURCE}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

to_display_text = _MODULE.to_display_text

__all__ = ["to_display_text"]
