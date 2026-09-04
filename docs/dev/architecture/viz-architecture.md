# Viz architecture

Canonical overview of the Tanga viewer (`py/pytanga/viz/`) after the
scene/layout/overlay remodel.  It documents the **ownership hierarchy**, the
**data flows**, and the **extension recipes** (new entities, new `*View`
controls, new overlay objects like `Dialog`/`Banner`).  Written for developers
and for AI agents: read the invariants + file map before touching code.

## Big picture

One hierarchy, one owner per concern — no parallel global-registry dicts.

```
Visualizer                facade + composition root + lifecycle (boot/loop)
|- Transport             WebSocketTransport: send / register / route / dispatch
|- LayoutHost            owns scenes AND layouts (+ register/resolve/dispatch)
|   |- scenes:  dict[name, Scene]        entity containers (add_scene)
|   `- layouts: dict[name, Layout]       first-class layouts (set_layout)
|       `- Layout { base: View, overlay: OverlayContainer }
|- ThemeHost / InteractionHost
`- OverlayContainer      per-layout: overlays, dialogs, banners, editor
```

There is **no `ControlHost`**.  Each `*View` wraps a `Control` that owns its own
value, serialization, and handlers (`serialize` / `register_handlers` /
`handle_event`); `LayoutHost` owns the tree walk that registers them and the
inbound dispatch that resolves them.

- **`Scene`** owns *entities* and the typed entity API.  One scene can appear in
  many panes (`SceneView(name)`) and many layouts.
- **`Layout`** is a `base` view tree plus an `OverlayContainer`.  URLs name
  **layouts** (`/?view=<name>`), never scenes.
- **`Visualizer`** wires everything together and exposes the public `viz.*` API
  through explicit thin forwarders (no `__getattr__`).

## Ownerships

| Concern | Owner | Notes |
|---|---|---|
| named scenes | `LayoutHost.scenes` | `add_scene(name)` auto-creates `Layout(name, SceneView(name))` |
| named layouts | `LayoutHost.layouts` | `set_layout(root, name)` / `add_layout(root, name)` |
| base view tree | `Layout.base` | `SplitView` / `StackView` / `SceneView` |
| view identity | `View.id` (auto `v0`…, overridable via `id=`) | stable across re-serializations; `remove_view(id)` |
| overlays (groups/dialogs/banners/editor) | `Layout.overlay` (`OverlayContainer`) | one per layout (shared instance today) |
| entities | `Scene` (`add_viz`/`add`/`update`/`remove`/`clear`) | |
| styles | `Scene.styles` (copy of the master `_global_styles`) | |
| control model (value/handlers/history) | the `Control` on each `*View` | `view.control` |
| `(id, event)` handlers | `ControlHandlerRegistry` (via `Transport`) | registered by `Control.register_handlers` |
| inbound routing | `Transport.route` data table -> `LayoutHost.dispatch_control_event` | |

## Data flows

- **Boot** — `Visualizer.__init__` builds `Transport` -> `LayoutHost`
  (+`add_scene("")`) -> `ThemeHost`/`InteractionHost`; `OverlayContainer` gets a
  back-reference to its owning `LayoutHost`, then `_register_routes()`.
- **URL -> layout** — `/` serves the `""` layout, `/?view=<name>` serves
  `layouts[name]`; `add_scene(name)` supplies scene-URL sugar for free.
- **Add an entity** — `viz.add(...)` -> `layout.scene("").add_viz(...)` ->
  `Scene.add`/`add_object` -> `SceneObject` + `VizNode` -> `flush()` -> `entity_*`
  messages.  `_resolve_scene_entity` turns MVs into `SceneEntity`.
- **Add a control** — build a `*View`, mount it via `set_layout` (or declaratively
  in `SceneView(overlay=[...])`); `LayoutHost.register` walks the tree and calls
  each `Control.register_handlers` (registers `(id, event)` handlers).
- **Inbound control event** — `control:*` -> `LayoutHost.dispatch_control_event` ->
  `resolve_control` **tree-walk** (layouts + dialogs) -> `control.handle_event`
  -> `Dispatch(event, value, push)` -> push + fire the handler.
- **Banner/dialog/editor** — `OverlayContainer.show_*` registers `(id, event)`
  handlers and sends `banner_*`/`dialog_*`/`editor_*` wire messages; the
  `*_closed`/`accept`/`close` routes call `OverlayContainer._on_*`.
- **Add/remove an overlay view** — `viz.add(view)` mounts a `View` in the
  global overlay and pushes a granular `overlay_define` (only that view, not
  the whole layout); `viz.remove_view(id)` removes it via `overlay_remove`.
  Per-scene overlays (`scene=…`) re-sync the layout instead.  Every `View`
  carries a stable `id` (auto `v0`…) so it can be addressed at runtime.
- **Layout re-push** — the frontend **reuses existing `ThreeJsView` scene
  panes** (keyed by scene name) across `view_layout` re-pushes, so only the
  DOM chrome rebuilds and the WebGL scene/camera are never torn down; a scene
  pane newly introduced by a re-push fetches its state with a
  `scene_sync_request` round-trip.

## Extension recipes

### New entity kind

1. Add the `SceneEntity` (or reuse `SceneObject` for non-geometry drawables).
2. Route it through `Scene.add_viz` — it already handles `color`/`opacity`/
   `style`/`label`/`parent_id`/`attach_to`; note `_resolve_scene_entity` for MV
   analysis (multivector -> `SceneEntity`).
3. Serialize it in the node layer (`VizSceneObject`/`SceneObject` in
   `scene.py` / `_nodes.py`).
4. Add a frontend renderer + a test (round-trip + flush).

### New control (`*View`)

1. `Control` dataclass in `_controls.py` with `_value_type` + `_fields()`
   (scalar controls) or `set_value`/`get_value` overrides (`Table`).  No
   central switch — `serialize()` merges `_fields()`.
2. `*View(ControlView)` in `views.py` whose `__init__` builds
   `self.control = <Control>(...)` (keep the constructor signature;
   `ControlView.__getattr__` forwards reads and `set_value`/`undo`/`redo` to the
   control; `ControlView.set_value` sets *and* pushes `control_update`).
3. `Control.handle_event(event, payload) -> Dispatch` for any new event or model
   mutation (see `Table.handle_event`).  The `on_*` fields *are* the handler
   declaration — `Control.register_handlers` maps `on_change` -> `"change"`, etc.
4. Frontend factory + `sendEvent(id, event, {value})`; add a server
   `_EVENT_MSG_MAP` entry for a new message name.
5. Tests: serialization round-trip, handler registration, dispatch.

### New overlay object (Dialog/Banner pattern)

Follow the `OverlayContainer` pattern exactly:

1. State in `OverlayContainer.__init__`:
   `self._things: dict[str|None, dict[str, Any]] = {}` + a counter.
2. Add `_next_*_id`, `_register_*`, `show_*`/`remove_*`/`clear_*` (+ `_async`
   variants using `await self._transport.send_async`), `_push_*` serializers,
   and `_on_close`/`_on_accept` handlers.
3. Register handlers via `self._transport.register(id, handler, event=...)`; use
   `self._layout` (the owning `LayoutHost`) to register dialog content and
   resolve control ids.
4. Add the inbound route in `Visualizer._register_routes` -> an
   `OverlayContainer._on_*` method; add `Visualizer.show_*`/`remove_*` forwarders.
5. Test the wire round-trip + handler lifecycle.

## Invariants + AI-agent orientation

- Every `id` is globally unique; `(id, event)` is the single handler key.
- Every `View` has a stable `id` (auto `v0`…, overridable via `id=`); its
  `_serialize()` emits `self.id` — there is no per-serialization id generator.
- `viz.remove_view(id)` removes a mounted overlay view (global overlay = a
  granular `overlay_remove`; per-scene overlay = a full re-sync).
- Controls live in **overlays/layouts**, never in `Scene`.
- No `add_*` facades and no runtime value API; value/history/serialization/
  handler registration live on the control (`Control.set_value`,
  `Control.serialize`, `Control.register_handlers`, `Table.undo`/`redo`).
- Inbound dispatch **walks the layout tree** (`LayoutHost.resolve_control`);
  there is no `_control_views` index and no `ControlHost`.
- `Visualizer.add` is **polymorphic**: a `View` -> the default layout overlay,
  everything else -> the main scene.

### File map

| File | Role |
|---|---|
| `visualizer.py` | `Visualizer` — facade, composition root, lifecycle |
| `_layout.py` | `Layout`, `OverlayContainer`, `LayoutHostImpl` |
| `scene.py` | `Scene`, `SceneObject`, `SceneConfig`, `_resolve_scene_entity` |
| `_hosts.py` | `ThemeHost`, `InteractionHost`, `OverlayHost` |
| `_controls.py` | `Control` + subclasses (value/serialize/handle_event/register_handlers), registry |
| `views.py` | `View` + `SceneView`/`StackView`/`GroupView`/`MenuView` + `*View` |
| `_ports.py` | `Transport`/`LayoutHost` protocols + `ServerState` |
| `_transport.py` | `WebSocketTransport` |
| `_scene_handle.py` | `VizSceneHandle` (per-scene proxy) |

### Test commands

```
uv run pytest py/tests/viz -q   # fast
uv run pytest -q                # full
uv run mkdocs build --strict    # docs
```

### Common pitfalls

- **Circular imports** — `scene.py` <-> `_scene_handle.py`; import `VizSceneHandle`
  and view classes lazily *inside* methods.
- **`Scene._host`** is a back-reference to the `Visualizer`, used only for
  `ActSceneObject` init and `VizSceneHandle` creation.
- **`OverlayContainer.configure(...)`** wires `transport`/`layout`
  post-construction (the layout host back-reference).
- **`set_layout` vs `add_layout`** — both take `(root, name="")`;
  `add_layout` raises if the name is taken; `set_layout` also registers
  handlers + injects `_push` callbacks and re-syncs the layout.
