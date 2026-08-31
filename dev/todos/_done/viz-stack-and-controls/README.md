# Viz Stack View & Controls — Overview

**Created:** 2026-08-24 | **Status:** Planned | **Branch:** `feat/multi-view`

## Goal

Extend the split-view system into a general view-composition model where *every*
UI element is a `View`:

- a **`StackView`** flow container that stacks views vertically, horizontally,
  or wraps to a new line (flex-like, content-sized);
- **controls as views** (`SliderView`, `ButtonView`, `DropdownView`) that render
  plain HTML — no Three.js, no scene binding;
- **`GroupView`** (renamed from `ControlGroupView`) — a titled view container (a
  `StackView` with title/position/collapse chrome) that holds control views,
  usable as a split pane *or* as an overlay on a `SceneView`;
- a **`SceneView` overlay layer** so views can float over the 3D canvas.

The existing scene-bound controls (`viz.add_slider(...)`, `controls_define`) stay
as-is and are **additive** to the new model.

## Architecture (short)

- **Everything is a `View`.** `SplitView` (draggable, absolute) and `StackView`
  (flow/flex, content-sized) are the two containers; `SceneView`, control views,
  `GroupView`, and `SpacerView` are leaves (or, for `SceneView`/`GroupView`,
  leaves that *also* host children).
- **Two-layer mirror** (as in split views): the Python tree in
  `py/pytanga/viz/views.py` serializes to `view_layout`; the JS tree in
  `templates/views/` materializes it.
- **Controls are self-rendering.** A control view wraps the existing
  `createSlider`/`createButton`/`createDropdown` factories and sends the existing
  `control:change`/`control:click` events; the Python side registers handlers by
  control `id` when the layout is set.

## Wire contract additions (fixed up front; both sides implement against this)

Every node keeps the shared `id` + per-axis `min_/max_/preferred_width|height`
(`Size | null`). New/`changed node types:

### `stack` — `StackView(direction, children)`

```json
{ "type": "stack", "id": "s3", "direction": "vertical",
  "min_width": null, "max_width": null, "min_height": null, "max_height": null,
  "preferred_width": null, "preferred_height": null,
  "children": [ ... ] }
```

`direction` ∈ `"vertical"` | `"horizontal"` | `"wrap"`.

### `group` — `GroupView(title, children, direction="vertical", position, collapsed)`

```json
{ "type": "group", "id": "g1", "title": "Actions", "direction": "vertical",
  "position": "bottom-right", "collapsed": false,
  "min_width": null, "max_width": null, "min_height": null, "max_height": null,
  "preferred_width": null, "preferred_height": null,
  "children": [ ... control view nodes ... ] }
```

`position` reuses the existing anchor strings
`"top-left" | "top-right" | "bottom-left" | "bottom-right"` (only meaningful
when the group is an overlay child of a `SceneView`).

### control leaf nodes

```json
{ "type": "slider_view", "id": "s1", "label": "Radius", "min": 0.0, "max": 5.0, "step": 0.01, "default": 2.0 }
{ "type": "button_view", "id": "b1", "label": "Reset" }
{ "type": "dropdown_view", "id": "d1", "label": "Mode", "options": ["a", "b"], "default": "a" }
```

The control node's `id` doubles as the `control_id` event key; the shared
`_serialize_one_control` (in `_controls.py`) supplies the kind-specific fields.

### `scene_view` overlay

```json
{ "type": "scene_view", "id": "v1", "scene": "main",
  "children": [ { "type": "group", "id": "g1", "position": "bottom-right", ... } ] }
```

`children` is the overlay layer: views floating over the canvas, anchored by
each child's `position`.

## Decisions (confirmed)

- Keep `viz.add_slider()` / `controls_define` (additive).
- Rename `ControlGroupView` → `GroupView`; a titled view container.
- Overlay anchoring reuses the existing `position` strings.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-stack-group-controls.md](./01-python-stack-group-controls.md) | Python `StackView`, `GroupView`, `SliderView`/`ButtonView`/`DropdownView`, `SceneView` overlay + serialization (+ tests) |
| 2 | [02-control-handler-registration.md](./02-control-handler-registration.md) | Register control-view handlers into `_handler_registry` on `set_layout`/`show` (+ tests) |
| 3 | [03-frontend-stack-view.md](./03-frontend-stack-view.md) | JS `StackView` (flex, vertical/horizontal/wrap, content sizing) + smoke |
| 4 | [04-frontend-control-views.md](./04-frontend-control-views.md) | JS `SliderView`/`ButtonView`/`DropdownView` (reuse factories, send events) + smoke |
| 5 | [05-frontend-group-overlay-build.md](./05-frontend-group-overlay-build.md) | JS `GroupView`, `ThreeJsView` overlay, `build.js` mapping + routing update |
| 6 | [06-fixed-splitter-line.md](./06-fixed-splitter-line.md) | Fixed splitter draws a thin line |
| 7 | [07-example-docs-changelog.md](./07-example-docs-changelog.md) | Rewrite example, docs, changelog, full validation |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/ -q` (extend `test_views.py`, plus
  `test_layout_api.py` / `test_server_layout.py` for handler registration).
- **JS (pure modules):** `node --test 'dev/src/js-tests/*.test.mjs'`.
- **DOM/browser modules** (`stack-view.js`, control views, `group-view.js`) are
  validated by browser smoke pages (add one per phase) + the manual viewer.
- Every phase ends with a runnable validation command before the next starts.

## Non-goals

- Removing or reworking the existing `viz.add_slider(...)` + `controls_define`
  path (it stays, used by `VisualizerApp` and other examples).
- The CSS2DRenderer "attached" control path (`parent_id`) — out of scope.
- Per-axis min/max constraints in `wrap` mode beyond natural (content) sizing.
