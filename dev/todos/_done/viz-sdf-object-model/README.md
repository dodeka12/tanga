# Viz SDF Object Model — Overview

**Created:** 2026-08-25 | **Status:** Implemented (Phase 6.4 manual browser smoke pending) | **Branch:** `feat/sdf-viewer`

## Goal

Redesign the standard viewer's SDF drawing API around a unified, composable
**object model**. This is the follow-up to the completed `viz-sdf-objects` plan
(per-object SDF proxy renderer) and replaces the "style-as-marker" opt-in with
explicit, typed SDF objects:

- **Per-entity SDF styles** — `SdfSphereStyle`, `SdfLineStyle`, `SdfCircleStyle`,
  `SdfPointStyle`, `SdfCylinderStyle`, `SdfPlaneStyle`, each derived from a
  common `SdfStyle` and carrying **only SDF-implementable** parameters (never
  `wireframe` / `texture_label` / `double_sided`).
- **`SdfObject`** — a first-class element that bundles a geometry entity + an
  optional id + its own per-entity SDF style. `Visualizer.add()` / `new()`
  accept it directly (no separate `style=SdfStyle(...)` switch).
- **Operator composition** — `+`/`|` (union), `-` (subtract), `&` (intersection),
  `^` (xor / symmetric difference), and unary `-`/`~` (subtract / intersection
  *polarity* for group membership), backed by an `ECompose` string enum and a
  `Combine` binary node.
- **Per-object materials** — a multi-member SDF object (`Combine` / `Composed` /
  `SdfGroup`) keeps an independent color/opacity **per member**. The group proxy
  switches from `float map()` to `vec2 map()` (distance + material index) plus a
  material table, reusing the fullscreen viewer's material machinery.

The fullscreen `SdfVisualizer` (`sdf_viewer.html`) is **unchanged**.

## Non-goals / backward compatibility

- Keep the existing `SdfStyle` marker + `Visualizer.add(Sphere(...),
  style=SdfStyle(...))` path working (deprecated, not removed).
- `SdfNode` (the low-level GLSL descriptor) stays internal; users deal with
  `SdfObject` / `Combine` / `Composed` / `SdfGroup`.
- The fullscreen `SdfVisualizer` and its wire contract are unchanged.
- Mutual shadows between SDF objects and meshes remain deferred (unchanged from
  `viz-sdf-objects`).

## Architecture (short)

```
Python backend                                          Frontend (three.js)
─────────────                                          ────────────────────
SdfObject(entity, id, style)  ── _entity_to_sdf() ──▶  SdfNode tree
   │  (leaf; operators via SdfElement base)
Combine(op, a, b)               (binary CSG node; from +,-,&,|,^)
Composed / SdfGroup             (ordered fold of elements + ECompose modes;
   │                              SdfGroup keeps runtime member transforms)
   ▼
sdf/serializer.py  ──▶  scene object { kind:"sdf", tree, members?, materials?, bound,
                                       transform, style }
   │
   ▼
renderers/factory.js ── case "sdf" ──▶ createSdfProxy()
   single member:  vec2 map()  + uMaterial[0] (index always 0)   (unchanged cost)
   multi member:   vec2 map()  + uMaterial[MAX_GROUP_MEMBERS]      (new)
```

Reuse (no reimplementation): `sdf/objects/*.js` tree emitters, `primitives.glsl` +
`combinators.glsl` + `sdf_common.glsl`, the raymarch shading core, the
directional-light model, and — for per-object materials — the fullscreen
viewer's `material-table.js` packing + `vec2 map` fold pattern.

## Wire contract (fixed up front)

### Single `SdfObject` (unchanged from `viz-sdf-objects`)

```json
{
  "id": "o1", "layer": "scene", "kind": "sdf", "sdfKind": "Sphere",
  "tree": { "kind": "sphere", "params": { "radius": 1.0 } },
  "bound": { "min": [-1.05, -1.05, -1.05], "max": [1.05, 1.05, 1.05] },
  "color": "#44ff44", "opacity": 1.0,
  "transform": { "position": [0,0,0], "rotation": [0,0,0], "scale": [1,1,1] },
  "style": { "style_type": "SdfSphereStyle" }
}
```

### Multi-member (`Combine` / `Composed` / `SdfGroup`) — new

