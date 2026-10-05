# Viz control range + menu auto-close — Overview

**Created:** 2026-10-05 | **Status:** Done | **Branch:** `fix/small-bugs`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make the numeric **range** (`min` / `max` / `step`) of `SliderView` and
`ValueEditView` changeable after creation (a view setter + a `Visualizer` API +
a granular `control_state` push applied by the frontend, with no `view_layout`
re-push), and make a menu bar / sub-menu **auto-close** after an option is
chosen (a button click or a dropdown change).

## Architecture (short)

- **Controls** are `*View` objects wrapping a `Control` model; runtime state is
  pushed as `control_update` (value) and `control_state`
  (`enabled`/`visible`/`selected`) — see
  `docs/dev/architecture/viz-controls-and-interactions.md`.
- **Range mutation** reuses the existing `control_state` seam: the view mutates
  `self.control.min/max/step`, clamps `value`, then pushes the changed fields.
- **Menus** are frontend-only overlay containers (`MenuView` is a `View`, not a
  `Control`); auto-close is a frontend behavior, not a wire message.

### Fixed wire/API contract (do not change across phases)

1. **`control_state` message** (server → client, global by id) gains optional
   `min` / `max` / `step` (only changed fields are present):

   ```json
   { "type": "control_state", "id": "<control-id>", "min": 0.0, "max": 10.0, "step": 0.5 }
   ```

   Handled in `viewer.js` next to `control_update` → `applyControlState(id, msg)`.

2. **View setters** — `set_min(v)`, `set_max(v)`, `set_step(v)`, and
   `set_range(min=None, max=None, step=None)` on `SliderView` and
   `ValueEditView`.  Mutating `min`/`max` clamps `control.value` into the new
   range; when the value is clamped the view also pushes `control_update`.

3. **Visualizer API** — `Visualizer.set_control_range(control_id, *, min=None,
   max=None, step=None)` resolves the control (`Slider` / `ValueEdit`), mutates
   + clamps, and pushes `control_state` (+ `control_update` when clamped).
   No-op on an unknown id.

4. **Menu auto-close** — a `MenuView` closes (walks `_parentMenu` to the root
   and calls `close()`) when a menu item is activated: a `button` `click` or a
   `select` `change`.  Checkboxes and sliders stay open.

## Decisions (confirmed)

- **`ValueEdit` is in scope** for the range setters (`min`/`max`/`step`);
  `digits`/`editable` are **not** (they are formatting/state, not range).
- **Menu auto-close scope** (recommended): buttons (`click`) and dropdowns
  (`change`) close the menu; checkboxes and sliders stay open (so you can
  toggle / drag repeatedly).
- **`__getattr__` removal is a separate plan** (`viz-control-view-forwarders`);
  this plan only adds the new setters and never touches
  `ControlView.__getattr__`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-control-range-python.md](./01-control-range-python.md) | `SliderView`/`ValueEditView` setters + `set_control_range` (layout + visualizer) + tests |
| 2 | [02-control-range-frontend.md](./02-control-range-frontend.md) | `control_state` `min`/`max`/`step` application (slider + value-edit) |
| 3 | [03-menu-auto-close.md](./03-menu-auto-close.md) | `MenuView` auto-close on option activation |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Architecture docs + changelog + PR |

## Testing as you go

```bash
uv run pytest py/tests/viz -q                     # Python side (phases 1-4)
node js/dev/tests/check-syntax.mjs                # JS syntax (phases 2-3)
uv run python tools/build-viewer-js.py --check    # bundle drift gate (phases 2-3)
uv run mkdocs build --strict                      # docs (phase 4)
```

> Note: the live frontend (`templates/viewer.js` + `templates/views/` +
> `templates/controls/`) is served directly as ES modules.
> `build-viewer-js.py` only bundles the **export** renderer library
> (`js/tanga-viewer.js`), so it does not gate edits to those files — but keep it
> in sync when any bundled module changes.

## Non-goals

- No `view_layout` re-push for a single range change (that is the point of
  `control_state`).
- No `digits`/`editable` runtime mutation for `ValueEdit`.
- No backend "close menu" concept — menu closing is frontend-only.
- No removal of `ControlView.__getattr__` (that is the separate
  `viz-control-view-forwarders` plan).
