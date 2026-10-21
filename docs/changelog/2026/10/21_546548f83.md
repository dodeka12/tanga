# Changes since version 2.21.1 (2.22.0-rc2)

## New Features

- **Compact control theme** — a built-in `"compact"` theme
  (`viz.set_theme("compact")`) is a dark-based density variant: smaller control
  fonts, tighter vertical spacing for checkboxes and sliders, and a stacked,
  borderless numeric stepper.  Control density and typography are now fully
  theme-able via the new `--tanga-control-*` and `--tanga-font-size-*` tokens.
- **`ParamsView`** — a composite view that renders a `dict` or `@dataclass` as a
  two-column table of controls (key/title left, control right).  Per-field UI is
  described by a `ControlUI` spec (`SliderUI`, `CheckboxUI`, …) via the
  `param_ui()` helper or raw `field(metadata={"param_ui": …})`; a single
  `on_change` receives the full state on every change.

## Breaking Changes

- **Control-view size floors moved to the theme.**  `ControlView` (and every
  concrete control view) no longer defaults to `min_width=Size.px(120)` /
  `min_height=Size.px(32)` — these are now `None`, and the on-screen floor comes
  from the theme's `--tanga-control-min-width` / `--tanga-control-min-height`
  tokens (unchanged defaults, 28 px for icon-only buttons).  Code that read
  `view.min_width` / `view.min_height` expecting the old default now sees `None`.

## Refactor

- **Font sizes tokenized.**  Control font sizes (labels, values, buttons, inputs,
  checkboxes, steppers, progress bars) now reference `--tanga-font-size-*`
  tokens instead of hardcoded px, and the vertical control / slider margins
  reference `--tanga-control-margin-y` / `--tanga-range-margin-y`.
- **`ParamsView` fully themed + sensible sizing.**  The params-view grid spacing
  and its minimum width are tokenized (`--tanga-params-row-gap` /
  `--tanga-params-key-gap` / `--tanga-params-title-margin` /
  `--tanga-params-min-width`); the view stretches to its container and sizes its
  height from the measured rows.
