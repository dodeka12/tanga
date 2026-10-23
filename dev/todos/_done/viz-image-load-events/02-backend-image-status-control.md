# Phase 2 — Backend `ImageStatus` control model

## Goal

Add the backend-only reserved control that normalizes incoming image events into
a record and fires the matching `(id, event)` handler.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- New: `py/tests/viz/test_image_status.py`

## Steps

- [x] **2.1 — `IMAGE_STATUS_ID` + `ImageStatusRecord` (`_controls.py`)**
  - Add `IMAGE_STATUS_ID = "image_status"` next to `CLIENT_LOG_ID`.
  - Add `@dataclass ImageStatusRecord` with `image_id: str`, `source: str | None
    = None`, `width: int | None = None`, `height: int | None = None`,
    `level: int | None = None`, `tile_version: int | None = None`,
    `browser_id: str | None = None`.

- [x] **2.2 — `ImageStatus(Control)` (`_controls.py`)**
  - Add a default no-op `async def _default_image_status_sink(record, event)`
    next to `_default_client_log_sink`.
  - Add `@dataclass ImageStatus(Control)` with `kind: str = "image_status"`,
    `on_image_loaded` / `on_image_tile_load` / `on_image_tile_loaded`
    (`ControlHandler`, default `_default_image_status_sink`).
  - Override `handle_event(self, event, payload) -> Dispatch`: parse the
    payload into an `ImageStatusRecord` and `return Dispatch(event, record)`.
  - Do **not** add these to `py/pytanga/viz/__init__.py` (internal, mirroring
    `ClientLog`/`ClientLogRecord`).

- [x] **2.3 — Unit tests (`test_image_status.py`)**
  - `handle_event` parses `image_id`/`source`/`width`/`height`/`level`/
    `tile_version`/`browser_id` and returns `Dispatch(event, record)` for each of
    the three event names.
  - `register_handlers` registers `on_image_loaded`/`on_image_tile_load`/
    `on_image_tile_loaded` under `("image_status", "<event>")` via a minimal fake
    transport (mirror `test_client_log.py`).

## Validation

```
uv run pytest py/tests/viz/test_image_status.py -q
```

## Notes

- Keep the record/control internal; the public surface is `Visualizer.on_image_*`
  (Phase 3).  Type hints may reference `pytanga.viz._controls.ImageStatusRecord`
  in docstrings, as `on_client_log` does for `ClientLogRecord`.
