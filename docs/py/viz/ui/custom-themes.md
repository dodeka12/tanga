# Custom Themes

Create and load your own viewer theme as plain CSS — a `tokens.css` plus
optional `overrides/*.css` in a local folder — without editing the bundled
`py/pytanga/viz/templates/themes/`.

## Theme folder layout

```text
my_theme/
  tokens.css          # required — :root { --tanga-*: ... } overrides
  overrides/          # optional — full re-styles of one element
    button.css        #   .tanga-action-button { ... }
    checkbox.css      #   .tanga-checkbox-input { ... }
```

## Create a theme

Start from a built-in theme with `copy_theme`:

```python
from pytanga.viz import copy_theme

copy_theme("pastel", "my_theme")
```

This copies `tokens.css` and `overrides/` into `my_theme/`. (`pastel` is the
best starting point — it has a full token sheet plus button/checkbox overrides.)
Edit the files, then load the theme.

## Load and switch to a theme

```python
from pytanga.viz import Visualizer, register_theme

register_theme("corp", "my_theme", label="Corporate")

viz = Visualizer()
viz.set_theme("corp")   # validate + push the theme live
viz.show()
```

You can also select the theme at construction time, before the browser connects:

```python
viz = Visualizer(theme="corp")
```

`VisualizerApp(theme=…)` forwards the same argument.  A single `ParamsView`
can use a local compact density (`ParamsView(dense=True)`) without changing the
global theme.

`register_theme` is global: register once, and the id is available to every
`Visualizer` (and to `list_themes()` / `theme_css_files()`).

## Work interactively with auto-reload

While editing `my_theme/tokens.css` or `my_theme/overrides/*.css`, turn on
auto-reload so each change shows up in the browser without a page reload:

```python
viz.enable_theme_auto_reload()   # poll interval, default 1.0 s
viz.wait()                       # edit files — the viewer refreshes on change
```

It polls the active theme's `tokens.css` + `overrides/*.css` and calls
`refresh_theme()` whenever one changes. Stop it with
`viz.disable_theme_auto_reload()`. To refresh once manually, call
`viz.refresh_theme()`.

## Themed exports

```python
viz.export_snapshot("scene.html", theme="corp")
```

## Themeable tokens

A theme's `tokens.css` overrides any of the CSS custom properties defined in
`base.css` (the single source of truth):

| Group | Tokens |
|-------|--------|
| Palette | `--tanga-bg`, `--tanga-fg`, `--tanga-fg-muted`, `--tanga-fg-strong`, `--tanga-accent`, `--tanga-accent-soft`, `--tanga-danger` |
| Surfaces | `--tanga-panel-bg`, `--tanga-panel-hover`, `--tanga-surface`, `--tanga-surface-strong`, `--tanga-input-bg` |
| Borders | `--tanga-border`, `--tanga-border-strong`, `--tanga-border-subtle` |
| Scrollbar | `--tanga-scrollbar-thumb`, `--tanga-scrollbar-thumb-hover`, `--tanga-scrollbar-track` |
| Elevation | `--tanga-shadow` |
| Typography | `--tanga-font`, `--tanga-font-size-title`, `--tanga-font-size-body`, `--tanga-font-size-label`, `--tanga-font-size-value`, `--tanga-font-size-log`, `--tanga-font-size-markdown` |
| Control chrome | `--tanga-icon-size`, `--tanga-icon-button-icon-size`, `--tanga-control-font-size`, `--tanga-control-padding`, `--tanga-control-label-margin-bottom`, `--tanga-button-font-size`, `--tanga-button-padding`, `--tanga-color-picker-height`, `--tanga-color-picker-padding`, `--tanga-step-button-icon-size` |
| Density | `--tanga-control-min-width`, `--tanga-control-min-height`, `--tanga-icon-control-size`, `--tanga-control-min-width-narrow`, `--tanga-control-margin-y`, `--tanga-range-margin-y`, `--tanga-params-row-gap`, `--tanga-params-key-gap`, `--tanga-params-title-margin`, `--tanga-params-min-width`, `--tanga-stack-gap`, `--tanga-group-nested-title-size` |
| Status/loading | `--tanga-status-ok`, `--tanga-status-err`, `--tanga-loading-bg`, `--tanga-spinner` |
| Warning banner | `--tanga-warning-bg`, `--tanga-warning-fg`, `--tanga-warning-button-bg`, `--tanga-warning-button-fg` |

### Component tokens

The group, log, markdown and control chrome read these component tokens.  The
`group-title` / `body` / `log` / `markdown` font sizes *alias* the type scale,
so setting `--tanga-font-size-title` or `--tanga-font-size-body` still scales
all of them.  Control text also aliases the body size through
`--tanga-control-font-size`, so existing themes keep their current rendering.

