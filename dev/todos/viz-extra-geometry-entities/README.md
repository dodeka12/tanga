# Extra Viz-only Geometry Entities (Disk, PartialDisk, Box, Ellipsoid, Ellipse, RegularPolygon) — Overview

**Created:** 2026-08-26 | **Status:** Implemented | **Branch:** `feat/geo-objects`

## Goal

Extend the set of geometric objects the visualizer can render. The SDF primitive
library already knows `sphere, ellipsoid, box, roundBox, cylinder, cappedCylinder,
cone, cappedCone, torus, capsule, segment, plane`, but only some of them are
available as `pytanga.geometry` entities. This plan adds the six most-wanted
**visualization-only** entities (no multivector representation, like `Cylinder` /
`Arc`):

- **3D**: `Disk`, `PartialDisk`, `Box`, `Ellipsoid`.
- **2D** (same classes, `normal` defaults to `+z`): `Disk`, `PartialDisk`,
  `Ellipse`, and a `regular_polygon(...)` factory returning `RegularPolygon`.

Every new object that can be rendered as an SDF solid gets an SDF mapping, and
every new object gets its own mesh style class **and** its own per-entity SDF
style class.

## Gap analysis (drives the backlog below)

| SDF object | Geometry entity today | This plan |
|---|---|---|
| `sphere` | `Sphere` | exists |
| `cylinder` / `cappedCylinder` | `Cylinder` | exists |
| `plane` | `Plane` | exists |
| `torus` (tube) | `Arc` | exists (partial) |
| `ellipsoid` | — | ✅ add `Ellipsoid` |
| `box` | — | ✅ add `Box` |
| `segment` | `Line` (bounded via `length`) | deferred |
| `roundBox` | — | deferred |
| `cone` | — | deferred |
| `cappedCone` | — | deferred |
| solid `torus` | — | deferred |
| `capsule` | — | deferred |
| *disk* (thin slab, new) | — | ✅ add `Disk` |
| *partial disk* (pie slab, new) | — | ✅ add `PartialDisk` |
| *ellipse* (filled, new) | — | ✅ add `Ellipse` |
| *regular polygon* (new) | — | ✅ add `RegularPolygon` + `regular_polygon()` |

## Scope boundaries (fixed up front)

- New entities live in `py/pytanga/geometry/entities/` but are **not** members of
  the `Entity` union, so `Geometry.create()` / `analyze()` reject them. They flow
  through the viz-only path (`Visualizer._add_to_scene` → `scene.add_object`),
  exactly like `Cylinder` / `Arc`.
- **One entity model for 2D + 3D.** All entities use 3D data fields; a `normal`
  (or `axis`) defaulting to `+z` makes them render correctly in the 2D viewer
  (`z = 0` plane, orthographic camera) and orientable in 3D. This matches the
  documented convention in `docs/py/geometry/entities.md` ("2D usage").
- **Angles are radians end-to-end** (matches `Arc.angle`); `start_direction` is
  auto-computed perpendicular to `normal` when omitted (deterministic, mirrors
  `Arc`).
- **Thickness is a style knob** (like `CircleStyle.tube_radius`), not a content
  field — the mesh renderers and the SDF slab both read it from the style.
- Each entity gets a dedicated mesh style class and a dedicated SDF style class,
  both registered in the canonical-default tables.


## Canonical wire contract (fixed up front; both sides implement against this)

Content fields are **always present** (no fallbacks computed on the frontend);
style fields arrive resolved (merged) inside `style`.

### Disk

```json
{
  "id": "d1", "layer": "scene", "kind": "Disk",
  "center": [0, 0, 0], "radius": 1.0, "normal": [0, 0, 1],
  "style": { "style_type": "DiskStyle", "color": "#ff8844", "opacity": 0.9,
             "thickness": 0.02, "wireframe": false }
}
```

### PartialDisk

```json
{
  "id": "p1", "layer": "scene", "kind": "PartialDisk",
  "center": [0, 0, 0], "radius": 1.0, "normal": [0, 0, 1],
  "angle": 1.5707963267948966, "startDirection": [1, 0, 0],
  "style": { "style_type": "PartialDiskStyle", "color": "#ffcc44", "opacity": 0.9,
             "thickness": 0.02, "wireframe": false }
}
```

### Box

```json
{
  "id": "b1", "layer": "scene", "kind": "Box",
  "center": [0, 0, 0], "size": [1, 1, 1], "rotation": null,
  "style": { "style_type": "BoxStyle", "color": "#88ccff", "opacity": 0.9,
             "wireframe": false }
}
```

- `size` = full side lengths (half-extents are `size / 2` on the SDF path).
- `rotation` is `null` or an Euler `[rx, ry, rz]` triple (a Python `Rotor` is
  converted to Euler at serialization time).

### Ellipsoid

```json
{
  "id": "e1", "layer": "scene", "kind": "Ellipsoid",
  "center": [0, 0, 0], "radii": [1.0, 0.5, 0.75], "rotation": null,
  "style": { "style_type": "EllipsoidStyle", "color": "#ffaa00", "opacity": 0.9,
             "wireframe": false }
}
```

### Ellipse (filled 2D)

