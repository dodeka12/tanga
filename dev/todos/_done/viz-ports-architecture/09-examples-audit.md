# Example audit after the scene/layout/overlay remodel

Follow-up inventory of `py/examples/` after the viewer remodel (phases 1–8 of
`viz-ports-architecture`).  It lists every example that still needs inspection
or rework, and the one underlying gap the migration surfaced.

## Context — what changed for examples

- `add_*` control facades (`add_slider`/`add_button`/`add_table`/…,
  `add_control_group`, `add_menu`) are **removed**; controls are declared as
  `*View` objects and mounted via `set_layout` / `viz.add(view)`.
- `control_position` (constructor arg + property) is **removed**.
- The runtime value API is **removed**: `set_control`, `set_control_value`,
  `set_control_view_value`, `get_control`, `update_control`, `undo_table`,
  `redo_table`, `can_undo_table`, `can_redo_table`, `clear_table_history`,
  `clear_controls`, `remove_control`, `remove_control_group`.
- `viz.add` is now **polymorphic** (entity → main scene, `View` → default
  layout overlay); `viz.layout` / `viz.add_layout` are new.
- `BannerHost`/`DialogHost`/`EditorHost`/`HostRuntime` are gone (folded into
  `OverlayContainer`).

## 1. Broken — reference removed APIs (raise `AttributeError` at runtime)

These call a method that no longer exists; the example crashes when the
handler fires.

- **`py/examples/viz/ui/controls/table_split.py`**
  - `viz.set_control_view_value(table_view, {"columns": _COLUMNS, "rows": _ROWS})`
    (line 53) in `_on_reset`.  The reset button breaks.
- **`py/examples/viz/ui/static/display_views.py`**
  - `viz.set_control("label", …)` / `viz.set_control("markdown", …)` (lines
    40–41) in `on_update`, plus the module docstring (line 10) that documents
    `viz.set_control`.  The "Update both views" button breaks.

## 2. Silent — `*View.set_value()` sets the model but does not push

`Control.set_value` (phase 5) only mutates the control model; it does **not**
push `control_update` to the browser (unlike the removed
`set_control`/`set_control_view_value`, which set *and* pushed).  These examples
were migrated to `set_value` in phase 5, so they don't crash, but the browser
never reflects the backend-side value change (synced sliders won't move, table
resets won't redraw):

- **`py/examples/viz/ui/controls/all_controls.py`**
  - Cross-synced radius sliders/stepper/readout (`on_radius`, `on_radius2`,
    `on_radius_value`, `on_reset`) call `self._radius2_view.set_value(...)` etc.
    (lines 71–85, 132–138).  The twin controls no longer follow the dragged one.
- **`py/examples/viz/ui/controls/table_data.py`**
  - `self._table.set_value({"columns": self._columns, "rows": self._rows})` in
    `on_reset` (line 94).  The reset button no longer redraws the grid.
- **`py/examples/viz/ui/controls/table_editing.py`**
  - `self._table.set_value({…})` in `on_reset` (line 137).  Same as above.

## 3. Underlying gap to resolve first

The examples in §1 and §2 all need a way to **push a backend-initiated control
value change** to the browser.  The value API removal left no public path for
this.  Options (pick one, then update the examples to use it):

1. **Give `ControlView` a `_push` callback** (like `LogView._push`, injected by
   `ControlHost._register_log_views`), so `view.set_value(x)` sets *and* pushes
   `control_update` through the transport.  Cleanest; matches the existing
   `LogView` pattern.
2. **Re-add a thin `Visualizer.set_control_value(cid, value, *, scene_name="")`
   forwarder** that resolves the control (tree-walk) + `control.set_value` +
   `_push_control_update`.  Preserves the old call-site shape.

Either way, the §2 examples should stop relying on `set_value` as a push and the
§1 examples need their `set_control*` calls replaced.

## 4. Examples migrated in phase 5 (verify at runtime)

These were rewritten to declarative `*View` + `set_layout`; they compile and
have no removed-API references, but their **runtime behaviour** was not exercised
(some overlap with §2):

- `py/examples/viz/ui/controls/all_controls.py` *(§2)*
- `py/examples/viz/ui/controls/table_data.py` *(§2)*
- `py/examples/viz/ui/controls/table_editing.py` *(§2)*
- `py/examples/viz/ui/controls/file_chooser.py`
- `py/examples/viz/ui/controls/controls_add_and_view.py`
- `py/examples/viz/ui/controls/control_group_single.py`
- `py/examples/viz/ui/controls/control_group_overlay.py`
- `py/examples/viz/ui/menus/menu_demo.py`
- `py/examples/viz/ui/banners/heavy_work.py`
- `py/examples/viz/interaction/two_spheres_interact.py`
- `py/examples/viz/ui/controls/control_position.py` — **deleted** (feature removed)

## 5. Unaffected

All other `py/examples/` files (100+ of 108) use only unchanged APIs
(`viz.add(entity)`, `viz.set_layout`, `viz.show`, `viz.update`, scenes, camera,
export, SDF, geometry algebra, …).  They compile and need no rework.

(Note: stale `__pycache__/*.pyc` for the old example names remain locally but are
git-ignored and harmless.)
