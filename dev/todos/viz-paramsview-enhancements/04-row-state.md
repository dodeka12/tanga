# Phase 4 — Row state (visible / enabled / title / options)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (`control_state`,
> `set_enabled`/`set_visible`, `View.setHidden`).  This makes the frontend
> `ParamsView` row-aware; it reuses `control_state`/`control_update`, no new wire
> message.

## Goal

Add public per-row `set_visible`/`set_enabled`/`set_title`/`set_options` that act
on the whole row (title + control), and make the frontend hide/grey/relabel rows.

## Files

- **Edit** `py/pytanga/viz/_params_ui.py` — `visible: bool | None` on `ControlUI`.
- **Edit** `py/pytanga/viz/views/params_view.py` — the four public methods.
- **Edit** `py/pytanga/viz/templates/views/params-view.js` — track rows by key;
  propagate child `visible`/`enabled` to the row; update title/options.
- **Edit** `py/pytanga/viz/templates/themes/views/params-view.css` — disabled-row
  title styling.
- **Edit** `py/tests/viz/test_params_view.py`.

## Steps

- [x] **4.1 — `ControlUI.visible`**
  - Add `visible: bool | None = None` (applied at build time like `enabled`).
- [x] **4.2 — Python row-state methods**
  - `set_visible(key, bool)` / `set_enabled(key, bool)` set the child control's
    flag and push `control_state`; `set_title(key, str)` updates `_titles` and
    pushes a title update; `set_options(key, list)` pushes new dropdown options.
- [x] **4.3 — row-aware frontend**
  - In `params-view.js`, keep `key → {row, keyEl, control}` and, on a child's
    visibility/enabled change, toggle the row (`display`/a disabled class) and
    update the `.tanga-params-key` text for titles/options.
- [x] **4.4 — CSS + tests**
  - Grey the key label when its row is disabled; test the four methods and
    initial `visible` from `ControlUI`.

## Validation

```bash
node js/dev/tests/check-syntax.mjs && uv run pytest py/tests/viz/test_params_view.py -q
```
