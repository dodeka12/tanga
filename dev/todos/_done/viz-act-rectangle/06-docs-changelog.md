# Phase 6 — Docs + changelog

## Goal

Document the new entity, style, interactive object, and draw flow; update the
architecture docs and the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md` (new entity kind recipe note)
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md` (interactive
  objects + square style)
- Edit: `docs/changelog/2026/09/13_feat-image-view.md` (append)
- Edit: `docs/py/geometry/entities.md` (add `Rectangle2D`)
- Edit: `py/pytanga/viz/__init__.py` (final export sweep, if not done earlier)

## Steps

- [x] **6.1 — architecture docs**
  - `viz-architecture.md`: add `Rectangle2D` to the entity file map / extension
    recipe example; note `ActRectangle2D` is a composite of `ActPoint` handles.
  - `viz-controls-and-interactions.md`: document `ActRectangle2D` + `SquarePointStyle`
    under "Interactive objects".

- [x] **6.2 — public docs**
  - Add a short `Rectangle2D` + `ActRectangle2D` + `draw_rectangle` usage section
    to `docs/py/geometry/entities.md` (and the viz overview if applicable).

- [x] **6.3 — changelog**
  - Append to `docs/changelog/2026/09/13_feat-image-view.md` per
    `dev/workflows/changelog.md` (New Features bullets).

## Validation

`uv run mkdocs build --strict && uv run pytest py/tests/viz -q && uv run ty check`

## Notes

- Final export sweep: confirm `Rectangle2D`, `Rectangle2DStyle`,
  `SquarePointStyle`, and `ActRectangle2D` are all importable from their public
  packages (`pytanga.geometry` / `pytanga.viz`).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
