# Phase 2 — Type coercion + inference fixes

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (control value
> coercion in `Control.handle_event`).  This is a correctness fix + additive
> `ControlUI` fields; no architecture change.

## Goal

Resolve real field types (fix the `from __future__ import annotations` bug),
coerce browser values to the field's type (int stays int), and infer
`Enum`/`Literal`/`X | None`.

## Files

- **Edit** `py/pytanga/viz/views/params_view.py` — resolve annotations via
  `typing.get_type_hints(type(source), include_extras=True)`; coerce in `_make_handler`.
- **Edit** `py/pytanga/viz/_params_ui.py` — `coerce` on `ControlUI`, `integer` on
  `ValueEditUI`/`SliderUI`; extend `infer_control_ui`.
- **Edit** `py/tests/viz/test_params_ui.py`, `py/tests/viz/test_params_view.py`.

## Steps

- [x] **2.1 — annotation resolution**
  - Replace `dataclasses.fields(source)` type reads with `get_type_hints`-resolved
    types in `ParamsView._initial_values`, so `"float"`/`"int"` strings resolve.
- [x] **2.2 — `infer_control_ui` for Enum / Literal / nullable**
  - `Enum` → `DropdownUI(options=member values)`; `Literal["a","b"]` →
    `DropdownUI(options=...)`; unwrap `X | None` (and `Optional[X]`) to `X` before
    inferring.
- [x] **2.3 — `coerce` / `integer` fields**
  - Add `coerce: Callable[[Any], Any] | None = None` to `ControlUI` (skip in
    `_ui_kwargs`); add `integer: bool = False` to `ValueEditUI`/`SliderUI`.
- [x] **2.4 — apply coercion**
  - In `_make_handler`, coerce `value` via `ui.coerce` when set, else the resolved
    field type (`int`/`float`/`bool`/`str`/`Enum`/`Literal`); `integer=True` implies
    `coerce=int`.
- [x] **2.5 — tests**
  - `int` field round-trips as `int`; string-annotated dataclass infers correctly;
    `Enum`/`Literal`/`Optional[X]` infer dropdowns; `coerce=`/`integer=True` work.

## Validation

```bash
uv run pytest py/tests/viz/test_params_ui.py py/tests/viz/test_params_view.py -q
```
