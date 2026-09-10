# Phase 1 — Backend `stretch` contract

## Goal

Replace `uniform` with `stretch` on the Python camera/config surface and thread
it through `fit_view2d` and `CoordinateSystem`.

## Files

- Edit: `py/pytanga/viz/camera.py`
- Edit: `py/pytanga/viz/_coordinate_system.py`
- Edit: `py/tests/viz/test_scene_session.py`
- Edit: `py/tests/viz/test_coordinate_system.py`

## Steps

- [x] **1.1 — `StretchMode` + validation in `camera.py`**
  - Add `StretchMode = Literal["fit", "fill", "fill_x", "fill_y"]`,
    `_STRETCH_MODES = ("fit", "fill", "fill_x", "fill_y")`, and
    `_validate_stretch(stretch) -> str` (raise `ValueError` on unknown values).
  - Replace `View2DConfig.uniform: bool = True` with
    `stretch: StretchMode = "fit"` and add `__post_init__` validating it.
  - Replace `CameraConfig2d.uniform: bool = True` with
    `stretch: StretchMode = "fit"` and add `__post_init__` validating it.
  - Update `get_camera_view2d` to pass `stretch=config.stretch` and refresh the
    `uniform` docstrings.

- [x] **1.2 — `fit_view2d` + `CoordinateSystem`**
  - In `_coordinate_system.py`, import `StretchMode`/`_validate_stretch` from
    `.camera`.
  - Change `fit_view2d`'s `uniform: bool = True` → `stretch: StretchMode =
    "fit"`, pass `stretch=stretch`, update the docstring.
  - Add `stretch: StretchMode = "fit"` to `CoordinateSystem.__init__` (validate
    it, store `self._stretch`), and change `_apply_camera` to pass
    `stretch=self._stretch` instead of `uniform=True`.

- [x] **1.3 — Update Python tests**
  - `test_scene_session.py`: `uniform is True`/`"uniform": True` → `stretch ==
    "fit"` / `"stretch": "fit"`.
  - `test_coordinate_system.py`: `uniform is True/False` → `stretch ==
    "fit"/"fill"`; rename the `test_border_and_uniform` test; add default-`fit`
    and `fill_x`/`fill_y` pass-through assertions.

## Validation

`uv run pytest py/tests/viz/test_scene_session.py py/tests/viz/test_coordinate_system.py -q && uv run ruff check py/pytanga/viz/camera.py py/pytanga/viz/_coordinate_system.py py/tests/viz/test_scene_session.py py/tests/viz/test_coordinate_system.py`

## Notes

- `CameraConfig.to_dict` serializes any non-`None` field, so `stretch="fit"`
  is emitted on the wire without extra code.
- `_coordinate_system.py` already imports `CameraConfig2d`/`View2DConfig` from
  `.camera`; extend that import, don't add a second one.
