# PR-2 scope — Visual Source Contract + Resolver

This layer extends the existing Final Episode Contract and existing `assets_resolved` / Final Production path. It does not create a second production package, state machine, Visual Grammar, asset manifest, or renderer.

Resolver inputs are exact locators only. It resolves both Primary and Approved Fallback candidates, records provenance, and does not choose a production path. An explicit selection file freezes `primary` or `fallback`; only that selected asset is projected into existing `image_resolution`, `asset_catalog`, asset placements, and renderer handoff.

Unresolved rights, missing bytes, SHA mismatch, path escape, unsupported capture adapter, and user-review-required selected assets fail closed.
