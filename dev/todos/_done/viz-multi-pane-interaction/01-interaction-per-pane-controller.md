# Phase 1 — Per-pane interaction controller

## Goal

Replace the `interaction.js` module singleton with an `InteractionController`
class so every `SplitView` pane keeps its own pointer state (camera, DOM
element, controls, websocket, space-dim, interactive-object registry, and
drag/click/hover/throttle state). Dragging then works independently in any
number of panes.

## Files

- Edit: `py/pytanga/viz/templates/interaction.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`
- Edit: `py/pytanga/viz/templates/viewer.js`

## Steps

- [x] **1.1 — Convert module state into a class**
  - Move `camera`, `rendererDomElement`, `controls`, `ws`, `_spaceDim`,
    `interactiveObjects`, `_throttles`, `_activeDrag`, `_dragStarted`,
    `_clickState`, `_hoverState`, `_hoveredObjectId` into `InteractionController`
    instance fields; the constructor takes
    `(camera, rendererDomElement, controls, websocket)`.
  - Keep the existing handler/raycast/drag logic but as private methods
    (`_onPointerDown`, `_onPointerMove`, `_onPointerUp`, `_onLostCapture`,
    `_onWheel`, `_onDblClick`, `_getInteractiveHit`, `_computeScreenPlaneVectors`,
    `_findMatchingTriggers`, …) reading `this.*`.
- [x] **1.2 — Attach listeners and expose the public API**
  - Attach the six pointer listeners (`pointerdown`, `pointermove`, `pointerup`,
    `lostpointercapture`, `wheel`, `dblclick`) to `this.rendererDomElement` in the
    constructor (unchanged event set).
  - Implement the README contract: `setSpaceDim`, `setCamera`, `setWebSocket`,
    `registerInteractive`, `unregisterInteractive`, `clearAllInteractive`.
- [x] **1.3 — Export the class, remove the old functions**
  - `export class InteractionController { ... }`; delete the seven module-level
    `export function …` (`initInteraction`, `setSpaceDim`, `setCamera`,
    `registerInteractive`, `unregisterInteractive`, `clearAllInteractive`,
    `setWebSocket`).
- [x] **1.4 — Wire `ThreeJsView` to own a controller**
  - Add `this._interaction = null` in the constructor.
  - In `_initScene()`, replace `initInteraction(this.camera, this.renderer.domElement, this.controls, this._ws)` with
    `this._interaction = new InteractionController(this.camera, this.renderer.domElement, this.controls, this._ws)`.
  - Update call sites: `setSpaceDim(spaceDim)` → `this._interaction.setSpaceDim(spaceDim)`
    (`:281`); `setCamera(this.camera)` → `this._interaction.setCamera(this.camera)`
    (`:304`); `clearAllInteractive()` → `this._interaction.clearAllInteractive()`
    (`:251`); `registerInteractive(...)` → `this._interaction.registerInteractive(...)`
    (`:549`, `:646`); `unregisterInteractive(...)` → `this._interaction.unregisterInteractive(...)`
    (`:565`).
- [x] **1.5 — Forward `setWebSocket` and update `viewer.js`**
  - In `ThreeJsView.setWebSocket(ws)` (`:130`), also call
    `if (this._interaction) this._interaction.setWebSocket(ws);`.
  - In `viewer.js`, remove
    `import { setWebSocket as setInteractionWebSocket } from './interaction.js'`
    (`:11`) and the `setInteractionWebSocket(ws)` call (`:199`); the ws already
    reaches every view via `_setWsOnAllViews`/`view.setWebSocket`.

## Validation

`node --check py/pytanga/viz/templates/interaction.js && node --check py/pytanga/viz/templates/views/three-view.js && node --check py/pytanga/viz/templates/viewer.js && uv run pytest py/tests/viz -q`

## Notes

- This is a pure state-locality refactor — do **not** change the JSON payload
  shapes (`interaction:drag_move`, `drag_start`, `drag_end`, …).
- The shared `raycaster`/`mouse` may become instance fields (safer) — either is
  acceptable as long as they are no longer module-global.
- Single-pane behaviour must remain byte-for-byte equivalent; the existing
  drag/hover/click/scroll/throttle algorithms are preserved.
