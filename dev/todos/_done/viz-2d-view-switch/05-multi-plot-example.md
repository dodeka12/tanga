# Phase 5 — Fix `multi_plot.py` split-pane plots

## Goal

Rewrite `py/examples/viz/plotting/multi_plot.py` so it correctly demonstrates
different 2D plots in separate split panes (the current file references scenes
that don't exist, so its panes render nothing).

## Files

- Edit: `py/examples/viz/plotting/multi_plot.py`

## Steps

- [x] **5.1 — Rewrite the example**
  - Keep the license header + `example-docs.md`-style docstring; fix the
    `Run with:` path to `uv run python py/examples/viz/plotting/multi_plot.py`
    and update `Keywords:`.
  - `Visualizer(reuse_existing=False, title="Tanga — Multi-Plot Split",
    space_dim=2, add_default_axes=False, add_default_grid=False)`.
  - Three named 2D scenes (`sin`, `pow`, `par`), each
    `viz.scene(name, space_dim=2, add_axes=False, add_grid=False)` with its own
    `CoordinateSystem(..., camera=False)`:
    - `sin`: `xlim=(0, 2*pi)`, `ylim=(-1.2, 1.2)`, plot `sin(x)`.
    - `pow`: `xlim=(0, 40)`, `ylim=(1.0, 1_000_000.0)`, `yscale="log"`, plot
      `x*x + x + 0.1`.
    - `par`: `xlim=(-5, 5)`, `ylim=(0, 25)`, plot `x*x`.
  - Horizontal `SplitView` with `sizes=[Size.percent(33), Size.percent(33),
    Size.percent(34)]` and `children=[SceneView("sin", camera=fit_view2d(...)),
    SceneView("pow", camera=fit_view2d(..., yscale="log")),
    SceneView("par", camera=fit_view2d(...))]`.
  - `viz.show(layout=layout)` + `viz.wait()`.

## Validation

`uv run ruff check py/examples/viz/plotting/multi_plot.py && uv run python tools/generate-example-docs.py --check`

## Notes

- `fit_view2d` now defaults `border_px=60` (Phase 3), so the panes get label
  margins without extra arguments.
- Use `PointPathStyle(line_thickness=2)` and distinct colors per plot.
