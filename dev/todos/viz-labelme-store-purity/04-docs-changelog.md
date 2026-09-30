# Phase 4 — Docs + changelog

## Goal

Update the developer docs for the entity-only store and append the branch
changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/changelog/2026/09/30_feat-calibrated-pane-interaction.md`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [ ] **4.1 — Update `viz-architecture.md`**
  - The `CoordinateMapper`/`LabelMeStore` text now says `LabelMeStore` maps
    labelme ↔ plain geometry, and the label apps own act creation.
- [ ] **4.2 — Append the branch changelog**
  - Add a `Refactor` bullet: `LabelMeStore` is entity-only; the label apps wrap
    entities into acts.  Add a `Bug Fixes` bullet for the `pixel_scale` base move.
- [ ] **4.3 — Full validation**
  - Run the full suite + docs build.

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- `docs/changelog/index.md` is updated at PR time, not now.
