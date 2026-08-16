# Phase 4 — `VizObjectRef`

**Status:** Planned (revised after design discussion)

## Goal

Add the `VizObjectRef` convenience class wrapping a `VizNode` (scene or
overlay) and a `VizSceneHandle`. Property setters delegate to the node and
mark the correct aspect (`full` / `style` / `transform`).

## Files

- New: `py/pytanga/viz/_object_ref.py`
- (export from `py/pytanga/viz/__init__.py` in Phase 5)

## API

### Identity & access

- [ ] `id` (read-only)
- [ ] `name`
- [ ] `layer` (read-only: `"scene"` or `"overlay"`)
- [ ] `scene`, `handle`, `scene_name`
- [ ] `parent` (get/set via reparent — scene nodes only)

### Data getters/setters

- [ ] `entity` — get geometry; set replaces it and marks `full`
      (scene nodes)
- [ ] `style` — get resolved style; set merges non-`None` fields and marks
      `style`
- [ ] `color` — get/set (marks `style`)
- [ ] `opacity` — get/set (marks `style`)
- [ ] `texture_label` — get/set (marks `style`, nested merge)

### Overlay-specific (labels/annotations/titles)

- [ ] `text` / `payload` — get/set (marks `full`)
- [ ] `position` — get/set (marks `full`)
- [ ] `attach_to` — get/set scene-node reference (marks `full`)
- [ ] `label_ids` — list of attached label ids via scene `get_label_ids`
- [ ] `labels` — list of `VizObjectRef` for those ids
- [ ] `update_label(text=None, style=None)` — proxy to scene `update_label`

### Transforms (scene nodes only; raise on overlay)

- [ ] `translate(x=0, y=0, z=0)` — accept numeric or `Point`/`Direction`/
      `Translator`; marks `transform`
- [ ] `rotate(angle, axis)` — numeric axis tuple or `Direction`; marks
      `transform`
- [ ] `scale_by(x=1, y=1, z=1)` — scalar (uniform) or component-wise
- [ ] `set_transform(position=None, rotation=None, scale=None)` — absolute
- [ ] `transform(op)` — `Rotor`/`GeneralRotor`/`Motor`/`Translator`/
      `Dilator` via `_transforms.py`; marks `transform`
- [ ] `transform` property — expose the node's `Transform`
- [ ] `world_matrix` — computed from parent chain

### Graph (meaningful on a `VizGroup` ref)

- [ ] `add(obj, ...)` — delegate to handle with `parent_id=self._id`; return `str`
- [ ] `new(obj, ...)` — delegate to handle with `parent_id=self._id`; return
      `VizObjectRef`
- [ ] `add_group(name=None)` — create child group; return `VizObjectRef`

### Lifecycle / passthroughs

- [ ] `update(**properties)` — mark `full`
- [ ] `remove()`
- [ ] `flush(fit_camera=False)`
- [ ] `animate_to(...)`
- [ ] `set_interaction(config)`
- [ ] `on_interaction(event_type, handler)`

## Steps

- [ ] `VizObjectRef.__init__(handle, node)`; dispatch scene vs overlay by
      `node.layer`.
- [ ] Identity/access properties.
- [ ] Data getters/setters delegating to node setters (aspect-correct).
- [ ] Overlay-specific accessors and label helpers.
- [ ] Transform mutators delegating to `VizSceneObject` (guard overlay).
- [ ] Group-scoped `add`/`new`/`add_group` (guard non-group refs).
- [ ] Lifecycle passthroughs to `VizSceneHandle`.

## Unit tests

File: `py/tests/viz/test_object_ref.py`.

- [ ] `test_entity_get_set` — `ref.entity = Point(...)` updates geometry and
      marks `full`.
- [ ] `test_style_merge` — `ref.style = PointStyle(size=0.2)` merges non-`None`
      and marks `style`.
- [ ] `test_color_opacity_texture_label` — accessors mark `style`.
- [ ] `test_translate_marks_transform` — `ref.translate(...)` marks only
      `transform`.
- [ ] `test_rotate_scale_set_transform` — transform mutators update TRS.
- [ ] `test_transform_operator` — `Rotor`/`Translator`/`Motor`/
      `GeneralRotor`/`Dilator` applied via `ref.transform(...)`.
- [ ] `test_overlay_ref_has_no_transform` — overlay ref raises on
      translate/rotate/scale/world_matrix.
- [ ] `test_labels_access` — `label_ids` and `labels` resolve attached labels.
- [ ] `test_update_label` — proxies label text/style updates.
- [ ] `test_group_add_new` — `group_ref.new(...)` attaches under the group.
- [ ] `test_group_non_group_guards` — group methods raise on a non-group ref.

## Verification

- [ ] `uv run pytest py/tests/viz/test_object_ref.py` passes.
- [ ] `ref.entity = Point(...)` marks `full`, not `transform`.
- [ ] `ref.color = "#..."` marks `style` only.
- [ ] `ref.translate(...)` marks `transform` only.
- [ ] `group_ref.new(Point(...))` attaches the new node under the group.
- [ ] Overlay refs (labels) raise on transform operations.