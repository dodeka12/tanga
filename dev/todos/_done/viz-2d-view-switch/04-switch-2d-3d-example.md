# Phase 4 — Checkbox 2D/3D switch example

## Goal

Add a runnable example that toggles a single scene between a flat 2D view and
a tilted 3D view with a `CheckboxView`.

## Files

- New: `py/examples/viz/camera/switch_2d_3d.py`
- New: `py/tests/viz/test_example_switch_2d_3d.py`

## Steps

- [x] **4.1 — Write the example**
  - Create `py/examples/viz/camera/switch_2d_3d.py` with the license header +
    `example-docs.md`-style docstring (description, `Run with:`, `Keywords:`).
  - `Visualizer(reuse_existing=False, title="Tanga — 2D/3D switch",
    space_dim=2, add_default_axes=False, add_default_grid=False)`.
  - Named scene `viz.scene("plot", space_dim=2, add_axes=False,
    add_grid=False)`; one `CoordinateSystem` sine plot
    (`xlim=(0, 2*pi)`, `ylim=(-1.2, 1.2)`, `labels=("x", "sin(x)")`).
  - Capture `cam_2d = scene.scene.config.camera` (the 2D camera the
    `CoordinateSystem` applied) and define a tilted
    `cam_3d = View3dConfig(point=(0,0,0), normal=(0.3,0.4,1.0),
    extent_u=8.0, extent_v=6.0, fov=50.0)`.
  - `layout = SceneView("plot", overlay=[GroupView("View mode",
    [CheckboxView("mode3d", label="3D", value=False, on_change=_on_3d)],
    position=EAnchor.TOP_LEFT)])`.
  - Async `_on_3d(value, _event)` calls
    `viz.set_space_dim(3 if value else 2, scene_name="plot",
    camera=cam_3d if value else cam_2d)`.
  - Guard the blocking tail with `if __name__ == "__main__":` around
    `viz.show(layout=layout)` + `viz.wait()`.

- [x] **4.2 — Non-interactive smoke test**
  - Add `test_example_switch_2d_3d.py` mirroring `test_example_split_view_app.py`
    (import via `importlib.util` from `_EXAMPLE_PATH`): assert the `"plot"`
    scene starts at `space_dim == 2`; then `module.viz.set_space_dim(3,
    scene_name="plot", camera=module.cam_3d)` flips it to `3`.

## Validation

`uv run ruff check py/examples/viz/camera/switch_2d_3d.py py/tests/viz/test_example_switch_2d_3d.py && uv run pytest py/tests/viz/test_example_switch_2d_3d.py -q && uv run python tools/generate-example-docs.py --check`

## Notes

- `CoordinateSystem` owns the camera in 2D (`camera="auto"`, default
  `border_px=60`), so `scene.scene.config.camera` is already the fitted
  `CameraConfig2d` after construction.
- Passing `cam_2d` (a `CameraConfig2d`) back into `set_space_dim(..., camera=…)`
  is fine — `_normalize_camera_config` passes `CameraConfig` through unchanged.
