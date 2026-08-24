# Viz-only Geometry Entities (Cylinder & Arc) — Overview

**Created:** 2026-08-24 | **Status:** Planned | **Branch:** `feat/multi-view`

## Goal

Add two geometric entities that exist **purely for visualization** and cannot be
converted into multivectors:

- **`Cylinder`** — length, radius, main axis, and origin.
- **`Arc`** — an arcing cylinder (partial torus) with origin, rotation axis,
  arc radius, cylinder radius, arc angle (**in radians**), and an optional
  **cone arrow tip at its end**.

Each entity gets its own default style class (`CylinderStyle`, `ArcStyle`) and
a Three.js frontend renderer, wired through the existing serializer / scene /
export pipeline.

## Scope boundaries (fixed up front)

- New entities live in `py/pytanga/geometry/entities/` but are **not** members
  of the `Entity` union, so `Geometry.create()` / `analyze()` reject them (they
  are not MV-representable). They flow through the viz-only path
  (`Visualizer._add_to_scene` → `scene.add_object`), exactly like `PointPath` /
  `Axis` / `Grid`.
- Each entity gets a dedicated style class with a canonical default registered
  in `_DEFAULT_STYLE_FOR_KIND` (`py/pytanga/viz/_styles/__init__.py`).
- Frontend renderers are new modules under `py/pytanga/viz/templates/renderers/`,
  dispatched by `factory.js` and listed in
  `export/_bootstrap/_html.py::_RENDERER_FILES`. They follow the **exact same
  `createEntityMesh` pipeline as every other renderer**, so the live viewer and
  static HTML export render them identically — the export bootstrap
  (`generate_bootstrap_js`) concatenates `_RENDERER_FILES` (imports and
  `export` keywords stripped), so `render_snapshot()` / `render_figure()` of a
  scene containing a `Cylinder`/`Arc` works out of the box with no extra wiring.

## Canonical wire contract (fixed up front; both sides implement against this)

### Cylinder

```json
{
  "id": "c1", "layer": "scene", "kind": "Cylinder",
  "origin": [0, 0, 0],
  "axis": [0, 0, 1],
  "length": 1.0,
  "radius": 0.1,
  "alignCenter": 0.0,
  "style": {
    "style_type": "CylinderStyle",
    "color": "#44aaff", "opacity": 0.9,
    "wireframe": false
  }
}
```

- `alignCenter` anchors `origin` along the axis: `0` (default) = the cylinder
  starts at `origin` and extends `length` along the normalized `axis`; `0.5` =
  `origin` is the center of the cylinder.  Intermediate values interpolate.
- `length` and `radius` are **content** fields (always present, positive).

### Arc

```json
{
  "id": "a1", "layer": "scene", "kind": "Arc",
  "origin": [0, 0, 0],
  "axis": [0, 0, 1],
  "radius": 1.0,
  "tubeRadius": 0.05,
  "angle": 6.283185307179586,
  "startDirection": [1, 0, 0],
  "arrow": null,
  "style": {
    "style_type": "ArcStyle",
    "color": "#ffcc44", "opacity": 0.9,
    "wireframe": false
  }
}
```

- `angle` is in **radians**; `2π` (the default) renders a full torus. The
  frontend clamps it to `[0, 2π]`.
- `startDirection` is a **normalized** vector perpendicular to `axis`. When the
  user omits it, it is computed on the Python side (deterministic), so the
  frontend always receives a valid arc start point.
- `arrow` is `null`, or `{ "length": 0.15, "radius": 0.1 }` when the arc's
  `show_arrow` is `True`. The effective length/radius are resolved on the Python
  side (defaults derive from `tubeRadius`) so the frontend never has to compute
  fallbacks.

## Architecture (short)

- **Python entity dataclasses** (`cylinder.py`, `arc.py`) are frozen, pure data
  containers with no `MV`-conversion branch — unlike `Point`/`Sphere`/… which
  route MVs through `_convert_mv`.
