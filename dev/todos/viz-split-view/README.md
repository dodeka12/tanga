# Viz Split View — Overview

**Created:** 2026-08-24 | **Status:** Planned | **Branch:** `feat/multi-view`

## Goal

Add nestable, draggable split views to the Tanga 3D viewer so a **single
browser page** can show **multiple scenes** (or control groups) in separate
panes, with horizontal/vertical splits and fixed or user-movable splitters.
The existing per-scene URLs (`/`, `/{name}`) keep working unchanged.

## Architecture (short)

- **Two-layer mirror.** A declarative Python `View` tree (in
  `py/pytanga/viz/views.py`) serializes to a `view_layout` JSON message; a
  parallel JS `View` class hierarchy (in `templates/views/`) materializes it
  into DOM + renderers.
- **`View` base (both sides) is split-agnostic.** It exposes per-axis
  preferred/min/max sizes (px or %), the current extent, and (frontend) emits
  `constraintschange`/`extentchange` events via native `EventTarget`.
- **`SplitView` is just one container** of `View`; `ThreeJsView`,
  `ControlGroupView`, and `SpacerView` are leaves.
- **One WebSocket, many scenes.** A layout tab subscribes to every scene its
  tree references; the server tags each message with `scene` and the frontend
  routes it to the matching pane.

## Canonical wire contract (fixed up front; both sides implement against this)

### `Size`

```json
{ "value": 320, "unit": "px" }     // absolute pixels
{ "value": 50,  "unit": "%" }      // % of the parent extent along that axis
{ "value": 2,   "unit": "fr" }     // flexible share (preferred only, never min/max)
{ "value": 0,   "unit": "auto" }   // unconstrained (min→0, max→∞, pref→natural)
```

`null` means "no constraint" and is equivalent to `auto` for min/max.

### `view_layout` message (server → client, once at handshake)

```json
{
  "type": "view_layout",
  "name": "",
  "root": {
    "type": "split", "id": "s1", "orientation": "horizontal",
    "movable": null,
    "sizes": [null, null],
    "children": [
      { "type": "scene_view", "id": "v1", "scene": "main",
        "min_width": null, "max_width": null,
        "min_height": null, "max_height": null,
        "preferred_width": null, "preferred_height": null },
      { "type": "split", "id": "s2", "orientation": "vertical",
        "movable": null, "sizes": [0.7, 0.3],
        "children": [
          { "type": "scene_view", "id": "v2", "scene": "side" },
          { "type": "control_group_view", "id": "v3", "scene": "side" }
        ] }
    ]
  }
}
```

Every view node carries `min_width`/`max_width`/`min_height`/`max_height` and
`preferred_width`/`preferred_height` as `Size | null`. `split` nodes carry
`orientation` (`"horizontal"` = children side-by-side, `"vertical"` = stacked),
optional `movable` (`true`/`false`/`null` = auto), and optional `sizes`
(initial splitter positions, fraction or px).

### `ready` (client → server)

- Single-scene tab (unchanged): `{ "type": "ready", "scene": "main" }`.
- Layout tab: `{ "type": "ready", "layout": "<name>", "scene": "" }`.

The server validates the layout name and subscribes the session to all scenes
referenced by that layout.

## Frontend `View` base contract (complete — later phases only *use* it)

- `el` — root DOM element.
- Extent (measured by the view's own `ResizeObserver`): `width`, `height`,
  `extent` getters.
- Per-axis constraints (`Size|null`): `minWidth`, `maxWidth`, `minHeight`,
  `maxHeight`, `preferredWidth`, `preferredHeight`; setters emit
  `constraintschange` (and `preferredchange` for the preferred pair).
- Resolve helpers: `minSizePx(axis, available)`, `maxSizePx(axis, available)`,
  `preferredPx(axis, available)`; `fixedX`, `fixedY`.
- Events (`EventTarget`): `extentchange`, `constraintschange`,
  `preferredchange`, `destroy`; sugar `on/off/emit`.
- Lifecycle: `mount(parentEl)`, `unmount()`, `destroy()`; hooks
  `_onExtentChanged(w, h)`, `_onMounted()`.

## Sizing / splitter semantics

- Fixed child (`min == max`) pins its splitter; otherwise the splitter is
  draggable but clamped so both neighbors stay within `[min, max]`.
- Positive leftover space (children fixed/maxed) is filled by an implicit
  `SpacerView`; negative overflow clips with a console warning.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-size-model.md](./01-python-size-model.md) | Python `Size` value type + parsing/serialization (+ tests) |
| 2 | [02-python-view-model.md](./02-python-view-model.md) | Python `View`/`SplitView`/`SceneView`/`ControlGroupView`/`SpacerView` + `view_layout` serialization (+ tests) |
| 3 | [03-visualizer-layout-api.md](./03-visualizer-layout-api.md) | `Visualizer.show(layout=...)`/`run(layout=...)`, layout registry, `?view=` URL |
| 4 | [04-server-multi-scene.md](./04-server-multi-scene.md) | `BrowserSession.scenes`, multi-scene `ready`, per-scene full-state push |
| 5 | [05-frontend-view-base.md](./05-frontend-view-base.md) | JS `Size` + `ViewEvent` + `View` base (EventTarget + ResizeObserver) |
| 6 | [06-frontend-split-view.md](./06-frontend-split-view.md) | Pure `resolveSplit` + `SplitView` DOM + `SpacerView` |
| 7 | [07-frontend-three-view.md](./07-frontend-three-view.md) | Extract `viewer.js` into `ThreeJsView` (backward compatible) |
| 8 | [08-frontend-control-group-view.md](./08-frontend-control-group-view.md) | `ControlGroupView` scoped panel + natural min-height |
| 9 | [09-frontend-bootstrap-layout.md](./09-frontend-bootstrap-layout.md) | Multi-view bootstrap, WS routing by scene, single render loop |
| 10 | [10-integration-example.md](./10-integration-example.md) | End-to-end example + integration checks |
| 11 | [11-docs-changelog.md](./11-docs-changelog.md) | Docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/test_views.py -q` (and the existing
  `test_scene_session.py` / `test_controls.py` for server/control changes).
- **JS (pure modules only — `size.js`, `view-event.js`, `split-resolver.js`):**
  Node's built-in test runner on `.mjs` tests in `dev/src/js-tests/`:
  `node --test 'dev/src/js-tests/*.test.mjs'`. No `package.json` needed (ESM via
  `.mjs`). Node v22 is already available in this environment.
- **DOM/browser modules** (`view.js`, `split-view.js`, `three-view.js`,
  `control-group-view.js`) are validated by browser smoke pages + the existing
  manual viewer, since the repo has no DOM test harness.
- Every phase ends with a runnable validation command before the next phase
  starts — no "test phase at the end".

## Guiding decisions / no-refactor rule

- The wire contract and the `View` base API above are **fixed now**; later
  phases implement *against* them and never change them, so no earlier phase is
  refactored.
- `ThreeJsView` extraction (Phase 7) precedes the multi-view bootstrap
  (Phase 9) so the bootstrap only *composes* an already-working view.
- Pure layout math lives in `split-resolver.js` (no DOM) so it is
  Node-testable independently of the DOM container.
