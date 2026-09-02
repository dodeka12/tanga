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
| Typography | `--tanga-font` |
| Status/loading | `--tanga-status-ok`, `--tanga-status-err`, `--tanga-loading-bg`, `--tanga-spinner` |
| Warning banner | `--tanga-warning-bg`, `--tanga-warning-fg`, `--tanga-warning-button-bg`, `--tanga-warning-button-fg` |

## Override targets

`overrides/*.css` targets the stable semantic class names:

- `.tanga-action-button` — buttons.
- `.tanga-checkbox-input` — checkboxes.
- `.tanga-range-input` — sliders.
- `.tanga-select-input` — dropdowns.
- `.tanga-group`, `.tanga-group-header`, `.tanga-group-title`, `.tanga-group-toggle` — control groups.
- `.tanga-menu-trigger` — menus.
- `.tanga-banner`, `.tanga-banner-close` — banners.
- `.tanga-dialog`, `.tanga-dialog-title` — dialogs.
- `.tanga-title-overlay` — viewport title.
- `.tanga-warning-banner` — warning banners.