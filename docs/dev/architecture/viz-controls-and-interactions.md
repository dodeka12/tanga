# Viz controls & interactions architecture

How interactive UI — panel controls, layout views, banners, editors, file
choosers, and interactive 3D objects — is wired end-to-end in `py/pytanga/viz/`.
Follow this contract when adding a new control, view, or interactive element.

## Concepts

Three orthogonal concerns, one model:

- **Scene** — a 3D/2D world of entities (incl. interactive objects) + a camera
  + scene chrome.
- **Layout** — a tree arranging *scene panes* (`SceneView`) and *widgets*
  (`ControlView`) in split/stack/overlay views (one per page).
- **Control** — one model `id + kind + value + handlers`, *placed* in a panel,
  attached to a 3D object, in a layout pane, or in a banner.
- **Interaction** — an interactive object (`ActPoint`, …) under the same event
  model; it differs only in payload richness and coalescing.

## Fixed contract

1. **Single global id namespace.** Every control and interactive object has a
   globally unique `id`. `scene` is a routing hint, not a storage key.
2. **One `(id, event)` registry.** `ControlHandlerRegistry` keys handlers by
   `(id, event)` — `change`, `click`, `press`, `release`, `cell_change`,
   `row_add`, `column_add`, `group_toggle`, `close`. Panel controls, layout
   views, banners, editors, and interactions all register here.
3. **One control model.** Each `ControlView` (layout) wraps a
   `pytanga.viz._controls.Control` (exposed as `view.control`) — the same
   dataclasses the panel controls use — and serializes its fields from it via
   `_serialize_one_control`.
4. **One client→server envelope.** The frontend sends every user action through
   `sendEvent(target, event, data)` in `templates/events.js`:
   `{ type: "event", target: "<id>", event: "<name>", data: {…} }`.
   `server.py` maps `event` → the control or interaction callback.
5. **Two dispatch tails, one registry.** Control/banner/editor/file-browser
   events route through `Visualizer._dispatch_event` (handler `(value, event)`);
   interactions route through `InteractionHandlerRegistry.dispatch` (handler
   `(event)`, with drag-move coalescing + camera caching) — reading from the
   same registry.

## Event names

Control events (→ `_control_callback`): `change`, `click`, `press`, `release`,
`cell_change`, `row_add`, `column_add`, `group_toggle`, `close` (banner/editor —
`data.value` is the editor's text or `null`), `file_browser_navigate`,
`file_browser_select`.

Interaction events (→ `_interaction_callback`, coalesced): `interaction:click`,
`interaction:dblclick`, `interaction:drag_start`, `interaction:drag_move`,
`interaction:drag_end`, `interaction:scroll`.

## Adding a new control kind

1. **Backend model** — add a `Control` dataclass in `py/pytanga/viz/_controls.py`
   (`id`/`label`/`tooltip` + kind fields) plus its branch in
   `_serialize_one_control` and `set_control_value`/`get_control_value`.
2. **Layout view** — add a `*View(ControlView)` in `py/pytanga/viz/views.py`
   whose `__init__` builds `self.control = <Control>(...)` (keep the constructor
   signature); the base `ControlView._serialize` already emits the fields from
   `self.control`.
3. **Frontend** — add a `create<Kind>` factory in
   `templates/controls-panel.js` (registering a `_controlRegistry` entry with an
   `owner` and an `apply(value)`), and, for a layout view, a
   `views/<kind>-view.js` whose `render()` calls it with `owner: 'layout'`.
   Send events via `sendEvent(id, "<event>", { value })`.
4. **Server routing** — if the kind introduces a new *event* (not just a value),
   add the `event`→message mapping to `server.py::_EVENT_MSG_MAP` and a branch
   in `Visualizer._dispatch_control_event`.
5. **Tests** — serialization round-trip, registration, and dispatch.

## Interactive objects

Register handlers with `Visualizer.on_interaction(object_id, event_type,
handler)` (stored under `(object_id, event_type.value)`). The per-pane frontend
`InteractionController` captures/throttles pointer events and sends them under
`interaction:*` names; the backend coalesces `drag_move`.
