# JS frontend coding style

The frontend (`py/pytanga/viz/templates/`) must be written so its logic can be
**unit-tested without a browser**.

## Rules

1. **Pure logic goes in DOM-free modules.** Any logic that does not need
   `document`, `window`, or `three` — reconciliation, sizing math, shader
   assembly, serialization helpers — lives in a `.js` module that imports none
   of those. Reference: `templates/views/reconcile.js` (layout reconciliation /
   orphan-map accounting).
2. **Unit-test pure modules with `node --test`.** Every pure module has a
   sibling `*.test.mjs` under `js/dev/tests/`, run with `node --test`.
3. **Keep DOM/WebGL glue thin.** `view.js` / `three-view.js` / `viewer.js` /
   `build.js` stay thin adapters over the pure modules; their behaviour is
   validated by the Playwright smoke (`js/dev/tests/reconcile-smoke.mjs`), not
   by unit tests.
4. **One live-view registry.** The frontend keeps a single `_viewRegistry`
   keyed by stable view id (see
   [`viz-architecture.md`](../architecture/viz-architecture.md)); do not add
   parallel id-indexed maps or orphan registries.

## Example

`templates/views/reconcile.js` exports the pure `collectNodeTypes` +
`planReconciliation`; `build.js` consumes them, and
`js/dev/tests/reconcile.test.mjs` asserts the reuse/orphan semantics (reuse by
id **and** type, create new ids, orphan unclaimed views).
