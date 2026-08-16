# Phase 13 — Entity content updates + legacy path removal

**Status:** Planned

## Goal

Consolidate the frontend update path into a single mechanism:

1. **Add a `content` aspect** so that replacing an entity's geometry (same
   kind) updates just the inner three.js mesh **in place** — preserving the
   node's transform, parent, style, and id mapping — instead of the current
   `full` → destroy-and-rebuild behavior.
2. **Remove the legacy flat-entity path** (`updateEntity`, `inPlaceUpdate`,
   `upsertLabel`, the `msg.entities`/`msg.labels` branches) and **collapse the
   three "backward compat" maps** (`entityMeshes`, `entityData`,
   `labelObjects`) into the single `sceneObjects` registry.

After this there is exactly one update path: aspect-scoped `object_update`
patches applied against `sceneObjects`.

## Wire format

```json
{
  "type": "object_update",
  "scene": "",
  "patches": [
    { "id": "a", "aspect": "content",
      "value": { "kind": "Line", "origin": [..], "direction": [..], "style": {..} } }
  ],
  "removed": []
}
```

`content.value` is the **leaf** — `kind` + geometry fields + resolved style
(+ color/opacity mirrors) — exactly what `_dispatch_entity` /
`VizSceneObject.serialize()` already produce, minus
`id/layer/parent_id/transform/visible`.

## Guiding decisions

- **`content` is self-contained and idempotent.** It carries the resolved
  style too, so re-applying it is safe, and `updateEntityMesh` (which already
  applies style) can be reused unchanged.
- **`set_entity` emits `content` only when the kind is unchanged.** A kind
  change (e.g. `Point` → `Line`) still emits `full`, because the node's `kind`
  field, renderer, and (potentially) resolved style all change. The frontend
  keeps `entityRequiresRebuild`'s `kind` check as a safety net.
- **`sceneObjects` becomes the single registry**, with entries shaped
  `{ obj, mesh, data, layer, el? }`:
  - `obj` — the `THREE.Object3D` the node lives under (the wrapper `Group` or
    the mesh itself for identity transforms; `CSS2DObject` for overlays).
  - `mesh` — the inner geometry object from `createEntityMesh` (the in-place
    update target).
  - `data` — the last-known JSON (diffing/merging, replaces `entityData`).
  - `layer` — `'scene'` | `'overlay'`.
  - `el` — an overlay DOM element (annotations / fixed labels).

## Steps

### Python — `py/pytanga/viz/_nodes.py`

- [ ] Factor the "resolved leaf" out of `VizSceneObject.serialize()` into a
      `_serialize_content()` helper returning `kind` + geometry + resolved
      style + color/opacity mirrors (no `id/layer/parent_id/transform/
      visible`). Reuse it from `serialize()` and the new patch.
- [ ] Add `content` to `VizSceneObject.patch()`:
      `{ "id", "aspect": "content", "value": self._serialize_content() }`.
- [ ] `set_entity(entity)`: mark `content` when
      `type(entity).__name__ == self.kind`, otherwise `full`.

### Python — `py/pytanga/viz/scene.py`

- [ ] `flush()`: iterate aspects `("full", "style", "transform", "content")`.

### Frontend — `py/pytanga/viz/templates/viewer.js`

- [ ] Delete `entityMeshes`, `entityData`, `labelObjects`; redefine
      `sceneObjects` entries as `{ obj, mesh, data, layer, el? }`.
- [ ] `upsertObject`: store `mesh` + `data` in the entry (both layers).
- [ ] `applyObjectPatch`:
  - [ ] `content` → new `updateEntityContent(id, value)`.
  - [ ] `style` → merge into `entry.data` (replaces `entityData`).
