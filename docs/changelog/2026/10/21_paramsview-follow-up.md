# Changes since version 2.22.0 (2.23.0-rc2)

## New Features

- **Button captions + full-width rows** — `ButtonUI(label=…)` gives a button its
  own caption, and `ControlUI.full_width` renders a row without a key column
  (default on `ButtonUI`/`MarkdownUI`/`ProgressBarUI`), so button/status rows
  span the full panel width.
- **Nested groups share the panel handler** — a nested-group field change fires
  the parent `on_change` with the full state and a dotted `event.key`
  (`"surface.scale"`).
- **Dotted row API** — `set_value`/`set_visible`/`set_enabled`/`set_title`/
  `set_options` accept dotted keys, and `set_state` rebinds nested groups
  recursively.
- **Group row state** — `GroupView` gains `visible`/`enabled`/`title` and
  `set_visible`/`set_enabled`/`set_title`; disabling a group greys its header,
  collapses it, and locks the fold toggle.
- **Nested `extra_rows`** — `GroupUI(extra_rows=[RowSpec(…)])` adds button/status
  rows inside a nested group.
