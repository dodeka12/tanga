# Phase 3 — Full view reconciliation by id (C)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Replace the Phase 1 ad-hoc `reuse` map with a single persistent
`_viewRegistry: Map<view_id, View>` and reconcile **every** view type by id, so
restructuring the layout (reordering, adding, removing panes/controls) reuses
unchanged child views instead of tearing them all down. This is the general
mechanism behind the Phase 1 fix and the swap-pane example.

## Files

- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/pytanga/viz/templates/views/build.js`
- Edit: `py/pytanga/viz/templates/views/view.js` (base reconcile/update hooks)
- Edit: `py/pytanga/viz/templates/views/split-view.js`, `stack-view.js`,
  `group-view.js`, `toolbar-view.js`, `menu-view.js` (container `update`)
- Edit: `py/pytanga/viz/templates/views/three-view.js` (`updateFromNode`)
- Edit: leaf control views (`slider-view.js`, `button-view.js`, `dropdown-view.js`,
  `text-field-view.js`, `text-area-view.js`, `label-view.js`, `markdown-view.js`,
  `color-picker-view.js`, `checkbox-view.js`, `value-edit-view.js`, `table-view.js`,
  `file-chooser-view.js`) — in-place field updates.

## Steps

- [x] **3.1 — Persistent registry (`viewer.js`)**
  - Add module state `let _viewRegistry = new Map();` next to `_layoutRoot`.
  - `_buildLayout` no longer does a full `_destroyViewTree`; it reconciles against
    the previous `_viewRegistry` (the single orphan map) and destroys any registry
    entries the new tree did not claim (the "orphaned" set).

- [x] **3.2 — Reconcile in `buildViewTree` (`build.js`)**
  - Change the signature to `(node, ws, reuse, registry, newScenes)`; add a
    `registerView` helper. Containers are **recreated** (cheap DOM); **leaf
    views** (scene panes + simple controls + spacer/separator) are **reused by
    id** (`reuse.get(node.id)` + `update`/`updateFromNode`), so restructuring
    re-parents the expensive WebGL panes instead of tearing them down.
  - `table_view`, `file_chooser_view`, and `log_view` stay **recreated**
    (stateful; their `destroy()` already unregisters file-browser/log state).

- [x] **3.3 — Containers (recreated, not updated)**
  - `SplitView`/`StackView`/`GroupView`/`ToolbarView`/`MenuView` remain recreated
    each re-push (they are pure flexbox DOM). Children are re-added in the new
    order via `addChild`, so reordering (the swap-pane example) works with the
    reused leaf panes re-parented in place.

- [x] **3.4 — `ThreeJsView.updateFromNode(node)`**
  - Extract the Phase 1 reuse body (clearOverlays + setLock/setNavigation/
    setControls/setViewport/setBackgroundImage/setVisibilityFilter) into
    `updateFromNode`; overlay children are rebuilt after it in `build.js`.

- [x] **3.5 — Leaf control-view `update(node)`**
  - `View.update()` no-op; `ControlView.update(node)` refreshes `controlId`/
    `label`/`tooltip` and `_onMounted` is made idempotent (replaceChildren).
  - Subclass `update(node)` added for slider/button/dropdown/text-field/
    text-area/label/markdown/color-picker/checkbox/value-edit; spacer/separator
    reuse via the no-op `View.update`.

- [x] **3.6 — Control-registry sync**
  - Reused controls re-render (re-register) on re-mount; recreated/removed
    controls are cleaned by their existing `destroy()` (FileChooserView
    `unregisterFileBrowser`, MessageView `forgetMessageView`).

- [x] **3.7 — Rebuild + validate**
  - Rebuild the bundle (drift) and run the viz suite.

## Validation

```
uv run python tools/build-viewer-js.py --check
uv run pytest py/tests/viz -q
```

## Notes

- Reconciliation relies on **stable ids across re-serialization** = reusing the
  same Python `View` objects (the confirmed contract). No Python id-generation
  change is required.
- `_viewRegistry` is the single live-view orphan map; `_sceneRoutes`/`_viewById`
  remain derived routing indexes recomputed from the built tree.
- The live frontend (`viewer.js`/`views/`) is served directly and is not covered
  by `build-viewer-js.py`; `pytest py/tests/viz` gates the Python side, and there
  is no in-repo JS runner (use `node --check` where available).
