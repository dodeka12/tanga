# Phase 4 — `VizObjectRef`

**Status:** Planned

## Goal

Add the `VizObjectRef` convenience class that wraps a `VizNode` and a
`VizSceneHandle`, exposing property getters/setters and mutation methods. All
setters delegate to the node and set the appropriate dirty flag.

## Files

- New: `py/pytanga/viz/_object_ref.py`
- (export from `py/pytanga/viz/__init__.py` in Phase 5)

## API

### Identity & access

- [ ] `id` (read-only)
- [ ] `name`
- [ ] `scene`, `handle`, `scene_name`
- [ ] `parent` (get/set via reparent)

### Data getters/setters

- [ ] `entity` — get current resolved geometry; set replaces it and marks
      `dirty`
- [ ] `style` — get resolved style; set merges non-`None` fields into the
      resolved style and marks `dirty`
- [ ] `color` — get/set (sets `dirty`)
- [ ] `opacity` — get/set (sets `dirty`)
- [ ] `texture_label` — get resolved texture label; set merges into the style's
      `texture_label` (marks `dirty`)

### Labels

- [ ] `label_ids` — list of attached label ids via scene `get_label_ids`
- [ ] `labels` — list of `VizObjectRef` (or label refs) for those ids
- [ ] `update_label(text=None, style=None)` — proxy to scene `update_label` for
      each attached label

### Transforms

- [ ] `translate(x=0, y=0, z=0)` — accept numeric or `Point`/`Direction`/
      `Translator`; set only `transform_dirty`
- [ ] `rotate(angle, axis)` — accept numeric axis tuple or `Direction`; set only
      `transform_dirty`
- [ ] `scale(x=1, y=1, z=1)` — scalar (uniform) or component-wise
- [ ] `set_transform(position=None, rotation=None, scale=None)` — absolute
- [ ] `transform(op)` — accept `Rotor`, `GeneralRotor`, `Motor`, `Translator`,
      `Dilator`; compute matrix via `_transforms.py`, apply to `Transform`
- [ ] `transform` property — expose the node's `Transform`
- [ ] `world_matrix` — computed from parent chain

### Graph (meaningful on a `VizGroup` ref)

- [ ] `add(obj, ...)` — delegate to handle with `parent_id=self._id`; return `str`
- [ ] `new(obj, ...)` — delegate to handle with `parent_id=self._id`; return
      `VizObjectRef`
- [ ] `add_group(name=None)` — create child group; return `VizObjectRef`

### Lifecycle / passthroughs

- [ ] `update(**properties)` — mark `dirty`
- [ ] `remove()`
- [ ] `flush(fit_camera=False)`
- [ ] `animate_to(...)`
- [ ] `set_interaction(config)`
- [ ] `on_interaction(event_type, handler)`

## Steps

- [ ] Implement `VizObjectRef.__init__(handle, node)`.
- [ ] Implement identity/access properties.
- [ ] Implement data getters/setters delegating to `VizObject` setters
      (Phase 2) so dirty flags are set correctly.
- [ ] Implement label accessors and `update_label`.
- [ ] Implement transform mutators delegating to `Transform` + `_transforms.py`
      conversions; set only `transform_dirty`.
- [ ] Implement group-scoped `add` / `new` / `add_group` (only valid for a
      `VizGroup` node; raise on non-group refs).
- [ ] Implement lifecycle passthroughs to `VizSceneHandle`.

## Unit tests

File: `py/tests/viz/test_object_ref.py`.

- [ ] `test_entity_get_set` — `ref.entity = Point(...)` updates geometry and
      sets `dirty`, not `transform_dirty`.
- [ ] `test_style_merge` — `ref.style = PointStyle(size=0.2)` merges into the
      resolved style.
- [ ] `test_color_opacity_texture_label` — accessors read/write the resolved
      style and mark `dirty`.
- [ ] `test_translate_marks_transform_dirty` — `ref.translate(...)` sets only
      `transform_dirty`.
- [ ] `test_rotate_scale_set_transform` — transform mutators update TRS.
- [ ] `test_transform_operator` — `Rotor` / `Translator` / `Motor` /
      `GeneralRotor` / `Dilator` applied via `ref.transform(...)`.
- [ ] `test_labels_access` — `label_ids` and `labels` resolve attached labels.
- [ ] `test_update_label` — proxies label text/style updates.
- [ ] `test_group_add_new` — `group_ref.new(...)` attaches under the group.
- [ ] `test_group_non_group_guards` — group methods raise on a non-group ref.

## Verification

- [ ] `uv run pytest py/tests/viz/test_object_ref.py` passes.
- [ ] `ref.entity = Point(...)` marks the node dirty but not transform-dirty.
- [ ] `ref.translate(...)` marks only `transform_dirty`.
- [ ] `ref.style = PointStyle(size=0.2)` merges into the resolved style.
- [ ] `group_ref.new(Point(...))` attaches the new node under the group.
- [ ] `ref.texture_label = TextureLabelStyle(text="x")` updates the resolved
      texture label and marks dirty.
