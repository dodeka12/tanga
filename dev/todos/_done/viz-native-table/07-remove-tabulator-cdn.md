# Phase 7 — Remove the Tabulator CDN and stale references

## Goal

Delete the Tabulator CSS/JS CDN loading and every remaining Tabulator reference so
the table is fully dependency-free.

## Files

- Edit: `py/pytanga/viz/templates/viewer.html`
- Edit: `py/pytanga/viz/templates/controls-panel.js` (final cleanup of `.tabulator-*` mentions)
- Edit: `py/pytanga/viz/templates/views/table-view.js` (comment)

## Steps

- [x] **7.1 — `viewer.html` CDN**
  - Remove the two `document.write` lines loading `tabulator_midnight.min.css` /
    `tabulator.min.js`.
  - Remove the `/tabulator/` branch (and its `OPTIONAL_SEEN.tabulator`) in the
    optional-missing loader.

- [x] **7.2 — Stale references**
  - Grep `py/pytanga/viz/templates/` for `Tabulator`/`tabulator` and remove/rewrite
    the remaining mentions (the `typeof Tabulator === 'undefined'` guard is already
    gone after Phase 3; drop the `.tabulator-editor` guard comment too).

## Validation

`grep -rni 'tabulator' py/pytanga/viz/templates/ || echo clean && uv run pytest py/tests/viz/test_themes.py -q`

## Notes

- `themes/controls/table.css` keeps the `tanga-table-*` class names (ours), not
  `tabulator-*`.
- After this phase, reload the examples with DevTools network tab open — no
  `tabulator` request should appear.
- Removing `tabulator_midnight.min.css` removes the last non-themeable table
  stylesheet; the table is now styled only by `controls/table.css` + tokens, so the
  `test_components_drift_guard` must still pass.
