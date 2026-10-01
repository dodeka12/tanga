# Pointer event contract — unified fields + pixel frame — Overview

**Created:** 2026-10-01 | **Status:** Done | **Branch:** `feat/calibrated-pane-interaction`

## Goal

Make click and drag events carry the **same position fields in the same
coordinate frame**, so custom handlers (like the calibrated labeler's
click-to-place point) never receive a world position that was silently
recomputed in a different pixel frame.  Fixes the bug where a click-created
point appears below the cursor while drag-created shapes land correctly.

## Architecture (short)

Two small inconsistencies caused the bug:

1. **`screen_position` was client/viewport coords, not canvas-local.**  The
   frontend raycaster uses `(clientX - rect.left, clientY - rect.top)`, but the
   payloads sent raw `[clientX, clientY]`.  This was masked for drags (they use
   the raycast `world_position`; `delta_pixels` is relative) and only exposed
   when the backend fed `screen_position` into `pixel_ray` for clicks.
2. **Click did not carry the picking ray.**  `DragEvent` has `ray_origin` /
   `ray_direction`; `ClickEvent` did not.  So `_resolve_click_anchor`
   reconstructed the ray via `pixel_ray(screen_position)` (wrong frame) instead
   of using the frontend's ray like `_send_drag_anchor` does.

The fix unifies both, while keeping the "ideal anchor" recompute for active
objects (e.g. `ActPoint`'s center) intact.

### Fixed wire contract (decided up front)

- Every pointer-interaction event (`click`, `dblclick`, `drag_start`,
  `drag_move`, `drag_end`) sends `screen_position` in **canvas-local** pixel
  coordinates: `[clientX - rect.left, clientY - rect.top]` (top-left origin of
  the renderer canvas).  Relative fields (`delta_pixels`, `world_delta`) stay
  frame-independent deltas and are unchanged.
- `click` and `dblclick` now carry `ray_origin` / `ray_direction` (the picking
  ray), exactly like `drag_start`.
- The backend resolves the ideal anchor for click **and** drag_start from the
  **frontend's ray**: `act.click_anchor(ray_origin, ray_direction)` /
  `act.drag_anchor(ray_origin, ray_direction)`.  No more
  `event.camera.pixel_ray(screen_position)` reconstruction.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Decisions (confirmed)

- Add `ray_origin`/`ray_direction` to `ClickEvent` (parity with `DragEvent`)
  rather than a new event subtype.
- Keep the backend `click_anchor`/`drag_anchor` recompute — it is what resolves
  the ideal anchor for active objects.  Only its *input* changes (frontend ray
  instead of `pixel_ray`).
- `screen_position` becomes canvas-local everywhere; `delta_pixels`/`world_delta`
  are untouched (already frame-independent).
- The surface/mapper plane stays where it is (`mapper.plane()` on the backend,
  serialized as `{point, normal}` and used by `_getSurfaceHit`).  No change to
  `_surface.py` or the mapper.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-frontend-pixel-frame-click-ray.md](./01-frontend-pixel-frame-click-ray.md) | JS: canvas-local `screen_position` + click/dblclick ray |
| 2 | [02-backend-click-event-model.md](./02-backend-click-event-model.md) | Python: `ClickEvent.ray_origin/ray_direction` + parse |
| 3 | [03-backend-click-anchor-resolution.md](./03-backend-click-anchor-resolution.md) | Python: `_resolve_click_anchor` uses the event ray + tests |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Update architecture docs + changelog |

## Testing as you go

```
node js/dev/tests/check-syntax.mjs            # JS (phase 1)
uv run pytest py/tests/viz -q                  # viz suite (phases 2-3)
uv run pytest -q                               # full (final phase)
uv run mkdocs build --strict                   # docs (final phase)
```

## Non-goals

- Changing `delta_pixels` / `world_delta` (already relative).
- Removing `Camera.pixel_ray` (it stays as a general utility).
- Changing the `InteractionSurface` / mapper plane serialization.
