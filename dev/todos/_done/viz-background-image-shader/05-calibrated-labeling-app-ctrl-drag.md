# Phase 5 — Ctrl+left-drag brightness/contrast in the calibrated labeling app

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> — the `(id, event)` registry and `InteractionSurface`/`DragBinding` resolution).
>  This phase only edits an example; it introduces no new architecture.

## Goal

Update `py/examples/apps/calibrated_labeling_app.py` so holding **Ctrl** and
dragging with the **left mouse button** on the calibrated pane adjusts the
background's brightness (vertical) and contrast (horizontal), matching
`py/examples/viz/image/image_canvas.py`.

## Files

- Edit: `py/examples/apps/calibrated_labeling_app.py`
- Edit: `py/tests/viz/test_interaction_surface.py` (or `test_background_surface.py`)

## Steps

- [x] **5.1 — Add a Ctrl modifier drag binding to the calibrated surface.**
  - In `_CalibratedLabeler.__init__`, add a second
    `DragBinding(MouseButton.LEFT, self._on_brightness_contrast_drag, ModifierKey.CTRL)`
    and pass it in `CalibratedSurface(..., drag_bindings=[self._draw_binding, self._ctrl_binding])`.
  - Rename the existing draw binding to `self._draw_binding` for clarity (keep its
    `enabled=False` gating).

- [x] **5.2 — Implement the brightness/contrast handler.**
  - `async def _on_brightness_contrast_drag(self, event, _surface) -> bool`:
    read `dx, dy = event.delta_pixels`, read current uniforms from
    `viz.set_background_uniform`/the background `ImageView`, then
    `set_background_uniform("u_contrast", max(0.0, contrast + 0.005*dx))` and
    `set_background_uniform("u_brightness", brightness + 0.005*dy)`; return `True`.
  - `_CalibratedLabeler` needs a reference to the `Visualizer` (or a callback) to
    call `set_background_uniform` — thread it through the constructor.

- [x] **5.3 — Confirm the Ctrl binding wins over the draw binding.**
  - `InteractionSurface._resolve_drag_handler` picks the most specific binding, so
    `{CTRL}` beats the modifier-less draw binding; verify a Ctrl+drag does not
    create a shape and a plain drag still draws (no behavior regression in draw mode).

- [x] **5.4 — Tests.**
  - Add a case in `test_interaction_surface.py` (or `test_background_surface.py`)
    asserting a `DragBinding(LEFT, handler, ModifierKey.CTRL)` on a
    `CalibratedSurface` resolves to the Ctrl handler over the general/draw handler.

## Validation

`uv run pytest py/tests/viz/test_interaction_surface.py py/tests/viz/test_background_surface.py -q`

## Notes

- Manual smoke: `uv run python py/examples/apps/calibrated_labeling_app.py` — Ctrl
  + left-drag on the left pane changes brightness/contrast; the draw toolbar and
  the "Noise image"/"Swap views" controls keep working.
- Keep the `0.005` scale factors in sync with `image_canvas.py::on_drag` for a
  consistent feel.
