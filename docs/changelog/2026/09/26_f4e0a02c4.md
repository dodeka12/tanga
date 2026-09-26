# Changes since version 2.11.0

## New Features
- **Themable `ProgressBarView` control** — a read-only progress indicator with a
  determinate mode (title above + total steps + percent readout) and an animated
  indeterminate mode for "something is running", plus an optional status text
  line below the bar.  It follows the existing control stack (`ProgressBar`
  control, `ProgressBarView` view, JS factory + view, theme CSS) and is updated
  at runtime via `set_progress` / `set_text` / `set_total` /
  `set_indeterminate`.
