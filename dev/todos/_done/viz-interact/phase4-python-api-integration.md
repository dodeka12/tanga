# Phase 4 — Python API: Visualizer Integration

Wire the Python-side control API into the existing `Visualizer` class, server
message dispatch, and export exclusions. This phase connects all previous work
into the user-facing API.

References: [Overview](./README.md) | [Phase 1](./phase1-protocol-and-data-model.md) | [Phase 2](./phase2-frontend-control-panel.md) | [Phase 3](./phase3-frontend-attachable-controls.md)

---

## 4.1 New Methods on `Visualizer`

### 4.1.1 `add_slider(id, *, label, min, max, step, default, on_change=None, parent_id=None)`

Creates a slider control and adds it to the scene's control registry.

```python
def add_slider(
    self,
    cid: str,
    *,
    label: str = "",
    min: float = 0.0,
    max: float = 1.0,
    step: float = 0.01,
    default: float | None = None,
    on_change: Handler | None = None,
    parent_id: str | None = None,
) -> str:
    """Add a slider control. Returns the control ID."""
    ctrl = Slider(
        id=cid,
        label=label,
        min=min,
        max=max,
        step=step,
        default=default if default is not None else min,
        on_change=on_change,
        parent_id=parent_id,
    )
    self._scene.add_control(ctrl)
    if on_change is not None:
        self._handler_registry.register(cid, on_change)
    self._push_controls()
    return cid
```

### 4.1.2 `add_dropdown(id, *, label, options, default, on_change=None, parent_id=None)`

```python
def add_dropdown(
    self,
    cid: str,
    *,
    label: str = "",
    options: list[str] | None = None,
    default: str = "",
    on_change: Handler | None = None,
    parent_id: str | None = None,
) -> str:
    ctrl = Dropdown(
        id=cid,
        label=label,
        options=options or [],
        default=default,
        on_change=on_change,
        parent_id=parent_id,
    )
    self._scene.add_control(ctrl)
    if on_change is not None:
        self._handler_registry.register(cid, on_change)
    self._push_controls()
    return cid
```

### 4.1.3 `add_button(id, *, label, on_click=None, parent_id=None)`

```python
def add_button(
    self,
    cid: str,
    *,
    label: str = "",
    on_click: Handler | None = None,
    parent_id: str | None = None,
) -> str:
    ctrl = Button(id=cid, label=label, on_click=on_click, parent_id=parent_id)
    self._scene.add_control(ctrl)
    if on_click is not None:
        self._handler_registry.register(cid, on_click)
    self._push_controls()
    return cid
```

### 4.1.4 `add_group(id, *, title, controls=None, position="bottom-right", collapsed=False, parent_id=None, on_toggle=None)`

```python
def add_group(
    self,
    gid: str,
    *,
    title: str = "",
    controls: list[str] | None = None,
    position: str = "bottom-right",
    collapsed: bool = False,
    parent_id: str | None = None,
    on_toggle: Handler | None = None,
) -> str:
    """Create a control group. Controls are referenced by their IDs."""
    group = ControlGroup(
        id=gid,
        title=title,
        controls=controls or [],
        position=position,
        collapsed=collapsed,
        parent_id=parent_id,
        on_toggle=on_toggle,
    )
    self._scene.add_group(group)
    if on_toggle is not None:
        self._handler_registry.register(f"__group__{gid}", on_toggle)
    self._push_controls()
    return gid
```

### 4.1.5 `remove_control(control_id)` / `remove_group(group_id)` / `clear_controls()`

Clean up the Python-side registry and push a `controls_clear` if all controls
are gone, or a `controls_define` with the remaining controls.

```python
def remove_control(self, cid: str) -> None:
    self._handler_registry.unregister(cid)
    self._scene.remove_control(cid)
    self._push_controls()

def remove_group(self, gid: str) -> None:
    self._handler_registry.unregister(f"__group__{gid}")
    self._scene.remove_group(gid)
    self._push_controls()

def clear_controls(self) -> None:
    self._handler_registry.clear()
    self._scene.clear_controls()
    self._push_controls_clear()
```

