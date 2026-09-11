# Phase 3 — `add_*` facade over `*View` (implicit overlay panel)

## Goal

Reimplement the individual `add_*` methods so each builds its `*View`, registers
handlers through the shared helper, and places the view in an implicit per-scene
`GroupView` overlay panel. Unify control-id lookup, removal, and value updates on
a `_control_views` registry so every control — orphan, grouped, or declarative —
resolves the same way.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- (No change to `_scene_handle.py` — its `add_*` methods keep forwarding to
  `_add_scene_*`.)

## Steps

- [x] **3.1 — Add state (`visualizer.py` `__init__`)**
  - Add `self._orphan_groups: dict[str, GroupView] = {}` next to `_scene_groups`.
  - Add `self._control_views: dict[str, tuple[str, ControlView]] = {}` mapping
    control id → `(scene_name, ControlView)`.

- [x] **3.2 — `_get_or_create_orphan_group(scene_name)`**
  - Lazily build `GroupView("", position=EAnchor.BOTTOM_RIGHT, collapsed=False)`
    per scene and mount it the same way `_add_scene_group` mounts explicit groups
    (global overlay for `""`, scene overlay for named scenes).
  - Return the existing group when already present.

- [x] **3.3 — `_mount_orphan_control(scene_name, view)`**
  - Register the view's handlers via `_register_control_view_handlers(view)`.
  - Append `view` to the scene's orphan group children.
  - Record `self._control_views[view.id] = (scene_name, view)`.
  - Call `_sync_overlays()` (no `_push_controls`).

- [x] **3.4 — Rewrite each `_add_scene_*`**
  - Replace the manual `Control(...)` construction, `scene.add_control(...)`,
    `_handler_registry.register(...)`, and `_push_controls(...)` with:
    build the matching `*View`, then `_mount_orphan_control(scene_name, view)`.
  - Keep returning `cid` and keep the public `add_*` forwarding methods unchanged
    (signature already widened in Phase 1).
  - Cover: slider, dropdown, button, file_chooser, text_field, text_area,
    color_picker, checkbox, value_edit, table.

- [x] **3.5 — Route `_resolve_control` through `_control_views`**
  - Check `self._control_views` first and return a `ControlRef` from the stored
    `(scene_name, ControlView)`.
  - Keep the existing `scene._controls` and declarative-layout/dialog fallbacks
    for any callers that still construct controls outside `add_*`.

- [x] **3.6 — Consolidate value/field updates**
  - `set_control_value`: resolve via `_control_views`/`_resolve_control` instead of
    `scene._controls`, then `_set_control_value` + `_push_control_update`.
  - `update_control`: resolve via `_resolve_control`; keep routing `value=` through
    `set_control_value`, and for other fields `_sync_overlays()` instead of
    `_push_controls`.

- [x] **3.7 — Update removal/clear**
  - `_remove_scene_control`: unregister handlers, remove the view from its orphan
    group (or `_control_views`), drop the `_control_views` entry, `_sync_overlays()`.
  - `_clear_scene_controls`: clear the orphan group, `_control_views` entries,
    explicit groups, and handlers; `_sync_overlays()` (drop `_push_controls_clear`).

- [x] **3.8 — `_add_scene_group` resolves ids via `_control_views`**
  - Replace the `scene._controls.get(cid)` + `control_to_view(ctrl)` round-trip
    with a lookup in `self._control_views` reusing the stored `ControlView`.

## Validation

```
uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_layout_api.py py/tests/viz/test_control_value_api.py py/tests/viz/test_banner.py py/tests/viz/test_table.py py/tests/viz/test_file_chooser.py -q
```

## Notes

- Existing `add_control_group(controls=[...])` call sites must keep working: they
  reference control ids created by `add_*`, now resolved via `_control_views`.
- The orphan panel is created lazily, so `add_*` still works before the server
  starts (same as `add_control_group` today).
