# Phase 6 — Example script (phase-shifted 2D sin surface)

> **Architecture note — check the developer docs.** Before implementing, check
> `dev/workflows/example-docs.md` (header/`Keywords:` contract) and
> `docs/dev/architecture/viz-architecture.md` ("New entity kind") for the
> example's API usage.

## Goal

Add an example that builds a synthetic depth surface from phase-shifted sines of
different frequencies, plus a synthetic color image and a segmentation mask, and
shows the `DepthImage` entity (colormap mode, image mode, and live segment
switching via the ref API).

## Files

- New: `py/examples/viz/image/depth_surface.py`
- New: `py/tests/viz/test_depth_image_example.py`

## Steps

- [x] **6.1 — Surface generator.**
  - Add a module-level `_surface(width, height)` returning the depth array
    `z = (sin(2π f1 x + φ1) · sin(2π f2 y + φ2) + 1) / 2` scaled to `[0, 1]`
    (`float32`), using **phase-shifted sines of different frequencies** along x
    and y (e.g. `f1=3, f2=5, φ1=0.3, φ2=1.1`).

- [x] **6.2 — Color image + segmentation mask.**
  - A `_color_image(w, h)` gradient (uint8 RGB) at a different (higher)
    resolution than the depth map.
  - A `_segmentation(w, h)` with a few integer regions (e.g. 0 background, 1/2/3
    quadrants) to demonstrate filtering.

- [x] **6.3 — Build the scene.**
  - `viz = Visualizer(add_default_grid=False)` (3D).
  - `data = DepthImageData(image=…, depth=…, segmentation=…)`;
    `ref = viz.new(DepthImage(data), style=DepthImageStyle(mesh_scale=0.5,
    render_mode="depth", colormap="turbo"))`.
  - Demonstrate the live API in a couple of lines: `ref.set_selected_segments([1,
    2])`, `ref.set_uniform("u_render_mode", 1)` (image), and a commented note on
    toggling back to colormap/plain.  Optionally bind a key/drag handler via
    `ref.handle.on_key` to cycle modes.
  - Header per `dev/workflows/example-docs.md` (license + `<name>.py — …`
    docstring, `Run with:`, `Keywords: depth image, surface, segmentation, custom shader`).

- [x] **6.4 — Smoke test.**
  - `test_depth_image_example.py`: import the example's `_surface`/`_color_image`/
    `_segmentation`; assert shapes/dtypes; build a `DepthImage` from them and
    assert its serialized payload `kind == "depth_image"` with a `depth` block and
    `segmentation` block present.  (Do not open a browser.)

## Validation

`uv run pytest py/tests/viz/test_depth_image_example.py -q && uv run python py/examples/viz/image/depth_surface.py --help 2>/dev/null || true`

## Notes

- The script opens a browser and blocks (`viz.show(); viz.wait()`); the CI gate is
  the headless smoke test, not the script run.
- Keep the example's surface small enough (e.g. 128×128 depth, 512×384 image) to
  stay fast.
