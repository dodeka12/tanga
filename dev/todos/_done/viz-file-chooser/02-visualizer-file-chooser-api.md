# Phase 2 — `Visualizer` file-chooser API + dispatch

## Goal

Expose the control and the browser on `Visualizer` (and `VizSceneHandle`), wire
the client→server messages, and fire `on_change`.

## Steps

- [x] **2.1 — State**
  - No new state needed server-side (controls live in `scene._controls`); the
    browser itself is stateless.

- [x] **2.2 — `add_file_chooser(...) -> str`**
  - `add_file_chooser(cid, *, label="", value="", placeholder="", root=None,
    accept="", on_change=None, parent_id=None)` + `_add_scene_file_chooser(...)`
    mirroring `_add_scene_button`; register `on_change` under `cid`.

- [x] **2.3 — `open_file_chooser` / `close_file_chooser`**
  - `open_file_chooser(cid, *, scene_name="", path=None)` → push
    `file_browser_show` (path = `path` or the control's `value` or `root`).
  - `close_file_chooser(cid, *, scene_name="")` → push `file_browser_close`.

- [x] **2.4 — Dispatch (`server.py` + `visualizer.py`)**
  - `server.py`: route `file_browser_navigate` / `file_browser_select` to the
    control callback (like `control:*` / `banner_closed`).
  - `visualizer.py`: handle them in `_dispatch_control_event` (or a sibling):
    - `file_browser_navigate` → `list_directory(path, root=<control root>)` →
      push `file_browser_listing`.
    - `file_browser_select` → set the control `value`, and
      `await on_change(path, event)`.

- [x] **2.5 — `VizSceneHandle` scoped API**
  - `add_file_chooser(...)` (uses `self._name`), `open_file_chooser(cid)`,
    `close_file_chooser(cid)`.

- [x] **2.6 — Tests (`test_file_chooser.py`)**
  - `add_file_chooser` registers handler + pushes the control.
  - `open_file_chooser` pushes `file_browser_show`.
  - `_dispatch("file_browser_select", …)` updates value + calls `on_change`.
  - `_dispatch("file_browser_navigate", …)` pushes a listing.

## Validation

`uv run pytest py/tests/viz/test_file_chooser.py py/tests/viz/test_controls.py -q`
