# Phase 4 — `ImageCanvas` backend helper

## Goal

The user-facing helper (analogous to `CoordinateSystem`) that owns a dedicated
2D scene, the `ImageView`, the `ActImagePlane`, and an overlay `VizGroup`, and
exposes the public API: `set_image`/`add_image`, `set_uniform`,
`register_shader`/`register_uniform`, overlay `add`/`update`/`remove`/`clear`,
and mouse handlers.

## Files

- Edit: `py/pytanga/viz/_image_view.py` (`ImageCanvas` part)
- Edit: `py/pytanga/viz/__init__.py` (re-export `ImageCanvas`)
- New: `py/tests/viz/test_image_canvas.py`

## Steps

- [x] **4.1 — `ImageCanvas.__init__`**
  - Build a `View2DConfig` framing the pixel frame (extent = `frame` with a
    small `border_px`), `stretch="fit"` by default, and a `Scene`/scene handle
    owned by the canvas (dedicated scene name from a counter, e.g. `imgc0`).
  - Establish the **y-down pixel frame**: the image plane and overlay group are
    placed so world `(px, py)` = pixel `(px, py)` (y increasing downward).

- [x] **4.2 — overlay group + draw API**
  - A `VizGroup` in the pixel frame; `add`/`update`/`remove`/`clear` delegate to
    it (any drawable entity, like `CoordinateSystem`).

- [x] **4.3 — image/shader/uniform API**
  - `set_image`, `add_image`, `set_uniform`, `register_shader`,
    `register_uniform` forward to the `ImageView`.

- [x] **4.4 — interaction + handlers**
  - Own an `ActImagePlane`; expose `on_click`/`on_drag`/`on_drag_start`/
    `on_drag_end` plus `on_interaction(event_type, handler)`; default handlers
    read `world_position` (pixel coords) and may call `set_uniform`.

- [x] **4.5 — scene surface + framing**
  - `scene_view()` returns a `SceneView` referencing the dedicated scene (for
    `SplitView` placement); `fit_to_image()` sets the camera to the pixel frame.

- [ ] **4.6 — re-export + tests**
  - Re-export `ImageCanvas`.
  - `py/tests/viz/test_image_canvas.py`: scene creation, frame camera config,
    overlay delegation, uniform forwarding, and that `scene_view()` references
    the dedicated scene.

## Validation

`uv run pytest py/tests/viz/test_image_canvas.py -q && uv run ruff check py/pytanga/viz/_image_view.py py/tests/viz/test_image_canvas.py`

## Notes

- `ImageCanvas` imports `Scene`/`VizGroup`/`ActImagePlane` lazily inside methods
  to avoid circular imports (mirrors `CoordinateSystem`'s lazy imports).
- Transport/serialization wiring (sending the image entity + binary bytes) is
  deliberately deferred to Phases 5–7.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
