# Changes since version 1.17.0 (2.0.0-rc2)

## New Features
- **Configurable CSV delimiter & decimal separator** — `TableView.to_csv` /
  `from_csv` (and `Table.to_csv` / `from_csv`) now take `delimiter` and
  `decimal_separator`. Import auto-detects the delimiter (`;` vs `,`) and
  decimal separator (`,` vs `.`) so German/European CSV files load without
  configuration, normalizing numbers to the canonical `.` decimal form; both
  parameters can be overridden explicitly, and export defaults to the `,`/`.`
  (US) dialect.

## Bug Fixes
- **`SplitView` fills leftover space in flow containers** — a `SplitView`
  nested directly in a `StackView`/`GroupView`/`ToolbarView` no longer collapses
  to zero height/width: it now defaults `preferred_width`/`preferred_height` to
  `Size.fr(1)` so it grows to fill the remaining space (its
  absolutely-positioned children give it no intrinsic cross-axis extent).
  Explicit `preferred_*`/`size` values still override the default.
- **`TableView` shrinks to fit narrow flow containers** — a `TableView` nested
  in a narrower `GroupView`/`StackView` pane no longer overflows its parent and
  produces a whole-widget horizontal scrollbar: its pinned width is now capped at
  the container width, so the table's own grid scrolls horizontally while the
  title bar (control buttons) stays fixed.
- **Opaque sticky column headers** — scrolled table rows no longer show through
  the column titles: the sticky header tint is now painted over the opaque theme
  background, so the headers stay legible when data scrolls underneath them.
- **Column resize grows the table instead of squeezing the neighbour** —
  dragging a column's right edge now resizes only that column and grows/shrinks
  the total table width (with a horizontal scrollbar) rather than shrinking the
  next column to the right.
- **Checkbox aligns like other toolbar controls** — a `CheckboxView` in a
  toolbar is now centered vertically in its field and given the same 6px
  left/right margins as sliders/dropdowns, instead of sitting at the top-left
  corner.

