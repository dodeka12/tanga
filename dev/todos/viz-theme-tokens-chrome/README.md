# Viz theme tokens & group chrome — Overview

**Created:** 2026-11-11 | **Status:** Planned | **Branch:** `feat/theme-tokens-chrome`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Ship the consumer request in `_input/pytanga-theming-fonts-spacing-titles.md`:

1. every hardcoded font size in group / log / markdown chrome becomes a
   theme-able token (and a dead `--tanga-font-size-title` becomes live);
2. every spacing knob a theme is expected to reach becomes a token — including
   the stack gap, which the JS size maths must **read back** so CSS stays the
   single source of truth;
3. `GroupView` can drop its title and its whole header bar
   (`title=None`/`""`, `show_header=…`, `collapsible=…`);
4. per-instance `font_size` / `title_size` overrides for `LogView`,
   `MarkdownView` and `GroupView`;
5. user + developer docs, a worked spacing example, tests and a changelog.

## Background (verified 2026-11-11)

- `themes/views/group-view.css` hardcodes every group font size and the header
  spacing (`:9`, `:24`, `:40-41`, `:53`, `:71`, `:78-80`).
- `--tanga-font-size-title` (`base.css:75`) is **dead**: only
  `compact/tokens.css:17` sets it, so the `compact` theme's title override has
  no effect.
- `group-view.js` also writes the header `marginBottom`/`gap` **inline**, so
  those values cannot be themed at all.
- `stack-view.js:50` bakes the default gap (`GAP = 4`) into inline CSS, and
  `minSizePx`/`preferredPx` (`stack-view.js:113/122`, and `GroupView`'s
  overrides) never pass `this.gap` to `stackMinSize`/`stackPreferredSize` —
  those functions already accept a `gap` argument, so an explicit `gap=` is
  already measured wrong today.
- `group-view.js:147` renders `this.title || 'Controls'`; `GroupView` has no
  `collapsible` / `show_header` option (the word only appears in prose docs).
- `themes/views/markdown-view.css` has **no table rules at all**.
- Theme reload already works: `themes.js:29` appends `?v=`, the server sends
  `Cache-Control: no-cache` for theme files (`server.py:966/1013`), and
  `Visualizer.refresh_theme()` / `enable_theme_auto_reload()` exist
  (`visualizer.py:469-483`).  That part is a **docs** gap only.

## Architecture (short)

- All look & feel stays in `templates/themes/`: new tokens are declared once in
  `base.css :root` (aliasing the existing type scale) and consumed by exactly
  one component sheet, which references `var(--tanga-*)` only.
- **(A) Size maths reads the computed gap.**  `StackView` gains `_gapPx()`: an
  explicit Python `gap` wins; otherwise the *computed* `gap` of the flex
  container (which is `var(--tanga-stack-gap)`) is read and passed into
  `stackMinSize` / `stackPreferredSize` from `StackView` **and** `GroupView`.
  This extends the documented pattern where `ControlView.minSizePx` reads the
  computed CSS floor; `params-view.js::_cssPx` uses the same technique.
- **(B) Instance overrides are scoped inline custom properties**
  (`el.style.setProperty('--tanga-font-size-log', …)`), documented as the third
  permitted inline category next to computed geometry — only the scoped custom
  property is inline, never a resolved appearance property.
- Group chrome is created/removed by the view itself
  (`_ensureHeader()` / `_teardownHeader()`), so `show_header` / `collapsible`
  also work when `build.js` reuses a live view by id.

### Fixed contract (do not change across phases)

1. **`group` node serialization** always emits `title` (`string | null`),
   `show_header`, `collapsible`; emits `title_size` only when set:

   ```json
   { "type": "group", "title": "Controls", "show_header": true,
     "collapsible": true, "collapsed": false, "title_size": 15.0 }
   ```

2. **`control_state`** keeps its shape; `title` may be `null` to clear the
   title text.  No new keys — `show_header` / `collapsible` / `title_size` are
   construction-time.
3. **`log` / `markdown` nodes** gain `font_size` only when set; the `markdown`
   *control* payload mirrors `Label`: `{ "value": …, "font_size": 16.0 }`.
4. **Python API**
   - `GroupView(title: str | None = "", *, show_header: bool = True,
     collapsible: bool = True, title_size: float | None = None, …)`.
   - `GroupView.set_title(title: str | None)`; `set_collapsed()` raises
     `ValueError` when `collapsible=False`; `collapsed=True` with
     `collapsible=False` or `show_header=False` raises `ValueError`.
   - `show_header=False` normalises `collapsible` to `False`.
   - `LogView(text, *, font_size: float | None = None, …)`.
   - `MarkdownView(markdown, *, font_size: float | None = None, …)` →
     `Markdown(font_size=…)`.
