# Multi-Scene Support for Visualizer

Enable the `Visualizer` to manage multiple named scenes, each served at a
unique URL path under the same HTTP+WebSocket server. Scenes run concurrently
in memory; multiple browser tabs/iframes can connect to different scenes
simultaneously.

## Motivation

Currently the visualizer is a 1:1:1 `Visualizer`→`Scene`→`VizServer` pipeline.
Users need to create multiple `Visualizer` instances on different ports for
different views, which is cumbersome for workflows like:

- **reveal.js presentations** where each slide embeds a different scene URL
- **Jupyter notebooks** displaying multiple scenes side-by-side in iframes
- **Control-driven scene switching** from the Python side (dropdown selects a
  scene, only the originating browser navigates)

## Architecture Overview

- `Visualizer` owns `self._scenes: dict[str, Scene]` — key `""` is the **main
  scene** for full backward compatibility.
- `viz.scene(name)` returns a `VizSceneHandle` proxy that exposes the same API
  as `Visualizer` (`add`, `update`, `remove`, `controls`, `animate_to`, etc.)
  but targets the named scene.
- The server serves `viewer.html` at `GET /` and `GET /{name:.*}`. The
  frontend reads `window.location.pathname` to determine which scene to
  request via WebSocket.
- All WebSocket messages include a `"scene"` field so the frontend can filter
  updates for its own scene.
- Each browser connection gets a unique `browser_id` (assigned by the server
  on handshake). All client→server messages include this ID. Control handlers
  receive `browser_id` as a keyword argument.
- Python-triggered navigation: `viz.navigate_to(scene, target=...)` where
  `target` is `"all"`, `"scene:<name>"`, or `"browser:<id>"`.
- No built-in scene selector UI — users build their own with
  `viz.list_scenes()` and `viz.add_dropdown(...)`.

## Phase 1 — Python Data Model & Server

### 1.1 `Scene` → scene name

**File:** `py/pytanga/viz/scene.py`

- [ ] 1.1.1 Add `name: str = ""` field to `Scene.__init__`
- [ ] 1.1.2 Add `"name"` to `SceneConfig.to_dict()` output

### 1.2 Browser session tracking in `VizServer`

**File:** `py/pytanga/viz/server.py`

- [ ] 1.2.1 Add `BrowserSession` dataclass with `id: str`, `scene: str`,
  `remote_addr: str`, `ws: web.WebSocketResponse`
- [ ] 1.2.2 Add `self._browser_sessions: dict[str, BrowserSession]` to
  `VizServer.__init__`
- [ ] 1.2.3 In `_ws_handler`: on connection, generate UUID browser_id, create
  `BrowserSession`, store in `_browser_sessions`, and send
  `{"type": "browser_id", "browser_id": "..."}` to the client **before**
  processing `ready`
- [ ] 1.2.4 Update `_push_full_state` to accept an optional `scene_name`
  parameter and send only that scene's config + state
- [ ] 1.2.5 Update `_build_app` to add catch-all route `GET /{name:.*}` →
  `_index_handler` (serves `viewer.html` for any path)
- [ ] 1.2.6 In `_ws_handler`: parse `"scene"` field from the `ready` message;
  validate the scene exists; if not, send `navigate` to `""` (main scene) and
  update the session's scene
- [ ] 1.2.7 Add `push_navigate(scene_name, target)` method that filters
  sessions by target (`"all"`, `"scene:<name>"`, `"browser:<id>"`) and sends
  `{"type": "navigate", "scene": "..."}`
- [ ] 1.2.8 In `_ws_handler`: on disconnect, remove the browser session
- [ ] 1.2.9 Update control event dispatch to extract `browser_id` from
  incoming messages and pass it to handlers

### 1.3 Multi-scene support in `Visualizer`

**File:** `py/pytanga/viz/visualizer.py`

- [ ] 1.3.1 Replace `self._scene` with `self._scenes: dict[str, Scene]` —
  initialize with main scene as `self._scenes[""] = Scene(config)`
- [ ] 1.3.2 Keep `self._scene` as a `@property` returning `self._scenes[""]`
- [ ] 1.3.3 Add `self._scene` setter for backward compat (sets
  `self._scenes[""]`)
- [ ] 1.3.4 Add `scene(name: str) → VizSceneHandle` method — creates the scene
  if it doesn't exist (inheriting default styles from the visualizer), returns
  a handle
- [ ] 1.3.5 Add `navigate_to(scene_name: str, target: str = "all")` —
  delegates to `VizServer.push_navigate()`
- [ ] 1.3.6 Add `list_scenes() → list[str]` — returns all scene names
- [ ] 1.3.7 Add `list_browsers() → list[dict]` — returns `[{id, scene,
  remote_addr}]` for all connected browsers
