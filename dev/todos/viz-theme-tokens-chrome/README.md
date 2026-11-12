# Viz theme tokens & group chrome — Overview

**Created:** 2026-11-11 | **Status:** Done | **Branch:** `feat/theme-tokens-chrome`

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
5. `GroupView` gets a styling `variant` (`EGroupVariant`: `default` / `small` /
   `tiny`) with per-variant tokens for panel padding, title font size,
   title background and header spacing; `ParamsView` assigns `small` to the
   groups it creates for its fields and `tiny` to deeper ones, and
   `GroupUI(variant=…)` overrides that per field;
6. clicking anywhere on a collapsible group's header folds/unfolds it, and a
   `ParamsView` row's key label carries its control's tooltip;
7. the `all_controls` example gains a `ParamsView` (with a nested sub-group) and
   a Dark/Compact theme menu, and the `compact` theme overrides every new token;
8. user + developer docs, a worked spacing example, tests and a changelog.

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
- The group title has no background and a hardcoded `14px` size
  (`group-view.css:51-55`); the panel padding is hardcoded (`:7`), and the only
  top-vs-nested distinction is the `.tanga-group-nested` class that
  `params-view.js:57` adds after the fact.  There is no sibling/child level
  token split today.
- `ParamsView._build_group()` (`params_view.py:230`) is the **only** framework
  construction of a `GroupView`; a top-level `ParamsView` does not wrap itself
  in one (the outer panel is user code).  That makes the sub-group variant a
  pure `ParamsView` decision.
- `group-view.js` only folds via the toggle button (`:110-114`); the header has
  no click handler, so clicking the title does nothing.
- `ParamsView` rows render the key label as a **sibling** of the control
  (`params-view.js:59-62`) and value rows set `hide_label=True`, so the
  control's tooltip never reaches the row title.
- `all_controls.py` contains no `ParamsView` and no theme switcher;
  `compact` is the existing dense theme and `Visualizer.set_theme()` /
  `list_themes()` already exist.

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
- **(C) Group variants are a model-level string enum, applied as a CSS class.**
  `EGroupVariant` (`default`/`small`/`tiny`) is construction-time state on
  `GroupView`; the frontend adds `tanga-group-<variant>`, and `group-view.css`
  re-scopes the **generic** consumer properties (`--tanga-group-padding`,
  `--tanga-group-title-font-size`, `--tanga-group-title-bg`,
  `--tanga-group-header-*`) to the matching variant knobs.  Consumers never
  branch on the variant.  `ParamsView` picks `small` for the groups it creates
  at depth 0 and `tiny` at depth ≥ 1; `GroupUI.variant` overrides per field.
  `.tanga-group-nested` stays as a deprecated alias for `variant="small"`.
- **Header click-to-fold is interaction, not chrome.**  The header click handler
  delegates to the existing `setCollapsed()` (so pin/restore, constraints and
  `control:group_toggle` stay in one place) and ignores clicks on the fold
  toggle or any interactive child.
- Group chrome is created/removed by the view itself
  (`_ensureHeader()` / `_teardownHeader()`), so `show_header` / `collapsible`
  also work when `build.js` reuses a live view by id.

### Fixed contract (do not change across phases)

1. **`group` node serialization** always emits `title` (`string | null`),
   `show_header`, `collapsible`; emits `title_size` and `variant` only when set
   (i.e. `variant` is omitted for the default):

   ```json
   { "type": "group", "title": "Controls", "show_header": true,
     "collapsible": true, "collapsed": false, "title_size": 15.0,
     "variant": "small" }
   ```

2. **`control_state`** keeps its shape; `title` may be `null` to clear the
   title text.  No new keys — `show_header` / `collapsible` / `title_size` /
   `variant` are construction-time.
3. **`log` / `markdown` nodes** gain `font_size` only when set; the `markdown`
   *control* payload mirrors `Label`: `{ "value": …, "font_size": 16.0 }`.
