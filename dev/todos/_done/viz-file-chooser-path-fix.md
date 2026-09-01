# Viz: `FileChooserView` path fixes — select write-back + `root` clamp

> **Superseded by** [`viz-unified-controls/`](viz-unified-controls/) — this
> tactical fix is now Phase 1 of the unified-controls plan. Keep this file for
> the recorded analysis; implement via the folder plan.


**Date:** 31 August 2026 · **Status:** Planned · **Branch:** `fix/file-chooser-bug`

**Cross-references:** [`viz-file-chooser-select-path.md`](viz-file-chooser-select-path.md) (the read-only
bug report this plan implements); `dev/todos/_done/viz-file-chooser/` (the feature these bugs are in).

## Goal

Two fixes to `Visualizer` file-chooser path handling, both from the same gap:
`_find_control` resolves only **panel** controls (`scene._controls`), never the
layout `ControlView`s registered by `set_layout`.

- **A — selected path never written back / pushed.** `_handle_file_browser_select`
  does `ctrl.value = path` only for panel controls; a layout `FileChooserView`
  resolves to `None`, and even panel controls never push a `control_update`.
- **B — `root` ignored when navigating from a layout view.** `_handle_file_browser_navigate`
  reads `root` only from `_find_control`.

## Design (fixed contract)

In `py/pytanga/viz/visualizer.py`:

1. `_find_control(cid)` → `(scene_name, control) | None` so callers push with the
   right scene (a named-scene panel chooser must not be looked up in `""`).
2. New `_find_control_view(cid) -> ControlView | None` walks `self._layouts` via
   `iter_control_views` (local import, like `_register_control_handlers`).
3. `_handle_file_browser_navigate` resolves `root` from the panel control **or**
   the layout view.
4. `_handle_file_browser_select` updates **and pushes**:
   - panel → `self.set_control_value(cid, path, scene_name=scene_name)`
   - view  → `self.set_control_view_value(view, path)`

Both setters already push `control_update`; the frontend already applies it to
view controls (`viewer.js` → `applyControlValue` → the `createFileChooser`
registry entry). No JS change.

```python
def _find_control(self, cid: str) -> tuple[str, Any] | None:
    """Return ``(scene_name, control)`` for *cid* from any scene, or ``None``."""
    for name, scene in self._scenes.items():
        ctrl = scene._controls.get(cid)
        if ctrl is not None:
            return name, ctrl
    return None

def _find_control_view(self, cid: str) -> ControlView | None:
    """Return the layout control view with id *cid*, or ``None``."""
    from .views import iter_control_views

    for layout in self._layouts.values():
        for view in iter_control_views(layout):
            if view.id == cid:
                return view
    return None
```

```python
async def _handle_file_browser_navigate(self, payload: dict[str, Any]) -> None:
    from ._file_browser import list_directory

    if self._server is None:
        return
    cid = payload.get("control_id")
    path = payload.get("path") or ""
    found = self._find_control(cid) if cid else None
    if found is not None:
        root = getattr(found[1], "root", None)
    else:
        view = self._find_control_view(cid) if cid else None
        root = getattr(view, "root", None) if view is not None else None
    message = list_directory(path, root=root)
    message.update({"type": "file_browser_listing", "control_id": cid})
    await self._server.push_raw(json.dumps(message))
```

```python
async def _handle_file_browser_select(self, payload: dict[str, Any], event: Any) -> None:
    cid = payload.get("control_id")
    path = payload.get("path") or ""
    if cid:
        found = self._find_control(cid)
        if found is not None:
            scene_name, _ctrl = found
            self.set_control_value(cid, path, scene_name=scene_name)
        else:
            view = self._find_control_view(cid)
            if view is not None:
                self.set_control_view_value(view, path)
    handler = self._handler_registry.get(cid) if cid else None
    if handler is not None:
        try:
            await handler(path, event)
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Error in file chooser handler for %r", cid
            )
```

## Files Touched

| File | Change |
|------|--------|
| `py/pytanga/viz/visualizer.py` | `_find_control` tuple return; add `_find_control_view`; fix both file-browser handlers. |
| `py/tests/viz/test_file_chooser.py` | Four new tests (below). |
| `docs/changelog/2026-08-31_fix-file-chooser-bug.md` | New branch changelog. |

## Steps

- [ ] **1 — Backend resolution + handlers** (`py/pytanga/viz/visualizer.py`)
  - `_find_control` returns `(scene_name, control) | None`.
  - Add `_find_control_view(cid)`.
  - `_handle_file_browser_navigate` resolves `root` from panel or view.
  - `_handle_file_browser_select` updates + pushes for panel and view; the
    `on_change` dispatch is unchanged.
  - **Validation:** `uv run pytest py/tests/viz/test_file_chooser.py py/tests/viz/test_layout_api.py -q`

- [ ] **2 — Tests** (`py/tests/viz/test_file_chooser.py`)
  - `test_dispatch_file_browser_select_panel_pushes` — panel select pushes
    `("", "fc", "/data/x.csv")` (monkeypatch `_push_control_update`).
  - `test_dispatch_file_browser_select_view_sets_and_pushes` — layout
    `FileChooserView` select sets `view.value` and pushes `("", "fc", "/data/x.csv")`.
  - `test_dispatch_file_browser_select_named_scene` — `viz.scene("other").add_file_chooser("fc", on_change=…)`
    pushes `("other", "fc", "/x.csv")`.
  - `test_dispatch_file_browser_navigate_view_root` — layout `FileChooserView(root=…)`
    navigate clamps to `root`.
  - **Validation:** `uv run pytest py/tests/viz/test_file_chooser.py -q`

- [ ] **3 — Changelog** (`docs/changelog/2026-08-31_fix-file-chooser-bug.md`)
  - Title `# Changes since version <last-release>` — `uv run python tools/last-release.py`
    currently prints `1.12.0`.
  - Two **Bug Fixes** bullets: (1) `FileChooserView` shows the selected path
    (write-back + push, panel and view); (2) `FileChooserView` Browse honours
    `root=` on navigate.
  - **Validation:** `uv run pytest py/tests/viz/ -q`

## Validation (final)

```
uv run pytest py/tests/viz/test_file_chooser.py py/tests/viz/test_layout_api.py -q
uv run pytest py/tests/viz/ -q
```

## Non-goals

- `open_file_chooser` stays panel-only (layout views open via their own Browse
  button); unchanged.
- No frontend/JS edits — `control_update` already reaches view controls.
- The `seating-plan` app's own `set_control_view_value` workaround is not removed
  here (separate downstream app).

## Notes

- `_find_control` has exactly two callers, both in this file, so the return-type
  change is contained.
- `_push_control_update` no-ops when `_server`/`_loop` is unset, so the new push
  paths are safe under the existing no-server tests.
