# Phase 3 — Frontend flex layout

## Goal

Wire the `gap`/`align`/`justify` and per-child flex model into the DOM views so
flow containers actually lay children out with flexible sizing and spacing.

## Files

- Edit: `py/pytanga/viz/templates/views/stack-view.js`
- Edit: `py/pytanga/viz/templates/views/group-view.js`
- Edit: `py/pytanga/viz/templates/views/control-view.js`
- Edit: `py/pytanga/viz/templates/views/spacer-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`
- New: `dev/src/js-tests/stack-view-flex-smoke.html`

## Steps

- [ ] **3.1 — `stack-view.js`: container knobs.**
  - Accept `gap = null`, `align = 'stretch'`, `justify = 'start'` in the
    constructor; store them.
  - In `_applyFlex()`, set `s.gap = (this.gap == null ? GAP : this.gap) + 'px'`,
    `s.alignItems = this.align`, `s.justifyContent = this.justify` (in addition
    to the existing `display`/`flexDirection`/`flexWrap`).

- [ ] **3.2 — `stack-view.js`: per-child flex.**
  - Import `flowFlex`/`flexCss` from `./flow-size.js` and `stackMainAxis` from
    `./stack-size.js`.
  - In `addChild(view)`, after mounting, compute the main-axis size spec:
    `const mainAxis = stackMainAxis(this.direction)`;
    `const pref = mainAxis === 'x' ? view.preferredWidth : view.preferredHeight`.
  - Set `view.el.style.flex = flexCss(flowFlex(pref))`.
  - If `pref && pref.unit === 'fr'`, set the main-axis min to `0` only when the
    child has no explicit min on that axis (`view.minWidth === null` for `x`,
    `view.minHeight === null` for `y`), so a growing child can shrink.

- [ ] **3.3 — `group-view.js`: forward knobs.**
  - Accept `gap`, `align`, `justify` in the constructor and pass them to
    `super({ direction, children: [], gap, align, justify })`.
  - `_applyFlex()` is inherited from `StackView`, so it now reads the stored
    values; verify the content div gets the same `gap`/`align`/`justify`.

- [ ] **3.4 — `control-view.js`: stop overriding flex/floors.**
  - Remove `this.el.style.flexShrink = '0'`.
  - Keep the `minWidth`/`minHeight` defaults as a safety net for direct JS
    construction, but they will be overridden/cleared by `build.js` (3.5). Do
    not add any new hardcoded flex.

- [ ] **3.5 — `build.js`: pass knobs + make Python authoritative.**
  - In `applySizeSpecs(view, node)`, assign all six fields unconditionally:
    `view.minWidth = node.min_width ?? null`, etc. (this clears a JS default
    when Python serialized `null`).
  - `stack` branch: `new StackView({ direction, scrollable, gap: node.gap, align: node.align, justify: node.justify })`.
  - `group` branch: pass `gap: node.gap, align: node.align, justify: node.justify` too.

- [ ] **3.6 — `spacer-view.js`: fill leftover in flow.**
  - Set `this.el.style.flex = '1 1 0'` (inert under `SplitView`'s absolute
    positioning, active in a flow container).

- [ ] **3.7 — Smoke page.**
  - `stack-view-flex-smoke.html`: build a horizontal `StackView` with a
    `TextAreaView` (`preferredWidth = { value: 1, unit: 'fr' }`), a `ButtonView`,
    and `gap = 8`; assert the stack's computed `gap` is `8px`, `alignItems` is
    `stretch`, the text area's computed `flex` is `1 1 0`, and the button's is
    `0 1 auto`.

## Validation

```powershell
node --test 'dev/src/js-tests/*.test.mjs'
```

Open `dev/src/js-tests/stack-view-flex-smoke.html` in a browser and confirm all
log lines read `ok:`.

## Notes

- The Python defaults from phase 1 mean `node.min_width`/`node.min_height` for a
  control leaf are `{value:120,unit:'px'}`/`{value:32,unit:'px'}`, so the JS
  safety-net values and the serialized values agree; no visual regression.
- Existing smoke pages (`stack-view-smoke.html`, `control-view-smoke.html`,
  `group-view-smoke.html`) should keep passing; re-open them if their assertions
  hardcode the old `flexShrink`/min behavior.
