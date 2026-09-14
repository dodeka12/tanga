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
  centre handle translates, with overridable handlers.
- **Custom image shaders** — `ImageCanvas.register_shader()` replaces the standard
  brightness/contrast shader with a custom fragment shader; `register_uniform()` /
  `set_uniform()` drive arbitrary custom uniforms end-to-end.
- **Per-handler enable/disable + cursors** — active elements can register drag/click
  handlers disabled (`DragBinding`/`ClickBinding` ``enabled=``) and toggle them at
  runtime (`set_handler_enabled`/`set_click_enabled`/`refresh_interaction`), with
  optional hover (`ActSceneObject(cursor=…)`) and during-interaction
  (`InteractionConfig.cursor`) cursors plus a per-scene `set_cursor()` override.

## Doc Changes

- Reorganised the visualization docs to mirror `py/examples/viz`: a new
  `docs/py/viz/ui/` section consolidates controls, control views, layouts, split
  views, menus, dialogs, display views, banners, the file chooser, and themes
  (moved out of `app/`, `interaction/`, and `visualizer/`); `interaction/` now
  covers object interaction only, and `visualizer/` keeps the core viewer API.
- Added `docs/py/viz/image/` — `ImageCanvas` (`image-canvas.md`), custom shaders
  (`custom-shaders.md`), and drag/click interaction (`interaction.md`).
- Added `docs/py/ga/quadric/` — `BasisQ2`/`BasisQ3` bases, conic-space usage and
  visualization, and the point-tuple 7→8 Cayley–Bacharach effect.
