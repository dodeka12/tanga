# Phase 5 — Frontend `Size`, `ViewEvent`, `View` base

## Goal

The JS `View` base class from the fixed contract: extent via `ResizeObserver`,
per-axis constraints, `EventTarget` events, split-agnostic. Pure pieces
(`Size`, `ViewEvent`) are Node-tested.

## Steps

- [x] **5.1 — `templates/views/size.js`**
  - `Size` mirroring the canonical JSON (`px/%/fr/auto`), `fromJSON`, `toJSON`,
    `resolve(available, natural)`, `equals`. No DOM/three imports.

- [x] **5.2 — `templates/views/view-event.js`**
  - `class ViewEvent extends Event { constructor(type, detail) { super(type); this.detail = detail; } }`.

- [x] **5.3 — `templates/views/view.js` — `View extends EventTarget`**
  - Extent: `width`/`height`/`extent` measured by a per-instance `ResizeObserver`
    on `el`, synced in `_syncExtent` (emit `extentchange`).
  - Constraints: `minWidth/maxWidth/minHeight/maxHeight/preferredWidth/preferredHeight`
    setters → normalize via `Size.fromJSON`, compare, emit `constraintschange`
    (and `preferredchange` for the preferred pair).
  - Helpers: `minSizePx/maxSizePx/preferredPx(axis, available)`, `fixedX/fixedY`.
  - Lifecycle: `mount/unmount/destroy`; hooks `_onExtentChanged(w, h)`, `_onMounted`.
  - Sugar: `on(type, handler, opts)` (returns unsubscribe), `off`,
    `emit(type, detail)` (dispatches a `ViewEvent`).

- [x] **5.4 — Node tests `dev/src/js-tests/size.test.mjs`, `view-event.test.mjs`, `view.test.mjs`**
  - `Size` parse/resolve/equals/round-trip; `ViewEvent.detail` passthrough;
    `View` extent/constraint/event/unsubscribe logic (with a `ResizeObserver`
    stub).
  - Run: `node --test 'dev/src/js-tests/*.test.mjs'`.

- [x] **5.5 — Browser smoke**
  - `dev/src/js-tests/view-smoke.html`: instantiate a `View`, mount it, resize
    it, and log `extentchange`/`constraintschange` (manual check; serve the
    file over HTTP so ES modules load).

- [x] **5.6 — Validate**
  - `node --test 'dev/src/js-tests/*.test.mjs'` (green) + open the smoke page.

## Validation

`node --test 'dev/src/js-tests/*.test.mjs'`

## Notes

- `view.js` is DOM-only (ResizeObserver), so it is validated by the browser
  smoke page, not Node. Pure logic stays in `size.js`/`split-resolver.js`.
