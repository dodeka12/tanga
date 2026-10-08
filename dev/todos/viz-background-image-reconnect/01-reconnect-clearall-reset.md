# Phase 1 — Reset background state on `clearAll` + guard `setBackgroundImage`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — "Layout
> re-push" and "Image background").  This stays inside the existing `ThreeJsView`
> scene-content lifecycle; no architecture change.

## Goal

Fix the reported reconnect black-pane bug: after `clear_all` + a reused-pane
`view_layout` rebuild, the background quad must be re-created (not "updated" on a
disposed mesh) so it renders again.

## Files

- Edit: `py/pytanga/viz/templates/views/three-view.js`
- Edit: `js/dev/tests/serve-smoke.py` (regression trigger)
- Edit: `js/dev/tests/reconcile-smoke.mjs` (regression assertion)

## Steps

- [x] **1.1 — Reset background refs in `clearAll()`.**
  - In `three-view.js` `clearAll()` (currently ~line 456–486), after
    `this.sceneObjects.clear();` add:
    ```js
    this._backgroundMesh = null;
    this._backgroundImage = null;
    ```
  - The `while` loop above already removes/disposes the quad (it is a direct
    scene child); these two lines only drop the stale handles so the next
    `setBackgroundImage()` takes the `createImageBackground()` path.

- [x] **1.2 — Guard the `setBackgroundImage()` reuse branch.**
  - In `setBackgroundImage()` (~line 810–814) change the reuse condition to only
    reuse a mesh still attached to the pane:
    ```js
    if (this._backgroundMesh && this._backgroundMesh.parent === this.scene) {
        updateImageBackground(this._backgroundMesh, this._backgroundImage);
    } else {
        this._backgroundMesh = createImageBackground(this._backgroundImage);
        this.scene.add(this._backgroundMesh);
    }
    ```
  - Defense-in-depth: any future path that detaches/disposes the quad without
    clearing the field self-heals by rebuilding instead of writing to a dead mesh.

- [x] **1.3 — Regression: simulate reconnect in the browser smoke.**
  - In `serve-smoke.py`, add a `ButtonView("btn_reconnect", label="Reconnect")`
    whose `async` handler re-sends the full state to the connected session —
    `clear_all`, background frames, `view_layout`, and scene state — mirroring
    the `ready`-handler call to `server._push_full_state(...)` in
    `py/pytanga/viz/server.py` (~line 1147).  Resolve the session ws/scenes/layout
    the same way the `ready` handler does (`_resolve_layout` + `_browser_sessions`).
  - In `reconcile-smoke.mjs`, after the existing swap/noise checks: click
    `button:has-text("Reconnect")`, wait, and assert the left background pane is
    still non-black (screenshot the left pane and require its max brightness to
    exceed a small threshold — the serve-smoke `_noise` background is random
    noise, so a uniformly-black pane means the regression reproduced).
  - This reproduces the client bug faithfully: the bug is in the
    `clear_all` → `view_layout` reuse sequence, which is identical whether the
    socket is new or reused.

## Validation

`node js/dev/tests/check-syntax.mjs`

(Behavioural gate — manual, per `js/dev/README.md`: `uv run python
js/dev/tests/serve-smoke.py` in one terminal, then
`node js/dev/tests/reconcile-smoke.mjs <printed-url>`.)

## Notes

- `clearAll()` is not called on a fresh connect (no scene routes exist yet), so
  these resets cannot affect initial load.
- three.js `Object3D.remove()` clears `parent`, so the `parent === this.scene`
  guard is `false` for a detached quad.
- Commit messages for the steps use the `fix(viz): 1.N — …` convention.
