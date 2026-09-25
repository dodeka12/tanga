# Phase 4 — JS tests under `js/dev/tests/`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add the JS validation for the frontend: **`node --test` unit tests** for the
pure reconciliation/orphan-map core (runs in pre-commit), a **node-only syntax
gate** (also pre-commit), and a **Playwright headless smoke** (manual) for the
DOM/WebGL behaviour. All local; none in GitHub Actions.

## Files

- New: `js/dev/tests/reconcile.test.mjs` (unit tests)
- New: `js/dev/tests/check-syntax.mjs` (node-only syntax gate)
- New: `js/dev/tests/serve-smoke.py` (headless server, no browser)
- New: `js/dev/tests/reconcile-smoke.mjs` (Playwright, manual)

## Steps

- [x] **4.1 — `reconcile.test.mjs` (`node --test`)**
  - Import the pure module from Phase 3
    (`../../py/pytanga/viz/templates/views/reconcile.js`).
  - Cover the reconciliation + orphan-map semantics:
    - empty live map → every node is a **create**, nothing reused/orphaned;
    - same tree re-pushed → all **reuse**, no create/orphan;
    - reordered children (same ids) → all **reuse** (order-independent);
    - a removed node id → reported **orphaned**;
    - an added node id → reported **create**;
    - same id but different `type` → not reused; old id **orphaned** + new
      **create** (the type-mismatch rule);
    - two nodes of the same scene but distinct ids (`sv0`/`sv1`) → both
      **reuse** independently (the original same-scene-pane bug);
    - nested `children` (+ `overlay`) traversal is complete.

- [x] **4.2 — `check-syntax.mjs` (node-only)**
  - Walk `py/pytanga/viz/templates/**/*.js` (ESM) and `js/dev/tests/*.mjs`, and
    spawn `node --input-type=module --check <file>` (`.js`) / `node --check
    <file>` (`.mjs`); fail non-zero on the first error.
  - **Verify in the node clone** that `--input-type=module --check` parses the
    ESM templates; if not, fall back to esbuild parse.

- [x] **4.3 — `serve-smoke.py` (headless server, no browser)**
  - Build a two-`SceneView("world")` layout with a "Swap panes" `ButtonView` and
    a `CameraView(background_image=...)` on the left pane.
  - `viz.set_layout(layout, name="demo")` then
    `viz.start_server(host="localhost", port=0)`; print `viz.url`; block.
  - No `show()` — so it never opens a browser.

- [x] **4.4 — `reconcile-smoke.mjs` (Playwright, manual)**
  - Launch system Chrome headless (`channel: 'chrome'`, SwiftShader flags).
  - `goto('http://localhost:<port>/?view=demo')`, wait for `.tanga-split` + two
    `.tanga-three-view` panes.
  - Capture the two `<canvas>` identities; click "Swap panes"; **assert the
    canvases are reused (same identity), only reordered**, no console errors.
  - Click "New noise" and **assert the canvas identity is unchanged** (background
    quad updates; the pane is not recreated).

## Validation

```
uv run python -m py_compile js/dev/tests/serve-smoke.py
# In the node-equipped clone (never in CI):
node --test js/dev/tests/*.test.mjs
node js/dev/tests/check-syntax.mjs
node js/dev/tests/reconcile-smoke.mjs
```

## Notes

- The unit tests target the pure `views/reconcile.js` (Phase 3), not the
  DOM/three classes — that is the testable seam. DOM/WebGL correctness is the
  Playwright smoke's job.
- No Playwright-bundled browser: use the already-installed system Chrome.

