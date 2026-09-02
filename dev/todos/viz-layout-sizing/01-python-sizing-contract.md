# Phase 1 — Python sizing contract

## Goal

Add the container-level sizing knobs (`gap` / `align` / `justify`) and the
control-size floors to the Python view model, and serialize them. No frontend
change yet: `build.js` ignores the new fields, so this phase is inert on the
wire.

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/tests/viz/test_views.py`

## Steps

- [ ] **1.1 — Add `gap`/`align`/`justify` to `StackView`.**
  - Add `gap: int | None = None`, `align: Literal[...] = "stretch"`,
    `justify: Literal[...] = "start"` keyword-only params to
    `StackView.__init__` after `scrollable`.
  - Validate `align`/`justify` against their allowed literals (raise
    `ValueError` on anything else, mirroring the existing `direction` check).
  - Store `self.gap`, `self.align`, `self.justify`.
  - `gap` accepts `None` (default) or a non-negative `int`; `0` means "no gap".

- [ ] **1.2 — Forward the new knobs through `GroupView`.**
  - Add the same three keyword-only params to `GroupView.__init__` and pass
    them explicitly to `super().__init__(direction, children, scrollable=..., gap=..., align=..., justify=..., **kwargs)`.

- [ ] **1.3 — Move control floors into `ControlView`.**
  - In `ControlView.__init__`, before `super().__init__(**kwargs)`, do
    `kwargs.setdefault("min_width", Size.px(120))` and
    `kwargs.setdefault("min_height", Size.px(32))`.
  - This makes the floors Python-authoritative and overridable; `min_width=None`
    / `min_height=None` still disable them (setdefault won't apply).

- [ ] **1.4 — Serialize the new fields.**
  - In `StackView._serialize`, add `result["gap"] = self.gap`,
    `result["align"] = self.align`, `result["justify"] = self.justify`.
  - `GroupView` inherits this; confirm `GroupView._serialize` calls
    `super()._serialize` (it does) so `group` nodes carry the fields too.

- [ ] **1.5 — Tests.**
  - `StackView("vertical", [], gap=8, align="center", justify="end")` serializes
    to a `stack` node with `gap == 8`, `align == "center"`, `justify == "end"`.
  - Defaults serialize as `gap is None`, `align == "stretch"`,
    `justify == "start"`.
  - `GroupView("t", [], gap=0)` serializes a `group` node with `gap == 0`.
  - Invalid `align`/`justify` raise `ValueError`.
  - `ButtonView("b1")` defaults to `min_width == Size.px(120)` and
    `min_height == Size.px(32)`; `ButtonView("b1", min_width=None)` has
    `min_width is None`.

## Validation

```powershell
uv run pytest py/tests/viz/test_views.py -q
```

## Notes

- Do **not** touch `_size.py`: `Size.fr` already exists and needs no change.
- `MenuView` is intentionally left out of this phase (see README non-goals).
