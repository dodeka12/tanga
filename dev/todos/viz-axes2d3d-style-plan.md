# Axes2D / Axes3D as Explicit Scene Objects with Per-Axis Styles

## Goal

Make `Axes2D` and `Axes3D` first-class scene objects (one object, one ID) instead
of Python-side conveniences that expand into many `Axis` objects. Each of these
two axes-group objects gets its own style class holding **one `AxisStyle` per
axis direction**, whose positive and negative halves share that same style.

## Current state (why this change)

- `AxisStyle` already defines per-axis appearance: `color`, `opacity`,
  `line_thickness` (all optional, `None` by default).
- `Axes2D` / `Axes3D` (_scene_objects.py) are dataclasses with an `expand()`
  method returning `list[Axis]` (up to 4 / 6 halves).
- `Visualizer._add_to_scene` has a special branch that loops `obj.expand()` and
  registers each `Axis` as its own `SceneObject(kind="Axis")`. Every half gets
  the same `properties` dict.
- `serializer._serialize_axis` runs per `Axis`, resolving against the canonical
  `"Axis"` default (`AxisStyle`).
- The frontend `createAxis` draws a single axis; there is no `Axes2D`/`Axes3D`
  renderer.

## Target design

- Keep `Axis` + `AxisStyle` exactly as today for standalone axes.
- `Axes2D` / `Axes3D` are **single** scene objects (kind `"Axes2D"`/`"Axes3D"`),
  same pattern as `Grid` (which draws many lines inside one `Group`).
- New style classes:
  - `Axes2DStyle(u: AxisStyle, v: AxisStyle)`
  - `Axes3DStyle(u: AxisStyle, v: AxisStyle, w: AxisStyle)`
- Serialization emits a single dict per group with an embedded `axes` list, each
  entry carrying the resolved per-direction `AxisStyle`.
- Frontend `axes2d.js` / `axes3d.js` renderers loop the embedded axes and call a
  shared axis-drawing base so all axes render identically.

## Changes

### 1. Styles — `py/pytanga/viz/_styles/_entity_styles.py`

- Add `Axes2DStyle(VizStyle)`:
  - fields: `u: AxisStyle = AxisStyle()`, `v: AxisStyle = AxisStyle()`
  - `to_dict()` → `{"style_type": "Axes2DStyle", "u": self.u.to_dict(), "v": self.v.to_dict()}`
- Add `Axes3DStyle(VizStyle)`:
  - fields: `u: AxisStyle = AxisStyle()`, `v: AxisStyle = AxisStyle()`, `w: AxisStyle = AxisStyle()`
  - `to_dict()` → `{"style_type": "Axes3DStyle", "u": ..., "v": ..., "w": ...}`

### 2. Styles registry — `py/pytanga/viz/_styles/__init__.py`