5. **Header semantics** — header rendered iff
   `show_header and (collapsible or title or icon)`.  `title=None` **and**
   `title=""` render no title text (the `'Controls'` fallback is removed —
   breaking).  `show_header=False` keeps the group's own panel padding/border
   and drops only the header block (padding/margin/border).
6. **CSS tokens** (declared in `base.css`):

   ```
   --tanga-group-title-font-size: var(--tanga-font-size-title);
   --tanga-group-body-font-size: var(--tanga-font-size-body);
   --tanga-group-toggle-font-size: 14px;
   --tanga-group-toggle-size: 22px;
   --tanga-group-header-padding: 0 0 6px;
   --tanga-group-header-margin-bottom: 6px;
   --tanga-group-header-gap: 6px;
   --tanga-font-size-log: var(--tanga-font-size-body);
   --tanga-log-row-padding: 3px 8px;
   --tanga-log-row-gap: 8px;
   --tanga-font-size-markdown: var(--tanga-font-size-body);
   --tanga-markdown-table-cell-padding: 2px 8px;
   --tanga-stack-gap: 4px;
   ```

7. **JS helper** — `export function resolveGapPx(value, fallback = GAP)` in
   `views/stack-size.js`: numbers pass through; `"12px"` → `12`;
   `"normal"` / `""` / `null` / unparsable → `fallback`.

## Decisions (confirmed)

- **Issue-faithful titles:** `title=None` *and* `title=""` render no title; the
  implicit `'Controls'` label is removed (breaking → changelog).  No in-repo
  call site relies on it (93 `GroupView(` sites, all with an explicit title;
  nested `ParamsView` groups always derive one).
- **(A) confirmed:** size maths reads the computed gap.
- **(B) confirmed:** instance overrides are scoped inline custom properties.
- `params-dense` precedence is **documented**, not re-tokenised (no `*-dense`
  tokens in this plan).
- `show_header` / `collapsible` / `title_size` / `font_size` are
  construction-time only; only `title` keeps a runtime setter.
- Nested `ParamsView` groups are untouched (`GroupUI` gains no fields).
- `LabelView.font_size` keeps its current inline `font-size` — out of scope.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-typography-tokens.md](./01-typography-tokens.md) | Typography tokens in `base.css`, consumed by the group/log/markdown sheets, compact-theme fix, token tests |
| 2 | [02-spacing-tokens-gap-math.md](./02-spacing-tokens-gap-math.md) | Spacing tokens, inline header styling removed, `resolveGapPx` + `_gapPx()` fed into the size maths, JS unit tests |
| 3 | [03-group-view-options-python.md](./03-group-view-options-python.md) | `title: str \| None`, `show_header`, `collapsible`, `title_size`, validation, serialization + Python tests |
| 4 | [04-group-chrome-frontend.md](./04-group-chrome-frontend.md) | Header create/teardown, title rendering without fallback, `_chromeY` no-header branch, guards, `build.js` |
| 5 | [05-instance-font-sizes.md](./05-instance-font-sizes.md) | `LogView(font_size=…)`, `MarkdownView`/`Markdown.font_size`, scoped-property overrides |
| 6 | [06-docs-example.md](./06-docs-example.md) | User docs (spacing, tokens, caching), architecture docs, example + regenerated example docs |
| 7 | [07-changelog-pr.md](./07-changelog-pr.md) | Branch changelog, PR prep, full validation sweep |

## Testing as you go

```bash
uv run pytest py/tests/viz -q
cd js/dev && npm run check && node --test tests/*.test.mjs
uv run mkdocs build --strict                        # from phase 6
uv run python tools/generate-example-docs.py        # after phase 6 example edits
uv run python tools/build-viewer-js.py --check      # phase 7 (expect no diff)
```

> The live frontend (`templates/views/`, `templates/viewer.js`) is served as ES
> modules and is **not** part of the export bundle `js/tanga-viewer.js`, so
> these edits create no bundle drift (re-verified in phase 7).

## Non-goals

- No `*-dense` token split and no change to `ParamsView(dense=True)` values.
- No new Python fields on `GroupUI`, no `LabelView` / `Label` changes.
- No runtime setters for `show_header` / `collapsible` / `title_size` /
  `font_size`.
- No markdown typography scale beyond font size and table cells (headings stay
  `em`-relative).
- No new theme files, no theme picker, no CSS preprocessor/bundler.
