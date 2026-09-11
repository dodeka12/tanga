# Phase 7 — Examples

## Goal

Update the shipped examples for the rename and demonstrate programmatic value
updates.

## Steps

- [x] **7.1 — Rename `default=` → `value=`**
  - `py/examples/viz/banners/heavy_work.py`
  - `py/examples/viz/interaction/two_spheres_interact.py`
  - `py/examples/viz/interaction/all_controls.py`
  - `py/examples/viz/scenes/split_view.py`

- [x] **7.2 — Demonstrate value updates**
  - Add a `set_control_value` / `set_control_view_value` call in one example
    (e.g. `all_controls.py` or `split_view.py`) to show the new API.

- [x] **7.3 — Validate**
  - Compile every example: `uv run python -c "import py_compile,glob; ..."`.

## Validation

`uv run python -c "import py_compile,glob; [py_compile.compile(f, doraise=True) for f in glob.glob('py/examples/viz/**/*.py', recursive=True)]"`

## Notes

- Keep example intent unchanged; only keyword renames + the new demo call.
