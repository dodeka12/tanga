# Phase 8 — Docs + changelog

## Goal

Document the new `underlay` layer + overlay/underlay renderer seams in the
developer architecture docs and record the change in the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- New: `docs/changelog/2026/09/19_cs-2d.md` (branch changelog; final name per
  `dev/workflows/changelog.md`)

## Steps

- [x] **8.1 — architecture docs**
  - `viz-architecture.md`: add the `layer="underlay"` value + `axes-overlay.js` /
    `grid-underlay.js` / `nice-ticks.js` / `axes-overlay-math.js` to the file map,
    and an "overlay coordinate system" extension recipe (underlay container →
    transparent WebGL → CSS2D labels → overlay DOM; two camera-driven objects).
  - `viz-controls-and-interactions.md`: note the `axes_overlay` / `grid_underlay`
    objects carry a static spec and read the camera (no event/control entries).

- [x] **8.2 — public API docs**
  - Document `CoordinateSystem.display_mode` (`"world"` / `"overlay"`) and the 2D
    / no-`size` constraint on the relevant public docs page.

- [x] **8.3 — changelog**
  - Per `dev/workflows/changelog.md`: create the branch changelog with the
    since-relative title from `uv run python tools/last-release.py`, and a
    `## New Features` bullet for the 2D overlay coordinate system (overlay axes +
    underlay grid, incl. standalone-HTML export).

- [x] **8.4 — full validation**
  - `uv run pytest -q` and `uv run mkdocs build --strict`.

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- The changelog filename uses the branch name (`cs-2d`) and is renamed to the
  hash form at PR time per `dev/workflows/pull-request.md` — do not predict the
  version number.
- If Phase 6 introduced a new bundle seam, reflect it in `viz-architecture.md`
  here (single source of truth for the file map).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
