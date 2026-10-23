# Phase 2 — Inject `_push_visibility` and send `view_visibility`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Wire `SceneView.set_visible` to the browser via a granular `view_visibility`
message, mirroring the existing `view_camera`/`view_viewport` dispatch pattern.

## Files

- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/tests/viz/test_layout_api.py`

## Steps

- [x] **2.1 — Push helper**
  - Add `_push_view_visibility(scene_view)` sending
    `{"type": "view_visibility", "view_id": scene_view.id, "hide": sorted(scene_view._hide)}`
    via `self._transport.send(...)` (mirror `_push_control_state`).
- [x] **2.2 — Inject on register**
  - In `LayoutHost.register`, import `iter_scene_views` and set
    `view._push_visibility = self._push_view_visibility` for each scene view.
- [x] **2.3 — Test**
  - Add a `test_layout_api.py` case: with a fake transport, `register` injects
    `_push_visibility`, and `scene_view.set_visible("e", False)` records exactly
    one `view_visibility` message with `view_id` and `hide == ["e"]`.

## Validation

`uv run pytest py/tests/viz/test_layout_api.py -q`
