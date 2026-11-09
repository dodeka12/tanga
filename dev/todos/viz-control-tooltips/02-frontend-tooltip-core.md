# Phase 2 — Frontend tooltip core

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Route every framework tooltip through one helper that (a) sets **and clears**
`title`, (b) records the intended text in `data-tanga-tooltip`, and (c) honours a
page-level `tooltipsEnabled` flag; then wire that helper into controls, groups,
menus and the hardcoded chrome affordances, and handle `tooltip` on the
`control_state` path.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/controls/button.js`
- Edit: `py/pytanga/viz/templates/controls/value-edit.js`
- Edit: `py/pytanga/viz/templates/controls/table.js`
- Edit: `py/pytanga/viz/templates/views/group-view.js`
- Edit: `py/pytanga/viz/templates/views/menu-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`
- Edit: `py/pytanga/viz/templates/views/dialog-view.js`
- Edit: `py/pytanga/viz/templates/views/banner-view.js`
- Edit: `py/pytanga/viz/templates/views/file-browser-view.js`
- Edit: `py/pytanga/viz/templates/views/file-chooser-view.js`
- Edit: `py/pytanga/viz/templates/viewer.js`

## Steps

- [x] **2.1 — `applyTooltip` + switch (`controls-panel.js`)**
  - Replace `_applyTooltip` with:
    ```js
    const TOOLTIP_ATTR = 'data-tanga-tooltip';
    let _tooltipsEnabled = true;

    function _syncTooltipTitle(el) {
        const text = el.getAttribute(TOOLTIP_ATTR) || '';
        if (text && _tooltipsEnabled) el.title = text;
        else el.removeAttribute('title');
    }

    export function applyTooltip(el, source) {
        if (!el) return;
        const text = typeof source === 'string'
            ? source
            : ((source && source.tooltip) || '');
        if (text) el.setAttribute(TOOLTIP_ATTR, text);
        else el.removeAttribute(TOOLTIP_ATTR);
        _syncTooltipTitle(el);
    }

    export function setTooltipsEnabled(enabled) {
        _tooltipsEnabled = !!enabled;
        document.querySelectorAll(`[${TOOLTIP_ATTR}]`).forEach(_syncTooltipTitle);
    }

    export function tooltipsEnabled() { return _tooltipsEnabled; }
    ```
    Keep the name `applyTooltip` exported so the 12 existing
    `applyTooltip(wrapper, ctrl)` call sites keep working (object *or* string
    source). Note the behavioural fix: an empty tooltip now **clears** `title`.

- [x] **2.2 — `tooltip` in `applyControlStateToElement`**
  - Add `if (state.tooltip !== undefined) applyTooltip(wrapper, state.tooltip);`
    next to the `selected` branch.

- [x] **2.3 — icon-only button (`controls/button.js`)**
  - Replace `btn.title = ctrl.tooltip || ctrl.label || ctrl.id || ''` with
    `const hoverText = ctrl.tooltip || ctrl.label || ctrl.id || '';` then
    `applyTooltip(btn, hoverText);` **and**
    `btn.setAttribute('aria-label', hoverText);`.
  - Add a `applyState` to the `registerControl` entry that calls
    `applyControlStateToElement(wrapper, state)` and then re-mirrors
    `state.tooltip` onto `btn` (same fallback expression) so a runtime tooltip
    change reaches the element that is actually hovered.

- [x] **2.4 — group view (`views/group-view.js`)**
  - `_renderTitle`: replace `wrap.title = this.tooltip || ''` with
    `applyTooltip(wrap, this.tooltip)`.
  - Add `setTooltip(text) { this.tooltip = text; applyTooltip(this._titleWrap,
    text); }` (called from `viewer.js` on `control_state`).
  - `_setupChrome`: `toggleBtn.title = 'Collapse / Expand'` →
    `applyTooltip(toggleBtn, 'Collapse / Expand')`.
  - Import `applyTooltip` from `../controls-panel.js`.

- [x] **2.5 — menu view (`views/menu-view.js` + `views/build.js`)**
  - Constructor option `tooltip = ''` → `this.tooltip = tooltip`.
  - `this._trigger.title = this.label || 'Menu'` →
    `applyTooltip(this._trigger, this.tooltip, this.label || 'Menu')`.
  - `build.js` `new MenuView({ … })`: pass `tooltip: node.tooltip`.

- [x] **2.6 — chrome affordance sweep**
  - Route the remaining hardcoded framework `title`s through `applyTooltip`
    (string form) so the switch suppresses them too:
    `controls/value-edit.js` (`Increase`/`Decrease`),
    `controls/table.js` (zoom buttons + `Resize` corner),
    `views/dialog-view.js` (`Dismiss`, `Resize`),
    `views/banner-view.js` (`Dismiss`),
    `views/file-browser-view.js` and `views/file-chooser-view.js`
    (`Parent directory`, `Accept the current directory`).
  - Leave `viewer.js` connection-status titles untouched (non-goal).

- [x] **2.7 — `control_state` → `setTooltip` (`viewer.js`)**
  - In the `control_state` branch add, after the `enabled` handling:
    ```js
    if (msg.tooltip !== undefined) {
        const host = _viewRegistry.get(msg.id);
        if (host && typeof host.setTooltip === 'function') host.setTooltip(msg.tooltip);
    }
    ```
    (`applyControlState` already covers panel controls; this covers groups.)

## Validation

```bash
node js/dev/tests/check-syntax.mjs && node --test js/dev/tests/*.test.mjs
```

> `js/dev/tests/reconcile-smoke.mjs` is a manual Playwright smoke that needs a
> live server (`uv run python js/dev/tests/serve-smoke.py`) — not part of the
> per-step gate.

## Notes

- Only `dropdown.js` and `value-edit.js` override `applyState`, and both delegate
  to `applyControlStateToElement`, so step 2.2 covers every control kind; the
  build-time `applyControlStateToElement(wrapper, ctrl)` calls re-apply the
  initial tooltip harmlessly.
- Elements that record a tooltip while the switch is off get the attribute but
  no `title`; `setTooltipsEnabled(true)` restores them all.
- `title`s set by user/theme JavaScript outside `applyTooltip` are not switched
  (documented limitation).