```json
{
  "id": "e2", "layer": "scene", "kind": "Ellipse",
  "center": [0, 0, 0], "radiusU": 1.0, "radiusV": 0.5, "normal": [0, 0, 1],
  "style": { "style_type": "EllipseStyle", "color": "#ff44ff", "opacity": 0.9,
             "thickness": 0.02, "wireframe": false }
}
```

### RegularPolygon

```json
{
  "id": "r1", "layer": "scene", "kind": "RegularPolygon",
  "center": [0, 0, 0], "radius": 1.0, "sides": 6, "normal": [0, 0, 1],
  "angle": 0.0,
  "style": { "style_type": "RegularPolygonStyle", "color": "#44ffaa", "opacity": 0.9,
             "thickness": 0.02, "wireframe": false }
}
```

- `radius` = circumradius. `sides` ≥ 3. `angle` is an in-plane rotation
  (radians).

## Architecture (short)

- **Python entities** — frozen, viz-only dataclasses under
  `py/pytanga/geometry/entities/`, coerced via `to_point` / `to_direction` /
  `to_float` (no `_convert_mv` branch), exported from `pytanga.geometry`.
- **Styles** — mesh styles in `_styles/_entity_styles.py`; SDF styles in
  `_styles/_sdf_style.py` (each carries only SDF-implementable knobs). Both are
  registered in `_styles/__init__.py` (imports + `ObjVizStyle` union +
  `_DEFAULT_STYLE_FOR_KIND`), in `_style_dict.py` (`_kind_to_key`,
  `_make_default_label_styles`, `_make_default_tex_label_styles`), and exported
  from `pytanga.viz`.
- **Serializer** — `_serialize_<kind>` in `viz/serializer.py`; new kinds added to
  the `SceneEntity` union in `viz/_types.py`.
- **Frontend** — new renderer modules under `templates/renderers/`
  (`disk.js`, `partial_disk.js`, `box.js`, `ellipsoid.js`, `ellipse.js`,
  `regular_polygon.js`), dispatched by `renderers/factory.js` and registered in
  the export bundle (`_RENDERER_FILES` in `export/_bootstrap/_html.py`), so the
  live viewer and static HTML export stay in lockstep.
- **SDF** — `Disk`/`Box`/`Ellipsoid`/`Ellipse` reuse existing primitives
  (`cappedCylinder`, `box`, `ellipsoid`); `PartialDisk` and `RegularPolygon`
  require **two new GLSL primitives** (`sdPartialDisk`, `sdRegularPolygon`) plus
  their JS emitters and Python constructors. Entity → SDF lowering lives in
  `sdf/object.py` (`_entity_to_sdf`) and `sdf/serializer.py` (`_dispatch_tree` /
  `_*_tree`).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-entities.md](./01-python-entities.md) | Six viz-only dataclasses + `regular_polygon()` + exports (+ tests) |
| 2 | [02-style-classes.md](./02-style-classes.md) | Mesh + SDF style classes, canonical defaults, exports (+ tests) |
| 3 | [03-serializer-wire-contract.md](./03-serializer-wire-contract.md) | `SceneEntity` wiring + `_serialize_*` (+ tests) |
| 4 | [04-frontend-renderers.md](./04-frontend-renderers.md) | Six Three.js renderers + factory dispatch + export bundle |
| 5 | [05-sdf-primitives.md](./05-sdf-primitives.md) | `sdPartialDisk` / `sdRegularPolygon` GLSL + emitters + Python constructors (+ tests) |
| 6 | [06-sdf-entity-mapping.md](./06-sdf-entity-mapping.md) | `_entity_to_sdf` + `_dispatch_tree` + `SDF_STYLE_BY_KIND` (+ tests) |
| 7 | [07-integration-tests.md](./07-integration-tests.md) | End-to-end example + full regression + JS syntax checks |
| 8 | [08-docs-changelog.md](./08-docs-changelog.md) | Docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/geometry/test_viz_entities.py
  py/tests/viz/test_viz_styles.py py/tests/viz/test_serializer.py -q` for the
  new/updated unit tests, plus the existing `py/tests/viz/` and
  `py/tests/viz/sdf/` suites for regression.
- **JS (browser modules):** `node --input-type=module --check` on each touched
  renderer / `factory.js`; `uv run pytest py/tests/viz/test_export_renderers.py
  -q` verifies the export bundle stays in lockstep with the on-disk renderer set.
  DOM/Three.js behavior is validated by browser smoke + the manual viewer.
- Every phase ends with a runnable validation command before the next phase.

## Guiding decisions / no-refactor rule

- The wire contract above is **fixed now**; later phases implement *against* it
  and never change it.
- Radians end-to-end; `startDirection` / `rotation` are resolved **Python-side**
  so the frontend always receives concrete, valid values.
- Mesh renderers follow the shared `createEntityMesh` pipeline (like
  `cylinder.js` / `arc.js`), never a bespoke path.
- New SDF primitives are **additive** — the existing primitive library and its
  wire contract are unchanged.
- Only SDF-implementable knobs live on `Sdf*Style` classes (never `wireframe` /
  `texture_label` / `double_sided`).

## Deferred (not in this plan)

`RoundBox`, `Cone`, `CappedCone`, solid `Torus`, `Capsule`, and an explicit
`Segment` entity — the remaining SDF objects without a matching Geometry entity
(see the gap table above). They follow the same phase pattern when picked up.

