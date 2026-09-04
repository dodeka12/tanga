# Phase 1 — Shared layout enums (`EStackDirection` / `EStackAlign` / `EStackJustify`)

## Goal

Replace the three `Literal` type aliases for stack layout with `StrEnum`s and
use them in `StackView`, `GroupView`, and `MenuView`.  No behaviour change:
`StrEnum` members are `str`, so plain-string callers and the serialized JSON
remain identical.

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/tests/viz/test_views.py`

## Steps

- [x] **1.1 — Define the three enums (`views.py`)**
  - Replace `StackDirection` / `StackAlign` / `StackJustify` `Literal` aliases
    (top of `views.py`) with `EStackDirection`, `EStackAlign`, `EStackJustify`
    `StrEnum` classes, exactly matching the values in the README contract.
  - Import `StrEnum` from `enum`.

- [x] **1.2 — Update `StackView`**
  - Annotate `direction: EStackDirection`, `align: EStackAlign = EStackAlign.STRETCH`,
    `justify: EStackJustify = EStackJustify.START`.
  - Keep the existing `not in (...)` validation working for both enum members
    and plain strings (verify `"stretch" in EStackAlign` is True); prefer
    validating against the enum class if it reads cleanly.

- [x] **1.3 — Update `GroupView`**
  - Mirror the `direction` / `align` / `justify` annotations and defaults to the
    enums (keep `direction` default `"vertical"` → `EStackDirection.VERTICAL`,
    `align` `"stretch"`, `justify` `"start"`).

- [x] **1.4 — Update `MenuView`**
  - Annotate `direction: EStackDirection | None = None` (leave `mode` as the
    existing `Literal["dropdown", "bar"]` — out of scope).

- [x] **1.5 — Export the enums (`__init__.py`)**
  - Import `EStackDirection`, `EStackAlign`, `EStackJustify` from `.views` and
    add them to `__all__`.

- [x] **1.6 — Tests (`test_views.py`)**
  - Assert `EStackJustify.SPACE_EVENLY == "space-evenly"` and the other enum
    members equal their string values.
  - Assert `StackView("horizontal", justify="start")` and
    `StackView("horizontal", justify=EStackJustify.SPACE_EVENLY)` serialize
    `justify` as `"start"` and `"space-evenly"` respectively (round-trip through
    `serialize_layout`).

## Validation

```
uv run pytest py/tests/viz/test_views.py py/tests/viz/test_layout_api.py py/tests/viz/test_banner.py -q
```

## Notes

- Do **not** touch `Orientation` (SplitView) or `MenuView.mode` — non-goals.
- `StrEnum` membership (`x in EStackJustify`) works for both the member and its
  string value; keep the existing raise messages if convenient.
