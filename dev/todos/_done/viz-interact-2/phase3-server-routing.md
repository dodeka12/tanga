# Phase 3 — Server WebSocket Routing

**Prerequisites:** Phase 1 (interaction dataclasses + `_parse_event()` exist)

**Goal:** Route 6 new `interaction:*` WebSocket message types in `VizServer`,
parse incoming JSON into event dataclasses, and dispatch via a new callback.

---

## 1. Motivation

The `VizServer._ws_handler()` currently routes three message types:
`ready`, `screenshot:data`, and `control:change` / `control:click` /
`control:group_toggle`. It needs 6 new routes for object interaction events
coming from the frontend. Each message must be parsed into the corresponding
`ClickEvent`, `DragEvent`, or `ScrollEvent` dataclass and dispatched.

---

## 2. Modified File: `py/pytanga/viz/server.py`

### 2.1 New Callback Type

Add a new callback type alias alongside the existing ones:

```python
InteractionCallback = Callable[[str, ControlEvent], Awaitable[None]]
"""Callback receiving the raw message type string and parsed event dataclass."""
```

### 2.2 New Callback Parameter in `start()`

Add `interaction_callback: InteractionCallback | None = None` to
`VizServer.start()`. Store as `self._interaction_callback`.

### 2.3 New Message Routing in `_ws_handler()`

In the `async for msg in ws:` loop, after the existing `control:*` routing,
add:

```python
elif msg_type.startswith("interaction:"):
    if self._interaction_callback is not None:
        try:
            event = _parse_event(data)
            asyncio.create_task(
                self._interaction_callback(msg_type, event)
            )
        except (ValueError, KeyError) as e:
            # Malformed event — log and ignore
            pass
```

The 6 message types are:
- `interaction:click`
- `interaction:dblclick`
- `interaction:drag_start`
- `interaction:drag_move`
- `interaction:drag_end`
- `interaction:scroll`

### 2.4 Import

```python
from ._interaction import _parse_event, ControlEvent
```

### 2.5 Thread Safety

The `dispatch()` call on `InteractionHandlerRegistry` internally uses
`asyncio.create_task()`, which is safe because we're already inside the
server's event loop (the `_ws_handler` is an async generator).

---

## 3. Implementation Checklist

- [x] Add `InteractionCallback` type alias to `server.py`
- [x] Add `interaction_callback` parameter to `VizServer.start()`
- [x] Store as `self._interaction_callback`
- [x] Add 6 `interaction:*` routing branches in `_ws_handler()`
- [x] Import `_parse_event` from `._interaction`
- [x] Wrap parsing in try/except to handle malformed events gracefully

---

## 4. Verification

- [x] Sending `{"type": "interaction:click", "event_type": "click", "object_id": "x", ...}` triggers callback
- [x] Sending `{"type": "interaction:drag_move", ...}` triggers callback with `DragEvent`
- [x] Sending malformed JSON → no crash, event silently dropped
- [x] Unknown `event_type` → no crash
- [x] Missing `interaction_callback` → events silently ignored (no crash)
