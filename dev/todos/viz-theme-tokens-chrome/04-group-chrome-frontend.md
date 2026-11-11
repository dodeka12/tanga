# Phase 4 — Group chrome (frontend)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make the browser honour the new group contract: create/remove the header bar
for `show_header` / `collapsible`, render no title when `title` is `null`/`""`
(the `'Controls'` fallback is deleted), apply `title_size` as a scoped custom
property, and keep the chrome measurement (`_chromeY`) correct without a header.

## Files

- Edit: `py/pytanga/viz/templates/views/build.js`
- Edit: `py/pytanga/viz/templates/views/group-view.js`
- Edit: `py/pytanga/viz/templates/themes/views/group-view.css`

## Steps

- [ ] **4.1 — Forward the new fields (`views/build.js:103-118`)**
  - Add `show_header: node.show_header,`, `collapsible: node.collapsible,` and
    `title_size: node.title_size,` to the `new GroupView({…})` call.  The reuse
    path already goes through `existing.update(node)`.

- [ ] **4.2 — Constructor state (`views/group-view.js:23-67`)**
  - Add `show_header = true, collapsible = true, title_size = null` to the
    destructured options, and after `super(...)`:
    ```js
    this.title = title ?? '';
    this.show_header = show_header !== false;
    this.collapsible = this.show_header && collapsible !== false;
    this.title_size = title_size == null ? null : Number(title_size);
    if (this.collapsed && !this.collapsible) this.collapsed = false;
    ```
    (Python validates; the last line keeps the client sane if a stale layout is
    re-pushed.)
  - `this.el.classList.add('tanga-group')` stays; add
    `this.el.classList.toggle('tanga-group-no-header', !this.show_header)` and
    `this.el.classList.toggle('tanga-group-static', !this.collapsible)` inside
    `_syncChromeClasses()` so `update()` can re-sync them.

- [ ] **4.3 — Split `_setupChrome()` into structure + header (`:69-133`)**
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
  - `_teardownHeader()`: disconnect `this._headerResizeObserver` (and null it),
    null `_header` / `_titleWrap` / `_toggleBtn`, reset `_lastHeaderHeight`,
    then `_invalidateChrome()`.
  - `destroy()` must call `_teardownHeader()` before `super.destroy()`.

- [ ] **4.4 — Title rendering & instance size (`_renderTitle`, `:135-151`)**
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

- [ ] **4.5 — `update(node)` semantics (`:153-175`)**
  - `this.title = node.title ?? this.title;` → track presence and treat `null`
    as "no title":
    ```js
    if ('title' in node) this.title = node.title ?? '';
    ```
  - Add `if ('show_header' in node) this.show_header = node.show_header !== false;`,
    `if ('collapsible' in node) this.collapsible = node.collapsible !== false;`,
    `if ('title_size' in node) this.title_size = node.title_size == null ? null : Number(node.title_size);`
    then re-run `_syncChromeClasses()`, `_ensureHeader()`, `_applyTitleSize()`.
  - Keep the `node.gap ?? this.gap` lines untouched (phase 2 handles the gap).
  - `setTitle(title)` (`:199-202`) → `this.title = title ?? '';` then
    `_ensureHeader()` + `_renderTitle()` so a rename can create/drop the header.

- [ ] **4.6 — Chrome measurement without a header (`_chromeY`, `:276-297`)**
  - Update the comment block at `:11-20` and add
    `const SHELL_FALLBACK = 18; // .tanga-group border 1px + padding 8px ×2`
    next to the existing fallbacks.
  - In `_chromeY()`: when `!this._header`, return
    `{ folded: 0, chrome: shell }` where `shell` is the measured
    `paddingTop + paddingBottom + borderTopWidth + borderBottomWidth` of
    `this.el`, falling back to `SHELL_FALLBACK` when the computed style is not
    available.  **Do not cache** the fallback value (same rule as today).
  - Leave the header-present path unchanged.

- [ ] **4.7 — Guards (`setCollapsed` / `setEnabled` / `setTooltip`)**
  - `setCollapsed(collapsed)`: first line `if (!this.collapsible) return;`.
  - `setEnabled(enabled)`: `if (!this.enabled && this.collapsible) this.setCollapsed(true);`
    — a static group must not collapse; add a
    `/* dim, don't fold */` comment.
  - `setTooltip(tooltip)`: target `this._titleWrap || this.el` so a headerless
    group still carries its tooltip.

- [ ] **4.8 — CSS (`themes/views/group-view.css`)**
  - Append:
    ```css
    /* A non-collapsible group cannot fold, so disabling dims its content
     * instead of collapsing the pane (see `setEnabled`). */
    .tanga-group.tanga-group-static.tanga-group-disabled > .tanga-group-content {
        opacity: var(--tanga-disabled-opacity);
    }
    ```
  - `.tanga-group-no-header` needs no rule (the header element is not created);
    it exists so themes can target the headerless variant.

## Validation

```bash
cd js/dev && npm run check
uv run pytest py/tests/viz/test_views.py -q
```

## Notes

- No DOM test harness exists in `js/dev`; the group chrome is verified manually
  (`uv run python py/examples/viz/ui/views/groups.py`-style script with a
  headerless group) plus the Python serialization tests from phase 3.
- `_applyCollapsed()` only hides `_content`, so a headerless group is
  unaffected.
- `this._lastHeaderHeight` must be reset in `_teardownHeader()`, otherwise a
  later header of the same height would not invalidate the chrome cache.
