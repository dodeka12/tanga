# Phase 4 — Extract `ControlHost`

## Goal

Move the entire control layer (registry, mounting, overlay/layout sync, value
API, table undo/redo, and the `control:*` dispatch) out of `Visualizer` into
`ControlHost`.  This is the largest phase; the public `add_*`/`set_control`/…
API stays, via forwarders.

## Files

- Edit: `py/pytanga/viz/_hosts.py`
- Edit: `py/pytanga/viz/visualizer.py`
- (tests stay green; no changes expected)

## Steps

- [x] **4.1 — State**
  - Move `_control_views`, `_orphan_groups`, `_orphan_group_position` /
    `_orphan_group_positions`, `_global_overlay`, `_scene_overlays`,
    `_scene_groups`, `_injected_overlay_ids`, `_menus`, `_menu_counter`, and the
    layout caches (`_layouts`, `_layouts_serialized`, `_scene_layouts_serialized`,
    `_layout_control_ids`) into `ControlHost`.

- [x] **4.2 — Registry + registration**
  - Move `_resolve_control`, `_register_view_handlers`,
    `_register_control_view_handlers`, `_register_control_handlers`,
    `_register_log_views`, and the `control_position` property/setter +
    `_orphan_position_for` / `_set_scene_control_position`.

- [x] **4.3 — Mounting + overlay/layout sync**
  - Move `_get_or_create_orphan_group`, `_mount_orphan_group`,
    `_prune_empty_orphan_group`, `_mount_orphan_control`, `_remove_group_view`,
    `_sync_overlays`, `_inject_scene_overlays`, `_layout_serialized_for`,
    `_scene_layout_for`, `_push_layout_updates(_threadsafe)`.

- [x] **4.4 — Value API + table undo/redo**
  - Move `set_control`, `get_control`, `set_control_value`,
    `set_control_view_value`, `update_control`, `remove_control` /
    `_remove_scene_control`, `remove_control_group` / `_remove_scene_group`,
    `clear_controls` / `_clear_scene_controls`, and `undo_table` / `redo_table` /
    `clear_table_history` / `can_undo_table` / `can_redo_table`.

- [x] **4.5 — Dispatch**
  - Move `_dispatch_event`, `_schedule_control_event`, `_push_control_update`,
    `_handle_file_browser_navigate` / `_handle_file_browser_select`, and the
    `control:*` / `control:group_toggle` core of `_dispatch_control_event` into
    `ControlHost` (expose as `dispatch(msg_type, payload, event)`).
  - `Visualizer._dispatch_control_event` becomes the thin router: close/accept
    → banner/dialog/editor hosts; everything else → `self._control_host.dispatch(...)`.

- [x] **4.6 — Containers + facades**
  - Move `add_control_group` / `_add_scene_group`, `add_menu`, and the 11
    `add_*` / `_add_scene_*` methods into `ControlHost` (facade collapse is
    phase 5; here they move as-is).

- [x] **4.7 — Wire `Visualizer`**
  - `__init__`: `self._control_host = ControlHost(runtime)`.
  - Public `add_*`/`set_control`/`get_control`/`set_control_value`/
    `set_control_view_value`/`update_control`/`remove_control`/
    `remove_control_group`/`clear_controls`/`undo_table`/`redo_table`/… become
    one-line forwarders.
  - Keep `viz._control_views` / `_orphan_groups` / `_scene_groups` /
    `_global_overlay` / `_scene_overlays` / `_resolve_control` /
    `_sync_overlays` / `_mount_orphan_control` / `_register_view_handlers` /
    `_add_scene_*` as delegating properties/forwarders.

- [x] **4.8 — Tests**
  - Full `py/tests/viz` suite passes unchanged.

## Validation

`uv run pytest py/tests/viz -q`

## Notes

- This phase is a pure move (no behavior change); `_handler_registry` stays a
  shared `Visualizer` field referenced through the `HostRuntime`.
- Do the move with `git mv`-style logic (edit in place), keeping signatures and
  docstrings identical.