```json
{
  "id": "g1", "layer": "scene", "kind": "sdf", "sdfKind": "SdfGroup",
  "tree": { "kind": "group", "children": [
      { "kind": "sphere", "params": { "radius": 1.0 } },
      { "kind": "cappedCylinder", "params": { "halfHeight": 1.5, "radius": 0.35 }, "combine": "subtract" }
  ]},
  "members": [
      { "transform": { "position": [0,0,0], "rotation": [0,0,0], "scale": [1,1,1] },
        "bound": { "min": [-1.05,-1.05,-1.05], "max": [1.05,1.05,1.05] } },
      { "transform": { "position": [0,0,0], "rotation": [0,0,0], "scale": [1,1,1] },
        "bound": { "min": [-0.4,-1.55,-0.4], "max": [0.4,1.55,0.4] } }
  ],
  "materials": [
      { "color": "#ffaa00", "opacity": 1.0 },
      { "color": "#44ff44", "opacity": 0.5 }
  ],
  "bound": { "min": [-1.55,-1.55,-1.05], "max": [1.55,1.55,1.05] },
  "transform": { "position": [0,0,0], "rotation": [0,0,0], "scale": [1,1,1] }
}
```

- `materials[i]` corresponds to member `i` (material index == member index, the
  fold assigns the winner's index by serialization order).
- `members` is present only for `SdfGroup` (runtime-transformable members);
  `Composed`/`Combine` are fixed trees and omit it.
- `tree.children[i]` carries the per-member `combine` mode; `Combine`'s binary
  structure lowers to nested `combine` nodes.



## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-sdf-styles.md](./01-python-sdf-styles.md) | Per-entity `Sdf*Style` classes + kind→style registry (+ tests) |
| 2 | [02-python-ecompose-sdfelement-operators.md](./02-python-ecompose-sdfelement-operators.md) | `ECompose` enum + `SdfElement` base (operators) + `Combine` (+ tests) |
| 3 | [03-python-sdfobject-entity-conversion.md](./03-python-sdfobject-entity-conversion.md) | `SdfObject` wrapper + `_entity_to_sdf()` (incl. `Cylinder`) (+ tests) |
| 4 | [04-python-composed-group-refactor.md](./04-python-composed-group-refactor.md) | `Composed`/`SdfGroup` refactor + `viz.add()`/`new()` accept `SdfObject`/`Combine` + serialization (+ tests) |
| 5 | [05-frontend-group-material-table.md](./05-frontend-group-material-table.md) | Per-object materials: `vec2 map()` + material table in the group proxy |
| 6 | [06-integration-example-tests.md](./06-integration-example-tests.md) | Examples + full regression + browser smoke |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/ -q` and `py/tests/viz/sdf/ -q`; new
  files `test_sdf_styles.py`, `test_ecompose_operators.py`, `test_sdf_object.py`,
  plus updated `test_sdf_group.py` / `test_composed.py`.
- **JS (pure modules):** `node --test 'dev/src/js-tests/*.test.mjs'`; extend
  `dev/src/sdf_proxy_smoke.mjs` for the `vec2 map` + material-table group.
- **DOM/browser modules** (`sdf.js`, `factory.js`) are validated by browser smoke
  pages + the manual viewer (no DOM test harness in the repo).
- Every phase ends with a runnable validation command before the next phase.

## Guiding decisions / no-refactor rule

- **Entity → SDF conversion happens at construction** (`_entity_to_sdf` in
  `SdfObject`/`Composed`/`SdfGroup`), never deep in the serializer. The
  serializer's `_dispatch_tree`/`_*_tree` stays for the fullscreen viewer's
  top-level entities only.
- **The proxy `map()` returns `vec2(distance, materialIndex)`** — single objects
  return `vec2(d, 0.0)` and groups propagate the winner's index, so `proxy.glsl`
  needs only one body (no float/vec2 split, and the extra component is
  negligible for single objects).
- **Operators live on `SdfElement` only** — geometry entities (`Sphere`, …) are
  not patched; `_coerce()` wraps a raw entity into an `SdfObject` on demand.
- **XOR is binary-only** — it cannot be a `SdfGroup`/`Composed` fold mode (the
  ordered fold is unary `acc = op(acc, d)`); it exists only as `A ^ B`.
- **`ECompose` is string-compatible** (`ECompose.SUBTRACT == "subtract"`), so the
  legacy string modes keep working.
