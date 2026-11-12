# Phase 4 — Group chrome (frontend)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make the browser honour the new group contract: create/remove the header bar
for `show_header` / `collapsible`, apply the `variant` class, fold/unfold on a
click anywhere on the header, render no title when `title` is `null`/`""`
(the `'Controls'` fallback is deleted), apply `title_size` as a scoped custom
property, keep the chrome measurement (`_chromeY`) correct without a header,
and put the control's tooltip on a `ParamsView` row's key label.

## Files

- Edit: `py/pytanga/viz/templates/views/build.js`
- Edit: `py/pytanga/viz/templates/views/group-view.js`
- Edit: `py/pytanga/viz/templates/views/params-view.js`
- Edit: `py/pytanga/viz/templates/themes/views/group-view.css`

## Steps

- [x] **4.1 — Forward the new fields (`views/build.js:103-118`)**
  - Add `show_header: node.show_header,`, `collapsible: node.collapsible,`,
    `title_size: node.title_size,` and `variant: node.variant,` to the
    `new GroupView({…})` call.  The reuse path already goes through
    `existing.update(node)`.

- [x] **4.2 — Constructor state (`views/group-view.js:23-67`)**
  - Add `show_header = true, collapsible = true, title_size = null,
    variant = 'default'` to the destructured options, and after `super(...)`:
    ```js
    this.title = title ?? '';
    this.show_header = show_header !== false;
    this.collapsible = this.show_header && collapsible !== false;
    this.title_size = title_size == null ? null : Number(title_size);
    this.variant = ['default', 'small', 'tiny'].includes(variant)
        ? variant : 'default';
    if (this.collapsed && !this.collapsible) this.collapsed = false;
    ```
    (Python validates; the `variant` fallback and the last line keep the client
    sane if a stale/foreign layout is re-pushed.)
  - `this.el.classList.add('tanga-group')` stays; add a
    `_syncChromeClasses()` helper that toggles all state classes so `update()`
    can re-sync them:
    ```js
    _syncChromeClasses() {
        this.el.classList.toggle('tanga-group-no-header', !this.show_header);
        this.el.classList.toggle('tanga-group-static', !this.collapsible);
        this.el.classList.toggle('tanga-group-small', this.variant === 'small');
        this.el.classList.toggle('tanga-group-tiny', this.variant === 'tiny');
        // Deprecated alias kept for one release (see phase 1 CSS).
        this.el.classList.toggle('tanga-group-nested', this.variant === 'small');
    }
    ```
    Call it once in the constructor after `this.el.classList.add('tanga-group')`
    and before `_setupChrome()`.
  - Remove the `if (isGroup) control.el.classList.add('tanga-group-nested');`
    line from `params-view.js:57` — `GroupView` owns the class now (it is
    toggled by `_syncChromeClasses()` for `variant === 'small'`).  Keep
    `isGroup` for `isFullWidth` and the `tanga-params-row-group` class.

- [x] **4.3 — Split `_setupChrome()` into structure + header (`:69-133`)**
  - `_setupChrome()` keeps the `this.el` inline styles,
    `_content` creation/append, then calls `this._ensureHeader()` first,
    followed by `_applyFlex()`, `_applyScroll()`, `_applyCollapsed()`.
  - `_ensureHeader()` returns early when
    `!this.show_header || !(this.collapsible || this.title || this.icon)` and
    `_teardownHeader()`s an existing header in that case; otherwise it builds
    the header **once** and inserts it with
    `this.el.insertBefore(this._header, this._content)` (never appendChild —
    a late header must stay above the content).
  - Move the current header/title-wrap/toggle/ResizeObserver construction
    (`:80-132`) verbatim into `_ensureHeader()`, minus the inline appearance
    removed in phase 2, plus `this._applyTitleSize()`.
  - Attach the click-to-fold handler once, on the header:
    ```js
    this._header.addEventListener('click', (event) => {
        if (!this.collapsible || !this.enabled) return;
        // The toggle has its own handler; never fold twice.
        if (event.target.closest('.tanga-group-toggle')) return;
        if (event.target.closest('button, a, input, select, textarea, [role="button"]')) return;
        this.setCollapsed(!this.collapsed);
        sendControlEvent('control:group_toggle', this.groupId, this.collapsed);
    });
    ```
    `setCollapsed()` early-returns when the state is unchanged and remains the
    only place that pins/restores the min/max sizes and emits
    `constraintschange`, so the click path adds no new state logic.  The
    `enabled` guard matters because `setEnabled(false)` collapses the pane and
    disables the toggle — a header click must not re-expand it.
  - `_teardownHeader()`: disconnect `this._headerResizeObserver` (and null it),
    null `_header` / `_titleWrap` / `_toggleBtn`, reset `_lastHeaderHeight`,
    then `_invalidateChrome()`.
  - `destroy()` must call `_teardownHeader()` before `super.destroy()`.

- [x] **4.4 — Title rendering & instance size (`_renderTitle`, `:135-151`)**
  - Delete the `'Controls'` fallback:
    ```js
    _renderTitle() {
        const wrap = this._titleWrap;
        if (!wrap) return;
        wrap.replaceChildren();
        if (this.icon) { /* unchanged */ }
        if (!this.icon_only && this.title) {
            const span = document.createElement('span');
            span.className = 'tanga-group-title';
            span.textContent = this.title;
            wrap.appendChild(span);
        }
        wrap.style.display = wrap.childElementCount ? '' : 'none';
        applyTooltip(wrap, this.tooltip);
    }
    ```
    Hiding an empty wrap keeps the toggle button flush right instead of leaving
    a 6px gap.
  - Add:
    ```js
    // Instance override (scoped custom property only — never a resolved
    // appearance value), so every theme rule for `.tanga-group-title` still
    // applies except the font size.
    _applyTitleSize() {
        if (this.title_size == null) {
            this.el.style.removeProperty('--tanga-group-title-font-size');
        } else {
            this.el.style.setProperty(
                '--tanga-group-title-font-size', `${this.title_size}px`
            );
        }
    }
    ```
    Call it from `_ensureHeader()` and from `update()`.

