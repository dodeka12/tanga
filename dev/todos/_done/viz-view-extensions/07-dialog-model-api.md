# Phase 7 — Dialog model + API (sibling of `Banner`)

## Goal

Add a `Dialog` data model and wire serialization, plus `show_dialog` /
`remove_dialog` / `clear_dialogs` (with `_async` variants) and an `on_close`
callback that rides the existing `close` dispatch path.

## Files

- New: `py/pytanga/viz/_dialog.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_scene_handle.py`
- Edit: `py/pytanga/viz/__init__.py`
- New: `py/tests/viz/test_dialog.py`

## Steps

- [x] **7.1 — `Dialog` dataclass + serializers (`_dialog.py`)**
  - `Dialog(id, title="", content: View, align_x=0.5, align_y=0.5,
    dismissable=True, on_close=None)`; validate `align_x/align_y ∈ [0,1]`.
  - `serialize_dialog(dialog, scene=None) -> dict` producing `dialog_define`
    with `content = dialog.content._serialize(_make_id_gen())` (import the id
    generator from `views.py` or duplicate the counter).
  - `serialize_dialog_remove(id, scene=None)` and `serialize_dialog_clear(scene=None)`.

- [x] **7.2 — `Visualizer` dialog API (`visualizer.py`)**
  - `show_dialog(content, *, id=None, title="", align_x=0.5, align_y=0.5,
    dismissable=True, on_close=None, scene_name=None) -> str`; store under
    `self._dialogs` (mirror `self._banners`), register `on_close` under
    `(id, "close")` and any control-view handlers in `content` (reuse
    `iter_control_views`), then push `dialog_define`.
  - `remove_dialog(id)` / `clear_dialogs(scene_name=None)` and `_async` variants
    that push `dialog_remove` / `dialog_clear`.

- [x] **7.3 — `VizSceneHandle` dialog API (`_scene_handle.py`)**
  - `show_dialog` / `remove_dialog` / `clear_dialogs` forwarding to
    `self._viz` scoped by `self._name`.

- [x] **7.4 — Export (`__init__.py`)**
  - Export `Dialog` (+ `__all__`).

- [x] **7.5 — Tests (`test_dialog.py`)**
  - `serialize_dialog` shape (global `scene=None` → `null`; scoped scene name);
    `content` is a serialized view node; `align` out-of-range raises.
  - `_dispatch_control_event("close", {"id": dlg_id})` invokes and unregisters
    `on_close` (mirror `test_banner.py` close tests).

## Validation

`uv run pytest py/tests/viz/test_dialog.py -q`
