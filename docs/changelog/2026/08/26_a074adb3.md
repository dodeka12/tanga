# Changes since version 1.4.0

## New Features
- **`ActPoint` drag lifecycle handlers** — `ActPoint` (and the
  `ActSceneObject` base) now accepts `on_drag_start=` / `on_drag_end=`
  callbacks in addition to the existing move-phase `handler=`.  These are
  registered directly with the act-point instance and fire on
  `DRAG_START` / `DRAG_END` events as pure notifications (their return
  value is ignored, so they never override the default movement).
- **`clear()` re-add options** — `Visualizer.clear()` and
  `VizSceneHandle.clear()` accept `add_axes=` / `add_grid=` flags to re-add
  the default coordinate axes / grid after clearing (default `False` leaves
  the scene empty; re-add is subject to the visualizer's
  `add_default_axes` / `add_default_grid` constructor flags).
- **`ActPoint` label support** — `viz.add(ActPoint(...), label=...)` now
  creates an attached label, matching the regular entity path (including
  `label_style`, `attach_to`, and `parent_id`).

## Bug Fixes
- **2D pointer interaction (`ActPoint` drag & hover)** — interactive objects
  in `space_dim=2` scenes were unresponsive because the interaction module
  kept the initial perspective camera after the view switched to an
  orthographic camera (so raycast hits always missed), and the drag
  screen-plane scale used the perspective FOV, which is `undefined` for
  orthographic cameras (producing NaN deltas).  The interaction module now
  tracks the live camera, and drag scaling falls back to the orthographic
  frustum height in 2D.
- **Removing an entity now removes its attached labels** — `Scene.remove()`
  (and therefore `Visualizer.remove()` / `VizSceneHandle.remove()`) also
  removes labels attached via `parent_id` to the removed object or any of its
  descendants, so labels no longer leak after their parent is removed.