- Import `Axes2DStyle`, `Axes3DStyle`.
- Add both to `ObjVizStyle` union.
- Add canonical entries to `_DEFAULT_STYLE_FOR_KIND`:
  - `"Axes2D": Axes2DStyle()` (default `u`, `v` = `AxisStyle()`)
  - `"Axes3D": Axes3DStyle()` (default `u`, `v`, `w` = `AxisStyle()`)
  (The existing `"Axis"` canonical stays as the per-axis fallback when a
  direction's `AxisStyle` is sparse.)

### 3. Scene objects — `py/pytanga/viz/_scene_objects.py`

- `Axes2D` / `Axes3D`: keep as single dataclasses (origin/dirs/ranges/major/minor/
  labels). No functional change required; `expand()` may remain for tests/back-compat
  but is **no longer used** by the add/serialize path.
- Ensure the 2D origin z-padding logic is available to the serializer (extract or
  expose `_pad_origin` / `_AXES_Z`, or duplicate the small helper in the serializer).

### 4. Serializer — `py/pytanga/viz/serializer.py`

- Import `Axes2D`, `Axes3D` from `._scene_objects`.
- In `serialize_entity`, add `isinstance` branches **before** the generic `Axis`/`Grid`
  cases (they are distinct types, so ordering only matters for clarity).
- Add `_serialize_axes2d(ent, props, *, kind, styles_map)` and
  `_serialize_axes3d(...)`.
- Each emits a single dict with:
  - `"kind": "Axes2D"` / `"Axes3D"`
  - `"origin": [...], "dir_u": [...], "dir_v": [...], ("dir_w": [...])`
  - `"range_u": [...], "range_v": [...], ("range_w": [...])`
  - `"major_interval"`, `"minor_interval"?`, `"labels": [...]`
  - `"axes": [ {start, end, label, value_step, major_interval, label_at_major,
            label_format, label_size?, style}, ... ]`
- Per-direction style resolution: for direction index `i`, take that direction's
  `AxisStyle` (from the user `props["style"]` if it is `Axes2DStyle`/`Axes3DStyle`,
  else from canonical `"Axes2D"`/`"Axes3D"`), then resolve sparse fields against the
  canonical `"Axis"` default using `_style_to_output(style_i, "Axis", styles_map)`.
  Each of the negative/positive halves of a direction reuses the **same** resolved
  `style`.
- Reuse the existing half-expansion logic (start/end, `value_step` ±1, name label on
  positive half only; 2D origin padded to `_AXES_Z`).

### 5. Visualizer — `py/pytanga/viz/visualizer.py`

- **Remove** the `if isinstance(obj, (Axes3D, Axes2D)): ... obj.expand() ...` branch
  in `_add_to_scene`.
- `Axes2D` / `Axes3D` then flow through the generic viz-level drawable path
  (`add_object` with `kind = type(obj).__name__`), exactly like `Grid`/`Axis`.
- In `_add_default_scene_objects`, widen the guard:
  ```python
  has_axis_or_grid = any(
      obj.kind in ("Axis", "Grid", "Axes2D", "Axes3D")
      for obj in scene._objects.values()
  )
  ```

### 6. Frontend

- Refactor `templates/renderers/axis.js` to expose a reusable base, e.g.
  `export function addAxis(group, start, end, opts)` (or `drawAxis(group, axisEntry)`)
  that draws the line, value labels, and the name label at the end — reading
  color/opacity/format from the resolved `axisEntry.style`. `createAxis(ent)` becomes
  a thin wrapper that builds a `Group` and calls `addAxis` once.
- Add `templates/renderers/axes2d.js` exporting `createAxes2D(ent)`:
  - `new THREE.Group()`
  - for each `ent.axes`, call the shared `addAxis` base.
  - `tagEntity(group, ent)`
- Add `templates/renderers/axes3d.js` exporting `createAxes3D(ent)` (same shape).
- Register in `templates/renderers/factory.js`:
  - import `createAxes2D`, `createAxes3D`
  - add `case 'Axes2D':` / `case 'Axes3D':`.

### 7. Exports — `py/pytanga/viz/__init__.py`

- Re-export `Axes2DStyle`, `Axes3DStyle` (alongside the already-exported names).

### 8. Tests — `py/tests/viz/test_scene_session.py`

- Add tests:
  - `Axes2DStyle`/`Axes3DStyle` construction with named `u`/`v`/`w`.
  - serialize `Axes2D(style=Axes2DStyle(u=..., v=...))` → one object with
    `kind == "Axes2D"` and `axes` list; confirm both ± halves of direction `u`
    carry the `u` style, both halves of `v` carry the `v` style.
  - same for `Axes3D`.
  - sparse `AxisStyle` (e.g. only `color`) falls back to canonical `"Axis"` defaults
    for `opacity`/`line_thickness`.
  - default `Axes2D`/`Axes3D` (no style) use canonical `"Axes2D"`/`"Axes3D"` →
    default `AxisStyle`s.
- Update any tests asserting the old `kind == "Axis"` expansion behavior.

### 9. Docs

- Update `docs/py/viz/axes-grid.md`: `Axes2D`/`Axes3D` now single scene objects;
  document `Axes2DStyle`/`Axes3DStyle` and per-direction `AxisStyle`.
- Update `docs/py/viz/styles.md` style/default tables with the new classes.

## Verification

- `uv run pytest py/tests/viz -q`
- Manual smoke: `Axes2D`/`Axes3D` still auto-inserted and render; per-axis colors
  differ in the live viewer; standalone `Axis` styling unaffected.