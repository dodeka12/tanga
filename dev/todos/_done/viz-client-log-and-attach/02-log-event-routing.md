# Phase 2 — Wire `ClientLog` into the event protocol

## Goal

Route `event:"log"` through the unified envelope to the `ClientLog` control and
expose `viz.on_client_log(handler)`.

## Files

- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_client_log.py`

## Steps

- [x] **2.1 — `_EVENT_MSG_MAP` entry (`server.py`)**
  - Add `"log": "control:log"` to `_EVENT_MSG_MAP` so the `event` branch in
    `_ws_handler` maps the short event name to the `control:*` route.

- [x] **2.2 — `LayoutHostImpl` holds a `client_log` control (`_layout.py`)**
  - Add `client_log: Any = None` to `LayoutHostImpl.__init__`; store
    `self._client_log = client_log`.
  - In `dispatch_control_event`, immediately after
    `ctrl = self.resolve_control(cid) if cid else None`, add:
    `if ctrl is None and self._client_log is not None and cid == self._client_log.id: ctrl = self._client_log`.
  - This runs `ClientLog.handle_event` with the full payload (not the lossy
    `value`-only fallback).

- [x] **2.3 — `Visualizer` construction + API (`visualizer.py`)**
  - In `__init__`, import `CLIENT_LOG_ID`/`ClientLog`, construct
    `self._client_log = ClientLog(CLIENT_LOG_ID)`, call
    `self._client_log.register_handlers(self._transport)`, and pass
    `client_log=self._client_log` to `LayoutHostImpl(...)`.
  - Add `def on_client_log(self, handler)`: replace `self._client_log.on_log`
    and re-register it under `(CLIENT_LOG_ID, "log")` via the transport (so the
    swap takes effect at runtime).

- [x] **2.4 — Dispatch test**
  - Add a `test_client_log.py` case that drives
    `LayoutHostImpl.dispatch_control_event("control:log",
    {"control_id": CLIENT_LOG_ID, "level": "error", "message": "boom"})` with a
    fake transport and asserts the registered sink received a `ClientLogRecord`
    with `level == "error"` (proving the `_client_log` resolution path, not just
    the unit `handle_event`).

## Validation

`uv run pytest py/tests/viz/test_client_log.py py/tests/viz/test_layout_api.py -q`

## Notes

- The `_client_log` hook is a single attribute now; if other backend-only sinks
  appear later, generalize to a `_system_controls` mapping in a follow-up.
- `ControlEvent` already carries `browser_id`; `ClientLogRecord` reuses that
  field (no `scene` for now — matching `ControlEvent`).
