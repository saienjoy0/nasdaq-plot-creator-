# PR-0 scope — Formal 2026-08-06 baseline

This branch intentionally does not implement Visual Source acquisition.

It reuses the existing daily materializer, Story Engine gate, Final Production builder, strict Remotion finalizer, consistency checks and immutable handoff builder, then records their exact SHA-bound result as the pre-Visual-Source baseline.

Non-goals: image search, source resolution, TTS generation, preview rendering, final rendering, editorial changes, causality changes, narration changes, Visual Grammar changes, Financial Visual changes.
