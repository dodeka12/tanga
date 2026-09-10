# Phase 4 — Frontend: `column` values + context submenu

## Goal

Render the `"column"` kind as a dropdown populated from the live source column,
and add the "From column…" submenu to the header context menu.

## Files

- Edit: `py/pytanga/viz/templates/controls/table.js`
- Edit: `py/pytanga/viz/templates/themes/controls/table.css`

## Steps

- [x] **4.1 — `normalizeColumnType` keeps `source`**
  - In `table.js`, add `source: Number.isInteger(t.source) ? t.source : null` to
    the normalized object.

- [x] **4.2 — `columnValues(ci)` helper**
  - Replace the `enumValues(ci)` helper with a `columnValues(ci)` that:
    - `enum` → `t.values`;
    - `column` → de-duped (insertion-order, skip empty strings) string values of
      `rows[source]`, guarding an out-of-range `source` (→ `[]`);
    - otherwise `[]`.

- [x] **4.3 — `openEditor` treats `column` like `enum`**
  - Change the `kind === 'enum'` branch to `kind === 'enum' || kind === 'column'`
    and use `columnValues(ci)` for the dropdown options (keep the current-value
    fallback option).

- [x] **4.4 — Context menu submenu**
  - In `openTypeMenu`, add `'column'` to the option list and render it as
    "From column…".
  - Clicking it swaps the menu to a submenu of the **other** columns
    (`columns.map((title, idx) => ...)` excluding `i`, plus a "‹ Back" item);
    each column button sends
    `sendControlEvent('control:column_type_change', ctrl.id, { col: i, type: 'column', source: idx })`.

- [x] **4.5 — CSS**
  - In `table.css`, add submenu styling (`.tanga-table-type-menu-submenu` /
    a back item class) consistent with the existing `.tanga-table-type-menu`
    and `.tanga-table-type-menu-item` rules.

## Validation

```
node --check py/pytanga/viz/templates/controls/table.js
```

## Notes

- Computing the values client-side keeps the dropdown fresh after the source
  column is edited (no full-grid push is sent on `cell_change`).
- Keep the menu's existing close-on-outside-click / Escape behavior for the
  submenu too.
