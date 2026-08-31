# Control Value API — Overview

**Created:** 2026-08-27 | **Status:** Done | **Branch:** `feat/control-api`

## Goal

Let the backend programmatically update the *value* of an interactive control
after it has been created, for both control surfaces — the `add_*` panel /
attached controls and the layout-API `*View` controls — without tearing down
and rebuilding the panel. As a breaking-change foundation, unify the split
`default` / `value` field naming on a single `value` field.

## Background

- Controls are created on the `Visualizer` (`add_slider`, `add_dropdown`,
  `add_color_picker`, `add_checkbox`, `add_text_field`, …) or as layout views
  (`SliderView`, `DropdownView`, `ColorPickerView`, `CheckboxView`, …).
- Today the "current value" field is named inconsistently: `default` for
  slider/dropdown/color/checkbox vs `value` for text/textarea/file-chooser.
- The only way to change a control after creation is the undocumented
  `update_control(cid, **fields)`, which mutates the stored dataclass and
  re-pushes a full `controls_define` — making the frontend rebuild the whole
  panel (losing collapse/drag/focus state).

## Architecture (short)

- **One value field.** Every value-bearing control uses `value` (renamed from
  `default` where needed); the wire format emits `"value"`.
- **Python helpers.** `get_control_value` / `set_control_value` (and a parallel
  `set_control_view_value`) normalize the uniform `value` argument to the
  per-kind field and type-check it.
- **Lightweight `control_update` message.** `{type, scene, id, value}` updates
  one control's DOM value in place — no panel rebuild. The panel
  (`controls-panel.js`) and the layout views (`views/*-view.js`) render through
  the same `create*` factories, so a single id-keyed registry covers both.

## Canonical wire contract (fixed up front)

### Control `value` field (in `controls_define`)

`slider`, `dropdown`, `color`, `checkbox` controls serialize `"value"` in place
of `"default"` (matching `text`, `textarea`, `file_chooser`):

```json
{ "id": "radius", "kind": "slider", "label": "Radius",
  "min": 0, "max": 5, "step": 0.1, "value": 2.0 }
{ "id": "mode", "kind": "dropdown", "options": ["a", "b"], "value": "a" }
{ "id": "color", "kind": "color", "value": "#ff0000" }
{ "id": "wire", "kind": "checkbox", "value": true }
```

### `control_update` message (server → client)

```json
{ "type": "control_update", "scene": "", "id": "radius", "value": 3.5 }
```

- `id` is the control id (globally unique app-wide — controls already share the
  `ControlHandlerRegistry` namespace).
- `scene` is informational/for logging; the frontend applies the update
  id-keyed and no-ops if that control isn't rendered in the browser.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-data-model.md](./01-python-data-model.md) | Rename `default` → `value` in `_controls.py` dataclasses + serialization (+ tests) |
| 2 | [02-python-view-model.md](./02-python-view-model.md) | Rename in `views.py` `*View` controls (+ tests) |
| 3 | [03-visualizer-scene-handle.md](./03-visualizer-scene-handle.md) | Rename in `visualizer.py` `add_*` + `_scene_handle.py` wrappers |
| 4 | [04-frontend-rename.md](./04-frontend-rename.md) | Rename in JS factories + view classes + smoke pages |
| 5 | [05-value-update-api.md](./05-value-update-api.md) | Value helpers + `set_control_value` / `set_control_view_value` |
| 6 | [06-control-update-message.md](./06-control-update-message.md) | `control_update` wire message + frontend in-place update |
| 7 | [07-examples.md](./07-examples.md) | Update examples for the rename + demonstrate value updates |
| 8 | [08-docs-changelog.md](./08-docs-changelog.md) | Docs + changelog (breaking-change entry) |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_views.py
  py/tests/viz/test_banner.py py/tests/viz/test_entry_points.py
  py/tests/viz/test_layout_api.py py/tests/viz/test_file_chooser.py -q`.
- **JS:** browser smoke pages under `dev/src/js-tests/` (no DOM test harness);
  pure-module tests via `node --test 'dev/src/js-tests/*.test.mjs'` where
  applicable.
- **Docs:** `uv run mkdocs build --strict`.

## Guiding decisions / no-refactor rule

- **`default` → `value` is a hard, breaking rename** — no `default` alias is
  kept, so the old `add_slider(default=…)` / `SliderView(default=…)` keywords
  stop working. Recorded in the changelog's Breaking Changes section.
- The value-update path is **in-place** (a new `control_update` message), never
  a full `controls_define` re-push, so UI state (collapse, drag, focus) is
  preserved.
- Do not change the layout/view rendering architecture; the update path reuses
  the existing `create*` factories and the single id namespace.
