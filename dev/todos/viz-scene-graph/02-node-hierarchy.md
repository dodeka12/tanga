# Phase 2 — Node hierarchy (`_nodes.py`)

**Status:** Planned

## Goal

Introduce the scene-graph node classes that become the authoritative source of
truth for the visualizer: `Transform`, `VizNode` (base), `VizObject`
(drawable), and `VizGroup` (container). Replace the flat `SceneObject` registry
with a node registry/tree while keeping `Scene` as the container facade.

## Files

- New: `py/pytanga/viz/_nodes.py`
- Modify: `py/pytanga/viz/scene.py` (adopt the node registry; keep public API)

## Key decisions

- Store **only** the resolved style on `VizObject` (no separate user-stored
  style). Style updates are a non-`None` merge into the resolved instance.
- Two independent flags per node: `dirty` (object changed) and
  `transform_dirty` (transform changed).
- `Transform` is TRS-canonical (position + Euler rotation + scale), deriving a
  4×4 matrix via `_transforms.py`.

## Steps

### `_nodes.py`

- [ ] `class Transform`
  - [ ] fields: `position`, `rotation` (Euler, order `"XYZ"`), `scale`
  - [ ] `matrix() -> np.ndarray` derived from TRS (use `_transforms.py`)
  - [ ] `from_matrix(M)` / `set_matrix(M)` (decompose via `to_trs`)
  - [ ] `apply_matrix(M, space="local")`:
    - `"local"`: `M_new = M_current @ M`
    - `"world"`: `M_new = M @ M_current`
  - [ ] mutation helpers `translate(...)`, `rotate(axis, angle)`,
        `scale(...)`, `set(...)`, each returning updated values so callers can
        pick up dirty state
- [ ] `class VizNode`
  - [ ] fields: `id`, `name`, `parent`, `children`, `transform`, `visible`,
        `layer`, `kind`, `dirty`, `transform_dirty`
  - [ ] `add_child(node)` / `remove_child(node)` (reparent bookkeeping)
  - [ ] `world_matrix()` (parent chain multiplication)
  - [ ] `serialize() -> dict` (base fields incl. `parent_id`, `transform`)
- [ ] `class VizObject(VizNode)`
  - [ ] fields: `entity` (resolved geometry) + `style` (resolved style only)
  - [ ] `serialize() -> dict` (calls into per-kind serialization, Phase 3)
  - [ ] setters/delegates that mark `dirty`: `set_entity`, `set_style`
        (merge), `set_color`, `set_opacity`, `set_texture_label`
- [ ] `class VizGroup(VizNode)`
  - [ ] no `entity` / `style`
  - [ ] `kind = "VizGroup"`
  - [ ] `serialize() -> dict` produces `{kind: "VizGroup", transform, ...}`
- [ ] Keep a `kind` string for dispatch symmetry with existing serializer.

### `scene.py` integration

- [ ] Add a node registry to `Scene` (`dict[str, VizNode]`, `_order` for DFS
      pre-order, `_removed_ids`).
- [ ] Reimplement `Scene.add`/`add_object`/`add_label` to build `VizObject`
      nodes; accept optional `parent_id`.
- [ ] Reimplement `update`, `update_entity`, `update_label`, `remove`, `clear`
      against nodes.
- [ ] Add `Scene.add_group(name)` returning a `VizGroup`.
- [ ] Add a `Scene.get_node(object_id)` accessor (replacing private `_get`
      usage).
- [ ] Keep `SceneObject` as a thin compatibility shim if needed, or remove
      after all callers migrate (see Phase 3/5).

## Unit tests

File: `py/tests/viz/test_nodes.py`

- [ ] `test_transform_matrix` — TRS builds the expected 4×4 matrix.
- [ ] `test_transform_from_matrix` — decomposition round-trips.
- [ ] `test_transform_apply_local` — `M_new = M_current @ M` for `space="local"`.
- [ ] `test_transform_apply_world` — `M_new = M @ M_current` for `space="world"`.
- [ ] `test_transform_mutators` — `translate`/`rotate`/`scale` update the
      canonical TRS.
- [ ] `test_node_parenting` — `add_child`/`remove_child` maintain parent and
      children consistently.
- [ ] `test_node_world_matrix` — parent chain matrix multiplication is correct.
- [ ] `test_object_dirty_on_set_entity` — `set_entity` sets `dirty` only.
- [ ] `test_object_dirty_on_set_style` — `set_style` merges non-`None` and sets
      `dirty` only.
- [ ] `test_group_serialize` — `VizGroup.serialize()` emits `kind == "VizGroup"`
      with transform and no geometry fields.

## Verification

- [ ] `uv run pytest py/tests/viz/test_nodes.py` passes.
- [ ] Existing viz smoke tests still add/update/remove entities via `Scene`.
- [ ] A `VizGroup` with children serializes children after the parent
      (DFS pre-order) with correct `parent_id`.
- [ ] `transform_dirty` stays independent of `dirty` (set transform → only
      `transform_dirty` becomes True).
