# Phase 7 — Docs + changelog

## Goal

Document the two viz-only entities and their styles, and record the change per
`dev/workflows/changelog.md`.

## Steps

- [x] **7.1 — Docs `docs/py/geometry/entities.md`**
  - Add a "Visualization-only entities" section for `Cylinder` and `Arc`:
    - `Cylinder(origin, axis, length, radius)` with the center-based `origin`
      semantics.
    - `Arc(origin, axis, radius, tube_radius, angle=2π, start_direction=None,
      show_arrow=False, arrow_length=None, arrow_radius=None)`, noting `angle`
      is **radians** and `start_direction` is auto-computed when omitted.
    - Note both are **not** convertible to multivectors (no MV representation,
      excluded from the Entity coverage matrix).

- [x] **7.2 — Docs `docs/py/viz/styles/styles.md`**
  - Add `CylinderStyle` / `ArcStyle` to the style-class list and to the
    wireframe-capable styles (`wireframe`, `wireframe_dash`, `wireframe_color`,
    `wireframe_opacity`).

- [x] **7.3 — `docs/changelog/2026-08-24_feat-multi-view.md`**
  - Append a New Features bullet (under the existing `## New Features`):
    `- **Viz-only geometry entities** — `Cylinder` and `Arc` (arcing cylinder
    with optional cone arrow tip, radians angle) with `CylinderStyle`/`ArcStyle`
    defaults and Three.js renderers.`

- [x] **7.4 — Validate**
  - `uv run mkdocs build --strict` (note any pre-existing warnings separately).

## Validation

`uv run mkdocs build --strict`.

## Notes

- Do **not** predict a release version; the changelog title already reads
  `# Changes since version 1.0.1`.
- The changelog is renamed to its hash form at PR time
  (`dev/workflows/pull-request.md`).
