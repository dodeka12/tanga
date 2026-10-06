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

- [x] **4.1 — Update `viz-architecture.md`**
  - The `CoordinateMapper` bullet now says `LabelMeStore` is a pure data store
    (plain geometry in/out) and the label apps own act creation.
- [x] **4.2 — Append the branch changelog**
  - Added `Refactor` bullets for the entity-only `LabelMeStore` and the
    `pixel_scale`-on-`ActSceneObject` move.
- [x] **4.3 — Full validation**
  - `pytest -q` (3708 passed, 1 skipped) + `mkdocs build --strict` (clean).

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- `docs/changelog/index.md` is updated at PR time, not now.
