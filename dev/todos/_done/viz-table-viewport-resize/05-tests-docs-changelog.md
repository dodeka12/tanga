# Phase 5 — Tests, docs, changelog

## Goal

Cover the new logic, document the zoom/resize/row-height controls, and record
the change.

## Files

- Edit: `dev/src/js-tests/table-keyboard.test.mjs`
- Edit: `py/tests/viz/test_control_value_api.py`
- Edit: `docs/py/viz/interaction/controls.md`
- Edit: `py/examples/viz/ui/controls/table_editing.py` (+ regenerated docs)
- Edit: `docs/changelog/2026-09-05_fix-examples.md`, `docs/changelog/index.md`

## Steps

- [x] **5.1 — JS tests**
  - Unit-test `clamp` (and re-verify `fitColumnWidths` under a `colScale`
    multiplier) in `table-keyboard.test.mjs`.
- [x] **5.2 — Python tests**
  - Confirm the Phase 1 preferred-size defaults serialize and an explicit
    `preferred_height=` still overrides.
- [x] **5.3 — Docs**
  - Document the title-bar `+`/`−` zoom (column width / row height), the
    row-height/column zoom semantics, and the resize corner in `controls.md`;
    update the `table_editing.py` docstring.
- [x] **5.4 — Changelog**
  - Append bullets to `docs/changelog/2026-09-05_fix-examples.md`; refresh
    `docs/changelog/index.md` if needed.

## Validation

`uv run pytest py/tests/viz/ -q && node --test 'dev/src/js-tests/*.test.mjs' && uv run mkdocs build --strict`
