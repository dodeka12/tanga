# Phase 8 — Docs + changelog

## Goal

Write a **canonical architecture document** for the Tanga viewer under
`docs/dev/architecture/` that describes the `Visualizer` / `LayoutHost` /
`Layout` / `OverlayContainer` / `Scene` model — overall architecture, intended
**ownerships**, **data flows**, and **extension recipes** (new `*View` classes,
new entities, new overlay objects like `Dialog`/`Banner`).  It must be written
for two audiences: **developers** (who extend the library) and **AI agents**
(who need invariants, a file map, and test commands to make changes safely).

## Files

- Add: `docs/dev/architecture/viz-architecture.md` — the new canonical doc.
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md` — rewrite the
  stale sections (it still describes `HostRuntime`, `BannerHost`/`DialogHost`/
  `EditorHost`, the `add_*` facades, and the `ControlHost` value API).
- Edit: `docs/dev/index.md` — add the new doc to the reading order + Fast
  Orientation.
- Add: `docs/changelog/2026-09-03_feat-view-architecture.md` — branch changelog
  (per `dev/workflows/changelog.md`).

## Steps

- [x] **8.1 — New `viz-architecture.md`**
  One doc, the sections below (write them in this order).  Use the current
  post-refactor code as the source of truth — do not describe the pre-refactor
  global-registry model.

- [x] **8.2 — Rewrite `viz-controls-and-interactions.md`**
  Bring it in line with the new model; it becomes the *controls/interactions*
  deep-dive that `viz-architecture.md` links to.

- [x] **8.3 — Update `docs/dev/index.md`**
  Add `viz-architecture.md` to the reading order (before
  `viz-controls-and-interactions.md`) and to Fast Orientation.

- [x] **8.4 — Changelog**
  Append a `## Refactor` bullet to the branch changelog (see
  `dev/workflows/changelog.md` for title/format).

## Validation

`uv run mkdocs build --strict && uv run pytest -q`

---

## 8.1 doc outline (what `viz-architecture.md` must contain)

### 1. Big picture (one diagram + one paragraph)

An ASCII tree showing the composition root and the single ownership hierarchy
(no parallel global registries):

