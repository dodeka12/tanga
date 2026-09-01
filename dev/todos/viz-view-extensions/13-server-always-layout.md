# Phase 13 — Server always serves a layout (`server.py`)

## Goal

Make the WebSocket handshake always send a `view_layout`: layout tabs keep their
named layout; single-scene tabs get their auto-derived single-scene layout. Also
track the requested layout name on the session for the later re-push (Phase 15).

## Files

- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/visualizer.py` (wire the new callback)
- Edit: `py/tests/viz/test_server_layout.py`

## Steps

- [x] **13.1 — Track `layout` on `BrowserSession`**
  - Add `layout: str | None = None` to `BrowserSession`; set it in the `ready`
    handler from `data.get("layout")`.

- [x] **13.2 — `_scene_layout_callback`**
  - Add a `scene_layout_callback` parameter to `VizServer.__init__` (mirroring
    `layout_callback`); wire it in `Visualizer.start_server` to `_scene_layout_for`.

- [x] **13.3 — Always resolve `layout_payload` in `ready`**
  - In the `ready` handler: when `layout` is present use `_layout_callback`, else use
    `_scene_layout_callback(scene_name)`. `layout_payload` is then always set, so
    `_push_full_state` always sends `view_layout` (before scene data, as today).

- [x] **13.4 — Tests**
  - `test_server_layout.py`: a single-scene `ready {scene}` now yields a `view_layout`
    via `_scene_layout_callback`; the layout `ready {layout}` path is unchanged.

## Validation

`uv run pytest py/tests/viz/test_server_layout.py -q`
