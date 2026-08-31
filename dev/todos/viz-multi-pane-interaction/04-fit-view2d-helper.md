# Phase 4 — `fit_view2d` helper

## Goal

Expose the `xlim`/`ylim` → `View2DConfig` computation as a reusable,
module-level `fit_view2d(...)`, and make `CoordinateSystem` use it internally so
apps can embed an exact per-pane camera at layout-construction time.

## Files

- Edit: `py/pytanga/viz/_coordinate_system.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/tests/viz/test_coordinate_system.py`

## Steps

- [x] **4.1 — Implement `fit_view2d`**
  - Add a module-level function matching the README contract, computing
    `span_x = make_scale(xscale, base).to_world(xhi) - make_scale(xscale, base).to_world(xlo)`
    (same for y) and returning
    `View2DConfig(xmin=-span_x/2, xmax=span_x/2, ymin=-span_y/2, ymax=span_y/2, border_world=border_world, border_px=border_px, uniform=uniform)`.
- [x] **4.2 — Reuse it in `CoordinateSystem._apply_camera`**
  - Replace the inline `View2DConfig(...)` construction in `_apply_camera` with a
    call to
    `fit_view2d(self._xlim, self._ylim, xscale=self._xscale, yscale=self._yscale, base=self._base, border_world=self.border_world, border_px=self.border_px, uniform=True)`.
  - Confirm the existing 2D coordinate-system tests still pass (values must be
    identical — no drift).
- [x] **4.3 — Export from `pytanga.viz`**
  - Extend the existing `_coordinate_system` import in `__init__.py` to include
    `fit_view2d`, and add `"fit_view2d"` to `__all__`.
- [x] **4.4 — Add a unit test**
  - Assert `fit_view2d((0, 10), (0, 4))` yields `xmin=-5, xmax=5, ymin=-2, ymax=2, uniform=True`.
  - Assert the log-scale case: `fit_view2d((0.1, 100), (0.1, 100), xscale="log", yscale="log")`
    produces bounds matching the log span (`log10(hi) - log10(lo)`), consistent
    with `CoordinateSystem`'s own camera for the same limits.

## Validation

`uv run pytest py/tests/viz/test_coordinate_system.py -q && uv run ruff check py/pytanga/viz/_coordinate_system.py py/pytanga/viz/__init__.py`

## Notes

- `make_scale` / `LinearScale` / `LogScale` are already imported in
  `_coordinate_system.py`; reuse them so `fit_view2d` and `CoordinateSystem`
  cannot drift apart.
- Keep `fit_view2d` free of any scene/handle dependency so it can be called
  before `VisualizerApp.run()`.
