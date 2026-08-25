# Viz SDF Objects — Overview

**Created:** 2026-08-25 | **Status:** Done | **Branch:** `feat/sdf-viewer`

## Goal

Let the **standard viewer** render *some* scene objects as smooth, ray-marched
signed-distance-field (SDF) solids, mixed with the normal vertex/mesh pipeline
in the same scene, opted in **per object via a style class**. This is the
"bounding-volume proxy mesh" technique (option B): each SDF object becomes a
regular `Object3D`/mesh in the existing scene graph whose fragment shader
ray-marches *that one* object's distance field and writes `gl_FragDepth`, so
occlusion against meshes and against other SDF objects is handled by the
standard depth buffer with no offscreen target and no manual compositing.

The existing `SdfVisualizer` (fullscreen `sdf_viewer.html`) is **unchanged**;
this plan turns SDF rendering into a *per-object renderer option* of the
standard viewer rather than a separate viewer.

## Non-goals / deferred

- **Cross-object CSG** (union/intersect/subtract *across* two scene objects).
  A single object can still be internally `Composed` (its own combinator tree,
  e.g. a bead with a drilled hole). See "Guiding decisions".
- **Mutual shading** — SDF objects casting/receiving shadows on other objects
  is deferred to Phase 6 (shared rasterized shadow maps).
- `wireframe`, `TripleReflection`, `VersorFactors` — already unsupported by the
  SDF serializer; behaviour unchanged.

## Architecture (short)

```
Python backend                                     Frontend (three.js)
─────────────                                     ────────────────────
Entity + SdfStyle (style class)
    │
    ▼
serializer.py  ──detects SdfStyle──▶  sdf/serializer.py  (local-space tree)
    │                                      │
    │                                      └─▶ sdf/bounds.py  (local AABB)
    ▼
scene object { kind:"sdf", sdfKind, tree, bound,
               color, opacity, transform, parent_id, style, interaction }
    │   (same scene_update / object_update WS messages)
    ▼
scene-builder.js ──▶ renderers/factory.js ──▶ case "sdf"
                                                 │
                                                 ▼
                              createSdfProxy(): proxy BoxGeometry (sized to bound)
                                + ShaderMaterial (passthrough vertex; fragment
                                ray-marches the single-object map(p) in LOCAL
                                space, writes gl_FragDepth)
```

Reuse (no reimplementation): `sdf/objects/*.js` tree emitters, `primitives.glsl`
+ `combinators.glsl` + `sdf_common.glsl`, the raymarch shading core from
`raymarch.glsl`, and the SDF viewer's directional-light uniform model. The only
things *replaced* are the global `composer.js` fold and the `material-table.js`
(both become per-object: `float map(vec3 p) { return <emitTree(tree)>; }` plus a
single `uColor`/`uOpacity` uniform).


## Wire contract (fixed up front; both sides implement against this)

A scene object with `kind:"sdf"` (server → client, inside the existing
`scene_update` / `object_update` messages):

```json
{
  "id": "obj-1",
  "layer": "scene",
  "kind": "sdf",
  "sdfKind": "Sphere",
  "tree": { "kind": "sphere", "params": { "radius": 1.0 } },
  "bound": { "min": [-1.0, -1.0, -1.0], "max": [1.0, 1.0, 1.0] },
  "color": "#ff4444",
  "opacity": 1.0,
  "transform": { "position": [0, 0, 0], "rotation": [0, 0, 0], "scale": [1, 1, 1] },
  "parent_id": null,
  "style": { "style_type": "SdfStyle" },
  "interaction": null
}
```

- `tree` is the `SdfNode.to_dict()` of the object, emitted in **local (object)
  space**; `transform` carries *all* placement (intrinsic geometry placement
  composed with any user `transform=`).
- `bound` is a conservative **local-space AABB** used to size the proxy box.
- `color` / `opacity` are the resolved style values (same priority as the mesh
  path: per-entity props > style > canonical > builtin).
- The frontend treats `kind:"sdf"` like any other scene-layer object: transform
  wrap, `parent_id` parenting, labels, interaction, and removal all reuse
  `scene-builder.js` unchanged.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-sdf-style.md](./01-python-sdf-style.md) | `SdfStyle` style class + serializer routing to emit `kind:"sdf"` (+ tests) |
| 2 | [02-python-local-space-bounds.md](./02-python-local-space-bounds.md) | Local-space tree emission + conservative AABB `bound` computation (+ tests) |
| 3 | [03-frontend-sdf-proxy.md](./03-frontend-sdf-proxy.md) | `createSdfProxy()` — proxy box + per-object raymarch shader with `gl_FragDepth` |
| 4 | [04-frontend-factory-wiring.md](./04-frontend-factory-wiring.md) | `factory.js` `case "sdf"`, update/rebuild, disposal, WebGL2 gate + mesh fallback |
| 5 | [05-integration-example-tests.md](./05-integration-example-tests.md) | Mixed example + Python tests + browser smoke + regression |
| 6 | [06-shared-shadow-maps.md](./06-shared-shadow-maps.md) | *(deferred)* mutual SDF↔SDF / SDF↔mesh shadows via shared shadow maps |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/ -q` and the SDF-specific suites under
  `py/tests/viz/sdf/` (serializer, primitives); new files `py/tests/viz/sdf/
  test_sdf_style.py`, `test_bounds.py`, `test_standard_serializer_sdf.py`.
- **JS (pure modules only):** Node's built-in test runner on `.mjs` tests in
  `dev/src/js-tests/` — `node --test 'dev/src/js-tests/*.test.mjs'` (ESM, no
  `package.json`). Pure candidates: a bounds/`emitTree` helper and any
  non-DOM GLSL assembly helper.
- **DOM/browser modules** (`sdf.js`, `factory.js`) are validated by browser
  smoke pages + the existing manual viewer, since the repo has no DOM test
  harness.
- Every phase ends with a runnable validation command before the next phase
  starts — no "test phase at the end".

## Guiding decisions / no-refactor rule

- **Coordinate space is decided now:** SDF proxy trees are **local-space**; the
  node `Object3D` transform carries all placement. This is what makes
  animation (tweens on `position`/`rotation`/`scale`), interaction, and
  `parent_id` parenting work identically for SDF and mesh objects. The
  world-space `SdfVisualizer` path stays as-is.
- **Single-object `map()`:** the global `composer.js` fold is not reused; each
  proxy marches only its own `emitTree(tree)`. Consequently CSG is *per-object*
  only (cross-object CSG is a non-goal).
- **Lighting:** reuse the SDF viewer's directional-light uniform model
  (`lightPreamble` / `setLightUniforms`), factored into a shared module so both
  viewers use one source of truth; defaults align with the standard viewer's
  ambient + directional lights. A shading mismatch vs `MeshPhongMaterial` is
  accepted (cosmetic).
- **WebGL2 gate:** SDF objects need GLSL3 + `gl_FragDepth` (WebGL2). On WebGL1
  the renderer falls back to the mesh renderer for SDF-styled objects and warns
  once. The standard mesh pipeline keeps working on WebGL1.
- **No refactor:** the existing `Visualizer`, `SdfVisualizer`, mesh renderers,
  and the `scene_update`/`object_update` wire messages are unchanged; SDF
  objects are purely additive (`kind:"sdf"`).
