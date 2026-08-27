# Phase 5 — Group title bar + banner controls

## Goal

Render the group title-bar icon/tooltip in both the fixed panel and the
attached CSS2D group, and extend the banner's control builder to the new kinds.

## Steps

- [x] **5.1 — Fixed panel header (`_createGroupPanel`)**
  - Render `group.icon` (via `createIconElement`) before the title text.
  - Set `header.title = group.tooltip` when set.

- [x] **5.2 — Attached title bar (`controls-attached.js`)**
  - Render `group.icon` before `titleText`; set `titleBar.title = group.tooltip`.

- [x] **5.3 — `views/banner-view.js` `_buildControl`**
  - Add `text`/`textarea`/`color`/`checkbox` cases (buttons stay in the row,
    the rest in the stack).

- [x] **5.4 — Validate**
  - Manual viewer smoke: group with icon + tooltip; banner with a new control.

## Validation

Manual viewer smoke test.

## Notes

- Group icon/tooltip reuse the same `createIconElement` helper; the attached
  title bar uses the same fields as the fixed panel header.