## 4.2 Control Storage in `Scene`

Extend `py/pytanga/viz/scene.py` (or add to `_controls.py`) to store controls
and groups:

```python
class Scene:
    # ... existing fields ...
    _controls: dict[str, Control]
    _groups: dict[str, ControlGroup]

    def add_control(self, ctrl: Control) -> None:
        self._controls[ctrl.id] = ctrl

    def add_group(self, group: ControlGroup) -> None:
        self._groups[group.id] = group

    def remove_control(self, cid: str) -> None:
        self._controls.pop(cid, None)

    def remove_group(self, gid: str) -> None:
        self._groups.pop(gid, None)

    def clear_controls(self) -> None:
        self._controls.clear()
        self._groups.clear()
```

## 4.3 Push Controls to Frontend

### `_push_controls()`

Serializes all current controls and groups and sends via `push_raw`:

```python
def _push_controls(self) -> None:
    if self._server is None or self._loop is None:
        return
    from ._controls import serialize_controls
    groups = list(self._scene._groups.values())
    # Wire up control references from IDs
    # (groups store control IDs; resolve to Control objects)
    message = serialize_controls(groups, self._scene._controls)
    asyncio.run_coroutine_threadsafe(
        self._server.push_raw(json.dumps(message)), self._loop
    )
```

### `_push_controls_clear()`

```python
def _push_controls_clear(self) -> None:
    if self._server is None or self._loop is None:
        return
    asyncio.run_coroutine_threadsafe(
        self._server.push_raw(json.dumps({"type": "controls_clear"})),
        self._loop,
    )
```

## 4.4 Server Message Dispatch

Extend `VizServer._ws_handler` to dispatch `control:change`, `control:click`,
and `control:group_toggle` messages to registered handlers.

### Option A: Callback on `VizServer`

`VizServer` receives a new callback for control events:

```python
# In VizServer.__init__:
self._control_callback: Callable[[str, Any], Awaitable[None]] | None = None

# In VizServer.start():
async def start(self, flush_callback, config_callback, control_callback=None):
    self._control_callback = control_callback

# In _ws_handler:
elif msg_type == "control:change":
    if self._control_callback:
        await self._control_callback(msg_type, {
            "control_id": data.get("control_id"),
            "value": data.get("value"),
        })
elif msg_type == "control:click":
    if self._control_callback:
        await self._control_callback(msg_type, {
            "control_id": data.get("control_id"),
        })
```

Then `Visualizer.start()` passes a dispatch method:

```python
async def _dispatch_control_event(self, msg_type: str, payload: dict) -> None:
    cid = payload.get("control_id")
    if cid and (handler := self._handler_registry.get(cid)):
        if msg_type == "control:change":
            await handler(payload.get("value"))
        elif msg_type == "control:click":
            await handler(None)
```

### Option B: Visualizer Polls from Event Loop (simpler)

Instead of modifying `VizServer`, the `Visualizer` installs an async task
that listens for control events on an `asyncio.Queue` filled by the server.

**Recommendation: Option A** — it's cleaner and follows the existing pattern
(`flush_callback`, `config_callback`). Only one new parameter on `VizServer`.

## 4.5 Push Controls on Browser Connect

When a new WebSocket client connects, the server sends the full state via
`_push_full_state`. Extend this to also send controls:

```python
async def _push_full_state(self, ws):
    # ... existing clear_all, scene_config, flush ...
    
    # Push controls
    if self._control_callback:
        # The callback can return the serialized controls message
        # Or we add a dedicated "flush controls" callback
        pass
```

More directly: After `_push_full_state`, `Visualizer._push_controls()` is
called. Since `_push_full_state` already sends `clear_all`, the controls will
be re-sent in the next `flush` cycle. But for responsiveness, explicitly push
controls after the scene update:

In `_ws_handler`, after `await self._push_full_state(ws)`, add control push.
This requires a callback on `VizServer` that returns the serialized controls
JSON. Or simpler: Visualizer calls `_push_controls()` in a `on_client_connect`
hook.

