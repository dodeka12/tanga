# Phase 5 — Frontend CDN wiring

## Goal

Load Tabulator (CSS + JS) in the live viewer page, and teach the optional-
dependency error detector about it.

## Files

- Edit: `py/pytanga/viz/templates/viewer.html`

## Steps

- [ ] **5.1 — CDN loader**
  - In the `document.write` CDN block (the `url(pkg, file)` helper), add:
    - `<link rel="stylesheet" href="url('tabulator-tables@6.5.2', 'dist/css/tabulator_midnight.min.css')">`
    - `<script src="url('tabulator-tables@6.5.2', 'dist/js/tabulator.min.js')">`
  - Keep the pinned `@6.5.2` version and the jsdelivr/unpkg dual path, exactly
    like `katex@0.16.11`.

- [ ] **5.2 — Error detector**
  - In the loader IIFE's `error` handler, add a
    `else if (/tabulator/.test(src) && !OPTIONAL_SEEN.tabulator)` branch pushing
    `'Tabulator (editable tables)'` to `OPTIONAL_MISSING` (mirror the
    `marked`/`katex`/`html2canvas` cases).

## Validation

Manual viewer smoke: open the viewer and confirm no "Optional libraries
unavailable" warning; confirm `window.Tabulator` is defined in the console.
`uv run pytest py/tests/viz/test_frontend_version.py -q` for the template-hash
regression.

## Notes

- No `viewer.js`/`build.js` change here — Tabulator is a UMD global (like
  `marked`), so `controls-panel.js` references the bare `Tabulator` symbol.
- `tabulator_midnight` is Tabulator's built-in dark theme; it needs no custom
  override CSS.