| Token | Default | Consumed by |
|-------|---------|-------------|
| `--tanga-icon-size` | `24px` | `base.css` (Material Symbols glyphs; compact lowers this) |
| `--tanga-icon-button-icon-size` | `18px` | `controls/button.css` (icon-only buttons) |
| `--tanga-control-font-size` | `var(--tanga-font-size-body)` | `controls/text-field.css`, `controls/value-edit.css`, `controls/dropdown.css` |
| `--tanga-control-padding` | `4px 6px` | `controls/text-field.css`, `controls/value-edit.css`, `controls/dropdown.css` |
| `--tanga-control-label-margin-bottom` | `2px` | `base.css` (control labels) |
| `--tanga-button-font-size` | `var(--tanga-control-font-size)` | `controls/button.css` |
| `--tanga-button-padding` | `5px 12px` | `controls/button.css` |
| `--tanga-color-picker-height` | `28px` | `controls/color-picker.css` |
| `--tanga-color-picker-padding` | `2px` | `controls/color-picker.css` |
| `--tanga-step-button-icon-size` | `10px` | `controls/value-edit.css` |
| `--tanga-icon-control-size` | `28px` | `base.css` + `controls/button.css` (icon-only button tile) |
| `--tanga-group-padding-base` | `8px 12px` | `views/group-view.css` (all variants) |
| `--tanga-group-title-bg-base` | `transparent` | `views/group-view.css` (all variants) |
| `--tanga-group-header-padding-base` | `0 0 6px` | `views/group-view.css` (all variants) |
| `--tanga-group-header-margin-bottom-base` | `6px` | `views/group-view.css` (all variants) |
| `--tanga-group-header-gap-base` | `6px` | `views/group-view.css` (all variants) |
| `--tanga-group-padding` | `var(--tanga-group-padding-base)` | `views/group-view.css` (default variant) |
| `--tanga-group-title-font-size` | `var(--tanga-font-size-title)` | `views/group-view.css` |
| `--tanga-group-title-bg` | `var(--tanga-group-title-bg-base)` | `views/group-view.css` |
| `--tanga-group-title-padding` | `0` | `views/group-view.css` |
| `--tanga-group-title-radius` | `0` | `views/group-view.css` |
| `--tanga-group-body-font-size` | `var(--tanga-font-size-body)` | `views/group-view.css` |
| `--tanga-group-toggle-font-size` | `14px` | `views/group-view.css` |
| `--tanga-group-toggle-size` | `22px` | `views/group-view.css` |
| `--tanga-group-header-padding` | `var(--tanga-group-header-padding-base)` | `views/group-view.css` |
| `--tanga-group-header-margin-bottom` | `var(--tanga-group-header-margin-bottom-base)` | `views/group-view.css` |
| `--tanga-group-header-gap` | `var(--tanga-group-header-gap-base)` | `views/group-view.css` |
| `--tanga-stack-gap` | `4px` | `views/stack-view.js` + stack size maths |
| `--tanga-font-size-log` | `var(--tanga-font-size-body)` | `views/message-view.css` |
| `--tanga-log-row-padding` | `3px 8px` | `views/message-view.css` |
| `--tanga-log-row-gap` | `8px` | `views/message-view.css` |
| `--tanga-font-size-markdown` | `var(--tanga-font-size-body)` | `views/markdown-view.css` |
| `--tanga-markdown-table-cell-padding` | `2px 8px` | `views/markdown-view.css` |

The `*-base` tokens are the **all-variants** knobs: setting
`--tanga-group-padding-base`, `--tanga-group-title-bg-base` or
`--tanga-group-header-*-base` moves the default, `small` and `tiny` groups at
once.  The `small` / `tiny` knobs move one level only.  The plain
`--tanga-group-*` tokens are the default-variant consumers, so a theme that sets
only `--tanga-group-padding` changes top-level groups and leaves nested ones
alone.

| Token | `small` default | `tiny` default |
|-------|-----------------|----------------|
| `--tanga-group-{small,tiny}-padding` | `var(--tanga-group-padding-base)` | `var(--tanga-group-padding-base)` |
| `--tanga-group-{small,tiny}-title-font-size` | `var(--tanga-group-nested-title-size)` (13 px) | `var(--tanga-font-size-label)` (12 px) |
| `--tanga-group-{small,tiny}-title-bg` | `var(--tanga-group-title-bg-base)` | `var(--tanga-group-title-bg-base)` |
| `--tanga-group-{small,tiny}-header-padding` | `var(--tanga-group-header-padding-base)` | `var(--tanga-group-header-padding-base)` |
| `--tanga-group-{small,tiny}-header-margin-bottom` | `var(--tanga-group-header-margin-bottom-base)` | `var(--tanga-group-header-margin-bottom-base)` |
| `--tanga-group-{small,tiny}-header-gap` | `var(--tanga-group-header-gap-base)` | `var(--tanga-group-header-gap-base)` |

The variants default to today's rendering, except `tiny`, whose title is one
step smaller than `small`.  `--tanga-group-nested-title-size` is the deprecated
alias that feeds `--tanga-group-small-title-font-size`; it no longer styles
`.tanga-group-title` directly.