- [ ] 1.3.8 Add `scenes` property returning `dict[str, Scene]`
- [ ] 1.3.9 Update `flush()` to iterate all scenes and broadcast dirty diffs
  (each with the `"scene"` field)
- [ ] 1.3.10 Update `_on_client_connect` to send `browser_id` and
  `scene_list` message with all scene names
- [ ] 1.3.11 Update `_push_controls` / `_push_controls_async` to include the
  `"scene"` field in the message
- [ ] 1.3.12 Update `_dispatch_control_event` to pass `browser_id` to control
  handlers as a keyword argument
- [ ] 1.3.13 Update `_repr_html_` to embed the main scene URL (unchanged
  behavior)
- [ ] 1.3.14 Update `display_static` to accept optional `scene_name` parameter
  (defaults to main scene)
- [ ] 1.3.15 Update `start()` and `run()`: the flush callback passed to the
  server must include the scene name in messages

### 1.4 `VizSceneHandle` class

**File:** `py/pytanga/viz/_scene_handle.py` (new)

- [ ] 1.4.1 Create `VizSceneHandle` class with `__init__(self, visualizer,
  scene_name)`
- [ ] 1.4.2 Proxy methods: `add`, `update`, `update_entity`, `update_label`,
  `remove`, `clear`, `flush`, `set_title`, `set_annotation`
- [ ] 1.4.3 Proxy control methods: `add_slider`, `add_dropdown`, `add_button`,
  `add_group`, `remove_control`, `remove_group`, `clear_controls`
- [ ] 1.4.4 Proxy animation methods: `animate_to`, `timeline`
- [ ] 1.4.5 Properties: `name`, `url`, `scene`, `default_styles`,
  `default_label_style`, `default_label_styles`, `default_annotation_style`
- [ ] 1.4.6 `navigate_to(scene_name)` — calls
  `viz.navigate_to(scene_name, target=f"scene:{self.name}")`
- [ ] 1.4.7 `_repr_html_()` — returns iframe embedding
  `http://{host}:{port}/{name}`
- [ ] 1.4.8 `display_static(width, height)` — delegates to
  `viz.display_static(scene_name=self.name)`

### 1.5 Export `VizSceneHandle`

**File:** `py/pytanga/viz/__init__.py`

- [ ] 1.5.1 Add `VizSceneHandle` to imports and `__all__`

---

## Phase 2 — WebSocket Protocol

### 2.1 Browser ID assignment

- **Server → Client (on connect):**
  ```json
  {"type": "browser_id", "browser_id": "abc1234d"}
  ```

- **All Client → Server messages** include `"browser_id"`:
  ```json
  {"type": "control:change", "control_id": "pos_x", "value": 2.7, "browser_id": "abc1234d"}
  ```

### 2.2 Scene-aware messages

- [ ] 2.2.1 `scene_config` message includes `"name"` field
- [ ] 2.2.2 `scene_update` message includes `"scene"` field
- [ ] 2.2.3 `controls_define` message includes `"scene"` field
- [ ] 2.2.4 `controls_clear` message includes `"scene"` field
- [ ] 2.2.5 New message `navigate`: `{"type": "navigate", "scene": "scene1"}`
  (server → client)
- [ ] 2.2.6 New message `scene_list`:
  ```json
  {"type": "scene_list", "scenes": ["", "scene1", "group/sub"], "default": ""}
  ```
- [ ] 2.2.7 Client `ready` message includes `"scene"` field:
  ```json
  {"type": "ready", "scene": "scene1"}
  ```

---

## Phase 3 — Frontend (`viewer.js` + `viewer.html`)

### 3.1 Scene awareness

**File:** `py/pytanga/viz/templates/viewer.js`

- [ ] 3.1.1 On load, read `window.location.pathname` → strip leading `/` →
  use as scene name (empty string if at root)
- [ ] 3.1.2 Include `"scene"` in the `ready` WebSocket message
- [ ] 3.1.3 Store `browserId` from the `browser_id` assignment message; attach
  to all outgoing messages (`control:change`, `control:click`,
  `control:group_toggle`, `screenshot:data`)
- [ ] 3.1.4 In `handleMessage`: add scene filtering — only process
  `scene_update` and `scene_config` messages where `msg.scene === myScene`
  (process `clear_all`, `navigate`, `browser_id`, `scene_list`, `animate`,
  `timeline`, `screenshot` unconditionally)
- [ ] 3.1.5 Handle `navigate` messages: `window.location.href = "/" +
  msg.scene` (or just `"/"` when scene is `""`)
- [ ] 3.1.6 Handle `scene_list` messages: store available scenes list (for
  potential future UI, not rendered by default)
