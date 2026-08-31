# Phase 3 — Visualizer layout API + `?view=` URL

## Goal

Let users pass a layout to the existing entry points and open it under a single
URL, while `viz.show()`/`run()` without a layout keep opening scene URLs.

## Steps

- [x] **3.1 — Layout registry on `Visualizer`**
  - `_layouts: dict[str, View]` + `_layout_serialized: dict[str, dict]`.
  - `set_layout(root, name="")` → validates, serializes, stores.
  - Default layout name `""`.

- [x] **3.2 — `show(layout=...)` / `run(layout=...)`**
  - Accept `layout: View | None` and `layout_name: str | None`.
  - When `layout` is given: register it and open `/?view=<name>` (with the
    existing `token` query param preserved).
  - Without `layout`: current behavior, byte-for-byte (open `/{scene}` or `/`).

- [x] **3.3 — Wire a `LayoutCallback` into `VizServer`**
  - `LayoutCallback = Callable[[str], dict | None]` returning the serialized
    `view_layout` for a name; passed via `VizServer.start()` (matching the other
    callbacks) and stored — no behavior yet (Phase 4 consumes it).

- [x] **3.4 — Unit tests `py/tests/viz/test_layout_api.py` (+ `test_scene_session.py`)**
  - Registry get/set/overwrite; URL building for default + named layouts.
  - `show(layout=...)` registers the layout and opens the `?view=` URL
    (mock `_open_layout_browser`/`_open_browser_url` and inspect the URL/state).

- [x] **3.5 — Validate**
  - `uv run pytest py/tests/viz/test_layout_api.py py/tests/viz/test_scene_session.py -q`

## Validation

`uv run pytest py/tests/viz/test_views.py py/tests/viz/test_scene_session.py -q`

## Notes

- No server routing change: `?view=` reuses the catch-all `viewer.html` route.
  Scenes are never shadowed because `?view` is a query param, not a path.
