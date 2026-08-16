# Phase 6 — Frontend scene graph

**Status:** Planned

## Goal

Teach the browser to rebuild the Python-authored scene graph, honor
`parent_id` + `transform`, render `VizGroup` as a `THREE.Group`, and apply
transform-only updates in place without recreating geometry.

## Files

- Modify: `py/pytanga/viz/templates/viewer.js`
- Modify: `py/pytanga/viz/templates/renderers/factory.js`
- New: `py/pytanga/viz/templates/renderers/group.js`
- (possibly) `py/pytanga/viz/export/...` bootstrap for static export parity
      (defer complex export parity to Phase 7)

## Wire format additions

- Each serialized node gains:
  - `parent_id: str | null`
  - `transform: { position: [x,y,z], rotation: [x,y,z], scale: [x,y,z] }`
- New message type:
  ```json
  { "type": "transform_update", "scene": "...",
    "transforms": [ {"id": "...", "position": [...], "rotation": [...], "scale": [...] } ] }
  ```

## Steps

### `renderers/group.js`

- [ ] Add `createVizGroup(ent) -> THREE.Group` (no geometry).
- [ ] Tag the group with entity metadata for consistency.

### `renderers/factory.js`

- [ ] Add `case 'VizGroup': mesh = createVizGroup(ent); break;`.

### `viewer.js` — object creation/parenting

- [ ] In `upsertObject`, after `createEntityMesh`:
  - [ ] If `msg.parent_id` references a known `sceneObjects` entry, `parent.obj.add(mesh)`; otherwise `scene.add(mesh)`.
  - [ ] Apply `transform` (position / Euler rotation / scale) to the `Object3D`.
- [ ] In `createEntityMesh` result, set `mesh.userData.parentId = msg.parent_id || null`.
- [ ] In `updateEntity`, when a full rebuild happens, preserve and re-attach to the correct parent.

### `viewer.js` — transform updates

- [ ] Add a `handleTransformUpdate(msg)` branch:
  - [ ] For each `{id, position, rotation, scale}`, look up the `Object3D` in
        `sceneObjects` (or `entityMeshes` fallback).
  - [ ] Set `position`, `quaternion` from Euler (`XYZ`), and `scale` in place.
  - [ ] Do not dispose or recreate geometry.

### Removal / clear

- [ ] Ensure `parent` removal propagates children correctly via
      `removeFromParent`/`traverse` cleanup.
- [ ] Ensure `clear_all` resets the scene graph cleanly.

## Unit / smoke tests

No browser-level unit test framework is wired into the repo; cover the Python
side that the frontend consumes and add a JS renderer smoke test reference.

- [ ] `py/tests/viz/test_frontend_transform_shape.py`:
  - [ ] `test_transform_message_shape` — `transform_update` message serializes
        `{id, position, rotation, scale}` correctly.
  - [ ] `test_full_state_includes_parent_and_transform` — `full_state()` emits
        `parent_id` and `transform` on every node.
  - [ ] `test_group_kind_in_state` — groups are serialized with
        `kind == "VizGroup"`.
  - [ ] `test_dfs_preorder` — parents appear before children.
- [ ] Manual / existing `test_export_renderers.py`-style check that
      `createVizGroup` returns a `THREE.Group` with no geometry (if the test
      harness has a JS runner; otherwise verify visually via Phase 8 smoke).

## Verification

- [ ] `uv run pytest py/tests/viz/test_frontend_transform_shape.py` passes.
- [ ] Adding `grp = viz.add_group(...)` then `grp.new(...)` renders children
      parented under the group (visual smoke).
- [ ] A `transform_update` rotates a `VizGroup` without re-sending any child
      geometry (verify via WebSocket message inspection).
- [ ] Reparented and removed objects clean up their children/materials.
- [ ] Existing live-viewer smoke flows still work.
