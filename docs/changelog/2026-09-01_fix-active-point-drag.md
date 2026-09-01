# Changes since version 1.13.0

## New Features
- **`on_click` handler on `ActSceneObject` / `ActPoint`** — active objects now
  accept an `on_click(event, obj)` callback; providing it registers a `CLICK`
  trigger and dispatches a `ClickEvent` whose `world_position` is the ideal
  point (the object's centre) rather than the raw mesh-surface hit.

## Bug Fixes
- **`ActPoint` drag-start reports the ideal point, not the mesh hit** — the
  `DRAG_START` event (and `on_drag_start` handler) now receives the ideal
  anchor from `drag_anchor()` instead of the raw raycast hit on the rendered
  sphere, so a 2D point no longer carries a spurious off-plane z-component at
  drag start.
- **2D drags track the mouse when zoomed** — the pixel→world scale for
  orthographic (2D) cameras now divides by `camera.zoom`, so an `ActPoint`
  stays under the cursor after zooming instead of moving with a fixed,
  pre-zoom world scale.
- **A stationary click no longer emits `drag_end`** — `drag_end` is only sent
  once a drag has actually started (the pointer moved); a plain press-and-
  release on an `ActPoint` now falls through to click detection instead of
  reporting a spurious drag end.
- **`clear_controls()` no longer wipes entity interaction handlers** — the
  shared `(id, event)` handler registry now tags each entry with its origin
  (`control` vs `interaction`), so `clear_controls()` removes only panel
  control handlers and leaves `on_interaction` / `ActPoint` drag and click
  handlers intact regardless of call order.
