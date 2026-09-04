# Viz controls & interactions architecture

How interactive UI — control views, overlays, banners, editors, file choosers,
and interactive 3D objects — is wired end-to-end in `py/pytanga/viz/`.  Follow
this contract when adding a new control, view, or interactive element.  For the
overall scene/layout/overlay model, see
[`viz-architecture.md`](viz-architecture.md).

## Concepts

Three orthogonal concerns, one model:

- **Scene** — a 3D/2D world of entities (incl. interactive objects) + a camera
  + scene chrome.
- **Layout** — a tree arranging *scene panes* (`SceneView`) and *widgets*
  (`*View`) in split/stack/overlay views (one per page).
- **Control** — one model `id + kind + value + handlers`, wrapped by a
  `*View(ControlView)` and *placed* in an overlay `GroupView` or a
  `SceneView(overlay=[...])`, a layout pane, or a banner/dialog.
- **Interaction** — an interactive object (`ActPoint`, …) under the same event
  model; it differs only in payload richness and coalescing.

## Fixed contract

1. **Single global id namespace.** Every control, interactive object, and
   `View` has a globally unique, stable `id` (views auto-generate `v0`… and
   can override it via `id=`); `scene` is a routing hint, not a storage key.
   Stable ids are what make `viz.remove_view(id)` possible.
2. **One `(id, event)` registry.** `ControlHandlerRegistry` keys handlers by
   `(id, event)` — `change`, `click`, `press`, `release`, `cell_change`,
   `row_add`, `column_add`, `row_delete`, `toggle`, `close`, `accept`.  Layout
   views, banners, dialogs, editors, and interactions all register here.
3. **One control model.** Each `*View` wraps a `pytanga.viz._controls.Control`
   (exposed as `view.control`) and serializes its fields from it via
   `Control.serialize` (`_fields()` per kind).  `ControlView.__getattr__`
   forwards attribute reads *and* `set_value`/`get_value`/`undo`/`redo`/
   `can_undo`/`can_redo` to the control, so value and history live on the
   control, not on a host.
4. **One client→server envelope.** The frontend sends every user action through
   `sendEvent(target, event, data)` in `templates/events.js`:
   `{ type: "event", target: "<id>", event: "<name>", data: {…} }`.
   `server.py` maps `event` → the control or interaction callback.
5. **Tree-walk dispatch, one registry.** Inbound `control:*` events route to
   `LayoutHost.dispatch_control_event`, which resolves the control id by
   **walking the layout trees and dialog contents** (`resolve_control` — there is
   no `_control_views` index) and delegates to `control.handle_event`.
   Interactions route through `InteractionHost._dispatch_interaction_event`
   (handler `(event)`, with drag-move coalescing + camera caching) — reading
   from the same registry.

## Host layer

Control/overlay concerns are split out of `Visualizer` into hosts in
`py/pytanga/viz/_hosts.py`:

- `OverlayHost` — base that holds the two ports (`Transport` + `LayoutHost`);
  `_handler_registry`/`_push_message` are thin aliases over `Transport`.
- `LayoutHost` (in `_layout.py`) — the owner of scenes + layouts.  It registers
  a mounted view tree (`register` walks `iter_control_views` and calls each
  `Control.register_handlers`, injecting the `_push` callback), resolves control
  ids (`resolve_control` — layouts + dialogs), and runs the `control:*` /
  `file_browser_*` dispatch core (`dispatch_control_event`).  There is **no**
  `ControlHost`.
- `ThemeHost` / `InteractionHost` — theme selection and interactive-object
  handling.
- `OverlayContainer` (in `_layout.py`) — the per-layout overlay: `add(view)`,
  `show_banner`/`alert`/`confirm`, `show_dialog`, `open_editor`, and their
  `_on_close`/`_on_accept` handlers (the old `BannerHost`/`DialogHost`/
  `EditorHost` are folded into it).

`Visualizer` exposes the public API through explicit forwarders (no
`__getattr__`); `_register_routes()` installs the inbound routing table on the
`Transport`.

## View & layout model

The layout tree is the single render path for **every** page:

- `View` is the base for every pane/container (`SceneView`, `StackView`,
  `SplitView`, `GroupView`, `MenuView`, and the `*View` control wrappers);
  every view has a stable `id` (auto `v0`…, overridable) so it can be
  addressed/removed at runtime.
- `SceneView` is a pane that renders a named scene; its `overlay` lists views
  (e.g. a `GroupView`) that float over that pane's canvas, anchored by each
  child's `position` (`EAnchor`).
- `GroupView` is a titled `StackView` with an optional leading `icon`,
  `icon_only` mode, and a borderless fold button — the control-group container.
- `MenuView` is a hamburger `dropdown` or a permanent `bar` of options
  (`EControlVariant.MENU` flattens its control children).

