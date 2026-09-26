# Phase 1 — ProgressBar control model

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add the `ProgressBar` dataclass to `_controls.py` and unit-test its
serialization and value-dict handling.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- New: `py/tests/viz/test_progress_bar.py`

## Steps

- [x] **1.1 — `ProgressBar` dataclass (`_controls.py`)**
  - Add `@dataclass class ProgressBar(Control)` next to `Label`/`Markdown` (the
    read-only display controls) with `kind: str = "progress"` and fields
    `title: str = ""`, `value: float = 0.0`, `total: int = 0`,
    `indeterminate: bool = False`, `text: str = ""`.
  - Implement `_fields()` returning all five fields.
  - Override `get_value()` to return `{"title", "value", "total",
    "indeterminate", "text"}` and `set_value(value)` to accept a dict (update
    present keys) or a bare number (set `value` only).

- [x] **1.2 — Tests (`py/tests/viz/test_progress_bar.py`)**
  - `serialize()` includes `kind == "progress"` and all five fields.
  - `set_value(number)` / `set_value(dict)` / `get_value()` round-trip.
  - Defaults and the inherited `handle_event` pass-through behave.

## Validation

```bash
uv run pytest py/tests/viz/test_progress_bar.py py/tests/viz/test_controls.py -q
```

## Notes

- `ProgressBar` keeps the base `_value_type = None`; it overrides
  `get_value`/`set_value` directly (mirrors `Table`), so the inherited
  `ControlView.set_value` pushes the full dict.
