# View-plane drag scale (depth vs Euclidean distance) — Overview

**Created:** 2026-10-15 | **Status:** Done | **Branch:** `fix/view-plane-drag-scale`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`) for the subsystem(s) this work touches, so the new
> code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Make `VIEW_PLANE` drags (and screen-space marker sizing) use the correct
world-units-per-pixel scale under a **perspective camera**: the depth of the
dragged point *along the camera's view axis*, not its Euclidean distance from
the camera.  Resolves `_input/pytanga-view-plane-drag-scale.md`.

## Background / root cause

`screenWorldScale(camera, viewportPx, worldPos)` (`py/pytanga/viz/templates/camera-fit.js`)
computes the perspective scale from `dist = |worldPos - camera.position|`
(Euclidean), but the frustum height it multiplies is defined at a distance
*along the view axis*.  For a handle at angle `θ` off the optical axis,
`dist = depth / cos θ`, so the scale — and therefore the pixel→world drag delta —
is too large by `1 / cos θ`.  The error grows with distance from the image
centre and with drag length, which is exactly the reported overshoot.

`interaction.js` feeds this scale into `_computeScreenPlaneVectors` (the
`screenDx`/`screenDy` used by `_onPointerMove` / `setDragAnchor`), and
`views/three-view.js` uses the same helper for screen-space point markers.  Both
must switch to depth.

## Architecture (short)

- **Frontend only** (`py/pytanga/viz/templates/…` + the generated
  `js/tanga-viewer.js` bundle).  No Python behaviour change, no wire/schema
  change, no new `DragMode`/interaction seam.
- **Fixed contract:** `screenWorldScale(camera, viewportPx, worldPos, forward)`
  gains an optional 4th `forward` argument `{x, y, z}` (the camera's view
  direction, unit length).  The perspective branch computes
  `depth = |dot(normalize(forward), worldPos - camera.position)|` and uses it in
  both the pinhole-frustum branch and the `fov` branch.  When `forward` is
  omitted it falls back to the current Euclidean distance (preserves existing
  callers/tests).
- Callers pass `forward`: `interaction.js` uses the negated `extractBasis`
  third column (Three.js cameras look down local -Z); `three-view.js` uses
  `camera.getWorldDirection(...)`.

## Decisions (confirmed)

- Fix the shared `screenWorldScale` helper (fixes drags **and** markers at once)
  rather than reimplementing `VIEW_PLANE` as ray/plane intersection (larger,
  and doesn't fix markers).
- Add an **optional** `forward` param with a Euclidean-distance fallback (rather
  than making it required or deriving it from `camera.matrixWorld`) so the pure
  Node tests and any `forward`-less caller keep working.
- No Python change; the `Act*` handlers already consume the frontend's
  `world_position`/`world_delta`, so correcting the frontend scale is sufficient.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-screen-world-scale-depth.md](./01-screen-world-scale-depth.md) | Depth-based `screenWorldScale` + Node regression tests |
| 2 | [02-wire-callers.md](./02-wire-callers.md) | Pass the view direction from `interaction.js` and `three-view.js` |
| 3 | [03-rebuild-bundle.md](./03-rebuild-bundle.md) | Regenerate `js/tanga-viewer.js` + manifest |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Architecture-doc note + branch changelog |

## Testing as you go

- `node --check py/pytanga/viz/templates/camera-fit.js py/pytanga/viz/templates/interaction.js py/pytanga/viz/templates/views/three-view.js`
- `uv run pytest py/tests/viz/test_camera_fit_math.py -q`  (Node-executed math tests)
- `uv run pytest py/tests/viz -q`
- `uv run python tools/build-viewer-js.py --check`  (bundle drift gate)
- `uv run ruff check py/`  +  `uv run ruff format --check` on touched files

## Non-goals

- No browser/instrumented verification (a manual Playwright smoke may be run
  separately — see `docs/dev/workflows/js-frontend-testing.md`); the fix is
  pinned deterministically by the Node math tests.
- No change to `Act*` Python geometry or handle `drag_mode`; no rework of the
  `drag_anchor` / `setDragAnchor` protocol.
- No removal of the Euclidean fallback path for `forward`-less callers.