- [ ] New `updateEntityContent(id, content)`:
  - [ ] lookup `sceneObjects.get(id)` → `{ obj, mesh, data }`; if absent, return.
  - [ ] `updateEntityMesh(mesh, content, prev = data)`:
    - [ ] `true` → `entry.data = { ...data, ...content }` (in-place done).
    - [ ] `false` → `createEntityMesh({ ...data, ...content })` and swap the
          new mesh in, keeping `obj`/parent/transform:
      - [ ] identity transform (`entry.obj === entry.mesh`): remove the old
            node, add the new mesh under the same parent, set
            `entry.obj = entry.mesh = newMesh`.
      - [ ] wrapped (`entry.obj` is a `Group`): `removeEntityMesh(entry.mesh)`,
            `entry.obj.add(newMesh)`, `entry.mesh = newMesh`.
      - [ ] update `entry.data = { ...data, ...content }`, and
            re-`registerInteractive(id, entry.obj, data.interaction)` when
            `data.interaction` exists.
- [ ] `removeSceneObject(id)`: single `sceneObjects` lookup, branch on `layer`
      (scene → `removeEntityMesh(entry.obj)`; overlay →
      `entry.obj?.removeFromParent()`, `entry.obj?.element?.remove()`,
      `entry.el?.remove()`); keep `unregisterInteractive`/`detachGroup`/
      `cancelTween`.
- [ ] `clear_all`: clear only `sceneObjects` (plus existing reset steps).
- [ ] `handleAnimate` / render loop: pass `sceneObjects` to the animator.

### Legacy removal — `viewer.js`

- [ ] Remove `updateEntity()`, `inPlaceUpdate()`, `upsertLabel()`.
- [ ] Remove the `msg.entities` and `msg.labels` branches in `scene_update`.
- [ ] `scene_update` objects loop →
      `for (const obj of msg.objects) upsertObject(obj);` (drop the
      `hasSceneGraph` routing).
- [ ] Remove all `.set/.delete/.get/.clear` on the three deleted maps.

### Frontend — `py/pytanga/viz/templates/animator.js`

- [ ] `startTween(id, target, duration, easing, map)` and
      `updateTweens(map)`: read `map.get(id)?.obj` (map is now `sceneObjects`).

### Frontend — `py/pytanga/viz/templates/view_mode.js`

- [ ] `fitCamera(sceneObjects, ...)`: iterate entries and
      `box.expandByObject(entry.obj)` only for `entry.layer === 'scene' &&
      entry.obj`.

### Docs / notes

- [ ] Update `docs/py/viz/scene-graph.md`: `ref.entity = ...` → `content`.
- [ ] Append an entry to `IMPLEMENTATION-NOTES.md`.
- [ ] Update `README.md` phases table with Phase 13.

### Changelog

- [ ] Add a changelog entry per `dev/workflows/changelog.md`.

## Unit / smoke tests

- [ ] `py/tests/viz/test_nodes.py`: `test_set_entity_marks_content` (same kind)
      and `full` on kind change.
- [ ] `py/tests/viz/test_object_ref.py`: `test_entity_get_set` asserts
      `content` (was `full`).
- [ ] `py/tests/viz/test_node_serialization.py`: `test_aspect_content_patch`
      (shape `{id, aspect:"content", value:{kind, ...geometry}}`, no
      `parent_id/transform/visible`).
- [ ] `py/tests/viz/test_frontend_transform_shape.py`: `test_content_patch_shape`.
- [ ] `node --check` on `viewer.js`, `animator.js`, `view_mode.js`.
- [ ] Manual smoke: `demo_scene_graph.py`, `demo_animation_orbit.py` — verify
      parented + non-identity-transform objects, `attach_to` labels, tweens,
      camera fit, and reconnect.

## Verification

- [ ] `uv run pytest py/tests/viz -q` passes.
- [ ] `viz.update_entity(...)` on a same-kind entity mutates in place (no
      flicker/reparent); a kind change rebuilds via `full`.
- [ ] No `entityMeshes`/`entityData`/`labelObjects`/`updateEntity`/
      `inPlaceUpdate`/`upsertLabel` references remain in `viewer.js`.
- [ ] Static/animated export still works (untouched).

