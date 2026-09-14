# Phase 11 — Docs + changelog

## Goal

Update the developer architecture docs for the new seams (binary frame protocol,
export asset store, `ImageView`/`ActImagePlane`/`ImageCanvas`), and record the
change in the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- New: `docs/changelog/2026/09/13_feat-image-view.md` (branch changelog)
- (optional) Edit: public docs under `docs/py/viz/`

## Steps

- [x] **11.1 — architecture docs**
  - `viz-architecture.md`: add `ImageView`/`ImageCanvas`/`ActImagePlane` to the
    file map and an "image canvas" extension recipe (dedicated 2D scene, y-down
    pixel frame, overlay group).
  - `viz-controls-and-interactions.md`: document the binary image frame protocol
    and the image-plane interaction pattern (plane raycast → pixel coords →
    uniform), noting the JSON-only uniform/overlay update rule.

- [x] **11.2 — public API docs**
  - If `docs/py/viz/` has a plotting/coordinate-system page, add an `ImageCanvas`
    page or section; otherwise note it in `viz-architecture.md` only.

- [x] **11.3 — changelog + index**
  - Per `dev/workflows/changelog.md`: create the branch changelog with the
    since-relative title from `uv run python tools/last-release.py`, a `## New
    Features` bullet (image display via `ImageCanvas`), and any `## Breaking
    Changes`/`## Refactor` that apply; leave `docs/changelog/index.md` for PR
    time.

- [x] **11.4 — full validation**
  - `uv run pytest -q` and `uv run mkdocs build --strict`.

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- The changelog filename uses the branch name (`feat-image-view`) and is renamed to
  the hash form at PR time per `dev/workflows/pull-request.md` — do not predict
  the version number.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
