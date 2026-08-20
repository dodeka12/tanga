# Phase 10 — Documentation

**Status:** Done

## Goal

Update docs to describe the consolidated API and the deprecated aliases.

## Files

- Modify: `docs/py/viz/visualizer.md`
- Modify: `docs/py/viz/jupyter.md`
- Modify: `docs/py/viz/export.md`

## Steps

- [x] Document the serve/view lifecycle (`show`/`wait`/`start_server`/
      `stop_server`/`open_browser`/`animate`) and that `host`/`port` on
      `Visualizer(...)` are deprecated kwargs.
- [x] Document `export_snapshot` / `open_snapshot` / `display_snapshot`,
      `export_figure` / `export_glb`, and the `animation=` keyword.
- [x] Document `display()` / `display_row()` for live + static rows.
- [x] Add a "Deprecated aliases" table listing the old → new names.

## Verification

- [x] Updated `visualizer.md`, `jupyter.md`, `export.md` (spot-checked).