**Recommendation:** Add an optional `on_connect: Callable[[], Awaitable[None]]`
callback to `VizServer.start()`. `Visualizer` provides:

```python
async def _on_client_connect(self) -> None:
    self._push_controls()
```

## 4.6 Skip Controls in Exports

The `export/_bootstrap/` modules generate JavaScript for standalone HTML
exports. Controls must NOT be included because they require a WebSocket server.

### Approach

The export code in `_figure.py`, `_html.py`, and `_animated_figure.py` builds
a list of scene objects for the bootstrap. Controls and groups are separate
from entities and labels. The export serialization should explicitly exclude
the `controls` layer.

In `Scene.flush()` or `Scene.full_state()`, the returned lists only include
`layer == "scene"` and `layer == "overlay"` objects (entities, labels,
annotations). Controls are stored in `Scene._controls` and `Scene._groups`,
not in the `_objects` dict, so they are naturally excluded from `flush()`.

The `serialize_controls()` function is only called by
`Visualizer._push_controls()`, which is only invoked when the server is
running. Exports bypass this path entirely.

**No code changes needed** in the export modules, as long as controls are
stored separately from scene objects.

## 4.7 `__init__.py` Exports

Add new public symbols to `py/pytanga/viz/__init__.py`:

```python
from ._controls import Slider, Dropdown, Button, ControlGroup
```

These are the user-facing dataclasses that users import when constructing
controls manually (though the convenience methods on `Visualizer` are the
primary API).

## 4.8 Handler Lifecycle

- **Registration**: `add_slider`, `add_dropdown`, `add_button`, `add_group`
  automatically register the handler if `on_change`/`on_click`/`on_toggle` is
  provided.
- **Update**: Calling `add_slider` with the same `cid` replaces the handler
  (the old control is removed from `Scene._controls` and re-added).
- **Deregistration**: `remove_control` and `remove_group` unregister the
  handler.
- **Clear**: `clear_controls` unregisters all handlers.
- **Error handling**: Handler exceptions are caught and logged; they do NOT
  crash the server.

---

## 4.9 Implementation Checklist

- [ ] 4.1 Add `_controls` and `_groups` dicts and accessors to `Scene` in `scene.py`
- [ ] 4.2 Add `ControlHandlerRegistry` instantiation to `Visualizer.__init__`
- [ ] 4.3 Implement `add_slider()` method on `Visualizer`
- [ ] 4.4 Implement `add_dropdown()` method on `Visualizer`
- [ ] 4.5 Implement `add_button()` method on `Visualizer`
- [ ] 4.6 Implement `add_group()` method on `Visualizer`
- [ ] 4.7 Implement `remove_control()`, `remove_group()`, `clear_controls()` on `Visualizer`
- [ ] 4.8 Implement `_push_controls()` and `_push_controls_clear()` on `Visualizer`
- [ ] 4.9 Add `control_callback` parameter to `VizServer.start()` and dispatch logic in `_ws_handler`
- [ ] 4.10 Implement `_dispatch_control_event()` on `Visualizer` (or inline in the lambda)
- [ ] 4.11 Push controls on browser connect (after `_push_full_state`)
- [ ] 4.12 Resolve group control IDs to `Control` objects in `serialize_controls()`
- [ ] 4.13 Wire `sendControlEvent` and group IDs for `control:group_toggle` dispatching
- [ ] 4.14 Add handler error handling (try/except around handler calls, log exceptions)
- [ ] 4.15 Verify export code naturally excludes controls (no changes needed)
- [ ] 4.16 Export `Slider`, `Dropdown`, `Button`, `ControlGroup` from `__init__.py`
- [ ] 4.17 Unit test: `add_slider` → `_push_controls` sends correct JSON
- [ ] 4.18 Unit test: handler dispatch on `control:change` message
- [ ] 4.19 Unit test: `clear_controls` unregisters all handlers
- [ ] 4.20 Integration test: start server, add slider via Python, verify it appears in browser
- [ ] 4.21 Integration test: move slider in browser, verify Python handler fires and can modify scene