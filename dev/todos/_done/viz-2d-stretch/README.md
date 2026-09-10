# 2D camera stretch modes — Overview

**Created:** 2026-09-06 | **Status:** Done | **Branch:** `fix/examples`

## Goal

Replace the 2D camera's single `uniform: bool` switch with a richer `stretch`
parameter so a plot plane can fill the view on one axis while keeping the
aspect ratio on the other.  Four modes:

| `stretch` | x-axis | y-axis | scale |
|---|---|---|---|
| `"fit"` (default) | fills if limiting | fills if limiting | uniform (⟺ old `uniform=True`) |
| `"fill"` | fills | fills | non-uniform (⟺ old `uniform=False`) |
| `"fill_x"` | **fills** | derived from aspect | uniform |
| `"fill_y"` | derived from aspect | **fills** | uniform |

The plane's 3D world extent is **already** controlled by `CoordinateSystem`
`size=(sx, sy)`; `stretch` only changes how the 2D ortho camera frames that
plane (same scope as `uniform` today).

## Architecture (short)

- **Backend** (`camera.py`, `_coordinate_system.py`): `uniform` is replaced by
  `stretch` on `View2DConfig`, `CameraConfig2d`, `fit_view2d`, and
  `CoordinateSystem`. `CameraConfig.to_dict` serializes `stretch` automatically
  (non-`None`).
- **Frontend** (`templates/camera-fit.js`, `view_mode.js`, `fit_camera.js`):
  `orthoFrustum` dispatches on the `stretch` string; the per-camera
  `userData._view2d` stores `stretch` so resize recomputes the same mode.
- **Export** (`export/_bootstrap/_scene.py`): `js_apply_camera` + the initial
  2D `_view2d` mirror the same `stretch` resolution.

## Decisions (confirmed)

- **Replace `uniform` entirely** (no alias) with `stretch`, as requested by the
  user. `stretch="fit"` is the exact equivalent of `uniform=True`.
- **Fixed contract:**

  ```python
  StretchMode = Literal["fit", "fill", "fill_x", "fill_y"]

  View2DConfig(..., stretch: StretchMode = "fit")
  CameraConfig2d(..., stretch: StretchMode = "fit")
  fit_view2d(..., stretch: StretchMode = "fit")
  CoordinateSystem(..., stretch: StretchMode = "fit")
  ```

  ```js
  orthoFrustum(xmin, xmax, ymin, ymax, stretch, borderPx, width, height)
  camera.userData._view2d = { xmin, xmax, ymin, ymax, stretch, border_px }
  ```

- **`orthoFrustum` math** (content area `cw = w − 2·bp`, `ch = h − 2·bp`):
  - `fit` — `fit = max(extX/aspectContent, extY)`, then expand border back (letterbox, unchanged).
  - `fill` — `left/right = ±extX/2 · w/cw`, `top/bottom = ±extY/2 · h/ch` (unchanged).
  - `fill_x` — `left/right = ±(extX·w/cw)/2`, `top/bottom = ±(extX·h/cw)/2`.
  - `fill_y` — `left/right = ±(extY·w/ch)/2`, `top/bottom = ±(extY·h/ch)/2`.
  - Unknown/empty `stretch` → `"fit"`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-camera-stretch-contract.md](./01-camera-stretch-contract.md) | Backend: `StretchMode` + `stretch` on configs, `fit_view2d`, `CoordinateSystem` |
| 2 | [02-frontend-ortho-modes.md](./02-frontend-ortho-modes.md) | `orthoFrustum` modes, `view_mode.js`, `fit_camera.js` + node math test |
| 3 | [03-export-bootstrap.md](./03-export-bootstrap.md) | Export `_bootstrap/_scene.py` mirror |
| 4 | [04-examples.md](./04-examples.md) | Update `2d_view.py`, `modes.py`, `multi_plot.py` |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Changelog + example docs |

## Testing as you go

```bash
uv run pytest py/tests/viz -q
uv run ruff check py/pytanga/viz py/examples/viz/camera py/examples/viz/plotting py/tests/viz
node --check py/pytanga/viz/templates/camera-fit.js
node --check py/pytanga/viz/templates/view_mode.js
node --check py/pytanga/viz/templates/fit_camera.js
uv run python tools/generate-example-docs.py --check
uv run mkdocs build --strict
```

## Non-goals

- `size` is unchanged (already the plane's 3D world extent).
- No `uniform` backward-compat alias (full removal).
- `sdf_viewer.js` untouched (it does not use the 2D camera `uniform` flag).
- `fit_view2d` still frames the data span, not `size`; manual `size` placement
  remains the caller's responsibility (unchanged).
