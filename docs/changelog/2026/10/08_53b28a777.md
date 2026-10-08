# Changes since version 2.18.0 (2.18.1-rc1)

## Bug Fixes
- **Calibrated background image zoom now fills the pane** — zooming a
  `CameraView(…, navigation="2d", background_image=…)` pane scales the image up
  to fill the pane (the letterbox bars shrink, then crop at the edges) instead
  of pinning it to the initial fit size, keeping the 3D overlay pixel-locked to
  the image.
- **Vertical drag pans the calibrated image at the mouse speed** — panning and
  cursor-anchored zoom now scale the pan delta per axis by the base fit
  half-extents, so the image follows the pointer equally on both axes instead of
  lagging along the letterboxed axis in a non-square pane.
- **Smooth pane resizing without WebGL flicker** — resizing the window or
  dragging a splitter now stretches the last rendered frame (CSS-only) and
  freezes rendering until the size settles, then reallocates the drawing buffer
  and repaints once, instead of clearing it on every layout tick (which blanked
  and flickered the canvas until the drag ended).
