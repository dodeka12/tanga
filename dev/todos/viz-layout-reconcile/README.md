# Viz layout reconcile — Overview

**Created:** 2026-09-24 | **Status:** Done | **Branch:** `feat/ui-layout-update`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Stop tearing the frontend layout down and rebuilding it whenever one pane
changes. Today a `view_layout` re-push destroys every DOM view except one
`ThreeJsView` per scene name, so an unrelated sibling pane flashes off/on (see
`_input/pytanga-background-image-blank-pane.md`). We change the frontend to
**reconcile the whole view tree by stable view id** — reusing whatever is
unchanged (WebGL panes *and* DOM chrome/controls) and only creating/removing the
diff — and add a **granular `view_background_image`** message so swapping a
`CameraView.background_image` does not re-push the layout at all.

## Architecture (short)

- **Identity = `View.id`.** Every serialized node already carries a stable `id`
  (`sv0`/`v0`/`log0`, or an explicit `id=`). Reusing the same Python `View`
  object across `set_layout` keeps the id stable and therefore keeps the live
  frontend view. A *new* `View` object gets a new id → the old frontend view is
  destroyed and a new one created. This is the existing documented contract
  (`viz-architecture.md` "view identity"; `viz-controls-and-interactions.md`
  "Single global id namespace") and requires **no change to Python id
  generation**.
- **One orphan registry.** The frontend keeps a single
  `_viewRegistry: Map<view_id, View>` (all view types). `_sceneRoutes` (scene →
  panes) and the per-pane `view_camera`/`view_viewport`/`view_background_image`
  lookup are *derived* from it. The current transient, scene-name-keyed `reuse`
  `Map` is removed. `_controlRegistry` (control value/apply) stays a separate
  concern but is kept in sync by the reconcile.
- **Reconcile algorithm.** `_buildLayout` → `buildViewTree` walks the serialized
  tree; for each node it reuses the registry entry when `node.id` matches and the
  type is unchanged (updating fields in place and re-parenting children), else
  constructs a new view; afterwards any registry entry not claimed is destroyed.

### Fixed wire/API contract (do not change across phases)

1. **`view_background_image` message** (JSON, mirrors `view_camera`):

   ```json
   { "type": "view_background_image",
     "view_id": "<SceneView.id>",
     "image": { "id": "<image id>", "width": 640, "height": 480,
                "channels": 3, "dtype": 0, "source": "data", "url": null } }
   ```

   The pixel bytes for `image.id` are sent **first** via the existing binary
   frame transport (`_image_wire.encode_image_frame` → `Transport.send_bytes`),
   so `image-frames.js` has the frame before `ThreeJsView.setBackgroundImage`
   builds the texture.

2. **`Visualizer.set_background_image(view, image)`** — validates `view` is a
   `SceneView`, sets `view.camera_view.background_image = image`, updates
   `LayoutHost._background_frames[image.id]`, sends the binary frame, then sends
   the `view_background_image` JSON. Does **not** re-serialize/re-push the
   layout.

## Decisions (confirmed)

- **Scope = A + B + C** in dependency order, then the example, then docs.
- **Reconciliation keys on `View.id` only** (not scene name, not positional
  index); scene panes are reconciled exactly like every other view.
- **Example is self-contained** (no `data/tless/` dependency): it synthesizes a
  `PinholeCamera` + a small scene + the camera's `Frustum`, mirroring
  `pinhole_calibrated.py`'s two-pane structure, and streams random `uint8` noise
  at the camera's native resolution. (Alternative — reuse the T-LESS
  calibration + GT box — was considered and rejected to keep the 4 fps payload
  small.)
- **No change to Python auto-id assignment.** Object reuse is the identity
  mechanism; the plan does not make ids deterministic across re-construction.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-frontend-scene-pane-reuse.md](./01-frontend-scene-pane-reuse.md) | A: reuse `ThreeJsView` panes by `view.id`, not scene name (fixes the flash) |
| 2 | [02-granular-background-image.md](./02-granular-background-image.md) | B: `set_background_image` API + `view_background_image` wire message |
| 3 | [03-view-reconciliation.md](./03-view-reconciliation.md) | C: single `_viewRegistry` + reconcile every view type by id |
| 4 | [04-example-streaming-pane-swap.md](./04-example-streaming-pane-swap.md) | New example: 4 fps noise background + toolbar button that swaps panes |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Update architecture docs + API reference + changelog |

## Testing as you go

```bash
uv run pytest py/tests/viz -q                     # viz suite (covers the Python side)
node --input-type=module --check <file>           # JS syntax (where node is available)
uv run python tools/build-viewer-js.py --check    # export-library bundle drift gate
uv run python tools/generate-example-docs.py      # example gallery
uv run mkdocs build --strict                      # docs
```

> Note: the live frontend (`templates/viewer.js` + `templates/views/` +
> `templates/controls/` + `templates/renderers/`) is served directly by the
> server as ES modules. `build-viewer-js.py` only bundles the **export** renderer
> library (`js/tanga-viewer.js`), so it does not gate edits to those files.

## Non-goals

- No diffing on the server: `set_layout` still re-serializes and pushes the
  whole `view_layout`; the *frontend* reconciles it.
- No change to scene-entity updates (`scene_update`) or control-value updates
  (`control_update`) — those are already incremental.
- No change to `viz.add(view)`/`remove_view` global-overlay granularity.
- Not fixing the report's symptom 1 (first-push black pane) beyond what B
  sidesteps; that ordering race is a separate follow-up.
