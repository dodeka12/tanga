# Screen-space point markers — Overview

**Created:** 2026-09-29 | **Status:** Done | **Branch:** `fix/image-label-app`

## Goal

Let point markers (`SquarePointStyle`, `CirclePointStyle`, `IconPointStyle`,
`CrossHairPointStyle`) render at a constant **screen** size instead of a fixed
world/image-pixel size, so Act handles stay a consistent on-screen size no
matter how far the image is zoomed in or out.

## Architecture (short)

- **Flag** — `PointStyle` (`_styles/_entity_styles.py`) gains
  `screen_space: bool = False`; `to_dict()` emits `"screen_space": true` only
  when set.  When `screen_space=True`, the marker's `size` (and `thickness` /
  `arm_thickness`) are interpreted as **CSS pixels**.
- **Renderers** — the flat-marker renderers (`square_point.js`,
  `circle_point.js`, `icon_point.js`) and `crosshair_point.js` keep their
  current geometry build, but when `screen_space` is set they tag the mesh with
  `mesh.userData.isScreenSpace = true` so the view can rescale it without
  re-parsing styles.
- **View update** — `three-view.js` adds `_updateScreenSpaceMarkers()`, called
  each frame from `render()`.  It iterates the view's `sceneObjects`, finds
  screen-space marker meshes, and sets `mesh.scale = 1 / worldToScreenScale`
  per marker:
  - ortho (2D): `worldToScreenScale = viewportPx / ((top − bottom) / zoom)` —
    uniform.
  - perspective (3D): `worldToScreenScale = viewportPx / (2·dist·tan(fov/2))`
    (per-marker distance); flat markers also billboard
    (`quaternion.copy(camera.quaternion)`).
- **Opt-in** — Act handles (vertex/corner + translate/rotate) set
  `screen_space=True` on their `CirclePointStyle` / `IconPointStyle` styles.

## Decisions (confirmed)

- Add a `screen_space` flag (not reinterpret `size`), so the existing world-unit
  `size` behavior is preserved for regular points.
- Screen-space sizes are in **CSS pixels** (matching `LineMaterial.linewidth`).
- The view rescales markers by iterating its per-view `sceneObjects` (no global
  registry, no `scene.traverse`).
- The scale is per-marker and camera-type-aware, so Act entities also work in 3D
  (perspective distance + billboard).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-point-style-screen-space.md](./01-point-style-screen-space.md) | `PointStyle.screen_space` flag + serialization + tests |
| 2 | [02-renderers-screen-space.md](./02-renderers-screen-space.md) | screen-space tagging in the point renderers + scale helper |
| 3 | [03-view-rescale-markers.md](./03-view-rescale-markers.md) | per-frame `_updateScreenSpaceMarkers()` in the view |
| 4 | [04-handles-opt-in.md](./04-handles-opt-in.md) | Act handles opt in with `screen_space=True` |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | changelog + docs |

## Testing as you go

- Python: `uv run pytest py/tests/viz -q`
- JS: `node --test 'js/dev/tests/*.test.mjs'` and `node --check` on edited files
- Bundle: `uv run python tools/build-viewer-js.py` (after renderer edits) then `--check`
- Docs: `uv run python tools/generate-example-docs.py --check`

## Non-goals

- No new overlay/DOM layer for handles.
- No `gl_PointSize` / `THREE.Points` conversion (markers stay raycastable meshes).
- No per-marker depth sorting or occlusion handling changes.