### Worked example: denser panels, roomier log

```css
:root {
    --tanga-stack-gap: 2px;
    --tanga-group-padding-base: 6px 8px;
    --tanga-group-header-padding-base: 0 0 4px;
    --tanga-group-header-margin-bottom-base: 4px;
    --tanga-group-title-font-size: 13px;
    --tanga-group-title-bg-base: var(--tanga-surface);
    --tanga-group-title-padding: 1px 6px;
    --tanga-group-title-radius: 3px;
    --tanga-group-small-padding: 4px 6px;
    --tanga-group-small-title-font-size: 12px;
    --tanga-group-tiny-padding: 3px 5px;
    --tanga-group-tiny-title-font-size: 11px;
    --tanga-group-body-font-size: 12px;
    --tanga-font-size-log: 12px;
    --tanga-log-row-padding: 1px 6px;
}
```

The title background is painted on the title **text** (`.tanga-group-title`), so
pair it with `--tanga-group-title-padding` / `--tanga-group-title-radius` to get
a chip.  A full-width header background is not a token.

### Worked example: denser controls

```css
:root {
    --tanga-control-font-size: 11px;
    --tanga-control-padding: 2px 4px;
    --tanga-control-label-margin-bottom: 1px;
    --tanga-button-padding: 2px 8px;
    --tanga-icon-size: 14px;
    --tanga-icon-button-icon-size: 14px;
    --tanga-icon-control-size: 22px;
    --tanga-color-picker-height: 20px;
    --tanga-step-button-icon-size: 8px;
}
```

`--tanga-button-font-size` defaults to `--tanga-control-font-size`, so the
button text follows the control font unless a theme opts out.  The compact theme
sets these values out of the box, which is what makes its text fields, value
edits, dropdowns, color pickers and buttons shorter.

### Group variants

`GroupView(variant=…)` selects a presentational size variant — `default`,
`small` or `tiny`:

```python
from pytanga.viz import EGroupVariant, GroupView

GroupView("Small panel", […], variant=EGroupVariant.SMALL)
GroupView("Tiny panel", […], variant="tiny")   # strings are accepted too
```

The variants are applied as the classes `tanga-group-small` and
`tanga-group-tiny`; `tanga-group-nested` remains as a deprecated alias for
`small`.  A variant only re-scopes `--tanga-group-*` tokens; it does not change
layout semantics.

`ParamsView` styles its field groups as `small` at depth 0 and `tiny` deeper.
A bare `ParamsView` has no group chrome of its own, so wrap it in a
`GroupView(variant=…)` for the top-level panel.  The space **around** a group is
the parent's gap (`--tanga-stack-gap` in a stack, `--tanga-params-row-gap` in a
`ParamsView`); the space **inside** it is `--tanga-group-padding`.  There is no
group margin token.

### Per-instance overrides

`GroupView(title_size=…)`, `LogView(font_size=…)` and
`MarkdownView(font_size=…)` override one instance.  They set a scoped CSS custom
property on that view only, so the rest of the UI keeps following the theme.

```python
GroupView("Fine print", […], title_size=12)
LogView("log", font_size=12)
MarkdownView("notes", value="# Notes", font_size=14)
```

### Headerless and static groups

`GroupView(title=None)` and `GroupView(title="")` render no title text (there is
no implicit `"Controls"` fallback).  `show_header=False` removes the whole
header bar, and `collapsible=False` renders a static group without a fold
toggle.  A headerless group keeps the panel padding/border; a collapsible header
folds when any part of the bar is clicked.

### Dense params vs. the theme

`.tanga-params-dense` wins over the theme tokens by CSS specificity, so
`ParamsView(dense=True)` stays dense regardless of theme.  Use the tokens for
global density and `dense=True` for a single view.

### Live theme edits

`register_theme(…)` + `refresh_theme()` + `enable_theme_auto_reload()` work
together while you edit a theme.  Theme files are served with
`Cache-Control: no-cache`, and swapped stylesheet links carry a `?v=` version,
so an edit lands on the next reload (or immediately with auto-reload).

## Override targets

`overrides/*.css` targets the stable semantic class names:

- `.tanga-action-button` — buttons.
- `.tanga-checkbox-input` — checkboxes.
- `.tanga-range-input` — sliders.
- `.tanga-select-input` — dropdowns.
- `.tanga-text-input` — text fields.
- `.tanga-value-input`, `.tanga-step-button` — value edit (stepper).
- `.tanga-color-input` — color picker.
- `.tanga-group`, `.tanga-group-header`, `.tanga-group-title`, `.tanga-group-toggle` — control groups.
- `.tanga-menu-trigger` — menus.
- `.tanga-banner`, `.tanga-banner-close` — banners.
- `.tanga-dialog`, `.tanga-dialog-title` — dialogs.
- `.tanga-title-overlay` — viewport title.
- `.tanga-warning-banner` — warning banners.