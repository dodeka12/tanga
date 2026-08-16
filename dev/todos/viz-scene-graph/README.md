# Viz Scene Graph — Overview

**Created:** 2026-08-16 | **Status:** Planned (revised after design discussion)

## Target

Refactor the visualizer's flat `SceneObject` registry into a full **scene
graph** with persisted, fully-resolved visualization objects, explicit
per-object transforms, container nodes (`VizGroup`), first-class overlay
objects (labels/annotations/titles/controls), and a convenience reference
class (`VizObjectRef`) for mutating objects without tracking raw IDs.

The Python side becomes the authoritative source of truth: every node stores
its resolved geometry + style + transform and can serialize itself. The
browser rebuilds the same hierarchy via three.js and applies **partial,
aspect-scoped updates** (`full` / `style` / `transform`) in place, enabling
fast rotation/movement of compound objects without recomputing any vertices.

## Layer model (two sub-graphs)

- **Scene layer** nodes carry a canonical `Transform` (position + Euler
  rotation + scale) and participate in a parent/child tree (`VizGroup`
  containers). Rendered via `THREE.Object3D` hierarchy.
- **Overlay layer** nodes (labels, annotations, titles, controls) live in the
  screen/CSS plane. They carry a `position` anchor plus an optional
  `attach_to` scene-node reference — **no** `Transform`. The frontend
  **live-follows** the referenced node's resolved world position.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-transform-math.md](./01-transform-math.md) | `_transforms.py`: operator/entity → 4×4 matrix and TRS converters (+ unit tests) — **DONE** |
| 2 | [02-style-defaults.md](./02-style-defaults.md) | `VizStyleDefaults`: bundle default styles into one copyable holder; scenes snapshot a copy (+ unit tests) — **DONE** |
| 3 | [03-node-hierarchy.md](./03-node-hierarchy.md) | `_nodes.py`: `VizNode` / `VizSceneObject` / `VizOverlayObject` / `VizGroup` + aspect-dirty tracking + resolved-at-creation styles; migrate `Scene.add`/`add_label`/`add_object` to nodes (+ unit tests) — **DONE** |
| 4 | [04-node-serialization.md](./04-node-serialization.md) | Move serialization dispatch into node `serialize()`; emit `full/style/transform` aspect patches (+ unit tests) |
| 5 | [05-object-ref.md](./05-object-ref.md) | `VizObjectRef`: property/method API incl. labels and transform aspects (+ unit tests) |
| 6 | [06-entry-points.md](./06-entry-points.md) | `Visualizer` / `VizSceneHandle` `new()` / `add_group()` / `parent_id` / `attach_to` / control update (+ unit tests) |
| 7 | [07-frontend-scene-graph.md](./07-frontend-scene-graph.md) | Frontend: `object_update` aspect patches + parenting + live-follow overlays (+ smoke test) |
| 8 | [08-export-static.md](./08-export-static.md) | Ensure standalone and figure HTML exports still work end-to-end |
| 9 | [09-end-to-end.md](./09-end-to-end.md) | Live viewer + recording + GLTF compound/group verification |
| 10 | [10-example.md](./10-example.md) | Example script under `py/examples/viz` demonstrating `VizGroup` + direct transforms |
| 11 | [11-docs.md](./11-docs.md) | Update docs with the new scene-graph / `VizObjectRef` / `VizGroup` features |
| 12 | [12-changelog.md](./12-changelog.md) | Add a changelog entry following `dev/workflows/changelog.md` |
| 13 | [13-content-update.md](./13-content-update.md) | `content` aspect (in-place entity geometry update) + remove legacy flat-entity path and consolidate frontend maps — **PLANNED** |
| 14 | [14-render-pipeline-consolidation.md](./14-render-pipeline-consolidation.md) | Unify live/export render pipeline: shared `scene-builder.js` + single `objects`/`attach_to` wire format — **PLANNED** |

## Guiding decisions

- **Layer split:** `VizSceneObject` (Transform + parent/child graph) vs
  `VizOverlayObject` (position + `attach_to`). Only scene nodes get a
  `Transform`; overlay nodes have no rotation/scale.
- **Transform is additive ("extra transform on top").** Entity geometry keeps
  its own positions; a node's `transform` is an additional transform starting
  at identity.
- **Aspect-patch updates.** Instead of two boolean dirty flags, each node
  tracks which *aspects* changed (`full`, `style`, `transform`) and `flush()`
  emits an `object_update` message with a `patches` list. `style` is a coarse
  aspect (whole resolved style dict); `transform` is one aspect, not special.
- **Store only the resolved style** at creation (canonical + non-`None` user
  merges). Style patches re-serialize that resolved instance.
- **Default styles are snapshotted per scene.** The `Visualizer` owns a
  canonical `VizStyleDefaults` holder; each `Scene` receives a **copy** at
  creation.  Mutating the Visualizer defaults later does not affect existing
  scenes — mutate a scene's own holder to change its defaults.
- **Labels and overlays are first-class nodes**, not special-cased data. They
  expose the same patch aspects (`full`/`style`) and are discovered via
  `get_label_ids(...)` / the reference API.
- **Controls stay on a separate `controls_define` channel**, but are
  attachable to scene nodes (via `attach_to`) and gain an `update_control`
  path for post-creation mutation.
- **Frontend live-follows** overlay `attach_to` targets each frame; Python does
  not recompute overlay anchors on parent moves.
- **Python-authoritative graph**, serialized as a flat DFS pre-order list with
  `parent_id` / `attach_to`.
- **Backward compatible:** `add()` keeps returning a `str` id; `new()` returns
  a `VizObjectRef`.
- Operator→matrix math lives in a standalone `_transforms.py` module.
- Every implementation phase includes unit tests covering its main behaviors.