- [ ] 3.1.7 On reconnect/reload: persist `browserId` in `sessionStorage` so
  the same ID is reused across page navigations within the same browser
  session

### 3.2 Reconnect with scene preservation

- [ ] 3.2.1 The browser's URL already encodes the scene. On WebSocket
  reconnect, the `ready` message sends the scene from the URL path
- [ ] 3.2.2 The server validates the scene exists; if it was removed (e.g.
  server restart with different scenes), the server responds with a `navigate`
  to the main scene before sending config

---

## Phase 4 — Control Handler `browser_id` Integration

### 4.1 Update handler signatures

**File:** `py/pytanga/viz/visualizer.py`

- [ ] 4.1.1 Update `_dispatch_control_event` to extract `browser_id` from the
  payload and pass it to the handler
- [ ] 4.1.2 Handler call: `await handler(value, browser_id=browser_id)` for
  `control:change` and `control:group_toggle`; `await handler(None,
  browser_id=browser_id)` for `control:click`

### 4.2 Control examples

- [ ] 4.2.1 Users can write handlers that accept `browser_id` as a keyword
  argument:
  ```python
  def on_scene_change(selected_scene, browser_id=None):
      if browser_id:
          viz.navigate_to(selected_scene, target=f"browser:{browser_id}")
  ```

---

## Phase 5 — Export & Static Display

### 5.1 `SceneExporter` update

**File:** `py/pytanga/viz/export/_exporter.py`

- [ ] 5.1.1 Accept optional `scene_name` parameter (defaults to main scene)
- [ ] 5.1.2 Export the specified scene's state instead of always the main
  scene

### 5.2 `VizSceneHandle.display_static`

- [ ] 5.2.1 Delegates to a scene-specific export

---

## Phase 6 — Documentation

**File:** `docs/py/viz/scenes.md` (new)

- [ ] 6.1 Document multi-scene concept and URL structure
- [ ] 6.2 Document `viz.scene(name)` → `VizSceneHandle` API
- [ ] 6.3 Document `viz.navigate_to(scene, target=...)`
- [ ] 6.4 Document `viz.list_scenes()` and `viz.list_browsers()`
- [ ] 6.5 Document browser ID lifecycle and control handler integration
- [ ] 6.6 Example: dropdown-driven scene switching
- [ ] 6.7 Example: multiple iframes in Jupyter
- [ ] 6.8 Example: reveal.js presentation with different scene URLs

**File:** `docs/py/viz/visualizer.md`

- [ ] 6.9 Add `scene()`, `navigate_to()`, `list_scenes()`, `list_browsers()`
  to the Visualizer API reference

---

## Phase 7 — Tests & Smoke Testing

- [ ] 7.1 Unit test: `Scene` with name, `SceneConfig.to_dict()` with name
- [ ] 7.2 Unit test: `BrowserSession` creation and serialization
- [ ] 7.3 Unit test: `navigate_to` target filtering logic (all, scene:xxx,
  browser:xxx)
- [ ] 7.4 Unit test: `VizSceneHandle` proxy methods route to correct scene
- [ ] 7.5 Unit test: `VizSceneHandle._repr_html_` output format
- [ ] 7.6 Unit test: `list_scenes()` and `list_browsers()` return correct
  data
- [ ] 7.7 Smoke test: create two scenes, add entities to each, open both in
  separate browser tabs, verify independent rendering
- [ ] 7.8 Smoke test: dropdown control triggers `navigate_to` for only the
  originating browser
- [ ] 7.9 Smoke test: Jupyter notebook with two `VizSceneHandle._repr_html_()`
  iframes side by side

---

## Message Flow Summary

```
Browser A connects to /scene1
──────────────────────────────────────
1. WS open → server assigns browser_id "a1", sends {"type":"browser_id", "browser_id":"a1"}
2. Browser sends {"type":"ready", "scene":"scene1", "browser_id":"a1"}
3. Server validates "scene1" exists → sends scene_config + full_state for scene1
4. Server sends {"type":"scene_list", "scenes":["","scene1","scene2"], "default":""}
5. Browser renders scene1

Python calls: viz.navigate_to("scene2", target="browser:a1")
──────────────────────────────────────
6. Server sends {"type":"navigate", "scene":"scene2"} to browser "a1"
7. Browser A: window.location.href = "/scene2" → page reloads
8. Reconnect → ready with "scene":"scene2" → scene2 loads

Control event from browser A (dropdown value changed to "scene2")
──────────────────────────────────────
9. Browser sends {"type":"control:change", "control_id":"sel", "value":"scene2", "browser_id":"a1"}
10. Server dispatches to handler(value="scene2", browser_id="a1")
11. Handler calls: viz.navigate_to("scene2", target="browser:a1")
12. Browser A navigates to /scene2