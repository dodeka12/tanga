# Phase 6 — Docs + changelog

## Goal

Document the two new column kinds and the `enum_options` handler, and record the
branch changelog.

## Files

- Edit: `docs/py/viz/interaction/controls.md`
- Edit: `docs/py/viz/interaction/control-views.md`
- New: `docs/changelog/2026-09-07_fix-misc.md`

## Steps

- [x] **6.1 — `controls.md` ("Column types, alignment & persistence")**
  - Extend the column-type paragraph with the `column` and `custom` kinds:
    `column` = de-duped values of another column (header context submenu), and
    `custom` = backend-only, values from the `enum_options` handler at edit time.
  - Document the `enum_options` handler signature and
    `TableEnumOptionsRequest(col, row, current)`.

- [x] **6.2 — `control-views.md` (`TableView` signature)**
  - Add `enum_options=None` to the `TableView` signature block and note it is a
    backend-only provider (not serialized, not frontend-selectable).

- [x] **6.3 — Branch changelog**
  - Run `uv run python tools/last-release.py` to get the since-relative title.
  - Create `docs/changelog/2026-09-07_fix-misc.md` following
    `dev/workflows/changelog.md` (branch-name form `fix-misc`; `## New Features`
    bullets for the `column` and `custom` kinds + `enum_options` handler).

## Validation

```
uv run pytest py/tests/viz/test_table_types.py -q; uv run mkdocs build --strict
```

## Notes

- Finalize the changelog filename/hash rename at PR time per
  `dev/workflows/pull-request.md`; on this branch keep the branch-name form.
