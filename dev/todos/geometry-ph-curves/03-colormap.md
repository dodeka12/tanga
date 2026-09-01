# Phase 3 — Colormap primitive

## Goal

Add `py/pytanga/viz/_colormap.py` with a stop-based `Colormap` (plus a few
presets) that maps a normalized scalar to a CSS hex color, and export it from
the viz package.

## Files

- New: `py/pytanga/viz/_colormap.py`
- New: `py/tests/viz/test_colormap.py`
- Edit: `py/pytanga/viz/__init__.py` (import + `__all__`)

## Steps

- [ ] **3.1 — Implement `Colormap`**
  - Frozen dataclass holding `stops: tuple[tuple[float, str], ...]`
    (normalized, ascending; validate in `__post_init__`: ≥2 stops, `0 ≤ s ≤ 1`,
    strictly increasing).
  - `map(t)` clamps and linearly interpolates between bracketing stops,
    reusing `_lerp_color`/`_hex_to_rgb` from `viz/_point_path.py` (import them,
    do not duplicate).
  - `map_values(values, vmin=None, vmax=None)` normalizes a sequence to
    `[vmin, vmax]` (defaults to data min/max; constant data → 0.5) and maps each.
- [ ] **3.2 — Add presets**
  - `Colormap.viridis()`, `Colormap.turbo()`, `Colormap.coolwarm()` with
    hardcoded stop tables (no matplotlib).
- [ ] **3.3 — Export from `pytanga.viz`** (add to `__init__.py`/`__all__`).
- [ ] **3.4 — Tests**
  - `test_colormap.py`: endpoints clamp to first/last stop; midpoint
    interpolation; `map_values` min/max normalization and constant-input
    handling; preset tables are valid (ascending, in-range); invalid stops
    raise.

## Validation

`uv run pytest py/tests/viz/test_colormap.py -q`

## Notes

- Keep `Colormap` serialization-free for now (it is a Python-side parameter of
  `PHCurveStyle`, resolved during serialization in Phase 4).