4. **Python API**
   - `GroupView(title: str | None = "", *, show_header: bool = True,
     collapsible: bool = True, title_size: float | None = None,
     variant: EGroupVariant | str = EGroupVariant.DEFAULT, …)`.
   - `EGroupVariant(StrEnum)` lives in `views/_enums.py` with
     `DEFAULT = "default"`, `SMALL = "small"`, `TINY = "tiny"`; it is exported
     from `pytanga.viz` next to `EStackDirection` / `EStackAlign`.  A plain
     string is accepted and normalised; an unknown value raises `ValueError`.
   - `GroupView.set_title(title: str | None)`; `set_collapsed()` raises
     `ValueError` when `collapsible=False`; `collapsed=True` with
     `collapsible=False` or `show_header=False` raises `ValueError`.
   - `show_header=False` normalises `collapsible` to `False`.
   - `GroupUI(variant: EGroupVariant | str | None = None)`; when `None`, the
     owning `ParamsView` picks `SMALL` for a depth-0 field group and `TINY` for
     a deeper one.
   - `LogView(text, *, font_size: float | None = None, …)`.
   - `MarkdownView(markdown, *, font_size: float | None = None, …)` →
     `Markdown(font_size=…)`.
5. **Header semantics** — header rendered iff
   `show_header and (collapsible or title or icon)`.  `title=None` **and**
   `title=""` render no title text (the `'Controls'` fallback is removed —
   breaking).  `show_header=False` keeps the group's own panel padding/border
   and drops only the header block (padding/margin/border).  When
   `collapsible=True`, a click anywhere on the header (except the fold toggle
   or another interactive child) toggles the group; a static or disabled group
   ignores header clicks.
6. **CSS tokens** (declared in `base.css`; variant knobs are consumed only by
   the re-scope rules in `group-view.css`):

   ```
   /* shared defaults — a theme sets these to move every variant at once */
   --tanga-group-padding-base: 8px 12px;
   --tanga-group-title-bg-base: transparent;
   --tanga-group-header-padding-base: 0 0 6px;
   --tanga-group-header-margin-bottom-base: 6px;
   --tanga-group-header-gap-base: 6px;

   /* default (top-level) consumer tokens */
   --tanga-group-padding: var(--tanga-group-padding-base);
   --tanga-group-title-font-size: var(--tanga-font-size-title);
   --tanga-group-title-bg: var(--tanga-group-title-bg-base);
   --tanga-group-title-padding: 0;
   --tanga-group-title-radius: 0;
   --tanga-group-body-font-size: var(--tanga-font-size-body);
   --tanga-group-toggle-font-size: 14px;
   --tanga-group-toggle-size: 22px;
   --tanga-group-header-padding: var(--tanga-group-header-padding-base);
   --tanga-group-header-margin-bottom: var(--tanga-group-header-margin-bottom-base);
   --tanga-group-header-gap: var(--tanga-group-header-gap-base);

   /* variant="small" (ParamsView depth 0 sub-groups) */
   --tanga-group-small-padding: var(--tanga-group-padding-base);
   --tanga-group-small-title-font-size: var(--tanga-group-nested-title-size);
   --tanga-group-small-title-bg: var(--tanga-group-title-bg-base);
   --tanga-group-small-header-padding: var(--tanga-group-header-padding-base);
   --tanga-group-small-header-margin-bottom: var(--tanga-group-header-margin-bottom-base);
   --tanga-group-small-header-gap: var(--tanga-group-header-gap-base);

   /* variant="tiny" (ParamsView depth >= 1 sub-groups) */
   --tanga-group-tiny-padding: var(--tanga-group-padding-base);
   --tanga-group-tiny-title-font-size: var(--tanga-font-size-label);
   --tanga-group-tiny-title-bg: var(--tanga-group-title-bg-base);
   --tanga-group-tiny-header-padding: var(--tanga-group-header-padding-base);
   --tanga-group-tiny-header-margin-bottom: var(--tanga-group-header-margin-bottom-base);
   --tanga-group-tiny-header-gap: var(--tanga-group-header-gap-base);

   /* log / markdown */
   --tanga-font-size-log: var(--tanga-font-size-body);
   --tanga-log-row-padding: 3px 8px;
   --tanga-log-row-gap: 8px;
   --tanga-font-size-markdown: var(--tanga-font-size-body);
   --tanga-markdown-table-cell-padding: 2px 8px;
   --tanga-stack-gap: 4px;
   ```

   The `*-base` tokens are the **all-variants** knobs; each variant token
   defaults to its base, so a theme can move every group with one declaration
   or one level with a variant token.  The plain `--tanga-group-*` consumers
   keep working and target the default variant.  The variant defaults reproduce
   today's rendering (except `tiny`, which is one step smaller than `small`);
   the `compact` theme tightens them.
   `--tanga-group-nested-title-size` stays declared and feeds
   `--tanga-group-small-title-font-size`, so existing theme overrides keep
   working.  There is deliberately **no per-variant gap/margin token**: the
   space *around* a group is its parent's gap (`--tanga-stack-gap` /
   `--tanga-params-row-gap`), and the space *inside* it is
   `--tanga-group-padding`; a CSS `margin` would not be read by the size maths.

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
- `show_header` / `collapsible` / `title_size` / `variant` / `font_size` are
  construction-time only; only `title` keeps a runtime setter.
