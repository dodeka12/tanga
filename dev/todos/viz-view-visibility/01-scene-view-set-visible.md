# Phase 1 — `SceneView.set_visible` model + remove static filter

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Replace `SceneView(hide=…, show=…)` with runtime `SceneView.set_visible(...)`, and
migrate every caller so the repo stays importable after this phase.

## Files

- Edit: `py/pytanga/viz/views/scene_view.py`
- Edit: `py/tests/viz/test_views.py`
- Edit: `py/examples/viz/camera/pinhole_calibrated.py`
- Edit: `py/examples/viz/camera/calibrated_orbit_fallback_repro.py`
- Edit: `py/examples/viz/camera/pinhole_calibrated_streaming.py`
- Edit: `py/examples/viz/camera/pinhole_overlay.py`
- Edit: `py/examples/viz/image/pinhole_depth.py`
- Edit: `py/examples/apps/calibrated_labeling_app.py`

## Steps

- [x] **1.1 — Remove the static constructor filter**
  - Drop `hide`/`show` from `SceneView.__init__` and remove the `_normalize_id_set` import.
  - Add `self._hide: set[str] = set()` and `self._push_visibility = None`.
  - `_serialize()` emits `result["hide"] = sorted(self._hide)` when non-empty; drop the `show` field.
- [x] **1.2 — Add `set_visible`**
  - `set_visible(entity_id: str, visible: bool)` validates a non-empty str, then
    `self._hide.add(entity_id)` when `visible` is `False` / `discard` when `True`,
    and calls `self._push_visibility(self)` when the callback is set.
- [x] **1.3 — Migrate callers**
  - Replace each `SceneView(..., hide={id})` with `view = SceneView(...)` followed
    by `view.set_visible(id, False)`. In `pinhole_depth.py`, call it for both the
    depth surface and the frustum; update its docstring to not mention
    `SceneView(hide=…)`.
- [x] **1.4 — Update tests**
  - Replace `test_hide_show_serialize`, `test_hide_show_omitted_when_empty`, and
    `test_hide_rejects_non_string` with: `set_visible(False)` populates `_hide`
    and serializes `hide`; `set_visible(True)` empties it; an invalid id raises
    `ValueError`; a stubbed `_push_visibility` fires once per toggle.

## Validation

`uv run pytest py/tests/viz/test_views.py py/tests/viz/test_calibrated_labeling_example.py -q && uv run ruff check py/examples/viz/camera/pinhole_calibrated.py py/examples/viz/camera/calibrated_orbit_fallback_repro.py py/examples/viz/camera/pinhole_calibrated_streaming.py py/examples/viz/camera/pinhole_overlay.py py/examples/viz/image/pinhole_depth.py py/examples/apps/calibrated_labeling_app.py`
