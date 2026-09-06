# Viz Control-Host Extraction — Overview

**Created:** 2026-09-04 | **Status:** Done | **Branch:** `feat/view-architecture`

## Goal

Shrink the ~4870-line `Visualizer` God class by extracting the whole
control/overlay layer into specialized **host** classes behind one shared base,
so each kind of interactive thing (controls, banners, dialogs, the editor) owns
its own state, lifecycle, and wire messages.  `Visualizer` keeps its scene /
theme / camera / animation / export / Jupyter responsibilities and delegates
everything control-related to the hosts.  The public `viz.add_*` /
`viz.show_banner` / `viz.show_dialog` / `viz.open_editor` / … API is unchanged.

## Architecture (short)

- New module `py/pytanga/viz/_hosts.py`:
  - `HostRuntime` — a small dataclass bundling the shared plumbing each host
    needs: `server`, `loop`, `registry: ControlHandlerRegistry`,
    `on_server_loop(coro_factory)`, and a guarded `push_message(dict)`.
  - `OverlayHost` — base holding a `HostRuntime` + common helpers.
  - `ControlHost`, `BannerHost`, `DialogHost`, `EditorHost` subclasses.
- `Visualizer.__init__` builds one `HostRuntime` + the four hosts; its public
  methods become one-line forwarders; the `_` attributes that `VizSceneHandle`
  and the tests touch are kept as delegating properties/forwarders, so the
  refactor is behavior-preserving with zero test churn.
- `MenuView` stays a `View` container (not `ControlView`).

## Canonical contract (fixed up front)

### Host ownership (what moves out of `Visualizer`)

| Host | State | Wire | Methods it absorbs |
|------|-------|------|--------------------|
| `ControlHost` | `_control_views`, `_orphan_groups`, orphan positions, `_global_overlay`/`_scene_overlays`/`_scene_groups`/`_injected_overlay_ids`, `_menus`/`_menu_counter`, layout caches | `control_update`, `view_layout` | `_resolve_control`, `_mount_orphan_control`, `_register_*_handlers`, `_sync_overlays`/`_inject_scene_overlays`/`_push_layout_updates*`, value API (`set_control`/`get_control`/`set_control_value`/`set_control_view_value`/`update_control`/`remove_control`/`clear_controls`), `undo_table`/`redo_table`/`clear_table_history`/`can_*_table`, `_dispatch_event`/`_schedule_control_event`/`_push_control_update`/`_handle_file_browser_*` + the `control:*` dispatch core, `add_*`/`add_control_group`/`add_menu` |
| `BannerHost` | `_banners`, `_banner_counter` | `banner_define`/`banner_remove`/`banner_clear` | `_register_banner`/`_unregister_banner`, `show_banner`/`alert`/`confirm`/`remove_banner`/`clear_banners`, `_push_banner*` (+ async), `_on_close` |
| `DialogHost` | `_dialogs`, `_dialog_counter` | `dialog_define`/`dialog_remove`/`dialog_clear` | `_register_dialog`/`_unregister_dialog`/`_find_dialog`, `show_dialog`/`remove_dialog`/`clear_dialogs`, `_push_dialog*` (+ async), `_on_accept`/`_on_close` |
| `EditorHost` | *(none — one-shot)* | `editor_define` | `open_editor`, `_push_editor_define`, `_on_close` |

### Dispatch routing

`Visualizer._dispatch_control_event` stays the single server entry point and
becomes a thin router: `banner_closed`/`editor_closed`/`close` → the owning
host's `_on_close`; `accept` → `DialogHost._on_accept`;
`file_browser_*` / `control:*` / `control:group_toggle` → `ControlHost`.

### Facade de-dup

The 11 `_add_scene_*` methods collapse to one table-driven
`_add_scene_control(kind, cid, **fields)` keyed by `kind → ViewClass`; `add_*`
stay thin typed wrappers (same signatures/docstrings); `VizSceneHandle.add_*`
stay thin forwarders.

## Decisions (confirmed)

- Four hosts + a base; **no `MenuHost`** — menus are overlay containers, handled
  by `ControlHost` (same as `add_control_group` / orphan groups).
- `MenuView` stays a `View` container; a future "active menu element" feature
  adds `value`/`on_change`/`on_activate` to `MenuView` (the `GroupView` +
  `on_toggle` pattern), not a `ControlView`.
- Hosts hold a `HostRuntime` (not a `Visualizer` back-reference) for independent
  testability.
- Behavior-preserving: `VizSceneHandle` + tests unchanged; `Visualizer` exposes
  delegating properties/forwarders for the `_` attributes they touch.
- No change to scene/entity/theme/camera/animation/export/Jupyter code.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-overlay-host-banner.md](./01-overlay-host-banner.md) | `HostRuntime` + `OverlayHost` base; extract `BannerHost` |
| 2 | [02-dialog-host.md](./02-dialog-host.md) | Extract `DialogHost` |
| 3 | [03-editor-host.md](./03-editor-host.md) | Extract `EditorHost` |
| 4 | [04-control-host.md](./04-control-host.md) | Extract `ControlHost` |
| 5 | [05-facade-dedup.md](./05-facade-dedup.md) | Collapse `_add_scene_*` → `_add_scene_control` |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Docs + changelog + future-direction note |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz -q` (every phase).
- **JS guard (unchanged):** `node --check py/pytanga/viz/templates/controls-panel.js`.
- **Docs:** `uv run mkdocs build --strict` (final phase).

## Non-goals

- No new wire messages or behavior changes.
- No `MenuHost`; no `MenuView`→`ControlView` conversion.
- No `VizSceneHandle`/test churn (kept compatible via forwarders).
- No DI framework — a plain `HostRuntime` dataclass.
- No change to scene/entity/theme/camera/animation/export/Jupyter.