- **Nested `ParamsView` groups are styled through `EGroupVariant`**, not new
  layout fields: `GroupUI` gains only `variant`, `ParamsView` assigns `SMALL`
  at depth 0 and `TINY` deeper, and `GroupUI.variant` overrides that per field.
  The variant changes appearance only — padding, title font/background and
  header spacing — never layout semantics.
- **`*-base` tokens are the all-variants knobs.**  Each variant knob defaults to
  its shared base (`--tanga-group-small-padding:
  var(--tanga-group-padding-base)`, …), so a theme changes every group level
  with one declaration or one level with a variant token.  The plain
  `--tanga-group-*` consumers target the default variant.
- **Theme tokens only for the title surface.**  There is no per-instance
  `title_bg` / padding API; `title_size` stays the only per-instance title
  override.  The title background targets the `.tanga-group-title` **span**
  (a chip around the text, with `--tanga-group-title-padding` /
  `--tanga-group-title-radius`); a full-width header bar is out of scope.
- **No CSS `margin` on `.tanga-group`.**  Space around a panel comes from the
  parent stack/params gap; `--tanga-group-padding` is the space inside the
  panel.  `_chromeY()` / `_measureHeight()` never read margins, so adding one
  would desync the size maths.
- `.tanga-group-nested` is retained for one release as a deprecated alias for
  `variant="small"` (the frontend toggles it; `params-view.js` no longer owns
  it), and `--tanga-group-nested-title-size` is the alias that feeds
  `--tanga-group-small-title-font-size`.
- The theme menu in `all_controls.py` is an **example-level** picker over the
  existing `Visualizer.set_theme()`; no framework theme-picker widget is added.
- `LabelView.font_size` keeps its current inline `font-size` — out of scope.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-typography-tokens.md](./01-typography-tokens.md) | Typography + title-surface tokens in `base.css`, variant re-scope rules, compact-theme overrides, token tests |
| 2 | [02-spacing-tokens-gap-math.md](./02-spacing-tokens-gap-math.md) | Group padding + header-spacing tokens (default/small/tiny), inline header styling removed, `resolveGapPx` + `_gapPx()` fed into the size maths, JS unit tests |
| 3 | [03-group-view-options-python.md](./03-group-view-options-python.md) | `title: str \| None`, `show_header`, `collapsible`, `title_size`, `EGroupVariant` + `variant`, `GroupUI.variant`, `ParamsView` depth defaults, validation, serialization + Python tests |
| 4 | [04-group-chrome-frontend.md](./04-group-chrome-frontend.md) | Header create/teardown, variant class, header click-to-fold, title rendering without fallback, `_chromeY` no-header branch, guards, `build.js`, `ParamsView` row-title tooltips |
| 5 | [05-instance-font-sizes.md](./05-instance-font-sizes.md) | `LogView(font_size=…)`, `MarkdownView`/`Markdown.font_size`, scoped-property overrides |
| 6 | [06-docs-example.md](./06-docs-example.md) | User docs (spacing, tokens, variants, caching), architecture docs, `all_controls` ParamsView + theme menu, regenerated example docs |
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

- No `*-dense` token split and no change to `ParamsView(dense=True)` values;
  `compact` only overrides the new tokens.
- No new `GroupUI` fields beyond `variant`, and no `LabelView` / `Label`
  changes.
- No runtime setters for `show_header` / `collapsible` / `title_size` /
  `variant` / `font_size`.
- No numeric "nesting level" API and no layout/behaviour change from
  `variant` — it is a presentational string enum.
- No per-instance title background/padding kwargs and no CSS `margin` on
  `.tanga-group`; group chrome is themed through tokens only.
- No markdown typography scale beyond font size and table cells (headings stay
  `em`-relative).
- No new theme files and no framework theme-picker widget (the `all_controls`
  menu is an example over the existing `set_theme()`), no CSS
  preprocessor/bundler.