```
Visualizer                <- facade + composition root + lifecycle (boot/loop)
|- Transport             <- WebSocketTransport: send/register/route/dispatch
|- LayoutHost            <- owns scenes AND layouts (+ serialization)
|   |- scenes: dict[name, Scene]
|   `- layouts: dict[name, Layout]
|       `- Layout { base: View, overlay: OverlayContainer }
|- ControlHost           <- handler registration + inbound dispatch (tree-walk)
|- ThemeHost / InteractionHost
`- OverlayContainer      <- per-layout: overlays, dialogs, banners, editor
```

State the core principle: **one hierarchy, one owner per concern** — `Scene`
owns entities, `Layout` owns a base view + overlay, `LayoutHost` owns the
name-to-(scene, layout) maps, `Visualizer` wires them together and exposes the
public `viz.*` API.

### 2. Ownerships (a table)

| Concern | Owner | Notes |
|---|---|---|
| named scenes | `LayoutHost.scenes` | `add_scene(name)` |
| named layouts | `LayoutHost.layouts` | `set_layout(name, root)` |
| base view tree | `Layout.base` | `SplitView`/`StackView`/`SceneView` |
| overlays (groups/dialogs/banners/editor) | `Layout.overlay` (`OverlayContainer`) | |
| entities | `Scene` (`add_viz`/`add`/`update`/`remove`/`clear`) | |
| styles | `Scene.styles` (copy of the master `_global_styles`) | |
| control model (value/handlers/history) | the `Control` on each `*View` | `view.control` |
| `(id, event)` handlers | `ControlHandlerRegistry` (via `Transport`) | |
| inbound routing | `Transport.route` data table -> host `dispatch` | |

### 3. Data flows (short, each with the entry point -> path -> wire message)

- **Boot** — `Visualizer.__init__` builds `Transport` -> `LayoutHost` (+`add_scene("")`)
  -> `ControlHost`/`ThemeHost`/`InteractionHost` -> `layout.overlay.configure(...)`
  -> `_register_routes()`.
- **URL -> layout** — `/` serves `""`, `/?view=<name>` serves `layouts[name]`;
  `add_scene(name)` auto-creates `Layout(name, SceneView(name))`.
- **Add an entity** — `viz.add(...)` -> `layout.scene("").add_viz(...)` -> `Scene.add`/
  `add_object` -> `SceneObject` + `VizNode` -> `flush()` -> `entity_*` messages.
- **Add a control** — build `*View`, mount via `set_layout` (or `SceneView(overlay=[...])`);
  `ControlHost._register_view_handlers` registers `(id, event)` handlers.
- **Inbound control event** — `control:*` -> `ControlHost.dispatch` -> `_resolve_control`
  **tree-walk** -> `control.handle_event` -> `Dispatch` (event/value/push) -> push + handler.
- **Banner/dialog/editor** — `OverlayContainer.show_*` -> register `(id, event)` handlers
  -> `banner_*`/`dialog_*`/`editor_*` wire messages; `*_closed`/`accept`/`close` routes ->
  `OverlayContainer._on_*`.

### 4. Extension recipes (the "how do I add X" section — write each as numbered steps)

**4a. A new entity kind**
1. Add the `SceneEntity` (or reuse `SceneObject` for non-geometry drawables).
2. Route it through `Scene.add_viz` (handles `color`/`opacity`/`style`/`label`/
   `parent_id`/`attach_to`); note `_resolve_scene_entity` for MV analysis.
3. Add serialization in the node layer (`VizSceneObject`/`SceneObject`).
4. Frontend renderer + test.

**4b. A new control (`*View`)**
1. `Control` dataclass in `_controls.py` + branches in `_serialize_one_control` and
   `get_control_value`/`set_control_value`.
2. `*View(ControlView)` in `views.py` whose `__init__` builds `self.control = <Control>(...)`
   (keep the constructor signature; `ControlView.__getattr__` forwards reads/`set_value`/
   `undo`/`redo` to the control).
3. `Control.handle_event(event, payload) -> Dispatch` for any new event/mutation.
4. Frontend factory + `sendEvent(id, event, {value})`; server `_EVENT_MSG_MAP` for a new
   message name.
5. Tests: serialization round-trip, handler registration, dispatch.

**4c. A new overlay object (Dialog/Banner pattern)**
Follow the `OverlayContainer` pattern exactly:
1. Add state (`self._things: dict[str|None, dict[str, Any]]` + a counter) in
   `OverlayContainer.__init__`.
2. Add `_next_*_id`, `_register_*`, `show_*`/`remove_*`/`clear_*` (+ `_async` variants
   using `await self._transport.send_async`), `_push_*` serializers, and `_on_close`/`_on_accept`.
3. Register handlers via `self._transport.register(id, handler, event=...)`; use
   `self._control_host` for control-view resolution (dialogs).
4. Add the inbound route in `Visualizer._register_routes` -> an `OverlayContainer._on_*`
   method; add `Visualizer.show_*`/`remove_*` forwarders.
5. Test the wire round-trip + handler lifecycle.

### 5. Invariants + AI-agent orientation

- Every `id` is globally unique; `(id, event)` is the single handler key.
- Controls live in **overlays/layouts**, never in `Scene`.
- No `add_*` facades and no runtime value API on `ControlHost`; value/history live
  on the control (`set_value`, `Table.undo`/`redo`).
- Inbound dispatch **walks the layout tree** (`_resolve_control`); there is no
  `_control_views` index.
- File map (one line each): `visualizer.py`, `_layout.py`, `scene.py`, `_hosts.py`,
  `_controls.py`, `views.py`, `_transport.py`, `_ports.py`, `_scene_handle.py`.
- Test commands: `uv run pytest py/tests/viz -q` (fast), `uv run pytest -q` (full),
  `uv run mkdocs build --strict` (docs).
- Common pitfalls: circular imports (lazy-import `VizSceneHandle`/views inside methods),
  host back-reference is `Scene._host` (only for `ActSceneObject`/handle creation),
  `OverlayContainer.configure(...)` wires `transport`/`control_host` post-construction.

---

## 8.2 rewrite checklist (`viz-controls-and-interactions.md`)

- Replace `HostRuntime` -> `Transport` (ports model).
- Replace `BannerHost`/`DialogHost`/`EditorHost` -> `OverlayContainer`.
- Remove the `add_*` / `add_control_group` / `add_menu` facade description ->
  declarative `*View` + `set_layout` / `SceneView(overlay=[...])`.
- Remove the `ControlHost` value API (`set_control`/`get_control`/`update_control`/
  `undo_table`/…) -> control-owned `set_value`/`undo`/`redo` + tree-walk dispatch.
- Keep the `(id, event)` registry, `ControlView`/`Control` model, event-name table,
  and the interactive-object section (still accurate).
