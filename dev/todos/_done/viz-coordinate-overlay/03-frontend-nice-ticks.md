# Phase 3 — Frontend pure math (nice ticks + world↔data)

## Goal

Port the Python tick/scale math to two dependency-free ES modules so both the
live viewer and the export bundle compute the same "nice" ticks, and so the math
is Node-testable without a browser or `three`.

## Files

- New: `py/pytanga/viz/templates/nice-ticks.js`
- New: `py/pytanga/viz/templates/axes-overlay-math.js`
- New: `py/tests/viz/test_nice_ticks_math.py`
- New: `py/tests/viz/test_axes_overlay_math.py`

## Steps

- [x] **3.1 — `nice-ticks.js`**
  - Port `nice_linear_ticks` (1/2/5 × 10^k step snap, `max_ticks` default 8) and
    `log_ticks` (integer powers of `base`) from `py/pytanga/viz/_scale.py`
    faithfully, including the epsilon guards.
  - Add `formatValue(fmt, v)` supporting `.Nf` (decimals) and `.Ng` (significant
    digits) plus a plain fallback; match Python `format(v, fmt)` for common cases.
  - No `three`/DOM imports; expose `export function ...`.

- [x] **3.2 — `axes-overlay-math.js`**
  - `visibleWorldRect({left, right, top, bottom, zoom, x, y})` → `{xmin, xmax,
    ymin, ymax}` using half-extents `(right-left)/2/zoom` and
    `(top-bottom)/2/zoom` centred at `(x, y)` (2D ortho has no rotation).
  - `worldToData(rect, spec)` → `{xlo, xhi, ylo, yhi}` applying `base**v` for
    each `"log"` axis and identity for `"linear"`.
  - `ticksAndGrid(rect, spec, plotSizePx)` → `{xTicks, yTicks, xGridPx,
    yGridPx}` mapping each tick data value back to world → plot-px fraction, via
    `niceLinearTicks`/`logTicks` + `formatValue`.

- [x] **3.3 — Node tests**
  - `test_nice_ticks_math.py`: run `node --input-type=module -e` importing
    `nice-ticks.js`, assert parity with `_scale.py` for linear and log cases.
  - `test_axes_overlay_math.py`: assert `visibleWorldRect`, `worldToData`
    (linear vs log), and `ticksAndGrid` positions for a known rect; assert
    zoom-in shrinks the step (resolution jump).

## Validation

`uv run pytest py/tests/viz/test_nice_ticks_math.py py/tests/viz/test_axes_overlay_math.py -q`

## Notes

- Mirror `py/tests/viz/test_camera_fit_math.py` (skip when `node` is absent).
- Keep the two modules import-free so `node --input-type=module -e "import {…}
  from './py/pytanga/viz/templates/nice-ticks.js'"` works directly.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
