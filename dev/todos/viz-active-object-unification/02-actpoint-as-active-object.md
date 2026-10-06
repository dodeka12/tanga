# Phase 2 — `ActPoint` becomes an `ActiveObject`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`).
> This stays inside the existing `ActSceneObject`/composite recipe; no new seam.

## Goal

Make `ActPoint` a subclass of `ActiveObject`, give it a `handle_style`
constructor arg, and make it report itself as its own control point
(`_reshape_handles() -> [self]`).  `ActiveObject.__init__` gains the
point-side kwargs (`handler`, `on_drag_start`, `on_drag_end`, `drag_bindings`,
`click_bindings`, `cursor`) so `ActPoint` can pass them through.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/tests/viz/test_active.py` (as needed)

## Steps

- [x] **2.1 — Widen `ActiveObject.__init__`.**
  - Add keyword params `handler=None, on_drag_start=None, on_drag_end=None,
    drag_bindings=None, click_bindings=None, cursor=None` and pass them to
    `super().__init__(...)` alongside the existing `on_click`/`style`.
  - Keep `handle_style`, `translate_handle_style=None`, `rotate_handle_style=None`,
    `act_style=None` as-is (all default `None`).
- [x] **2.2 — Make `ActPoint` inherit `ActiveObject`.**
  - `class ActPoint(ActiveObject):`.
  - Add `handle_style: PointStyle | None = None` to `ActPoint.__init__` (do **not**
    add `translate_handle_style`/`rotate_handle_style`).
  - Call `super().__init__(handler=..., on_drag_start=..., on_drag_end=...,
    on_click=..., drag_bindings=..., click_bindings=..., cursor=..., style=style,
    handle_style=handle_style, act_style=act_style)`.
  - Keep the point-specific state (`_point`, `_drag_mode`, `_resolved_style`,
    `_required_drag_modifiers`) after `super().__init__`.
- [x] **2.3 — `ActPoint._reshape_handles()` returns `[self]`.**
  - Override `_reshape_handles` on `ActPoint` to `return [self]` so
    `_all_handles()` yields the point itself.
- [x] **2.4 — Tests.**
  - Add/adjust a `test_active.py` case asserting `isinstance(ActPoint(...), ActiveObject)`
    and `ActPoint(...)._all_handles() == [point]`.

## Validation

`uv run pytest py/tests/viz/test_active.py -q && uv run ruff check py/pytanga/viz/_active.py && uv run ty check py/pytanga/viz/_active.py`

## Notes

- Composite child handles are also `ActPoint`s; their `handle_style` stays `None`
  (the style is still applied at `_spawn_handle` time), so this change does not
  affect composite handle rendering.
