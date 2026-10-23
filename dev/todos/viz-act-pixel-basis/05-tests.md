# Phase 5 — roll + tilted-normal round-trip tests

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the `CoordinateMapper` bullet) for
> the `pixel_axes()`/`plane()` contract the tests exercise.

## Goal

Prove `load → Act → save` and `draw → Act → save` are pixel-exact with a camera
that has both roll and a tilted normal, and that defaults are unchanged.

## Files

- Edit: `py/tests/viz/test_labelme.py`
- Edit: `py/tests/viz/test_act_rectangle2d.py`, `test_act_ellipse.py`

## Steps

- [x] **5.1 — Roll + tilted camera helper.**
  - Build a `CameraCalibration` whose `R` includes a roll (rotation about the
    optical axis) and a tilt (a few degrees off `-z`); expose `pixel_axes()`.

- [x] **5.2 — Rectangle.**
  - `load → Act(from_entity) → save` returns the same 2-point `rectangle`
    (1e-6 px); a rectangle drawn in an Act with `dir_u`/`dir_v = pixel_axes()`
    exports as a 2-point `rectangle`.

- [x] **5.3 — Ellipse.**
  - `theta → load → Act → save` returns `theta` (mod pi) and the same radii;
    `axis_directions()` matches the pixel-space ellipse.

- [x] **5.4 — Circle + legacy ellipse.**
  - Circle and the legacy 3-point ellipse still load/export as before.

- [x] **5.5 — Default Acts unchanged.**
  - Default Acts (no `dir_u`/`dir_v`) keep 2.23.2 golden values.

- [x] **5.6 — `from_entity` round-trip.**
  - All three shapes: `entity → from_entity → save` reproduces the entity's frame.

## Validation

`uv run pytest py/tests/viz/test_labelme.py py/tests/viz/test_act_rectangle2d.py py/tests/viz/test_act_ellipse.py -q`

## Notes

- The existing round-trip test uses tilt but no roll; extend it rather than
  duplicating the mapper setup.
