# Viz Coordinate Overlay — Overview

**Created:** 2026-09-19 | **Status:** Done | **Branch:** `feat/cs-2d`

## Goal

Add `display_mode="overlay"` to `CoordinateSystem` (2D only). In this mode the
coordinate **axes** render as a fixed screen-space **overlay** frame at the image
borders (reusing the existing overlay layer), while the **background grid**
renders in a new, general-purpose **underlay** layer behind the (transparent)
scene. The data still pans/zooms underneath; the frame stays put and its tick
values + grid lines update live from the camera. `display_mode="world"` (default)
is unchanged, and everything works in standalone HTML export.

## Architecture (short)

- **Backend layers** — widen the scene-object `layer` from `scene`/`overlay` to
  also allow `underlay`. `CoordinateSystem(display_mode="overlay")` emits two
  payload-style objects: `axes_overlay` (overlay) and `grid_underlay` (underlay),
  each carrying a static spec.
- **Frontend (live)** — per scene pane, a fixed DOM stack:
  `underlay container (z:0) → WebGL canvas (z:1, transparent) → CSS2D labels
  (z:2) → overlay DOM (z:3)`. The frame renders as SVG/DOM into the overlay; the
  grid renders as SVG into the underlay. Both redraw each frame from the live
  ortho camera using shared pure math.
- **Frontend (export)** — the underlay/overlay renderers + math are bundled into
  the committed `js/tanga-viewer.js` (and inlined for `delivery="inline"` /
  `delivery="offline"`); the export adapters create/update them in their
  `requestAnimationFrame` loops, mirroring the live viewer. `delivery="cdn"`
  loads that same committed bundle via `_cdn.py` (jsDelivr).

## Canonical contract (fixed up front)

### Scene-object `layer`

`SceneObject.layer` becomes `Literal["scene", "overlay", "underlay"]`. `underlay`
objects are payload-style nodes (a generalized `VizOverlayObject` accepting a
`layer` kwarg) and serialize with `"layer": "underlay"`.

### `axes_overlay` (overlay layer)

```json
{
  "id": "<group_name>_axes_overlay",
  "layer": "overlay",
  "kind": "axes_overlay",
  "visible": true,
  "spec": {
    "xscale": "linear", "yscale": "linear", "base": 10.0,
    "value_format": ".4g", "labels": ["x", "y"],
    "border_px": 60.0,
    "axis": { "x": {"<AxisStyle.to_dict()>"}, "y": {"<AxisStyle.to_dict()>"} }
  }
}
```

### `grid_underlay` (underlay layer)

```json
{
  "id": "<group_name>_grid_underlay",
  "layer": "underlay",
  "kind": "grid_underlay",
  "visible": true,
  "spec": {
    "xscale": "linear", "yscale": "linear", "base": 10.0,
    "border_px": 60.0,
    "grid": { "<GridStyle.to_dict()>" }
  }
}
```

### Frontend math (pure modules)

- `nice-ticks.js`: `niceLinearTicks` / `logTicks` / `formatValue` — ports of
  `py/pytanga/viz/_scale.py`.
- `axes-overlay-math.js`: `visibleWorldRect`, `worldToData`, `ticksAndGrid`
  (pure, no `three`/DOM).

## Decisions (confirmed)

- `display_mode` `"world"` (default) | `"overlay"`; 2D-only, no explicit `size`
  (else `ValueError`).
- Axes frame reuses the **overlay layer** (SVG/DOM in the per-pane overlay).
- Grid is a **scene-level underlay** (`layer="underlay"`); controls stay in the
  existing overlay/layout system (out of scope for now).
- Value labels rendered with SVG/DOM text honoring `LabelStyle`; the grid uses
  SVG (canvas is a perf fallback).
- Overlay updates included in the animated export loop.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-scene-underlay-layer.md](./01-scene-underlay-layer.md) | Widen `layer` to `underlay` + node routing/serialization |
| 2 | [02-python-overlay-underlay-emit.md](./02-python-overlay-underlay-emit.md) | `display_mode` + emit `axes_overlay`/`grid_underlay` specs |
| 3 | [03-frontend-nice-ticks.md](./03-frontend-nice-ticks.md) | Pure JS `nice-ticks.js` + `axes-overlay-math.js` + Node tests |
| 4 | [04-overlay-underlay-renderers.md](./04-overlay-underlay-renderers.md) | SVG frame + SVG grid renderers |
| 5 | [05-live-viewer-wiring.md](./05-live-viewer-wiring.md) | `ThreeJsView` underlay/overlay containers + routing + transparent bg |
| 6 | [06-export-bundle-wiring.md](./06-export-bundle-wiring.md) | Bundle + export adapter wiring (static, figure, animated) |
| 7 | [07-example-tests.md](./07-example-tests.md) | Example + end-to-end/regression tests |
| 8 | [08-docs-changelog.md](./08-docs-changelog.md) | Architecture docs + public docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz -q` (targeted files per phase).
- **JS pure modules:** Node `--input-type=module -e` harness (see
  `py/tests/viz/test_camera_fit_math.py`); `node --check` for syntax.
- **Bundle/CDN:** `uv run python tools/build-viewer-js.py --check` — verifies the
  committed `js/tanga-viewer.js` (the file jsDelivr serves for `delivery="cdn"`)
  is fresh and contains the new modules.
- **Docs:** `uv run mkdocs build --strict`.

## Non-goals

- No 3D overlay / no explicit-`size` overlay.
- No layout-level underlay for controls (scene-level only).
- No new interaction / event / control entries.
- No `CoordinateSystem` teardown API.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
