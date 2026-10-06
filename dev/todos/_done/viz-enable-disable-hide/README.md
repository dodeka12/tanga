# Viz enable/disable/hide — Overview

**Created:** 2026-09-24 | **Status:** Done | **Branch:** `feat/ui-layout-update`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add first-class **hide/show** for every scene entity, **enable/disable** for
action objects (`Act*`), and **hide/show + enable/disable** for UI controls —
each toggled at runtime without re-pushing the layout or re-serializing
geometry. Ships with an example, user docs, and updated architecture docs.

## Architecture (short)

- **Entity visibility** joins the existing aspect-patch `object_update` channel
  (alongside `full`/`style`/`transform`/`content`/`interaction`): a new
  `visible` aspect, served by `VizSceneObject.patch("visible")` and consumed by
  `ThreeJsView._applyObjectPatch`.
- **Action-object enablement** rides the **existing** `interaction` aspect:
  `ActSceneObject.set_enabled(False)` flips `InteractionConfig.enabled` and
  re-registers (`refresh_interaction()`); no new wire aspect.
- **Control state** lives on the `Control` model (`enabled`/`visible`) and is
  pushed as a **granular `control_state` message** (mirrors `control_update`),
  so hiding one control never re-pushes `view_layout`.

### Fixed wire/API contract (do not change across phases)

1. **`visible` aspect patch** (in `object_update.patches`):

   ```json
   { "id": "<entity-id>", "aspect": "visible", "value": { "visible": false } }
   ```

2. **`control_state` message** (server → client, global by id):

   ```json
   { "type": "control_state", "id": "<control-id>", "enabled": false, "visible": false }
   ```

   Only changed fields are present; handled in `viewer.js` next to
   `control_update`, dispatched to `applyControlState(id, msg)`.

3. **`Control.serialize()`** emits `enabled`/`visible` **only when non-default**
   (`False`), matching the `tooltip` only-if-set convention.

4. **Entity API** — `set_visible` is the primary verb; `show` is **not** used on
   `Visualizer` (server `show()`) or `VizSceneHandle` (its `show()` serves +
   displays the scene). Use `set_visible(id, True)` to show:
   - `Visualizer.set_visible(object_id, visible, *, scene_name="")` and
     `Visualizer.hide(object_id, *, scene_name="")`.
   - `VizSceneHandle.set_visible / hide`.
   - `VizObjectRef.set_visible(visible)`.

5. **Action-object API** — `ActSceneObject.set_enabled(bool)`, `.enable()`,
   `.disable()`.

6. **Control API** — `ControlView.set_enabled / set_visible` (+
   `enable`/`disable`/`show`/`hide` sugar); `Visualizer.set_control_enabled(cid,
   bool)` / `set_control_visible(cid, bool)` (resolve + mutate + push; works for
   dialog/banner controls too).

## Decisions (confirmed)

- `enabled` applies **only to action objects** for entities; standard entities
  only get `visible`.
- `enabled` for action objects = `InteractionConfig.enabled` (stops
  hover/drag/click/scroll capture).
- Disabled controls grey out via a theme token (`--tanga-disabled-opacity`,
  `--tanga-disabled-fg`) in `base.css :root`, overridable per theme.
- The example demonstrates entity hide + control hide + control disable
  (grey-out); action-object disable is covered by tests + interaction docs.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-entity-visibility-python.md](./01-entity-visibility-python.md) | `visible` node/aspect + `Scene.set_visible` + public API + tests |
| 2 | [02-entity-visibility-frontend.md](./02-entity-visibility-frontend.md) | `scene-builder.js` reads `visible`; `three-view.js` handles the `visible` aspect |
| 3 | [03-action-object-enable.md](./03-action-object-enable.md) | `ActSceneObject.set_enabled/enable/disable` + tests |
| 4 | [04-control-state-python.md](./04-control-state-python.md) | `Control.enabled/visible` + `ControlView` setters + `control_state` push + Visualizer API + tests |
| 5 | [05-control-state-frontend.md](./05-control-state-frontend.md) | `applyControlState` + factories + `viewer.js` branch + themeable CSS |
| 6 | [06-example-hide-sphere.md](./06-example-hide-sphere.md) | `py/examples/viz/ui/controls/hide_sphere.py` + docs regen |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Architecture + user docs + changelog + PR |

## Testing as you go

```bash
uv run pytest py/tests/viz -q                     # Python side
node js/dev/tests/check-syntax.mjs                # JS syntax
uv run python tools/build-viewer-js.py --check    # export-library bundle drift gate
uv run python tools/generate-example-docs.py      # example gallery (after phase 6)
uv run mkdocs build --strict                      # docs (after phase 7)
```

> Note: the live frontend (`templates/viewer.js` + `templates/views/` +
> `templates/controls/` + `templates/renderers/`) is served directly by the
> server as ES modules. `build-viewer-js.py` only bundles the **export** renderer
> library (`js/tanga-viewer.js`), so it does not gate edits to those files.

## Non-goals

- No generic `enabled` flag on non-action entities (standard entities only get
  `visible`).
- No layout re-push for a single control state change (that is the point of
  `control_state`).
- No server-side layout diffing; unchanged from `viz-layout-reconcile`.
