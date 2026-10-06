# Phase 1 — Reuse the content leaf views (fixes the log-view bug)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make `log_view`, `file_chooser_view`, `table_view`, and `progress_bar_view`
reusable across a `view_layout` re-push, and make the registry-backed teardown
identity-safe.  This is the direct fix for
`_input/pytanga-log-view-destroyed-view-forgets-registry-entry.md`.

## Files

- Edit: `py/pytanga/viz/templates/views/reconcile.js`
- Edit: `py/pytanga/viz/templates/views/build.js`
- Edit: `py/pytanga/viz/templates/views/message-view.js`
- Edit: `py/pytanga/viz/templates/views/file-chooser-view.js`
- Edit: `py/pytanga/viz/templates/views/table-view.js`
- Edit: `py/pytanga/viz/templates/file-browser.js`
- Edit: `js/dev/tests/reconcile.test.mjs`

## Steps

- [x] **1.1 — Extend `REUSABLE_TYPES` (`reconcile.js`)**
  - Add `log_view`, `file_chooser_view`, `table_view`, `progress_bar_view` to the
    set.
  - Update the header comment (currently "Everything else (containers,
    `log_view`, `file_chooser_view`, `table_view`, unknown types) is rebuilt")
    to list only the still-rebuilt types: `split`/`stack`/`toolbar`/`menu`.
  - Note: `progress_bar_view` already has `update()` **and** a reuse branch in
    `build.js`, so this allow-list entry alone makes it reusable.

- [x] **1.2 — `MessageView` reuse + identity-safe destroy (`message-view.js`, `build.js`)**
  - Add `update(node)` refreshing `maxHistory` (`node.max_history ?? this.maxHistory`),
    `showDate`, `showUtcOffset`.  Keep the existing DOM rows (preserve live
    history); if `maxHistory` is set, trim overflow with the same FIFO logic as
    `appendLines`.  Do **not** touch `initialLines` or re-render on `update`.
  - Make `_onMounted()` idempotent: add a `this._initialized` flag and append
    `initialLines` only the first mount, so a re-mount keeps the accumulated rows
    instead of re-appending/duplicating them.
  - Make `destroy()` identity-safe:
    `if (this.messageId != null && _messageViews.get(this.messageId) === this) forgetMessageView(this.messageId);`
  - In `build.js` `log_view` branch (currently always `new MessageView(...)`),
    compute `existing = reuse.get(node.id)` and reuse it: `if (existing) {
    existing.update(node); view = existing; } else { view = new MessageView(...);
    registerMessageView(view.messageId, view); }`.  Keep `applySizeSpecs` +
    `registerView`.

- [x] **1.3 — `FileChooserView` reuse + identity-safe unregister (`file-chooser-view.js`, `file-browser.js`, `build.js`)**
  - Add `update(node)` refreshing `value`, `root`, `file_filter`, `folders_only`,
    `existing_only`; re-derive `_currentPath` from `value || root || ''` when the
    path inputs change.  (Re-mount re-renders via `ControlView._onMounted` →
    `rerender()`.)
  - In `file-browser.js` add `FileBrowserManager.unregisterIfCurrent(controlId,
    view)` (delete only when `this._views.get(controlId) === view`) and re-export
    it as `unregisterFileBrowserIfCurrent`.  Change `FileChooserView.destroy()`
    to call it (identity-safe), keeping `unregisterFileBrowser` for dialog
    teardown which legitimately forgets.
  - In `build.js` `file_chooser_view` branch, add `existing` reuse +
    `existing.update(node)` before the `new FileChooserView(...)` fallback.

- [x] **1.4 — `TableView` reuse (`table-view.js`, `build.js`)**
  - Add `update(node)` refreshing every serialized field with `??` fallback:
    `label`, `tooltip`, `columns`, `rows`, `allow_add_rows`, `allow_add_columns`,
    `allow_delete_rows`, `show_column_titles`, `show_row_numbers`,
    `allow_delete_columns`, `sortable`, `column_types`, `column_widths`,
    `row_height`, `sort`, then `super.update(node)`.
  - In `build.js` `table_view` branch, add `existing` reuse +
    `existing.update(node)` before the `new TableView(...)` fallback.
  - Note: like other `ControlView`s, the table re-renders its grid on re-mount
    (`rerender()` → `createTable(...)`); reuse preserves the view object, its
    size constraints, and its `_controlRegistry` entry rather than the transient
    in-grid editing/focus state.

- [x] **1.5 — `progress_bar_view`**
  - No code change beyond step 1.1 — confirm `progress-bar-view.js` `update()`
    and the `build.js` reuse branch already exist and are exercised once the
    type is allow-listed.

- [x] **1.6 — Reconcile planner unit tests (`js/dev/tests/reconcile.test.mjs`)**
  - Add tests asserting `log_view`, `file_chooser_view`, `table_view`,
    `progress_bar_view` are **reused** on an id-stable re-push (and still
    orphaned when their id is removed).
  - Update the existing `non-reusable leaf (table_view)` test (currently expects
    `table_view` to be created + orphaned) to expect reuse instead.

## Validation

```
node js/dev/tests/check-syntax.mjs
node --test 'js/dev/tests/*.test.mjs'
```

## Notes

- `MessageView` extends `View` (not `ControlView`), so its `_onMounted` is the
  only re-render hook — that's why the idempotency guard matters.
- The `log_view` branch lives in its own early-return block in `build.js` (before
  the shared `existing` lookup), so it needs its own `existing` lookup.
