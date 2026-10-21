# Phase 3 — Frontend `params_view` node + label-less controls

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (frontend control
> factories + `sendEvent`) and `docs/dev/architecture/viz-theme-system.md` (component
> sheets + `registry.json`).  This phase adds a view + component sheet following the
> existing frontend patterns; no documented contract changes.

## Goal

Render the `params_view` node as a two-column grid (key/title left, control right),
reusing the existing control factories, and make those factories honor the new
`hide_label` flag.

## Files

- **New** `py/pytanga/viz/templates/views/params-view.js` — `ParamsView` (JS).
- **Edit** `py/pytanga/viz/templates/views/build.js` — `params_view` branch.
- **Edit** control factories to honor `hide_label`: `slider.js`, `value-edit.js`,
  `dropdown.js`, `text-field.js`, `text-area.js`, `color-picker.js`, `checkbox.js`.
- **New** `py/pytanga/viz/templates/themes/views/params-view.css`.
- **Edit** `py/pytanga/viz/templates/themes/registry.json` — add the component sheet.

## Steps

- [x] **3.1 — `build.js` dispatch + `ParamsView` JS**
  - In `build.js`, add a `node.type === "params_view"` branch that builds a new
    `ParamsView({ id, title })` and, for each `node.rows[i]`, recursively calls
    `buildViewTree(row.control, …)` and attaches the child control with
    `{ key, title }` (reuse + registry flow unchanged).
  - `params-view.js`: `class ParamsView extends View` with `addRow({ key, title,
    control })`; render each row as
    `<div class="tanga-params-row"><span class="tanga-params-key">title</span><div
    class="tanga-params-control">child.el</div></div>`.  Treat it as a layout
    container (rebuilt on reconcile, children reused by id).
- [x] **3.2 — factories honor `hide_label`**
  - In the heading-label factories (`slider.js`, `value-edit.js`, `dropdown.js`,
    `text-field.js`, `text-area.js`, `color-picker.js`): when `ctrl.hide_label` is
    truthy, skip creating the `<label>`/label row (slider keeps the value readout or
    drops the label row — pick one and keep it consistent).
  - In `checkbox.js`: when `ctrl.hide_label`, render a bare `<input
    class="tanga-checkbox-input">` without the `.tanga-checkbox-row` label wrapper.
  - `button.js`/`label.js`/`markdown.js`/`progress-bar.js` need no change (their
    text is their content, not a separate label heading).
- [x] **3.3 — CSS + registry**
  - `params-view.css`: `.tanga-params-view` grid (`grid-template-columns: auto 1fr`,
    aligned rows), `.tanga-params-row`, `.tanga-params-key`,
    `.tanga-params-control`; colors/fonts via `var(--tanga-*)` so the compact theme
    tightens it automatically.
  - Add `views/params-view.css` to `registry.json` `components`.
- [x] **3.4 — build + syntax + smoke**
  - Rebuild the committed viewer bundle and run the JS gates; verify the drift-guard
    test (`test_themes.py::test_components_drift_guard`) passes with the new sheet.

## Validation

```bash
uv run python tools/build-viewer-js.py && node js/dev/tests/check-syntax.mjs && uv run pytest py/tests/viz/test_themes.py -q
```
