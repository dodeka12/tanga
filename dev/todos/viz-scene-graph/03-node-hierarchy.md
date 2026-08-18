# Phase 3 — Node hierarchy (`_nodes.py`)

**Status:** Done (revised after design discussion)

## Goal

Introduce the scene-graph node classes that become the authoritative source of
truth for the visualizer, and migrate the flat `SceneObject` registry onto
them. By the end of this phase:

- every drawable is a node (`VizSceneObject` or `VizOverlayObject`) with an
  **already-resolved** style stored at creation (canonical default + non-`None`
  user overlays), and
- `Scene.add` / `Scene.add_label` / `Scene.add_object` create nodes (resolving
  styles via the scene's own `style_defaults` from Phase 2).

The classes are:

- `Transform` (canonical TRS) — reused from Phase 1 primitives.
- `VizNode` (base: id/name/layer/kind/visible + aspect-dirty tracking).
- `VizSceneObject` (scene layer: has `Transform` + parent/child graph).
- `VizOverlayObject` (overlay layer: has `position` + optional `attach_to`,
  **no** `Transform`).
- `VizGroup` (a `VizSceneObject` container, `kind="VizGroup"`).

The existing `SceneObject` dataclass and `_objects` registry are kept as a
backward-compatible shim (serialized via `serializer.py`) until Phase 4 moves
serialization onto nodes and Phase 6 migrates the Visualizer callers.

## Files

- New: `py/pytanga/viz/_nodes.py`
- Modify: `py/pytanga/viz/scene.py`

## Key decisions

- **Layer split.** `VizSceneObject` carries a `Transform` and a parent/child
  graph; `VizOverlayObject` carries a `position` anchor + optional `attach_to`
  reference and no rotation/scale.
- **Transform is additive.** Entity geometry keeps its positions; the node
  `Transform` is an extra transform defaulting to identity.
- **Aspect-dirty tracking** replaces the boolean `dirty` /
  `transform_dirty` pair. Each node keeps a set of dirty aspects:
  `{"full"}`, or `{"style"}`, or `{"transform"}` (scene layer only). A full
  object change sets `{"full"}` (and clears `style`/`transform`).
- **Resolved style at creation.** `Scene` resolves each node's style from its
  own `style_defaults` holder (Phase 2) when the node is created. This phase is
  the single "cut-over": no style re-resolution happens later in Phase 4/5.

## Wire shape (agreed)

Node serialize (scene layer):

```json
{ "id": "...", "layer": "scene", "kind": "Point",
  "parent_id": null, "transform": {"position":[0,0,0],"rotation":[0,0,0],"scale":[1,1,1]},
  "visible": true, "...geometry...", "style": {...} }
```

Node serialize (overlay layer):

```json
{ "id": "...", "layer": "overlay", "kind": "label",
  "position": [x,y,z], "attach_to": "parent-or-null", "visible": true,
  "text": "...", "style": {...} }
```

## Steps

### `_nodes.py`

- [x] `class Transform` (reuse `_transforms` primitives)
  - [x] fields: `position`, `rotation` (Euler `"XYZ"`), `scale`
  - [x] `matrix()` derived from TRS
  - [x] `from_matrix(M)` / `set_matrix(M)` via `to_trs`
  - [x] `apply_matrix(M, space="local"|"world")`
  - [x] mutators `translate(...)`, `rotate(axis, angle)`, `scale_by(...)`,
        `set(...)` — note `scale_by` avoids clashing with the `.scale` field.
- [x] `class VizNode`
  - [x] fields: `id`, `name`, `layer`, `kind`, `visible`
  - [x] `_dirty_aspects: set[str]`
  - [x] `mark(kind="full")` — set the aspect (full clears style/transform)
  - [x] `dirty_for(aspect) -> bool`, `consume_dirty() -> set[str]`
  - [x] `serialize() -> dict` base fields (id/layer/kind/visible)
- [x] `class VizSceneObject(VizNode)`
  - [x] fields: `entity`, `style` (resolved), `transform`, `parent`,
        `children`, `name`
  - [x] `add_child` / `remove_child` / `world_matrix()`
  - [x] setters: `set_entity` (marks `full`), `set_style`/`set_color`/
        `set_opacity`/`set_texture_label` (each marks `style`),
        `set_transform`/`translate`/`rotate`/`scale_by` (each marks
        `transform`)
  - [x] non-`None` deep style merge helper
- [x] `class VizOverlayObject(VizNode)`
  - [x] fields: `position`, `attach_to`, `style` (resolved), `payload`
        (kind-specific: text/title/annotation)
  - [x] setters: `set_payload`, `set_position` (full), `set_style` (style)
- [x] `class VizGroup(VizSceneObject)`
  - [x] no `entity`/`style`; `kind="VizGroup"`.

### `scene.py` integration

- [x] Keep `SceneObject`/`Scene` existing behavior intact (all current tests
      must still pass) — the flat path stays the shim until Phase 4/6.
- [x] Add `_nodes: dict[str, VizNode]`; populate it from `add` / `add_label` /
      `add_object` by building a node whose style is resolved via
      `self.style_defaults` at creation.
- [x] Add node-construction helpers on `Scene` (e.g. `_make_scene_node(...)`,
      `_make_overlay_node(...)`) doing the resolve + store-in-`_nodes`.
- [x] Add `Scene.get_node(object_id) -> VizNode` accessor.
- [x] Add `Scene.add_group(name=None) -> VizGroup` (scene-graph group; this
      is distinct from the already-renamed `add_control_group`).
- [x] Add `Scene.add_node(node)` / `group_ids` / node-tree DFS helpers (used
      by Phase 4/6).

## Unit tests

File: `py/tests/viz/test_nodes.py`.

- [x] `test_transform_matrix` / `from_matrix` / `scale_by` / mutators.
- [x] `test_scene_object_aspects` — `set_entity` marks `full`; `set_style`
      marks `style`; `set_transform` marks `transform`.
- [x] `test_scene_object_parenting` — add/reparent/remove + world matrix.
- [x] `test_overlay_object_no_transform` — overlay has `position`/`attach_to`
      and no `Transform`.
- [x] `test_group_serialize` — `kind == "VizGroup"`, no geometry/style.
- [x] `test_resolved_style_creation` — canonical defaults + non-`None` merge.
- [x] `test_scene_add_populates_nodes` — `Scene.add(Point(...))` creates a
      `VizSceneObject` with a resolved style.
- [x] `test_scene_add_label_populates_nodes` — `Scene.add_label` creates a
      `VizOverlayObject` with resolved style and `attach_to`.
- [x] `test_get_node_and_add_group` — `get_node`/`add_group` round-trip.

## Verification

- [x] `uv run pytest py/tests/viz/test_nodes.py` passes.
- [x] Existing viz tests still pass (scene.py compatibility shim).
- [x] `VizSceneObject` transform changes set only the `transform` aspect.
- [x] `VizOverlayObject` has `position`+`attach_to`, not a `Transform`.
- [x] `Scene.add_group` returns a `VizGroup` distinct from control groups.
- [x] `Scene.add(...)` nodes carry a resolved style from `style_defaults`.
