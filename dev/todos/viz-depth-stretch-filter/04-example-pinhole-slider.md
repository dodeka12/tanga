# Phase 4 — Example: `pinhole_depth.py` grazing-angle slider

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (the `(id, event)`
> registry + `ControlHandler` `async def h(value, event)` shape) and
> `dev/workflows/example-docs.md` (docstring + `Keywords:` conventions).  The
> example uses the existing `SliderView`/`ControlEvent` contract; no new control
> architecture.

## Goal

Extend `pinhole_depth.py` so the depth map contains a box in front of a plane,
and a left control pane exposes a **Max grazing angle** slider that changes the
filter live via `ref.set_uniform("u_max_stretch", …)`.

## Files

- Edit `py/examples/viz/image/pinhole_depth.py`

## Steps

- [x] **4.1 — Box-in-plane depth map**
  - Replace/augment `_depth(...)` so the depth map has a central box at
    `Z ≈ 1.5` surrounded by a plane at `Z ≈ 3` (within the existing `_NEAR`/`_FAR`
    range; keep the existing `_IMAGE_W`/`_IMAGE_H`/`_DEPTH_W`/`_DEPTH_H`
    constants or adjust as needed).

- [x] **4.2 — Keep the surface reference + initial style**
  - Capture the `world.new(...)` return as `depth_ref`.
  - Add `max_grazing_angle=85` to the existing `DepthImageStyle(...)` (so the
    example starts filtered).

- [x] **4.3 — Slider + live uniform update**
  - Add a `SliderView("max_grazing_angle", label="Max grazing angle", min=0.0,
    max=89.0, step=1.0, value=85.0, on_change=…)` in a left `GroupView` (keep the
    existing two-pane `SplitView`; the slider pane goes on the left).
  - The handler is `async def _on_grazing_angle(value, _event)` calling
    `depth_ref.set_uniform("u_max_stretch", math.tan(math.radians(value)))`
    (`math` is already imported).  `0` ⇒ off, matching the shader guard.

- [x] **4.4 — Docstring**
  - Update the module docstring description + `Run with:` + `Keywords:` per
    `dev/workflows/example-docs.md` (add e.g. `depth jump filter`, `grazing
    angle`, `slider`, `uniform`).

## Validation

```bash
uv run python tools/generate-example-docs.py && uv run python tools/generate-example-docs.py --check
uv run ruff check py/examples/viz/image/pinhole_depth.py
```

## Notes

- Manual smoke (needs a browser):
  `uv run python py/examples/viz/image/pinhole_depth.py` — drag the slider and
  confirm the box/plane border triangles appear/disappear without a rebuild.
- We deliberately call `ref.set_uniform("u_max_stretch", …)` (no helper) so the
  example documents the raw live-uniform channel.
