# Phase 6 — Frontend scene graph

**Status:** Planned (revised after design discussion)

## Goal

Teach the browser to consume the Python-authored scene graph via the
`object_update` aspect-patch message: rebuild `parent_id`/`transform`
hierarchies, render `VizGroup` as a `THREE.Group`, apply `style` and
`transform` patches in place, and live-follow overlay `attach_to` targets.

## Files

- Modify: `py/pytanga/viz/templates/viewer.js`
- Modify: `py/pytanga/viz/templates/renderers/factory.js`
- New: `py/pytanga/viz/templates/renderers/group.js` + overlay renderers as
      needed.
- (possibly) `py/pytanga/viz/export/...` bootstrap for static export parity
      (defer complex parity to Phase 7).

## Wire format (agreed, Phase 3)

```json
{
  "type": "object_update",
  "scene": "",
  "patches": [
    { "id": "a", "aspect": "full",      "value": { "id":"a", "layer":"scene", "kind":"Point", "parent_id":null, "transform":{...}, "style":{...} } },
    { "id": "b", "aspect": "style",     "value": { "style": { "color": "#ff0000" } } },
    { "id": "c", "aspect": "transform", "value": { "position": [1,2,3], "rotation": [0,0,0], "scale": [1,1,1] } }
  ],
  "removed": ["x"]
}
```

The old `scene_update` message remains supported for backward compatibility
during the transition (Phases 7 checks exports).

## Steps

### `renderers/group.js`

- [ ] Add `createVizGroup(ent) -> THREE.Group` (no geometry).
- [ ] Tag with entity metadata (userData.kind = "VizGroup").

### `renderers/factory.js`

- [ ] Add `case 'VizGroup': mesh = createVizGroup(ent); break;`.

### `viewer.js` — aspect routing

- [ ] Add an `object_update` handler that iterates `patches` and dispatches
      by `aspect`:
  - [ ] `full` → existing `upsertObject`/`updateEntity` rebuild path,
        now honoring `parent_id`/`transform`/`layer`.
  - [ ] `style` → merge `value.style` into the stored `ent.style` and
        re-apply material/opacity (no geometry recreation).
  - [ ] `transform` → set `position`, Euler (order `"XYZ"`) quaternion, and
        `scale` on the `Object3D` in place.
- [ ] Keep `scene_update` (full dicts) working for legacy callers.

### `viewer.js` — object creation/parenting

- [ ] In the full/upsert path:
  - [ ] If `parent_id` references a known `sceneObjects` entry, parent
        `mesh.obj` under it; otherwise `scene.add(...)`.
  - [ ] Apply `transform` (position/quaternion/scale) to the `Object3D`.
  - [ ] Set `mesh.userData.parentId = parent_id || null`.

### Overlay live-follow

- [ ] Overlay nodes (labels/annotations/markers) store `attach_to` (not a
      `Transform`).
- [ ] Each frame (or on the parent's transform patch), position the overlay
      at the referenced scene node's resolved world position (CSS2DRenderer
      anchor). No geometry/matrix on the overlay itself.

### Removal / clear

- [ ] Ensure `removed` and `clear_all` dispose children/materials and remove
      overlay live-follow registrations.

## Unit / smoke tests

No browser-level unit test framework is wired in; cover the Python-authorized
message shape and add a JS renderer smoke reference.

- [ ] `py/tests/viz/test_frontend_transform_shape.py`:
  - [ ] `test_object_update_message_shape` — `{type:"object_update",
        patches:[...], removed:[...]}`.
  - [ ] `test_full_patch_includes_parent_and_transform`.
  - [ ] `test_style_patch_shape` — `{aspect:"style", value:{style:{...}}}`.
  - [ ] `test_transform_patch_shape` — `{aspect:"transform", value:{position,
        rotation, scale}}`.
  - [ ] `test_overlay_patch_has_attach_to` — overlay patch has `attach_to`,
        no `transform`.
  - [ ] `test_group_kind_in_state` — groups serialize `kind == "VizGroup"`.
  - [ ] `test_dfs_preorder` — parents appear before children.
- [ ] Manual / visual smoke via Phase 8 for actual THREE behavior.

## Verification

- [ ] `uv run pytest py/tests/viz/test_frontend_transform_shape.py` passes.
- [ ] `grp = viz.add_group(...)` then `grp.new(...)` renders children
      parented under the group (visual smoke, Phase 8).
- [ ] A `transform` patch moves a `VizGroup` without re-sending child geometry.
- [ ] A label with `attach_to` follows its node's transform.
- [ ] Existing live-viewer smoke flows still work.