Controls are added declaratively — build the `*View` and either pass it to
`set_layout` (or `viz.add(view)`, which mounts it in the default layout's
overlay) or list it in a `SceneView(overlay=[...])`.  The whole tree serializes
to one `view_layout` message via `serialize_layout(root, name=..., overlay=[...])`.

## View-mode unification

There is one view mode. A "single scene" is served as a layout whose root is a
one-`SceneView` stack (`StackView("vertical", [SceneView(name)])`) merged with
the global overlay (base scene `""` only) and per-scene overlays:

- `LayoutHost._scene_layout_for(scene_name)` resolves any scene to its
  serialized `view_layout` (the base scene reuses the default layout).
- The server always resolves a `view_layout` on `ready` (`layout` →
  `_layout_callback`, else `_scene_layout_callback(scene_name)`) and the
  frontend always renders through `_buildLayout` — there is no separate
  single-scene bootstrap.
- Global-overlay changes are **granular**: `viz.add(view)` pushes an
  `overlay_define` and `viz.remove_view(id)` pushes an `overlay_remove` (only
  the overlay view is sent, not the whole layout); per-scene overlays and
  `set_layout` re-push the full `view_layout` instead.
- On every `view_layout` the frontend **reuses the existing `ThreeJsView`
  scene panes** (keyed by scene name) rather than tearing them down, so only
  the DOM chrome rebuilds and the WebGL scene/camera survive; a scene pane
  newly introduced by a re-push fetches its state via `scene_sync_request`.

## Event names

Control events (→ `LayoutHost.dispatch_control_event`): `change`, `click`, `press`,
`release`, `cell_change`, `row_add`, `column_add`, `row_delete`, `undo`,
`redo`, `toggle` (group), `close` (banner/editor — `data.value` is the editor's
text or `null`), `file_browser_navigate`, `file_browser_select`.

Interaction events (→ `InteractionHost._dispatch_interaction_event`, coalesced):
`interaction:click`, `interaction:dblclick`, `interaction:drag_start`,
`interaction:drag_move`, `interaction:drag_end`, `interaction:scroll`.

## Adding a new control kind

1. **Backend model** — add a `Control` dataclass in `py/pytanga/viz/_controls.py`
   (`id`/`label`/`tooltip` + kind fields) with `_value_type` + `_fields()` (or
   `set_value`/`get_value` overrides for table-like kinds).  There is **no**
   central serialization/coercion switch — `serialize()` merges `_fields()` and
   `set_value` coerces via `_value_type`.
2. **Layout view** — add a `*View(ControlView)` in `py/pytanga/viz/views.py`
   whose `__init__` builds `self.control = <Control>(...)` (keep the constructor
   signature); the base `ControlView._serialize` emits the fields from
   `self.control`, and `ControlView.__getattr__` forwards `set_value`/`undo`/…
   Handler registration is automatic: the `on_*` constructor kwargs are
   dataclass fields on the control, and `Control.register_handlers` maps each
   `on_<event>` to its `(id, event)` registry entry at mount time.
3. **Frontend** — add a `create<Kind>` factory in `templates/controls-panel.js`
   (registering a `_controlRegistry` entry with an `owner` and an `apply(value)`),
   and, for a layout view, a `views/<kind>-view.js` whose `render()` calls it
   with `owner: 'layout'`.  Send events via `sendEvent(id, "<event>", { value })`.
4. **Server routing** — if the kind introduces a new *event* (not just a value),
   add the `event`→message mapping to `server.py::_EVENT_MSG_MAP`.  Event
   *handling* lives on the control: override `Control.handle_event(event,
   payload) -> Dispatch` in `_controls.py` to mutate the model and report which
   `(id, event)` handler to fire and what to push back (see `Table.handle_event`).
   For a kind whose handler must still fire when the control id is not
   resolvable, mirror the `parse_table_event` helper.
5. **Tests** — serialization round-trip, registration, and dispatch.

## Interactive objects

Register handlers with `Visualizer.on_interaction(object_id, event_type,
handler)` (stored under `(object_id, event_type.value)`).  The per-pane frontend
`InteractionController` captures/throttles pointer events and sends them under
`interaction:*` names; the backend coalesces `drag_move`.

## Follow-ups

- **Fold `interaction.js` onto `sendEvent`** — the interactive-object frontend
  (`templates/interaction.js`) still sends `interaction:*` messages directly
  rather than through `sendEvent` (the server already routes
  `event: "interaction:*"`).  Deferred: it touches the timing-sensitive drag
  path and isn't covered by the browser-less test suite.
- **Active menu element** — if menus gain a backend-visible "active element",
  add `value` / `on_change` / `on_activate` to `MenuView` directly (menus are
  overlay containers, not control leaves, and keyboard navigation is
  frontend-only).
