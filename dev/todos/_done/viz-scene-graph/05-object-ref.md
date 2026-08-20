# Phase 5 — `VizObjectRef`

**Status:** Done

> Note: operator application is exposed as ``apply_transform(op)`` (the
> ``transform`` name is taken by the read-only :attr:`transform` property that
> exposes the node's :class:`Transform`).

## Goal

Add the `VizObjectRef` convenience class wrapping a `VizNode` (scene or
overlay) and a `VizSceneHandle`. Property setters delegate to the node and
mark the correct aspect (`full` / `style` / `transform`).

## Files

- New: `py/pytanga/viz/_object_ref.py`
- (export from `py/pytanga/viz/__init__.py` in Phase 6)

## API

### Identity & access

- [x] `id` (read-only)
- [x] `name`
- [x] `layer` (read-only: `"scene"` or `"overlay"`)
- [x] `scene`, `handle`, `scene_name`
- [x] `parent` (get/set via reparent — scene nodes only)

### Data getters/setters

- [x] `entity` — get geometry; set replaces it and marks `full`
      (scene nodes)
- [x] `style` — get resolved style; set merges non-`None` fields and marks
      `style`
- [x] `color` — get/set (marks `style`)
- [x] `opacity` — get/set (marks `style`)
- [x] `texture_label` — get/set (marks `style`, nested merge)

### Overlay-specific (labels/annotations/titles)

- [x] `text` / `payload` — get/set (marks `full`)
- [x] `position` — get/set (marks `full`)
- [x] `attach_to` — get/set scene-node reference (marks `full`)
- [x] `label_ids` — list of attached label ids via scene `get_label_ids`
- [x] `labels` — list of `VizObjectRef` for those ids
- [x] `update_label(text=None, style=None)` — proxy to scene `update_label`

### Transforms (scene nodes only; raise on overlay)

- [x] `translate(x=0, y=0, z=0)` — accept numeric or `Point`/`Direction`/
      `Translator`; marks `transform`
- [x] `rotate(angle, axis)` — numeric axis tuple or `Direction`; marks
      `transform`
- [x] `scale_by(x=1, y=1, z=1)` — scalar (uniform) or component-wise
- [x] `set_transform(position=None, rotation=None, scale=None)` — absolute
- [x] `apply_transform(op)` — `Rotor`/`GeneralRotor`/`Motor`/`Translator`/
      `Dilator` via `_transforms.py`; marks `transform`
- [x] `transform` property — expose the node's `Transform`
- [x] `world_matrix` — computed from parent chain

### Graph (meaningful on a `VizGroup` ref)

- [x] `add(obj, ...)` — delegate to handle with `parent_id=self._id`; return `str`
- [x] `new(obj, ...)` — delegate to handle with `parent_id=self._id`; return
      `VizObjectRef`
- [x] `add_group(name=None)` — create child group; return `VizObjectRef`

### Lifecycle / passthroughs

- [x] `update(**properties)` — mark `full`
- [x] `remove()`
- [x] `flush(fit_camera=False)`
- [x] `animate_to(...)`
- [x] `set_interaction(config)`
- [x] `on_interaction(event_type, handler)`

## Steps

- [x] `VizObjectRef.__init__(handle, node)`; dispatch scene vs overlay by
      `node.layer`.
- [x] Identity/access properties.
- [x] Data getters/setters delegating to node setters (aspect-correct).
- [x] Overlay-specific accessors and label helpers.
- [x] Transform mutators delegating to `VizSceneObject` (guard overlay).
- [x] Group-scoped `add`/`new`/`add_group` (guard non-group refs).
- [x] Lifecycle passthroughs to `VizSceneHandle`.

## Unit tests

File: `py/tests/viz/test_object_ref.py`.

- [x] `test_entity_get_set` — `ref.entity = Point(...)` updates geometry and
      marks `full`.
- [x] `test_style_merge` — `ref.style = PointStyle(size=0.2)` merges non-`None`
      and marks `style`.
- [x] `test_color_opacity_texture_label` — accessors mark `style`.
- [x] `test_translate_marks_transform` — `ref.translate(...)` marks only
      `transform`.
- [x] `test_rotate_scale_set_transform` — transform mutators update TRS.
- [x] `test_transform_operator` — `Rotor`/`Translator`/`Motor`/
      `GeneralRotor`/`Dilator` applied via `ref.transform(...)`.
- [x] `test_overlay_ref_has_no_transform` — overlay ref raises on
      translate/rotate/scale/world_matrix.
- [x] `test_labels_access` — `label_ids` and `labels` resolve attached labels.
- [x] `test_update_label` — proxies label text/style updates.
- [x] `test_group_add_new` — `group_ref.new(...)` attaches under the group.
- [x] `test_group_non_group_guards` — group methods raise on a non-group ref.

## Verification

- [x] `uv run pytest py/tests/viz/test_object_ref.py` passes.
- [x] `ref.entity = Point(...)` marks `full`, not `transform`.
- [x] `ref.color = "#..."` marks `style` only.
- [x] `ref.translate(...)` marks `transform` only.
- [x] `group_ref.new(Point(...))` attaches the new node under the group.
- [x] Overlay refs (labels) raise on transform operations.