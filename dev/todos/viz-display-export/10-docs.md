# Phase 10 — Documentation

**Status:** Planned

## Goal

Update docs to describe the consolidated API and the deprecated aliases.

## Files

- Modify: `docs/py/viz/visualizer.md`
- Modify: `docs/py/viz/jupyter.md`
- Modify: `docs/py/viz/export.md`

## Steps

- [ ] Document the serve/view lifecycle (`show`/`wait`/`start_server`/
      `stop_server`/`open_browser`/`animate`) and the removal of `host`/`port`
      from `Visualizer(...)`.
- [ ] Document `export_snapshot` / `open_snapshot` / `display_snapshot`,
      `export_figure` / `export_glb`, and the `animation=` keyword.
- [ ] Document `display()` / `display_row()` for live + static rows.
- [ ] Add a "Deprecated aliases" table listing the old → new names.

## Verification

- [ ] Docs build/links render (spot-check the three pages).