- **Serializer** adds `_serialize_cylinder` / `_serialize_arc` leaves to
  `serializer.py::_dispatch_entity`, following the existing `_apply_defaults`
  style-merge pattern (content fields camelCase, style fields snake_case).
- **Styles** add `CylinderStyle` / `ArcStyle` to `_styles/_entity_styles.py`,
  register them in `_styles/__init__.py` (imports + `ObjVizStyle` union +
  `_DEFAULT_STYLE_FOR_KIND`), and export them from `pytanga.viz`.
- **Frontend** adds `renderers/cylinder.js` and `renderers/arc.js` (each with a
  `create*` + `update*`), dispatched by `renderers/factory.js` and listed in the
  export bundle (`_RENDERER_FILES`) — the same shared path as every other
  renderer, so static HTML export (`render_snapshot`/`render_figure`) picks
  them up automatically (imports are stripped, `export` keywords stripped).
- **Type wiring** adds `Cylinder` / `Arc` to the `SceneEntity` union in
  `viz/_types.py` so `Visualizer._resolve` passes them through unchanged.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-entities.md](./01-python-entities.md) | `Cylinder`/`Arc` dataclasses, auto `start_direction`, arrow-tip params (+ tests) |
| 2 | [02-style-classes.md](./02-style-classes.md) | `CylinderStyle`/`ArcStyle` + canonical defaults + exports (+ tests) |
| 3 | [03-serializer-wire-contract.md](./03-serializer-wire-contract.md) | `SceneEntity` wiring + `_serialize_cylinder`/`_serialize_arc` (+ tests) |
| 4 | [04-frontend-cylinder.md](./04-frontend-cylinder.md) | `cylinder.js` renderer + factory dispatch + export bundle |
| 5 | [05-frontend-arc.md](./05-frontend-arc.md) | `arc.js` renderer (with cone arrow tip) + factory dispatch + export bundle |
| 6 | [06-integration-tests.md](./06-integration-tests.md) | End-to-end example + full regression + JS syntax checks |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/geometry/test_viz_entities.py
  py/tests/viz/test_viz_styles.py py/tests/viz/test_serializer.py -q` for the
  new/updated unit tests, plus the existing `py/tests/viz/` suite for
  regression.
- **JS (browser modules):** `node --input-type=module --check` on each touched
  renderer/`factory.js` for syntax; `uv run pytest
  py/tests/viz/test_export_renderers.py -q` verifies the export bundle stays in
  lockstep with the on-disk renderer set and that `createCylinder`/`createArc`
  appear in the generated bootstrap. DOM/Three.js behavior is validated by
  browser smoke + the manual viewer (no DOM test harness in the repo).
- **Static HTML export:** because the renderers ride the shared pipeline,
  `test_export_static.py`-style assertions (`"function createCylinder("` /
  `"function createArc("` in `render_snapshot()` output) prove the standalone
  export works out of the box — see Phase 6.
- Every phase ends with a runnable validation command before the next phase
  starts — no "test phase at the end".

## Guiding decisions / no-refactor rule

- The wire contract above is **fixed now**; later phases implement *against* it
  and never change it, so no earlier phase is refactored.
- `Arc.angle` is radians end-to-end (Python stores/serializes radians; the
  frontend passes the value straight to `THREE.TorusGeometry`'s `arc` parameter
  after clamping to `[0, 2π]`).
- `startDirection` and the arrow tip's length/radius are resolved **Python-side**
  so the frontend always receives concrete, valid values (mirrors how `Line`
  resolves `length` before serializing).
- Renderers are implemented **like every other renderer** — a module under
  `templates/renderers/` dispatched by `factory.js` and registered in
  `_RENDERER_FILES` — rather than a bespoke path, so the live viewer and static
  HTML export stay in lockstep automatically (`test_export_renderers.py` +
  `test_export_static.py`).
