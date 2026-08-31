# Phase 8 — Docs + changelog

## Goal

Document the new entities, their styles, and the SDF availability; add the
branch changelog.

## Files

- Modify: `docs/py/geometry/entities.md`
- Modify: `docs/py/viz/sdf-objects.md`
- New: `docs/changelog/YYYY-MM-DD_feat-geo-objects.md` (see `dev/workflows/changelog.md`)

## Steps

- [x] **8.1 — `docs/py/geometry/entities.md`**
  - Extend the "Visualization-only entities" section with `Disk`, `PartialDisk`,
    `Box`, `Ellipsoid`, `Ellipse`, `RegularPolygon` (+ the `regular_polygon()`
    factory), with a field table and a short usage snippet for each.
  - Note the 2D convention (`normal` defaults to `+z`; use with
    `Visualizer(space_dim=2)`).

- [x] **8.2 — `docs/py/viz/sdf-objects.md`**
  - Extend the per-entity style table with the six new `Sdf*Style` classes and
    their knobs (`thickness` where applicable).
  - Note the two new SDF primitives (`partialDisk`, `regularPolygon`) available
    from `pytanga.viz.sdf`.

- [x] **8.3 — Changelog**
  - Create `docs/changelog/YYYY-MM-DD_feat-geo-objects.md` per
    `dev/workflows/changelog.md` (use `# Changes since version <last-stable>`
    from `uv run python tools/last-release.py`; `## New Features` section
    describing the six entities + two SDF primitives + style classes).
  - Do **not** touch `docs/changelog/index.md` (that happens at PR time).

- [x] **8.4 — Validate**
  - `uv run python -c "import pytanga.geometry, pytanga.viz; ..."` smoke check
    that the new public names import cleanly.

## Validation

`uv run python -c "from pytanga.geometry import Disk, PartialDisk, Box, Ellipsoid, Ellipse, RegularPolygon, regular_polygon; from pytanga.viz import DiskStyle, BoxStyle, EllipsoidStyle, SdfDiskStyle, SdfBoxStyle; print('ok')"`

## Notes

- Keep doc snippets consistent with the README wire contract and field names.
- Changelog bullets follow the `- **Headline** — sentence` style, wrapped at
  ~80 columns.
