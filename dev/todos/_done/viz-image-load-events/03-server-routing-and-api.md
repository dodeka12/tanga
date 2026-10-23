# Phase 3 — Server routing + `Visualizer.on_image_*` API

## Goal

Route the three `image_*` events through the unified envelope to the reserved
`image_status` control, and expose `viz.on_image_loaded` / `on_image_tile_load` /
`on_image_tile_loaded`.

## Files

- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_image_status.py`

## Steps

- [x] **3.1 — `_EVENT_MSG_MAP` entries (`server.py`)**
  - Add `"image_loaded": "control:image_loaded"`,
    `"image_tile_load": "control:image_tile_load"`,
    `"image_tile_loaded": "control:image_tile_loaded"` next to `"log"`.

- [x] **3.2 — `LayoutHostImpl` resolution (`_layout.py`)**
  - Add `image_status: Any = None` to `__init__`; store `self._image_status`.
  - In `dispatch_control_event`, next to the `client_log` special-case, add:
    `if ctrl is None and self._image_status is not None and cid ==
    self._image_status.id: ctrl = self._image_status`.

- [x] **3.3 — `Visualizer` wiring + API (`visualizer.py`)**
  - In `__init__`, import and construct
    `self._image_status = ImageStatus(IMAGE_STATUS_ID)`, call
    `self._image_status.register_handlers(self._transport)`, and pass
    `image_status=self._image_status` to `LayoutHostImpl(...)`.
  - Add `on_image_loaded`, `on_image_tile_load`, `on_image_tile_loaded` methods
    (each sets the matching `self._image_status.on_*` field and re-registers via
    `self._transport`), mirroring `on_client_log`.

- [x] **3.4 — Routing tests (`test_image_status.py`)**
  - Assert `dispatch_control_event("control:image_loaded", {"control_id":
    IMAGE_STATUS_ID, "image_id": "img1", ...})` resolves the reserved control
    and fires the registered `on_image_loaded` handler with an
    `ImageStatusRecord` (mirror the `client_log` dispatch test).
  - Assert `Visualizer.on_image_loaded(h)` replaces and re-registers the handler.

## Validation

```
uv run pytest py/tests/viz/test_image_status.py py/tests/viz/test_client_log.py -q
```

## Notes

- `server.py` already injects `browser_id` into `event_data` before routing, so
  `ImageStatus.handle_event` receives it via `payload["browser_id"]`.
- Follow the existing single-attribute hook (`self._client_log`); if more
  backend-only sinks appear later, generalize to a `_system_controls` mapping in
  a follow-up (same note as the `client_log` work).
