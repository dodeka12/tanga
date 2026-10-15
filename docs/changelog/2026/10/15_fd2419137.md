# Changes since version 2.19.0

## Bug Fixes
- **`VIEW_PLANE` drags no longer overshoot under perspective cameras** — the
  frontend pixel→world scale now uses the handle's depth along the camera's
  view axis instead of its Euclidean distance from the camera, so handles and
  screen-space markers track the pointer correctly across the frame.
- **Ctrl+drag on a polygon vertex inserts again** — polygon vertex handles now
  register a Ctrl drag binding, so Ctrl+left-drag routes to the vertex handler
  (insert a new vertex) instead of falling through to the pane's interaction
  surface (for example the calibrated labeling app's brightness/contrast).
- **Ctrl+drag no longer creates a shape in the calibrated labeling app** — the
  drag-start/drag-end shape-creation handlers now skip shape creation when Ctrl
  is held, so Ctrl+drag only adjusts the background brightness/contrast.
- **Zoom no longer detaches a dragged point from the pointer** — the viewport
  crop wheel handler now ignores the wheel while a drag is in progress, so a
  dragged point or shape stays under the pointer instead of drifting when the
  camera zooms.
