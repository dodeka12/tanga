# Phase 2 — Spacing tokens & computed-gap size maths

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make the group-header spacing and the stack gap themeable, stop inlining the
header's appearance from JS, and make `StackView`/`GroupView` size maths read
the **computed** gap — so `--tanga-stack-gap` (or an explicit Python `gap`)
drives both the CSS layout and the measured min/preferred size.  This also
fixes the latent bug where `this.gap` was never passed to the size functions.

## Files

- Edit: `py/pytanga/viz/templates/themes/base.css`
- Edit: `py/pytanga/viz/templates/themes/views/group-view.css`
- Edit: `py/pytanga/viz/templates/views/group-view.js`
- Edit: `py/pytanga/viz/templates/views/stack-view.js`
- Edit: `py/pytanga/viz/templates/views/stack-size.js`
- New: `js/dev/tests/stack-size.test.mjs`

## Steps

- [ ] **2.1 — Declare the spacing tokens (`themes/base.css`)**
  - Next to `--tanga-params-row-gap` (`base.css:70`):
    `--tanga-stack-gap: 4px;`
  - Next to the group typography tokens added in phase 1:
    ```css
    --tanga-group-header-padding: 0 0 6px;
    --tanga-group-header-margin-bottom: 6px;
    --tanga-group-header-gap: 6px;
    ```
  - `--tanga-group-header-padding` is a shorthand on purpose: today's header
    has only `padding-bottom: 6px`, so `0 0 6px` preserves the look while
    letting a theme add vertical air (`4px 0 8px`).

- [ ] **2.2 — Consume them in `themes/views/group-view.css`**
  - `.tanga-group-header` (`:36-45`): replace `padding-bottom: 6px;` with
    `padding: var(--tanga-group-header-padding);` and `margin-bottom: 6px;`
    with `margin-bottom: var(--tanga-group-header-margin-bottom);`
  - `.tanga-group-title-wrap` (`:68-72`): `gap: var(--tanga-group-header-gap);`

- [ ] **2.3 — Stop inlining the header appearance (`views/group-view.js`)**
  - In `_setupChrome()` delete `marginBottom: '6px'` (`:86`) and the
    `display`/`alignItems`/`justifyContent` trio (`:83-85`) — all four are
    already declared by `.tanga-group-header`.
  - Delete `display`/`alignItems`/`gap` on `titleWrap` (`:95-99`) — declared by
    `.tanga-group-title-wrap`.
  - Keep the structural inline styles on `this.el` (`:70-74`), the
    `overflow: 'hidden'` (`:77-78`) and the `flexShrink: '0'` header guard
    (`:89-91`), which are conditional/geometry, not appearance.

- [ ] **2.4 — Add `resolveGapPx` (`views/stack-size.js`)**
  - Keep `GAP = 4` and keep the existing optional `gap` parameters of
    `stackMinSize` / `stackPreferredSize` unchanged (they are already correct).
  - Add and export:
    ```js
    /**
     * Resolve a CSS gap value (as returned by `getComputedStyle(el).rowGap`)
     * to a px number.  Browsers report `"normal"` for `gap: normal`, and an
     * element outside the document reports `""`; both fall back.
     */
    export function resolveGapPx(value, fallback = GAP) {
        if (typeof value === 'number') return Number.isFinite(value) ? value : fallback;
        const px = parseFloat(value);
        return Number.isFinite(px) ? px : fallback;
    }
    ```

- [ ] **2.5 — `views/stack-view.js`: themeable + measured gap**
  - `_applyFlex()` (`:50`):
    ```js
    s.gap = this.gap == null ? `var(--tanga-stack-gap, ${GAP}px)` : `${this.gap}px`;
    this._gapCache = null;
    ```
  - Add:
    ```js
    // The used gap: an explicit Python `gap` wins, otherwise the computed CSS
    // gap (`var(--tanga-stack-gap)`), so a theme moves the layout *and* the
    // size maths.  A detached element reports no gap — never cache that.
    _gapPx() {
        if (this.gap != null) return this.gap;
        if (this._gapCache != null) return this._gapCache;
        if (typeof getComputedStyle !== 'function') return GAP;
        const cs = getComputedStyle(this._content);
        const raw = (this.direction === 'vertical' ? cs.rowGap : cs.columnGap) || cs.gap;
        const px = resolveGapPx(raw, null);
        if (px === null) return GAP;
        this._gapCache = px;
        return px;
    }
    ```
  - Pass it through: `minSizePx` → `stackMinSize(axis, this.direction,
    this.children, available, this._gapPx())`; `preferredPx` →
    `stackPreferredSize(…, this._gapPx())`.
  - Invalidate on theme change and on mount: register
    `this._onThemeChange = () => { this._gapCache = null; this._relayout(); }`
    in the constructor via `document.addEventListener('tanga:themechange', …)`
    (guard `typeof document !== 'undefined'`, as `params-view.js:22-24` does),
    remove it in `destroy()`, and override `mount(host)` to clear `_gapCache`
    before calling `super.mount(host)`.
  - Import `resolveGapPx` alongside `GAP` from `./stack-size.js`.

- [ ] **2.6 — `views/group-view.js`: pass the gap in its two overrides**
  - `minSizePx` / `preferredPx`: pass `this._gapPx()` as the fifth argument to
    `stackMinSize` / `stackPreferredSize`.
  - `_content` is the retargeted flex container, so `_gapPx()` measures the
    right element; do **not** re-implement the cache here.

- [ ] **2.7 — New JS unit test (`js/dev/tests/stack-size.test.mjs`)**
  - `node:test` + `node:assert/strict`, importing
    `../../py/pytanga/viz/templates/views/stack-size.js` (same relative import
    style as the other pure-module tests in `js/dev/tests/`).
  - `resolveGapPx`: `12 → 12`, `'12px' → 12`, `'12.5px' → 12.5`,
    `'normal' → 4` (fallback), `'' → 4`, `null → 4`, `0 → 0`,
    `('12px', null) → 12`, `('normal', null) → null`.
  - `stackMinSize` with stub children (`{ minSizePx: () => 10 }`): default gap
    → `24`; explicit gap `12` → `32`; `wrap` direction → `0`; cross axis → `10`.
  - `stackPreferredSize` with the same stubs and explicit `gap` → `32` (the
    regression test for the dropped argument).

## Validation

```bash
cd js/dev && npm run check && node --test tests/stack-size.test.mjs
```

## Notes

- `getComputedStyle` on a detached element returns an empty declaration; the
  helper therefore returns `GAP` **without caching**, mirroring
  `GroupView._chromeY()`'s "never cache a fallback" behaviour.
- A theme that sets `--tanga-stack-gap` now also changes `ToolbarView` /
  `MenuView` spacing (both subclass `StackView`).  Intended; documented in
  phase 6.
- `ParamsView` does not use `StackView`; its spacing stays on the
  `--tanga-params-*` tokens, and `.tanga-params-dense` keeps winning by CSS
  specificity (documented in phase 6).
