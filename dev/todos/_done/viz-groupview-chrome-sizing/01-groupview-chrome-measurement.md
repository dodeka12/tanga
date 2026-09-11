# Phase 1 — GroupView chrome measurement

## Goal

Replace the hardcoded `HEADER_HEIGHT = 28` with a `_chromeY()` helper that
measures the panel chrome from the rendered DOM (with fallback constants), and
wire it into the group's `min`/`max`/`preferred` sizing so expanded height =
content + chrome and collapsed height = the title bar's bottom border.

## Files

- Edit: `py/pytanga/viz/templates/views/group-view.js`
- Edit: `dev/src/js-tests/scrollable-stack.test.mjs`

## Steps

- [x] **1.1 — Add `_chromeY()` + fallback constants.**
  - Replace `const HEADER_HEIGHT = 28` with documented `FOLDED_FALLBACK = 38`
    and `CHROME_FALLBACK = 53` (comment derives them from
    `themes/views/group-view.css`: folded = 1 + 8 + (22 + 6 + 1) = 38,
    chrome = 2 + 16 + 29 + 6 = 53).
  - Initialize `this._chromeY = null` in the constructor.
  - Implement `_chromeY()`:
    - Return the cached value if `this._chromeY` is set.
    - If `this._header` is missing or lacks `getBoundingClientRect` (fake DOM),
      return the fallback object (do **not** cache it).
    - Otherwise measure `elRect`/`headerRect`; if the header rect has zero
      height (not yet laid out), return the fallback object.
    - Compute `folded = Math.round(headerRect.bottom - elRect.top)` and
      `chrome = folded + marginBottom(header) + paddingBottom(el) + borderBottomWidth(el)`
      via `getComputedStyle`, round, cache, and return `{ folded, chrome }`.

- [x] **1.2 — Use the measured chrome in sizing.**
  - `_pinCollapsed()` → `Size.px(folded)`.
  - `minSizePx` collapsed → `folded`; expanded → `Math.max(explicit, contentMin + chrome)`.
  - `maxSizePx` collapsed → `folded`.
  - `preferredPx` collapsed → `folded`; expanded → `contentPref + chrome` (or `null`).
  - Rewrite the block comment (lines ~187–192) to describe the measured chrome
    and the "content + small margin" / "bar position" semantics.

- [x] **1.3 — Update existing JS test assertions.**
  - In `scrollable-stack.test.mjs`, change the folded assertions `28` → `38`
    (min/max/`minHeight.value`/`maxHeight.value`, and the `'28px'` CSS
    assertions → `'38px'`), and relax the scrollable min bound `< 50` → `< 60`
    (now `53`). Update the comments to match.

## Validation

```powershell
node --test 'dev/src/js-tests/*.test.mjs'
```

## Notes

- Phase 1 is correct for the theme active at first layout but caches forever;
  Phase 2 adds invalidation so runtime theme changes re-measure.
