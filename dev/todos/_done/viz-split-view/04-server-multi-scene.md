# Phase 4 — Server multi-scene subscription

## Goal

One `BrowserSession` can subscribe to many scenes; on `ready {layout}` the
server sends `view_layout` then full state for every referenced scene. The
single-scene path stays byte-for-byte compatible.

## Steps

- [x] **4.1 — `BrowserSession` gains `scenes: list[str]`**
  - Keep `scene: str` (first scene, for `get_browser_sessions`/logs) and add
    `scenes: list[str]` defaulting to `[]`.

- [x] **4.2 — Handle `ready {layout}`**
  - In `_ws_handler`: if `data.get("layout")` is present, look it up via the
    layout callback; subscribe to the layout's `scenes` list; set
    `session.scenes = [...]`, `session.scene = scenes[0]`.
  - Missing/invalid layout → `navigate` to main (mirror the existing
    invalid-scene branch).  `view_layout` now carries `"scenes"` (from
    `iter_scene_names`) so the server reads it directly.

- [x] **4.3 — `_push_full_state` loops scenes**
  - Send `clear_all` once, then `view_layout` (if any), then per scene
    `scene_config` + full `scene_update` (each tagged `scene`), then
    `scene_list`; controls/animation-stop are pushed per scene by the caller.

- [x] **4.4 — Unit tests `py/tests/viz/test_server_layout.py` (+ `test_scene_session.py`)**
  - `_push_full_state` layout ordering (view_layout before per-scene data);
    single-scene push; layout payload omitted when absent.
  - Single-scene `ready` regression covered by `test_scene_session.py`.

- [x] **4.5 — Validate**
  - `uv run pytest py/tests/viz/test_server_layout.py py/tests/viz/test_scene_session.py -q`

## Validation

`uv run pytest py/tests/viz/test_scene_session.py -q`

## Notes

- Broadcast `push` already tags `message["scene"]`; no change there. The
  frontend (Phase 9) switches from dropping non-matching scenes to routing them.
