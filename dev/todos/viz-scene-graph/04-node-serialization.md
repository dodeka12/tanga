# Phase 4 — Node serialization (aspect patches)

**Status:** Planned (revised after design discussion)

## Goal

Move serialization out of `serializer.py`'s large `isinstance` dispatch and
into node `serialize()` methods. Emit both full object dicts and
aspect-scoped patches via a single `object_update` message. The leaf field
layout (`position`, `center`, `normal`, `radius`, `style:{...}`) must remain
stable so existing frontend renderers keep working, plus the new
`parent_id` / `transform` / `attach_to` keys.

## Files

- Modify: `py/pytanga/viz/_nodes.py` (per-kind `serialize()`)
- Modify: `py/pytanga/viz/serializer.py` (remove dispatch, keep leaf helpers)
- Modify: `py/pytanga/viz/scene.py` (walk node tree; emit `object_update`)
- Modify: `py/pytanga/viz/visualizer.py` (`_flush_scene_async` pushes patches)

## Wire format

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

Aspect semantics (Python authoritative):

- `full` — create/replace the node: complete dict (geometry + style +
  transform/position as applicable by layer).
- `style` — coarse: send the node's whole resolved style dict. JS merges and
  re-applies materials/opacity.
- `transform` — scene layer only: send `{position, rotation, scale}`; JS
  applies to the `Object3D` in place without recreating geometry.

## Steps

### Per-kind serialize (move leaf serializers into `_nodes.py`)

- [ ] Base `VizNode.serialize()` returns id/layer/kind/visible.
- [ ] `VizSceneObject.serialize()`:
  - [ ] adds `parent_id`, `transform`, geometry fields, resolved `style`.
  - [ ] calls per-kind `_serialize_<kind>` helpers (moved from serializer.py).
  - [ ] supports `Point`, `Direction`, `HPoint`, `PointPair`(+Imag),
        `Line`, `Plane`, `Circle`(+Imag), `Sphere`(+Imag), `Space`,
        `PointPath`, `Axis`, `Axes2D`, `Axes3D`, `Grid`, and operators.
- [ ] `VizOverlayObject.serialize()`:
  - [ ] adds `position`, `attach_to`, and kind-specific `payload`
        (label text / annotation / title), and resolved `style`.
- [ ] `VizGroup.serialize()`: `{kind:"VizGroup", parent_id, transform, ...}`.

### Patch generation

- [ ] `VizNode.patch(aspect) -> dict`:
  - [ ] `full` → `{id, aspect:"full", value: serialize()}`
  - [ ] `style` → `{id, aspect:"style", value: {style: <resolved style dict>}}`
  - [ ] `transform` → `{id, aspect:"transform", value: <transform trs dict>}`
- [ ] `Scene.flush()` walks DFS pre-order and collects patches per node's
      dirty aspects (see Phase 3 `consume_dirty()`); returns
      `(patches, removed)`. `full_state()` still returns complete lists for
      initial sync / export.

### serializer.py cleanup

- [ ] Keep `_apply_defaults`, `_style_to_output`, `_style_for_kind`, all
      `_serialize_<kind>` leaf helpers, `_serialize_label`.
- [ ] Delete `serialize_entity`'s `isinstance`/`elif` dispatch (keep a thin
      backward-compat trampoline if other callers remain; migrate them).
- [ ] Keep `serialize_scene_update` for now (used by existing tests) but add
      `serialize_object_update(patches, removed)`.

### visualizer.py

- [ ] `_flush_scene_async` consumes `(patches, removed)` and pushes via a new
      server push path (or generic `push_raw`).

## Backward compatibility

- [ ] Existing `SceneObject` path + `scene_update` message must keep working
      (Phase 8 export readers) until `new()`/`VizObjectRef` become primary in
      Phase 6. The new `object_update` message is additive.

## Unit tests

File: `py/tests/viz/test_serializer.py` (extend) + new
`py/tests/viz/test_node_serialization.py`.

- [ ] `test_point_serialize` — point node output matches previous leaf layout
      plus `parent_id`/`transform`.
- [ ] `test_representative_kinds_serialize` — parametrized over
      `Point`/`Line`/`Plane`/`Sphere`/`Circle`/`PointPair`/`PointPath`/
      `Grid`/`Axis`/operators.
- [ ] `test_resolved_style_present` — resolved merged style dict.
- [ ] `test_imaginary_variants` — `ImagPointPair`/`ImagCircle`/`ImagSphere`.
- [ ] `test_aspect_full_patch` — full patch shape.
- [ ] `test_aspect_style_patch` — style patch carries only `{style: ...}`.
- [ ] `test_aspect_transform_patch` — transform patch carries `{position,
      rotation, scale}` and no geometry/style.
- [ ] `test_overlay_label_patch` — `position` + `attach_to`, no transform.
- [ ] `test_full_state_equiv` — `full_state()` matches prior `serialize_entity`
      modulo added keys.
- [ ] `test_removed_tracking` — add/update/remove cycles.
- [ ] `test_group_serialize_shape` — `kind == "VizGroup"`.

## Verification

- [ ] `uv run pytest py/tests/viz/test_serializer.py py/tests/viz/test_node_serialization.py` passes.
- [ ] `full_state()` output byte-equivalent (modulo new keys) to prior
      `serialize_entity` for representative entities/operators.
- [ ] Color-only change emits a `style` patch (no geometry/transform).
- [ ] Transform-only change emits a `transform` patch.
- [ ] No `Unknown entity type` regression.
- [ ] Existing viz smoke/export tests pass.