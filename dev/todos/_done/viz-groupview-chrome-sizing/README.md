# Viz GroupView Chrome Sizing — Overview

**Created:** 2026-09-02 | **Status:** Done | **Branch:** `feat/viz-layout-sizing`

## Goal

Make a `GroupView`'s vertical size hints — its collapsed height and its expanded
`min`/`preferred` height — reflect the *actually rendered* title bar and panel
chrome instead of a hardcoded `HEADER_HEIGHT = 28`. After this plan:

- `GroupView.preferredPx('y')` is the content height **plus the panel chrome
  (title bar + padding/border/margins)**, i.e. "content + a small margin" with
  no large gap.
- A collapsed `GroupView` is sized to the **position of the title bar's bottom
  border** (the drawn horizontal rule), so the splitter sits on that line
  rather than on top of the header text.
- Both track the active CSS theme automatically (fonts, paddings, borders),
  because they are measured from the rendered DOM, not constants.

This is a follow-up fix to `dev/todos/viz-layout-sizing` (same feature branch,
which is not yet merged).

## Architecture (short)

Pixel sizing is resolved entirely in the JS frontend: `split-resolver.js` calls
each child's `minSizePx`/`preferredPx`, and the Python backend only serializes
declarative constraints (`Size.px(...)`, `min_height`, …). So the fix lives in
`group-view.js`.

- `_chromeY()` measures the chrome from the DOM once and caches it; fallback
  constants (38 / 53) cover the fake-DOM tests and the pre-layout state.
- The seven `HEADER_HEIGHT` usages are replaced with the measured `{ folded, chrome }`.
- A header `ResizeObserver` + a document `tanga:themechange` event invalidate
  the cache and re-emit `preferredchange`/`constraintschange` so containers
  re-layout.

## Fixed contract (up front)

### `_chromeY()` returns `{ folded, chrome }` (px)

- `folded = round(header.getBoundingClientRect().bottom - el.getBoundingClientRect().top)`
  — the title bar's bottom border position relative to the pane top (the
  collapsed pane height).
- `chrome = folded + marginBottom(header) + paddingBottom(el) + borderBottomWidth(el)`
  — the full vertical chrome above and below the content.
- **Fallback** when DOM measurement is unavailable (`getBoundingClientRect`
  missing, or a zero-height header rect): `FOLDED_FALLBACK = 38`,
  `CHROME_FALLBACK = 53` (derived from `themes/views/group-view.css`; keep a
  derivation comment next to the constants).
- The measured result is cached in `this._chromeYCache`.

### Sizing rules (structure unchanged, values now measured)

- `minSizePx(main axis)` expanded = `max(explicitMin, contentMin + chrome)`.
- `preferredPx(main axis)` expanded = `explicitPreferred ?? (contentPref + chrome)`
  (`null` for a scrollable group).
- Collapsed (min/max/preferred along the main axis) = `folded`.
- `_pinCollapsed()` pins `min = max = Size.px(folded)` on the main axis.

### Invalidation

- A `ResizeObserver` on `this._header` clears `_chromeY` and re-emits when the
  header's **height** changes.
- A `CustomEvent('tanga:themechange')` on `document` (dispatched by `viewer.js`
  after a `theme_define` applies) clears `_chromeY` and re-emits.
- Re-emit = `preferredchange` + `constraintschange` (full size field list).

## Decisions (confirmed)

- Measure from the rendered DOM ("the horizontal bar that is drawn anyway")
  rather than hardcoding or tokenizing; fallback constants only for the
  fake-DOM tests and pre-layout state.
- Continue on branch `feat/viz-layout-sizing` (the unmerged feature this fixes).
- Dispatch the theme-change event from `viewer.js` (co-located with the existing
  `applyThemeBackgrounds` post-theme hook), not from `themes.js`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-groupview-chrome-measurement.md](./01-groupview-chrome-measurement.md) | `_chromeY()` + fallback constants, replace `HEADER_HEIGHT`, update JS tests |
| 2 | [02-theme-invalidation.md](./02-theme-invalidation.md) | Header `ResizeObserver` + `tanga:themechange` invalidation + focused tests |
| 3 | [03-example.md](./03-example.md) | Natural fixed banner in `layout_sizing.py` + regenerate example docs |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Sizing docs + branch changelog + full validation |

## Testing as you go

- **JS:** `node --test 'dev/src/js-tests/*.test.mjs'`
- **Python:** `uv run pytest py/tests/viz/ -q`
- **Docs:** `uv run python tools/generate-example-docs.py --check` and
  `uv run mkdocs build --strict`
- **Browser smoke:** open `dev/src/js-tests/split-view-smoke.html` (and the
  `layout_sizing.py` example) to eyeball the folded/expanded `GroupView`.

## Non-goals

- Fixing the pre-existing horizontal-`GroupView` axis bug (the header is added
  to `x` for `direction="horizontal"`; out of scope here).
- Converting the chrome to CSS custom properties/design tokens (direct
  measurement supersedes it).
- Any Python backend pixel math (there is none to change).
