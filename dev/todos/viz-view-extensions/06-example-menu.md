# Phase 6 — Example: menus

## Goal

Demonstrate the menu system end-to-end: a global hamburger menu
(`add_menu(scene_name=None)`), a per-pane menu (`SceneView(overlay=[MenuView(...)])`),
sub-menus, and a permanent horizontal strip.

## Files

- New: `py/examples/viz/menus/menu_demo.py`
- (regenerate docs after adding the example)

## Steps

- [x] **6.1 — Example script**
  - Create `py/examples/viz/menus/menu_demo.py` with the required header
    (one-line description, `Run with:`, `Keywords:` — see
    `dev/workflows/example-docs.md`).
  - Use `set_layout` with a split of two `SceneView` panes; give one pane a
    per-pane `MenuView` overlay (`position="top-left"`).
  - Add a global `add_menu(scene_name=None)` (hamburger) with a `variant="menu"`
    button / checkbox / slider option and a nested sub-menu.
  - Add a `mode="bar"` horizontal strip shown permanently (e.g. a `MenuView`
    placed in a horizontal `StackView` at the root).

- [x] **6.2 — Docs generation**
  - Run `uv run python tools/generate-example-docs.py` and confirm the example
    appears under the examples nav.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run ruff check py/examples/viz/menus/menu_demo.py`