- [x] **4.5 — `update(node)` semantics (`:153-175`)**
  - `this.title = node.title ?? this.title;` → track presence and treat `null`
    as "no title":
    ```js
    if ('title' in node) this.title = node.title ?? '';
    ```
  - Add `if ('show_header' in node) this.show_header = node.show_header !== false;`,
    `if ('collapsible' in node) this.collapsible = node.collapsible !== false;`,
    `if ('title_size' in node) this.title_size = node.title_size == null ? null : Number(node.title_size);`
    and
    `if ('variant' in node) this.variant = ['default', 'small', 'tiny'].includes(node.variant) ? node.variant : 'default';`
    then re-run `_syncChromeClasses()`, `_ensureHeader()`, `_applyTitleSize()`.
  - Keep the `node.gap ?? this.gap` lines untouched (phase 2 handles the gap).
  - `setTitle(title)` (`:199-202`) → `this.title = title ?? '';` then
    `_ensureHeader()` + `_renderTitle()` so a rename can create/drop the header.

- [x] **4.6 — Chrome measurement without a header (`_chromeY`, `:276-297`)**
  - Update the comment block at `:11-20` and add
    `const SHELL_FALLBACK = 18; // .tanga-group border 1px + padding 8px ×2`
    next to the existing fallbacks.
  - In `_chromeY()`: when `!this._header`, return
    `{ folded: 0, chrome: shell }` where `shell` is the measured
    `paddingTop + paddingBottom + borderTopWidth + borderBottomWidth` of
    `this.el`, falling back to `SHELL_FALLBACK` when the computed style is not
    available.  **Do not cache** the fallback value (same rule as today).
  - Leave the header-present path unchanged.

- [x] **4.7 — Guards (`setCollapsed` / `setEnabled` / `setTooltip`)**
  - `setCollapsed(collapsed)`: first line `if (!this.collapsible) return;`.
  - `setEnabled(enabled)`: `if (!this.enabled && this.collapsible) this.setCollapsed(true);`
    — a static group must not collapse; add a
    `/* dim, don't fold */` comment.
  - `setTooltip(tooltip)`: target `this._titleWrap || this.el` so a headerless
    group still carries its tooltip.

- [x] **4.8 — CSS (`themes/views/group-view.css`)**
  - The header is clickable now, so `.tanga-group-header` (`:36-45`) changes
    `cursor: grab` → `cursor: pointer`, and the
    `.tanga-group-header:active { cursor: grabbing; }` rule (`:47-49`) is
    deleted (there is no drag handler).  Add:
    ```css
    .tanga-group.tanga-group-static .tanga-group-header,
    .tanga-group.tanga-group-disabled .tanga-group-header {
        cursor: default;
    }
    ```
  - Append:
    ```css
    /* A non-collapsible group cannot fold, so disabling dims its content
     * instead of collapsing the pane (see `setEnabled`). */
    .tanga-group.tanga-group-static.tanga-group-disabled > .tanga-group-content {
        opacity: var(--tanga-disabled-opacity);
    }
    ```
  - `.tanga-group-no-header` needs no rule (the header element is not created);
    it exists so themes can target the headerless variant.  The
    `tanga-group-small` / `-tiny` rules live in phases 1–2; this phase only
    adds/toggles the classes.

- [x] **4.9 — `ParamsView` row-title tooltips (`views/params-view.js`, `build.js`)**
  - Import `applyTooltip` from `../controls-panel.js` (same import style as
    `group-view.js`).
  - `addRow({ key, title, control, full_width = false, tooltip = '' })`:
    after creating `keyEl`, call
    `applyTooltip(keyEl, tooltip || control.tooltip || '')`.  The row title is
    a **sibling** of the control, so it never inherits the control's tooltip;
    this is the only place that can put it on the label.
  - Store `tooltip` in the `_rows.push({…})` entry so `setRowTitle` can
    re-apply it if the title is re-rendered.
  - In `views/build.js:171`, pass `tooltip: child.tooltip` into `addRow`
    (`ControlView` stores the serialized tooltip; `GroupView` rows are
    full-width and have no key label, so they are unaffected).
  - `applyTooltip` writes `data-tanga-tooltip` + the native `title`, so the
    page-wide `Visualizer.set_tooltips_enabled()` switch also covers row
    titles (do **not** set `keyEl.title` directly).
  - The tooltip is captured when the row is built; a layout re-push rebuilds
    the rows and refreshes it (no new `control_state` key).

## Validation

```bash
cd js/dev && npm run check
uv run pytest py/tests/viz/test_views.py -q
```

## Notes

- No DOM test harness exists in `js/dev`; the group chrome is verified manually
  (`uv run python py/examples/viz/ui/views/groups.py`-style script with a
  headerless group, one `variant="small"` group and one `variant="tiny"`
  group) plus the Python serialization tests from phase 3.
- Manual checks: clicking the title folds/unfolds; clicking the toggle does
  **not** double-toggle; a `collapsible=False` or disabled header ignores
  clicks; a `ParamsView` value row shows the control's tooltip on its key label
  and the Help → Show tooltips switch hides it.
- `_applyCollapsed()` only hides `_content`, so a headerless group is
  unaffected.
- `this._lastHeaderHeight` must be reset in `_teardownHeader()`, otherwise a
  later header of the same height would not invalidate the chrome cache.
