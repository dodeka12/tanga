# Phase 1 — `*View` / `add_*` feature parity

## Goal

Make the `SliderView` / `ButtonView` / `CheckboxView` view classes and their
`add_slider` / `add_button` / `add_checkbox` panel counterparts expose the exact
same features, and make `control_to_view` a complete lossless wrapper. No
behavior change to rendering or registration yet — this phase only widens the
parameter surface.

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_scene_handle.py`

## Steps

- [x] **1.1 — `SliderView.on_press` / `on_release` (`views.py`)**
  - Add `on_press: Handler | None = None` and `on_release: Handler | None = None`
    to `SliderView.__init__` and forward both into the wrapped `Slider(...)`
    (alongside the existing `on_change`).

- [x] **1.2 — Complete `control_to_view` (`views.py`)**
  - In the `Slider` branch, forward `on_press=ctrl.on_press` and
    `on_release=ctrl.on_release`.
  - Audit every branch so each `*View` receives **all** fields of its `Control`
    (no silent drops).

- [x] **1.3 — `add_slider` / `_add_scene_slider` / `VizSceneHandle.add_slider` gain `variant`**
  - Add `variant: EControlVariant = EControlVariant.DEFAULT` and pass it through
    to the `Slider(variant=...)` construction in `_add_scene_slider`.
  - Mirror the parameter in `VizSceneHandle.add_slider` and its forwarding call.

- [x] **1.4 — `add_button` / `_add_scene_button` / `VizSceneHandle.add_button` gain `variant`**
  - Add `variant: EControlVariant = EControlVariant.DEFAULT`, forward to
    `Button(variant=...)`, and mirror in `VizSceneHandle.add_button`.

- [x] **1.5 — `add_checkbox` / `_add_scene_checkbox` / `VizSceneHandle.add_checkbox` gain `variant`**
  - Add `variant: EControlVariant = EControlVariant.DEFAULT`, forward to
    `Checkbox(variant=...)`, and mirror in `VizSceneHandle.add_checkbox`.

## Validation

```
uv run pytest py/tests/viz/test_views.py py/tests/viz/test_controls.py py/tests/viz/test_layout_api.py -q
```

## Notes

- `Slider`, `Button`, and `Checkbox` already carry `variant` in `_controls.py`;
  this phase only surfaces it on the `add_*` API and press/release on the view.
- Keep `add_*` signatures keyword-only after `cid` (existing convention).
