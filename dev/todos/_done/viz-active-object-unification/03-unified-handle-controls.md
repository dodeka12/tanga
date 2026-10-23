# Phase 3 — Unified handle-control methods + style swap

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`).
> Refines the existing "Composite handle controls" contract; no new seam.

## Goal

Give every active object a single, uniform `set_handles_enabled` /
`set_handles_visible` / `set_drag_modifiers`, and make `ActPoint` swap its
rendering style between the active `handle_style` and the content `style`.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/tests/viz/test_active.py`, `py/tests/viz/test_act_rectangle2d.py` (as needed)

## Steps

- [x] **3.1 — Simplify `ActiveObject.set_handles_enabled`.**
  - Change signature to `set_handles_enabled(self, enabled: bool = True) -> None`
    (drop `*modifiers`); iterate `self._all_handles()` calling
    `handle.set_handles_enabled(enabled)`.
- [x] **3.2 — `ActiveObject.set_handles_visible`.**
  - Keep as-is (iterate `_all_handles()`, `set_visible` + `set_enabled`, flush).
    It now also works for a bare `ActPoint` via `_all_handles() == [self]`.
- [x] **3.3 — `ActiveObject.set_drag_modifiers` (bulk).**
  - Add `def set_drag_modifiers(self, *modifiers: ModifierKey) -> None:` that
    iterates `self._all_handles()` calling `handle.set_drag_modifiers(*modifiers)`.
- [x] **3.4 — `ActPoint` leaf methods.**
  - `set_drag_modifiers(self, *modifiers)` — set `_required_drag_modifiers =
    frozenset(modifiers)` + `refresh_interaction()` (overrides the bulk).
  - `set_handles_enabled(self, enabled=True)` — `self.set_enabled(enabled)`, then if
    `self._handle_style is not None`, swap the point's rendering style to
    `_handle_style` when enabled else `_body_style` (via `viz_handle.update_style`).
- [x] **3.5 — Tests.**
  - Assert `set_handles_enabled(False)` / `set_handles_visible(False)` /
    `set_drag_modifiers(SHIFT)` behave the same on a bare `ActPoint` and on a
    composite; assert the `handle_style`/`style` swap on a bare point.

## Validation

`uv run pytest py/tests/viz/test_active.py py/tests/viz/test_act_rectangle2d.py -q && uv run ruff check py/pytanga/viz/_active.py && uv run ty check py/pytanga/viz/_active.py`

## Notes

- The bulk methods call the leaf on each child `ActPoint`; for a composite child
  handle `_handle_style` is `None`, so its style swap is a no-op.
