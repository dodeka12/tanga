# Pixel↔world size mapping — Overview

**Created:** 2026-09-30 | **Status:** Done | **Branch:** `feat/calibrated-pane-interaction`

## Goal

Give the viewer **one clear home for "pixels → world size"** so every
scale-dependent computation (min radius/size, polygon auto-close tolerance,
rotate-handle offset) routes through it, and works identically for the image
canvas (`PlanarMapper`) and the calibrated image (`CalibratedPlaneMapper`).
This fixes the remaining calibrated-labeling scale bugs (ellipse start radius,
rotate-icon overlap, polygon endpoint snapping) and the hidden-handle
interaction bug, then diagnoses and fixes the regression where the calibrated
background image is no longer visible.

## Architecture (short)

Two *separate* pixel→world mappings, on opposite sides of the wire — they are
not the same quantity and never coexist in one namespace:

- **Backend — `CoordinateMapper`** (`pytanga.viz.camera`) maps **image pixels
  ↔ world** and nothing else.  Its `(u, v)` are the 2D image coordinates a
  labelme file stores; it never sees the screen or the viewport.  Two
  implementations of this one protocol:
  - `PlanarMapper` — `to_world(u, v) = Point(u, v, 0)` (image canvas: world == pixels).
  - `CalibratedPlaneMapper` — `to_world` casts `(u, v)` through the pinhole onto
    the plane at `depth`, then `camera_to_world`.
  - Add one method: `world_units_per_pixel() -> float` — the world size of one
    image pixel at the plane (`PlanarMapper` → `1.0`, `CalibratedPlaneMapper`
    → `depth / fx`).
- **Frontend — `screenWorldScale(camera, viewportPx, worldPos)`**
  (`camera-fit.js`) maps **screen pixels ↔ world** (zoom-aware).  It is a
  function, *not* a `CoordinateMapper`, and the backend never calls it.
  Screen-space markers already size through it.
- **Composites** (`_ActWithHandles` subclasses) gain a `pixel_scale: float =
  1.0` (world units per **image** pixel, sourced from `world_units_per_pixel()`)
  and convert handle-derived distances through it — never bare pixel/world
  literals.

### Data flow

```
image px (u,v) ──to_world / to_pixel──▶ world Point                    (labelme load/save, backend)
mapper.plane() ──serialized──▶ surface {point, normal}                  (sent to frontend)
mouse (clientX,clientY) → NDC → ray → ray ∩ plane() → world Point       (interaction, frontend)
marker size / drag delta  ← screenWorldScale(camera, viewportPx, …)     (frontend, zoom-aware)
```

The interactive path never calls `to_world` — it raycasts against the `plane()`
the backend provided.

### Fixed contract (decided up front)

1. `CoordinateMapper.world_units_per_pixel() -> float`
   (`PlanarMapper` = `1.0`, `CalibratedPlaneMapper` = `depth / fx`).
2. Composites add `pixel_scale: float = 1.0` (world units per camera pixel),
   stored as `self._pixel_scale`; a public `set_pixel_scale(value)` re-clamps
   nothing immediately (it only affects future resize/drag computations).
3. Handle-derived world distances use `handle_size_px = _resolve_handle_style().size`
   (fallback `6.0`) multiplied by `pixel_scale`:
   - polygon auto-close tolerance = `2 * handle_size_px * pixel_scale`
     (replaces `2 * size` which treated screen px as world units);
   - rotate-handle offset = `max(0.25 * max(hw, hh), 2 * handle_size_px *
     pixel_scale)` for rectangles/ellipses (proportional for large shapes,
     pixel-minimum for small shapes so it never overlaps the corner/radius
     handle);
   - `create_from_points` clamps the initial radius/size to `min_radius`/
     `min_size` when those are set (from `kwargs`).
4. `set_translate_handle_visible` / `set_rotate_handle_visible` also call
   `handle.set_enabled(visible)` so a hidden handle is not draggable.
5. The label apps compute `pixel_scale` from the mapper and set it on every
   shape (created **and** loaded), replacing the ad-hoc `0.5 * depth / fx`.
   The 0.5-camera-pixel minimum stays the same value, just routed through the
   mapper.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Decisions (confirmed)

- Pixel size for **min radius/size and auto-close tolerance** is **camera
  (image) pixels**, not screen pixels — so they are zoom-independent and share
  the single `world_units_per_pixel()` scale.  Screen-pixel sizing (6 px
  handles) stays on the frontend.
- The scale is a scalar (`depth / fx`), matching the existing `min_half`
  behaviour; `fx` is used (isotropic approximation, `fx ≈ fy`).
- The image regression is diagnosed **before** any fix (temporary debug in
  frontend + backend), per the user's instruction.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-coordinate-mapper-scale.md](./01-coordinate-mapper-scale.md) | Add `world_units_per_pixel()` to `CoordinateMapper` |
| 2 | [02-composite-size-mappings.md](./02-composite-size-mappings.md) | `pixel_scale` + create clamp + tolerance + rotate offset |
| 3 | [03-handle-visibility-and-styles.md](./03-handle-visibility-and-styles.md) | Hidden handles disabled; polygon end-handle styles |
| 4 | [04-label-apps-wire-scale.md](./04-label-apps-wire-scale.md) | Label apps compute the scale from the mapper |
| 5 | [05-image-debug-instrumentation.md](./05-image-debug-instrumentation.md) | Temporary frontend/backend debug for the image |
| 6 | [06-image-fix.md](./06-image-fix.md) | Fix the image regression, remove debug |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Developer docs + changelog |

## Testing as you go

```
uv run pytest py/tests/viz -q      # fast viz suite (per phase)
uv run pytest -q                   # full suite (before final phase)
node js/dev/tests/check-syntax.mjs # JS syntax after frontend edits
uv run mkdocs build --strict       # docs (final phase)
```

## Non-goals

- Changing the screen-space handle-marker sizing path (`_updateScreenSpaceMarkers`
  / `screenWorldScale`) — it is already correct.
- Moving the auto-close tolerance to the frontend (kept backend, camera-pixel
  based).
- Save/export of the calibrated labeling app.
