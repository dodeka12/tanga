# Phase 6 — Docs & example

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Document the new tokens, the computed-gap sizing contract, the scoped
custom-property instance overrides, the new `GroupView`/`LogView`/
`MarkdownView` options, and the already-existing live-theme-reload behaviour —
with a runnable example a theme author can copy.

## Files

- Edit: `docs/py/viz/ui/custom-themes.md`
- Edit: `docs/py/viz/ui/control-views.md`
- Edit: `docs/py/viz/ui/display-views.md`
- Edit: `docs/dev/architecture/viz-theme-system.md`
- Edit: `py/examples/viz/ui/themes/my_theme/tokens.css`
- Edit: `py/examples/viz/ui/themes/custom_theme_override.py`
- Regenerated: `docs/py/examples/**` (via `tools/generate-example-docs.py`)

## Steps

- [ ] **6.1 — `docs/py/viz/ui/custom-themes.md`: theming spacing & typography**
  - Extend the token table(s) with the phase-1/2 tokens:
    `--tanga-group-title-font-size`, `--tanga-group-body-font-size`,
    `--tanga-group-toggle-font-size`, `--tanga-group-toggle-size`,
    `--tanga-group-header-padding`, `--tanga-group-header-margin-bottom`,
    `--tanga-group-header-gap`, `--tanga-stack-gap`, `--tanga-font-size-log`,
    `--tanga-log-row-padding`, `--tanga-log-row-gap`,
    `--tanga-font-size-markdown`, `--tanga-markdown-table-cell-padding` — each
    with its default and the sheet that consumes it.
  - Add a worked snippet ("denser panels, roomier log"):
    ```css
    :root {
        --tanga-stack-gap: 2px;
        --tanga-group-header-padding: 0 0 4px;
        --tanga-group-header-margin-bottom: 4px;
        --tanga-group-title-font-size: 13px;
        --tanga-group-body-font-size: 12px;
        --tanga-font-size-log: 12px;
        --tanga-log-row-padding: 1px 6px;
    }
    ```
  - State that `--tanga-group-title-font-size` etc. **alias** the type scale, so
    setting `--tanga-font-size-title` / `--tanga-font-size-body` still scales
    everything.
  - Add `### Per-instance overrides` — `GroupView(title_size=…)`,
    `LogView(font_size=…)`, `MarkdownView(font_size=…)`, and explain they set a
    scoped CSS custom property on that view only, so the rest of the UI keeps
    following the theme.
  - Add `### Headerless and static groups` — `GroupView(title=None)` /
    `title=""` (no title text), `show_header=False` (no bar), `collapsible=False`
    (no fold toggle); note `show_header=False` keeps the panel padding/border.
  - Add `### Dense params vs. the theme` — `.tanga-params-dense` wins over the
    theme tokens by specificity, so `ParamsView(dense=True)` stays dense
    regardless of theme; use the tokens for global density, `dense=True` for a
    single view.
  - Add `### Live theme edits` — `register_theme(…)` + `refresh_theme()` +
    `enable_theme_auto_reload()`, noting theme files are served with
    `Cache-Control: no-cache` and swapped links carry `?v=` so an edit lands on
    the next reload.

- [ ] **6.2 — `docs/py/viz/ui/control-views.md`**
  - Update the `GroupView` parameter list: `title: str | None = ""`,
    `show_header: bool = True`, `collapsible: bool = True`,
    `title_size: float | None = None`, and `set_title(str | None)`.
  - Add a `!!! warning` note: an empty/`None` title no longer falls back to
    `"Controls"` — pass an explicit title to keep it.
  - Add `MarkdownView(font_size=…)` to its parameter list.

- [ ] **6.3 — `docs/py/viz/ui/display-views.md`**
  - `LogView(font_size=…)` documented next to `show_date` / `show_utc_offset`,
    including "`None` (default) follows the theme's `--tanga-font-size-log`".

- [ ] **6.4 — `docs/dev/architecture/viz-theme-system.md`** (architecture update)
  - Extend the "Density & typography tokens" list with the new component tokens
    and their consuming sheets; mention that the `compact` theme now overrides
    `--tanga-group-title-font-size`.
  - In "Stable class-name contract", extend the inline-style sentence: computed
    geometry **plus scoped instance custom properties** (decision B) are the
    only inline writes; a per-instance font size never writes a resolved
    `font-size`.
  - Add a paragraph for decision A: `StackView`/`GroupView` read the *computed*
    gap (`_gapPx()` → `stackMinSize`/`stackPreferredSize`) so `--tanga-stack-gap`
    moves the layout and the measured size together; an explicit Python `gap`
    wins.  Note the cache invalidation triggers (`_applyFlex`, `mount`,
    `tanga:themechange`).
  - Update the `GroupView` chrome description: a header exists only when
    `show_header and (collapsible or title or icon)`; `title=None`/`""` render
    no title (no `"Controls"` fallback); `_chromeY()` returns
    `{folded: 0, chrome: <shell>}` when there is no header.

- [ ] **6.5 — Example theme tokens (`my_theme/tokens.css`)**
  - Append a commented block so editing it visibly re-spaces the UI (this is the
    folder `custom_theme_autoreload.py` watches):
    ```css
    /* Spacing & typography — edit + save to see the reload. */
    --tanga-stack-gap: 2px;
    --tanga-group-header-padding: 0 0 4px;
    --tanga-group-header-margin-bottom: 4px;
    --tanga-group-title-font-size: 13px;
    --tanga-group-body-font-size: 12px;
    --tanga-font-size-log: 12px;
    --tanga-log-row-padding: 1px 6px;
    --tanga-markdown-table-cell-padding: 1px 6px;
    ```

- [ ] **6.6 — Example (`py/examples/viz/ui/themes/custom_theme_override.py`)**
  - Give the existing `GroupView("Themes", …)` a `title_size=14`.
  - Add a `MarkdownView("notes", value=…, font_size=14)` inside that group whose
    markdown contains a heading, a bullet list and a 2×2 **table**, so the new
    markdown tokens and table CSS are visible in one pane.
  - Update the module docstring's first line/explanation and the `Keywords:`
    line (3–8 task-oriented terms, e.g.
    `theme, custom theme, tokens, spacing, typography, markdown, table`).
  - Regenerate the example docs:
    ```bash
    uv run python tools/generate-example-docs.py
    ```

## Validation

```bash
uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict
```

## Notes

- `mkdocs build --strict` is the docs gate: a broken relative link or a missing
  nav entry fails it.
- Keep each docs page's existing tone (second person, short code blocks); do not
  restructure `custom-themes.md` beyond adding the new sections.
- The example uses the **built-in** `pastel` theme (it does not call
  `register_theme`); the spacing tokens are demonstrated by
  `my_theme/tokens.css` + `custom_theme_autoreload.py`, not by this example.
