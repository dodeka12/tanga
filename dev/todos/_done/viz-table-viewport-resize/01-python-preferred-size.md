# Phase 1 — Backend default size

## Goal

Give `TableView` a natural default size so flow containers bound it (and the
grid scrolls internally) instead of growing with content.

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/tests/viz/test_control_value_api.py`

## Steps

- [x] **1.1 — Default preferred size**
  - In `TableView.__init__`, before `super().__init__`, add
    `kwargs.setdefault("preferred_width", Size.px(480))` and
    `kwargs.setdefault("preferred_height", Size.px(320))`.
- [x] **1.2 — Tests**
  - Assert `TableView(...)` serializes `preferred_width = {480, px}` and
    `preferred_height = {320, px}`; an explicit `preferred_height=` still wins.

## Validation

`uv run pytest py/tests/viz/test_views.py py/tests/viz/test_control_value_api.py -q`

## Notes

- Matches the JS `TableView` defaults (currently dead because Python serializes
  `null` and `build.js` nulls them out).
