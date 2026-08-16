# Phase 2 — Node hierarchy (`_nodes.py`)

**Status:** Planned (revised after design discussion)

## Goal

Introduce the scene-graph node classes that become the authoritative source of
truth for the visualizer:

- `Transform` (canonical TRS) — reused from Phase 1 primitives.
- `VizNode` (base: id/name/layer/kind/visible + aspect-dirty tracking).
- `VizSceneObject` (scene layer: has `Transform` + parent/child graph).
- `VizOverlayObject` (overlay layer: has `position` + optional `attach_to`,
  **no** `Transform`).
- `VizGroup` (a `VizSceneObject` container, `kind="VizGroup"`).

Replace the flat `SceneObject` registry conceptually; full `Scene` adoption is
in this phase's `scene.py` integration section (kept as a backward-compatible
shim until Phase 3/5 migrate callers).

## Files

- New: `py/pytanga/viz/_nodes.py`
- Modify: `py/pytanga/viz/scene.py` (keep existing `SceneObject` working; add
  node-based accessors used by later phases; this phase also performs the
  control-group rename already landed.)

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
- **Resolved style only.** `VizSceneObject`/`VizOverlayObject` store a fully
  resolved style instance (canonical default + non-`None` user overlays).

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

- [ ] `class Transform` (reuse `_transforms` primitives)
  - [ ] fields: `position`, `rotation` (Euler `"XYZ"`), `scale`
  - [ ] `matrix()` derived from TRS
  - [ ] `from_matrix(M)` / `set_matrix(M)` via `to_trs`
  - [ ] `apply_matrix(M, space="local"|"world")`
  - [ ] mutators `translate(...)`, `rotate(axis, angle)`, `scale_by(...)`,
        `set(...)` — note `scale_by` avoids clashing with the `.scale` field.
- [ ] `class VizNode`
  - [ ] fields: `id`, `name`, `layer`, `kind`, `visible`
  - [ ] `_dirty_aspects: set[str]`
  - [ ] `mark(kind="full")` — set the aspect (full clears style/transform)
  - [ ] `dirty_for(aspect) -> bool`, `consume_dirty() -> set[str]`
  - [ ] `serialize() -> dict` base fields (id/layer/kind/visible)
- [ ] `class VizSceneObject(VizNode)`
  - [ ] fields: `entity`, `style` (resolved), `transform`, `parent`,
        `children`, `name`
  - [ ] `add_child` / `remove_child` / `world_matrix()`
  - [ ] setters: `set_entity` (marks `full`), `set_style`/`set_color`/
        `set_opacity`/`set_texture_label` (each marks `style`),
        `set_transform`/`translate`/`rotate`/`scale_by` (each marks
        `transform`)
  - [ ] non-`None` deep style merge helper
- [ ] `class VizOverlayObject(VizNode)`
  - [ ] fields: `position`, `attach_to`, `style` (resolved), `payload`
        (kind-specific: text/title/annotation)
  - [ ] setters: `set_payload`, `set_position` (full), `set_style` (style)
- [ ] `class VizGroup(VizSceneObject)`
  - [ ] no `entity`/`style`; `kind="VizGroup"`.

### `scene.py` integration

- [ ] Keep `SceneObject`/`Scene` existing behavior intact (all current tests
      must still pass).
- [ ] Add `_nodes: dict[str, VizNode]` (populated on `add_object` alongside
      `_objects`) so later phases can migrate incrementally.
- [ ] Add `Scene.get_node(object_id) -> VizNode` accessor.
- [ ] Add a `Scene.add_group(name=None) -> VizGroup` (scene-graph group; this
      is distinct from the already-renamed `add_control_group`).
- [ ] Add `Scene.group_ids` / node-tree DFS helpers (used by Phase 3/5).

## Unit tests

File: `py/tests/viz/test_nodes.py` (replace current prototype assertions to
match the layer split + aspect model; keep existing Transform tests).

- [ ] `test_transform_matrix` / `from_matrix` / `scale_by` / mutators.
- [ ] `test_scene_object_aspects` — `set_entity` marks `full`; `set_style`
      marks `style`; `set_transform` marks `transform`.
- [ ] `test_scene_object_parenting` — add/reparent/remove + world matrix.
- [ ] `test_overlay_object_no_transform` — overlay has `position`/`attach_to`
      and no `Transform`.
- [ ] `test_group_serialize` — `kind == "VizGroup"`, no geometry/style.
- [ ] `test_resolved_style_creation` — canonical defaults + non-`None` merge.

## Verification

- [ ] `uv run pytest py/tests/viz/test_nodes.py` passes.
- [ ] Existing viz tests still pass (scene.py compatibility shim).
- [ ] `VizSceneObject` transform changes set only the `transform` aspect.
- [ ] `VizOverlayObject` has `position`+`attach_to`, not a `Transform`.
- [ ] `Scene.add_group` returns a `VizGroup` distinct from control groups.