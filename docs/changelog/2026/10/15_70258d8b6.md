# Changes since version 2.18.0 (2.18.1-rc2)

## New Features

- **Background image shaders** — a calibrated `CameraView.background_image` now
  renders with the same brightness/contrast (and value-range) colour pipeline as
  `ImageCanvas`; `Visualizer.register_background_shader` /
  `register_background_uniform` / `set_background_uniform` drive custom shaders
  and uniforms via a granular `view_background_uniforms` message (no pixel
  re-send, no layout re-push).
- **Ctrl+drag brightness/contrast** — `calibrated_labeling_app.py` adjusts the
  background's contrast (horizontal) and brightness (vertical) while holding
  Ctrl and dragging with the left mouse button, matching the `ImageCanvas`
  demos.

## Bug Fixes

- **Exact trigger modifier matching + hit fall-through** — a trigger with no
  `modifiers` now fires only when no modifier keys are held (previously it
  matched *any* modifier), and pointer gestures now fall through to the pane's
  interaction surface when nearer entities do not register the gesture;
  ctrl+left-drag brightness/contrast now also works over label entities.
