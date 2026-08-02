# Viewer Identity & Browser Session Improvements

## Problem

1. All iframes share the same `sessionStorage` key (`tanga_browser_id`), causing collisions when multiple iframes embed different scenes from the same origin.
2. `list_browsers()` works but lacks a human-readable label for identifying specific viewers.
3. `navigate_to()` can't target a specific viewer by name.

## Design

- **`browser_id`** — server-assigned UUID per WebSocket connection. No persistence, no sessionStorage. Each new WS connection gets a fresh ID.
- **`viewer_name`** — optional friendly label passed via `?viewer=name` in the iframe URL. Read by viewer.js on load, sent in the `ready` message, stored in `BrowserSession.viewer_name`.

### SessionStorage removal

sessionStorage was used to preserve `browser_id` across reconnects so the server could map a new WS connection to an existing `BrowserSession`. However, after any reconnect the server already calls `_push_full_state()` — full scene config, entities, scene list. BrowserSession identity doesn't need to survive reconnects.

### Navigation target

Extend `target` parameter with `"viewer:<name>"`:

```python
viz.navigate_to("two")                          # target="all" (default)
viz.navigate_to("two", target="all")            # all browsers
viz.navigate_to("two", target="scene:one")      # browsers viewing scene "one"
viz.navigate_to("two", target="browser:a1b2")   # browser by id
viz.navigate_to("two", target="viewer:one")     # browser by viewer_name (new)
```

## Implementation Steps

### Step 1: viewer.js — viewer_name & sessionStorage removal

- [ ] Remove `let _browserId = sessionStorage.getItem(...)` (line 34), replace with `let _browserId = null`
- [ ] Remove `sessionStorage.setItem(...)` in `handleMessage` browser_id handler (line 483)
- [ ] Parse `viewer` from URL query params: `new URLSearchParams(location.search).get("viewer")`
- [ ] Send `viewer_name` in `ready` message payload

### Step 2: server.py — BrowserSession.viewer_name

- [ ] Add `viewer_name: str | None = None` field to `BrowserSession` dataclass
- [ ] In `_ws_handler` `ready` handler: set `current_session.viewer_name = data.get("viewer_name")`
- [ ] Include `"viewer_name"` in `get_browser_sessions()` output dict
- [ ] Add `"viewer:<name>"` target matching in `push_navigate()`

### Step 3: visualizer.py — VizSceneHandle.display()

- [ ] Add `display(viewer_name=None)` method to `VizSceneHandle`
  - If `viewer_name` is set, store `self._viewer_name = viewer_name`
  - Call `IPython.display.display()` internally and return None
- [ ] Update `_repr_html_()` to append `?viewer={self._viewer_name}` to iframe `src` when set

### Step 4: test_viz_multi_scene.ipynb — use display with viewer_name

- [ ] Replace `display(one)` with `one.display(viewer_name="browser-one")`
- [ ] Replace `display(two)` with `two.display(viewer_name="browser-two")`
- [ ] Replace `display(three)` with `three.display(viewer_name="browser-three")`
- [ ] Update `list_browsers()` cell to show `viewer_name` field

### Step 5: test_viz_multi_scene.py — verify

- [ ] Add a `list_browsers()` check with viewer_names after iframes connect
- [ ] Test `navigate_to("two", target="viewer:browser-one")`