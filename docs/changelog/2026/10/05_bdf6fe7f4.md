# Changes since version 2.14.0

## New Features
- **Runtime control range** — `SliderView` / `ValueEditView` `set_min` /
  `set_max` / `set_step` / `set_range` and
  `Visualizer.set_control_range(cid, *, min, max, step)` change a slider or
  value-edit's `min` / `max` / `step` after creation, pushed via the
  `control_state` wire message (the current value is clamped into the new
  range).
- **Menu auto-close** — choosing an option in a menu bar / sub-menu (a button
  click or a dropdown change) now closes the menu automatically; checkboxes
  and sliders stay open.
- **Layout reconciliation preserves stateful views** — `log_view`,
  `file_chooser_view`, `table_view`, `progress_bar_view`, and `group` are now
  reused across `set_layout()` re-pushes instead of rebuilt, so their runtime
  registries and content survive.
- **Group collapse round-trip** — `GroupView.on_toggle` / `set_collapsed`
  report and set a group's collapse state through the backend (pushed via
  `control_state`), instead of it being frontend-only.

## Bug Fixes
- **`LogView` stops receiving updates after a re-push** — a `LogView` with a
  stable `id` keeps receiving `.log()` updates after any `set_layout()` re-push
  that reuses its `id`.
- **Offline export fails on Windows** — the offline exporter now runs the
  esbuild launcher through Node.js, so `delivery="offline"` works on Windows
  (previously failed with `WinError 193`).
