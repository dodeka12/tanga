# Viz Scene Graph — Overview

**Created:** 2026-08-16 | **Status:** Planned

## Target

Refactor the visualizer's flat `SceneObject` registry into a full **scene
graph** with persisted, fully-resolved visualization objects, explicit
per-object transforms, container nodes (`VizGroup`), and a convenience
reference class (`VizObjectRef`) for mutating objects without tracking raw
IDs.

The Python side becomes the authoritative source of truth: every object
stores its resolved geometry + style + transform and can re-serialize itself.
The browser rebuilds the same hierarchy via three.js (`THREE.Group` /
`THREE.Object3D`) and applies transform-only updates in place, enabling fast
rotation/movement of compound objects without recomputing any vertices.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-transform-math.md](./01-transform-math.md) | `_transforms.py`: operator/entity → 4×4 matrix and TRS converters (+ unit tests) |
| 2 | [02-node-hierarchy.md](./02-node-hierarchy.md) | `_nodes.py`: `Transform`, `VizNode`, `VizObject`, `VizGroup` + dirty flags (+ unit tests) |
| 3 | [03-node-serialization.md](./03-node-serialization.md) | Move serialization dispatch into `VizObject.serialize()` (+ unit tests) |
| 4 | [04-object-ref.md](./04-object-ref.md) | `VizObjectRef`: property/method API incl. labels, texture label, transforms (+ unit tests) |
| 5 | [05-entry-points.md](./05-entry-points.md) | `Visualizer` / `VizSceneHandle` `new()` / `add_group()` / `parent_id` threading (+ unit tests) |
| 6 | [06-frontend-scene-graph.md](./06-frontend-scene-graph.md) | Frontend: `parent_id` + `transform` + `VizGroup` + `transform_update` (+ renderer smoke test) |
| 7 | [07-export-static.md](./07-export-static.md) | Ensure standalone and figure HTML exports still work end-to-end |
| 8 | [08-end-to-end.md](./08-end-to-end.md) | Live viewer + recording + GLTF compound/group verification |
| 9 | [09-example.md](./09-example.md) | Example script under `py/examples/viz` demonstrating `VizGroup` + direct transforms |
| 10 | [10-docs.md](./10-docs.md) | Update docs with the new scene-graph / `VizObjectRef` / `VizGroup` features |
| 11 | [11-changelog.md](./11-changelog.md) | Add a changelog entry following `dev/workflows/changelog.md` |

## Guiding decisions

- **Store only the resolved style** on each `VizObject`. Style updates are a
  non-`None` merge into that resolved instance.
- Separate **`dirty`** (object changed → full re-serialize) and
  **`transform_dirty`** (transform changed → lightweight `transform_update`).
- **Python-authoritative graph**, serialized as a flat DFS pre-order list with
  `parent_id`; three.js reconstructs the tree.
- **Backward compatible:** `add()` keeps returning a `str` id; `new()` returns
  a `VizObjectRef`.
- Container nodes are named **`VizGroup`**; a group's `VizObjectRef` exposes
  `add()` / `new()` to attach children directly.
- Operator→matrix math lives in a standalone `_transforms.py` module usable
  both by the scene graph and standalone user code.
- Every implementation phase includes unit tests covering its main behaviors.