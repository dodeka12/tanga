# Changes since version 2.26.1

## New Features
- **Themeable spacing and typography tokens** — group header spacing, stack
  gap, log rows, markdown tables, panel padding and the title background are now
  driven by `--tanga-*` tokens declared in `base.css`.
- **Group styling variants** — `GroupView(variant=…)` accepts the new
  `EGroupVariant` (`default` / `small` / `tiny`); `ParamsView` styles its field
  groups as `small` (depth 0) or `tiny` (deeper) and `GroupUI(variant=…)`
  overrides one field.  Per-variant tokens control padding, title font
  size/background and header spacing.
- **GroupView header control** — `show_header=`, `collapsible=` and
  `title_size=` let a group drop its bar, become static, or re-size its title.
- **Click-to-fold group headers** — clicking anywhere on a collapsible group's
  header (except the toggle) folds/unfolds it.
- **Per-instance font sizes** — `LogView(font_size=…)` and
  `MarkdownView(font_size=…)` override the theme for one pane.
- **Markdown tables are styled** — markdown tables now get borders, padding and
  a header background from the theme.
- **Expanded `all_controls` demo** — a `ParamsView` with a nested sub-group and
  a Dark/Compact theme menu.
- **Themeable control chrome** — text fields, value edits, dropdowns, color
  pickers and buttons now take their font size, inner padding, height and icon
  size from `--tanga-*` tokens.  The `compact` theme uses shorter values, so its
  controls are visibly less tall.

## Breaking Changes
- **`GroupView` no longer defaults the title to `"Controls"`** — a `title` of
  `None` or `""` renders no title; pass an explicit title to keep the old look.

## Bug Fixes
- **Menu option rows are fully clickable** — clicking the blank part of a
  button or checkbox option row now activates it instead of requiring a click
  on the label text; sliders keep their own track as the drag target.
- **`ParamsView` row titles show the control tooltip** — the key label is a
  sibling of the control, so it previously never received it.
- **`compact` theme title override now applies** — it set a token nothing
  consumed; the theme now also overrides the `small`/`tiny` variants.
- **`StackView`/`GroupView` measure an explicit `gap`** — the gap was never
  passed into the size arithmetic, so a non-default `gap` measured wrong.
- **Material Symbols now follow `--tanga-icon-size`** — the Google Material
  Symbols stylesheet's `24px` rule was overriding the base rule with equal
  specificity, so compact buttons stayed tall.  The base selector now outranks
  it, and the compact theme lowers the token to `14px`.
- **Group fold arrow now folds the group** — clicking the icon at the right of
  a group header toggled the group twice and left it unchanged; the header now
  resolves the toggle from the event path after the icon node is redrawn.

## Refactor
- **Group header appearance moved out of JS** — `margin-bottom` / `gap` are no
  longer inlined, so themes can target them.
- **`.tanga-group-nested` is now an alias for `variant="small"`** — deprecated
  for one release; `tanga-group-small` / `tanga-group-tiny` are the canonical
  classes.
