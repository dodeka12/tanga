# Phase 4 — Viz drawing (`PHCurveStyle` + serializer)

## Goal

Make PH curves drawable: add `PHCurveStyle` (with `num_points` and optional
`colormap`), register it as the canonical style for `PHCurve2D`/`PHCurve3D`,
teach the serializer to auto-sample a PH curve into a `PointPath` wire dict
(velocity → color), and let `Visualizer._resolve` pass PH curves through.

## Files

- Edit: `py/pytanga/viz/_styles/_entity_styles.py` (add `PHCurveStyle`)
- Edit: `py/pytanga/viz/_styles/__init__.py` (import, `ObjVizStyle`, `_DEFAULT_STYLE_FOR_KIND`)
- Edit: `py/pytanga/viz/serializer.py` (`_serialize_ph_curve` + dispatch)
- Edit: `py/pytanga/viz/_types.py` (`SceneEntity`, `VizInputType`)
- Edit: `py/pytanga/viz/__init__.py` (export `PHCurveStyle`)
- New: `py/tests/viz/test_phcurve_style.py`

## Steps

- [ ] **4.1 — Add `PHCurveStyle`**
  - `@dataclass` subclass of `VizStyle` with `color`, `opacity`,
    `line_thickness`, `num_points: int | None`, `colormap: Colormap | None`
    and a `to_dict()` (emit `style_type: "PHCurveStyle"`; serialize `colormap`
    as its `stops` list so it round-trips in dict form).
- [ ] **4.2 — Register canonical defaults**
  - `_DEFAULT_STYLE_FOR_KIND["PHCurve2D"]` and `["PHCurve3D"]` →
    `PHCurveStyle(color="#44aaff", opacity=1.0, line_thickness=2.0,
    num_points=200, colormap=None)`; add `PHCurveStyle` to `ObjVizStyle`.
- [ ] **4.3 — Add `_serialize_ph_curve(entity, props, *, kind, styles_map)`**
  - Merge style via `_style_to_output(props.get("style"), kind,
    styles_map=styles_map)`, then overlay non-`style` `props` (color/opacity).
  - Read `num_points` (default 200), `colormap`, `color`, `opacity`,
    `line_thickness`.
  - Sample: `pts = entity.positions_regular(num_points)`,
    `vels = entity.velocities_regular(num_points)`; speeds = `[v.mag() …]`.
  - Colors: `colormap.map_values(speeds)` when set, else `[None]*num_points`.
  - Return `{"kind": "PointPath", "points": [[x,y,z]…], "colors": […],
    "line_thickness": …, "color"/"opacity" if set,
    "style": {"style_type": "PointPathStyle", "color", "opacity",
    "line_thickness"}}` (omit `None` style fields).
  - Add `isinstance(entity, (PHCurve2D, PHCurve3D))` branches in
    `_dispatch_entity` (before the `PointPath` branch).
- [ ] **4.4 — Wire `_types.py`**
  - Add `PHCurve2D`/`PHCurve3D` to `SceneEntity` and `VizInputType` unions so
    `Visualizer._resolve` returns them unchanged.
- [ ] **4.5 — Export `PHCurveStyle` from `pytanga.viz`** (`__init__.py`/`__all__`).
- [ ] **4.6 — Tests**
  - `test_phcurve_style.py`: `serialize_entity(PHCurve2D(...))` yields
    `kind == "PointPath"`, `len(points) == num_points`, `len(colors) ==
    num_points`; with a `Colormap` the colors are hex strings varying with
    speed; without one, colors are all `None`; `viz.add(PHCurve3D(...),
    style=PHCurveStyle(num_points=8))` returns an id and the scene state
    serializes (mirror `test_serializer.py`/`test_node_serialization.py`
    patterns).

## Validation

`uv run pytest py/tests/viz/test_phcurve_style.py py/tests/viz/test_serializer.py -q`

## Notes

- Emitting `kind: "PointPath"` means zero frontend work — the existing renderer
  and `entityRequiresRebuild` path handle it.
- Do not add `PHCurveStyle` to the SDF style path.
