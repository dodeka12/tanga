# Phase 4 — Examples

## Goal

Update the examples that used `uniform` and demonstrate the new `stretch`
modes.

## Files

- Edit: `py/examples/viz/camera/2d_view.py`
- Edit: `py/examples/viz/camera/modes.py`
- Edit: `py/examples/viz/plotting/multi_plot.py`

## Steps

- [x] **4.1 — `2d_view.py`**
  - Change `uniform=True` → `stretch="fit"` and update the docstring that
    described `uniform`.

- [x] **4.2 — `modes.py`**
  - Change `uniform=False` → `stretch="fill"` and update the surrounding
    comment.

- [x] **4.3 — `multi_plot.py`**
  - Pass `stretch="fill"` to each `fit_view2d(...)` so the three plots fill
    their panes, and add a docstring note about `fill_x`/`fill_y`.

## Validation

`uv run ruff check py/examples/viz/camera/2d_view.py py/examples/viz/camera/modes.py py/examples/viz/plotting/multi_plot.py && uv run python tools/generate-example-docs.py && uv run python tools/generate-example-docs.py --check`

## Notes

- `split_view_app.py` calls `fit_view2d(...)` without a `uniform`/`stretch`
  argument, so it defaults to `"fit"` and needs no change.
