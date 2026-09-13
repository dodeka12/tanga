# Changes since version 2.3.0 (2.4.0-rc3)

## New Features
- **Image display via `ImageCanvas`** — display numpy (`uint8`/`uint16`/`float32`,
  1/3/4-channel) and PIL images on a shader-drawn plane with a pixel-coordinate
  frame (y-down, 1 unit = 1 pixel), per-image shaders/uniforms, mouse-driven
  uniform updates, and raw binary image transfer over the existing WebSocket.
- **`DragBinding` / `ClickBinding` handlers** — bind several drag/click handlers
  to specific mouse-button + modifier combos on an `ImageCanvas` (most specific
  wins, falling back to the general `on_drag`/`on_click`), replacing the single
  `drag_button`/`drag_modifiers` pair.  Handlers receive the `ImageCanvas` as
  their context argument, so no holder dict or closure is needed.
- **Rebindable camera controls** — `ImageCanvas(..., controls={...})` maps mouse
  buttons to pan/dolly/rotate, overriding the 2D/3D defaults.
- **Interactive rectangles** — a `Rectangle2D` entity (outline + optional fill,
  `Rectangle2DStyle`), square point markers (`SquarePointStyle`), and
  `ActRectangle2D` — a composite active object whose corner handles resize and
  centre handle translates, with overridable handlers.  `ImageCanvas.draw_rectangle()`
  drags out a preview and finalizes it into an `ActRectangle2D`.
