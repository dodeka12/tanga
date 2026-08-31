# Phase 1 — Python: `scrollable` flag on StackView/GroupView

## Goal

Add the `scrollable` keyword to `StackView` and `GroupView`, serialize it on the
`stack`/`group` nodes, and cover the round-trip with unit tests.

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/tests/viz/test_views.py`

## Steps

- [x] **1.1 — `StackView.scrollable`**
  - Add keyword-only `scrollable: bool = False` to `StackView.__init__`; store
    `self.scrollable`.
  - In `StackView._serialize`, add `result["scrollable"] = self.scrollable`
    before the return.

- [x] **1.2 — `GroupView.scrollable` passthrough**
  - Add keyword-only `scrollable: bool = False` to `GroupView.__init__` and
    forward it: `super().__init__(direction, children, scrollable=scrollable,
    **kwargs)`.
  - `GroupView._serialize` inherits the field via `StackView._serialize` (no
    change needed there).

- [x] **1.3 — Tests**
  - `TestStackView`: assert `StackView("vertical")` serializes
    `node["scrollable"] is False`, and `StackView("vertical", scrollable=True)`
    serializes `True`.
  - `TestGroupView`: assert `GroupView("Controls")` serializes
    `node["scrollable"] is False`, and `GroupView("Controls", scrollable=True)`
    serializes `True`.

## Validation

`uv run pytest py/tests/viz/test_views.py -q`

## Notes

- Keep the default `False` so existing serialized layouts are unchanged in
  behaviour (the field is additive).
