# Phase 3 — `fit_view2d` default pixel border

## Goal

Make `fit_view2d(...)` produce a per-pane camera with a label margin by
default, so 2D plots embedded in split panes no longer clip their axes/labels.

## Files

- Edit: `py/pytanga/viz/_coordinate_system.py`
- Edit: `py/tests/viz/test_coordinate_system.py`

## Steps

- [x] **3.1 — Change the default**
  - In `fit_view2d`, change `border_px: float = 0.0` → `border_px: float = 60.0`.
  - Update the `border_px` doc line to state the default matches
    `CoordinateSystem`'s label margin (`60.0` px).

- [x] **3.2 — Pin the default with a test**
  - In `test_coordinate_system.py`, add an assertion that
    `fit_view2d((0, 10), (0, 4)).border_px == 60.0`.

## Validation

`uv run pytest py/tests/viz/test_coordinate_system.py -q && uv run ruff check py/pytanga/viz/_coordinate_system.py py/tests/viz/test_coordinate_system.py`

## Notes

- `View2DConfig.border_px` and `CameraConfig2d.border_px` keep their `0.0`
  defaults (raw specs) — existing `test_scene_session.py` assertions on those
  defaults remain valid.
- `split_view_app.py` already calls `fit_view2d(...)` with the default border;
  it automatically gains the margin once this default lands, so no edit there.
