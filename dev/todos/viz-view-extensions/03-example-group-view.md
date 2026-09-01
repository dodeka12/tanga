# Phase 3 — Example: group view icons + borderless fold

## Goal

Ship a runnable example that demonstrates `GroupView` with a leading icon, an
icon-only group, and the borderless fold button.

## Files

- New: `py/examples/viz/scenes/group_view_icons.py`
- (regenerate docs after adding the example)

## Steps

- [x] **3.1 — Example script**
  - Create `py/examples/viz/scenes/group_view_icons.py` with the required header
    (one-line description, `Run with:`, `Keywords:` — see
    `dev/workflows/example-docs.md`).
  - Build a `Visualizer` + `set_layout` that places one or two `GroupView`s as a
    `SceneView` overlay: one with `icon=...` + title, one `icon_only=True`
    (no title), both `collapsed=False` and toggleable.
  - Use `EIconMaterial` icons (e.g. `SETTINGS`, `TUNE`) and show the borderless
    fold button.

- [x] **3.2 — Docs generation**
  - Run `uv run python tools/generate-example-docs.py` and confirm the example
    appears under the examples nav.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run ruff check py/examples/viz/scenes/group_view_icons.py`
