# Phase 2 — Composite bulk handle enable/visible

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  This stays inside the existing `_ActWithHandles`
> composite recipe; no architecture change.

## Goal

Add bulk, public `set_handles_enabled` / `set_handles_visible` on every `Act*`
composite, covering **all** handles (reshape + translate + rotate).

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/tests/viz/test_act_rectangle2d.py`
- Edit: `py/tests/viz/test_act_ellipse.py`
- Edit: `py/tests/viz/test_act_circle.py`
- Edit: `py/tests/viz/test_act_line.py`
- Edit: `py/tests/viz/test_act_polygon.py`

## Steps

- [x] **2.1 — Add the handle-enumeration hook.**
  - In `_ActWithHandles`, add `def _reshape_handles(self) -> list[ActPoint]: return []`
    and `def _all_handles(self) -> list[ActPoint]:` returning
    `[*self._reshape_handles(), *filter(None, (getattr(self, "_translate_handle", None), getattr(self, "_rotate_handle", None)))]`.
- [x] **2.2 — Override `_reshape_handles()` in each composite.**
  - `ActRectangle2D` → `self._corner_handles`; `ActEllipse` → `self._radius_handles`;
    `ActCircle` → `[] if self._radius_handle is None else [self._radius_handle]`;
    `ActPolygon` → `self._vertex_handles`; `ActLine` → `self._endpoint_handles`.
- [x] **2.3 — Add `set_handles_enabled`.**
  - `def set_handles_enabled(self, enabled: bool = True, *modifiers: ModifierKey) -> None:`
    iterate `self._all_handles()` calling `handle.set_enabled(enabled)` and
    `handle.set_drag_modifiers(*modifiers)`.
- [x] **2.4 — Add `set_handles_visible`.**
  - `def set_handles_visible(self, visible: bool) -> None:` iterate
    `self._all_handles()`, call `self._viz_handle.set_visible(handle.entity_id, visible)`
    and `handle.set_enabled(visible)`; then a single `self.flush()`.
- [x] **2.5 — Tests.**
  - Extend each composite test (using the existing `_FakeHandle` pattern) to assert
    `set_handles_enabled(False)` disables every handle, `set_handles_visible(False)`
    hides + disables every handle, and `set_handles_enabled(True, ModifierKey.SHIFT)`
    sets the Shift gate on each reshape handle.

## Validation

`uv run pytest py/tests/viz/test_act_rectangle2d.py py/tests/viz/test_act_ellipse.py py/tests/viz/test_act_circle.py py/tests/viz/test_act_line.py py/tests/viz/test_act_polygon.py -q`

## Notes

- `set_handles_enabled`/`set_handles_visible` are safe to call before `_init`
  (no handles yet → no-op).
- `set_handles_visible(False)` disables handles as well (visibility + enablement
  combined), matching `set_translate_handle_visible`.
