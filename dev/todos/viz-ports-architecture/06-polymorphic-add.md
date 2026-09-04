# Phase 6 — Polymorphic `Visualizer.add()` + `add_layout`/`set_layout`

## Goal

Make `Visualizer.add(x)` polymorphic: an entity goes to the main scene, a `View`
goes to the default layout's overlay.  Add `add_layout`/`set_layout` and the
`viz.layout[name]` accessor with `.base`/`.overlay` sugar.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_scene_handle.py`
- Edit: `py/pytanga/viz/_layout.py` (`__getitem__`, `base`/`overlay` properties)

## Steps

- [x] **6.1 — `LayoutHost` accessor**
  - `__getitem__(name)` → `Layout`; `base`/`overlay` properties default to `""`.
- [x] **6.2 — `add_layout`/`set_layout`/`add_scene`**
  - `add_layout(name, root)` (raise if taken), `set_layout(name, root)` (replace).
- [x] **6.3 — Polymorphic `add`**
  - `add(entity)` → `scene("").add`; `add(view)` → `layout[""].overlay.add(view)`.
- [x] **6.4 — Tests**
  - Green + new coverage for the accessor/polymorphic dispatch.

## Validation

`uv run pytest py/tests/viz -q`
