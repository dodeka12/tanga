# Table viewport, zoom + resize — Overview

**Created:** 2026-09-05 | **Status:** Done | **Branch:** `fix/examples`

## Goal

Make the native `TableView` grid a bounded, resizable widget with internal
scrollbars (instead of growing its container), give every row a standard height,
and add title-bar `+`/`−` zoom controls for column width and row height plus a
drag corner to resize the whole table.

## Architecture (short)

- **Bounded size.** `TableView` gains Python default `preferred_width` /
  `preferred_height` (480×320 px), so flow containers (`StackView` / `GroupView`
  / overlay) bound it and the scroll container (`overflow: auto`) scrolls. In a
  `SplitView` the splitter still owns the size (the table keeps filling its pane).
- **Standard row height.** A `--tanga-table-row-height` token (default `24px`)
  applied to every `td`/`th`; the frontend tracks a `rowHeight` value and writes
  the token on the table element.
- **Column zoom.** Column widths stay proportional (`weights[]` +
  `fitColumnWidths`), scaled by a `colScale` multiplier so `+`/`−` make columns
  wider/narrower while preserving relative widths; overflow → horizontal scroll.
- **Title bar.** The `<label>` becomes a flex row (label left, `+`/`−` controls
  right) with two groups — column width and row height.
- **Resize.** A bottom-right corner handle reports a new pixel size to
  `TableView` via an `onResize` callback, which sets `preferredWidth` /
  `preferredHeight` (emitting `preferredchange`) so the enclosing flow container
  re-lays-out.

## Fixed contract (up front)

| Item | Default | Notes |
|------|---------|-------|
| `TableView.preferred_width` | `Size.px(480)` | new Python default |
| `TableView.preferred_height` | `Size.px(320)` | new Python default |
| `--tanga-table-row-height` | `24px` | CSS token (base + light/pastel) |
| `rowHeight` (JS) | `24` | clamp `[16, 60]`, step `±4` |
| `colScale` (JS) | `1` | clamp `[0.25, 8]`, step `×/÷ 1.25` |

- Column fit: `contentWidth = (container.clientWidth − rowNumberW) × colScale`;
  `fitColumnWidths(contentWidth, weights)`; table `min-width` = Σ MIN + rowNumberW.
- `apply` (backend re-render) preserves `weights` (col count unchanged),
  `colScale`, `rowHeight`; resets `sortState` / `activeTd` / `editorCell`.
- Zoom + resize state is frontend-only display state (not persisted to the
  backend), consistent with the existing column `weights`.

## Decisions (confirmed)

- Corner grip only (not a full draggable border).
- Keep filling the `SplitView` pane (splitter resizes; the corner is inert there).
- No backend persistence for zoom/resize.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-preferred-size.md](./01-python-preferred-size.md) | Backend default `preferred_width`/`preferred_height`. |
| 2 | [02-row-height-scroll.md](./02-row-height-scroll.md) | Standard row-height token + bounded scroll. |
| 3 | [03-title-bar-zoom.md](./03-title-bar-zoom.md) | Title-bar `+`/`−` controls for column width + row height. |
| 4 | [04-resize-corner.md](./04-resize-corner.md) | Drag corner to resize the table (View wiring). |
| 5 | [05-tests-docs-changelog.md](./05-tests-docs-changelog.md) | JS/Python tests, docs, changelog. |

## Testing as you go

- Python: `uv run pytest py/tests/viz/test_views.py py/tests/viz/test_control_value_api.py py/tests/viz/test_themes.py -q`
- JS: `node --test 'dev/src/js-tests/*.test.mjs'`
- Docs: `uv run mkdocs build --strict`
- Smoke: `uv run python py/examples/viz/ui/controls/table_editing.py`, `table_split.py`

## Non-goals

- No full draggable border (edges) — corner grip only.
- No backend persistence of zoom/resize/row-height state.
- No row reordering / multi-cell selection (unchanged from the native-grid plan).
