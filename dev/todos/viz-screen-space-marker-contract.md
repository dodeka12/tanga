# Screen-space marker contract — single owner for scale, hover, and layering

**Created:** 2026-10-22 | **Status:** Done | **Branch:** `fix/act-points`

## Goal

Consolidate the frontend handling of screen-space point markers so a marker's
world placement (its `THREE.Group` transform) and its screen-space size (scale +
hover multiplier + draw order) each have exactly one owner and one code path.
This removes the recurring `entry.obj` (transform wrapper) vs `entry.mesh`
(marker leaf) split that caused hover-scale compounding and zoom-dependent
parallax drift.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Fixed contract (decided up front)

- `isScreenSpace` and `_hoverScale` live on the marker **leaf**, never on the
  wrapper `Group`.
- The wrapper `Group` carries only the entity `Transform` (canonical frame +
  placement) — see `docs/dev/architecture/viz-architecture.md` § "Canonical
  frame + transform placement".
- `_updateScreenSpaceMarkers()` is the **only** writer of the leaf `scale` each
  frame; it computes `screenWorldScale(...) * (_hoverScale || 1)`.
- Hover sets/clears `_hoverScale` on the leaf (via `_screenSpaceLeaf`) and never
  mutates `scale`; `unregisterInteractive`/`clearAllInteractive` reset hover.
- Flat overlay markers (circle/icon) layer above coplanar bodies / a standard
  point via `renderOrder = 1` + `polygonOffset` (factor/units `-1`), never a
  world-space `z` lift.  `SquarePointStyle`/`CrossHairPointStyle` are 3D markers
  and keep `renderOrder`/`polygonOffset` defaults.

## Steps

- [x] **1 — Extract the screen-space tag + layering into a shared helper**
  - Add `tagScreenSpaceMarker(mesh, screenSpace, { layered = false })` to
    `py/pytanga/viz/templates/renderers/utils.js`: set
    `mesh.userData.isScreenSpace = true`, and when `layered` also set
    `renderOrder = 1` + `polygonOffset` (`factor = -1`, `units = -1`) on
    `mesh.material` (guarded, since the crosshair is a `Group` with no material).
  - Use it in `circle_point.js`/`icon_point.js` with `{ layered: true }`, and in
    `square_point.js`/`crosshair_point.js` with the default (tag only).
  - Validation: `node js/dev/tests/check-syntax.mjs`.

- [x] **2 — Document the contract in the developer docs**
  - Add a short "Screen-space markers" note in
    `docs/dev/architecture/viz-architecture.md` (next to the screen-pixel sizing
    / `screenWorldScale` mention): leaf owns `scale` + `_hoverScale`; single
    per-frame sizing path; depth-bias layering for flat markers.
  - Validation: `uv run mkdocs build --strict`.

- [x] **3 — Rebuild the viewer bundle and validate the frontend**
  - Run `uv run python tools/build-viewer-js.py` (regenerates
    `js/tanga-viewer.js` + manifest from the renderer sources).
  - Run `node js/dev/tests/check-syntax.mjs`,
    `node --test 'js/dev/tests/*.test.mjs'`, and
    `uv run python tools/build-viewer-js.py --check`.
  - Validation: the three commands above all exit clean.

- [x] **4 — Branch changelog**
  - Add `docs/changelog/2026/10/22_fix-act-points.md` per
    `dev/workflows/changelog.md`, covering the screen-space marker fixes and the
    consolidation (Bug Fixes / Refactor bullets; title
    `# Changes since version 2.22.0 (2.23.0-rc3)` from `tools/last-release.py`).
  - Validation: `uv run mkdocs build --strict`.

## Testing as you go

```
node js/dev/tests/check-syntax.mjs
node --test 'js/dev/tests/*.test.mjs'
uv run python tools/build-viewer-js.py --check
uv run mkdocs build --strict
```

## Non-goals

- No shader-based screen-space sizing.
- No change to the Python `ActPoint`/style API or the wire format.
- No change to `square_point.js`/`crosshair_point.js` layering (3D markers that
  do not z-fight flat coplanar bodies).
