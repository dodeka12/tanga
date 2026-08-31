# Phase 2 — Frontend: scrollable behaviour + custom scrollbar

## Goal

Implement the size decoupling and the scroll region in the JS views, wire the
flag through `build.js`, and inject a custom thin dark scrollbar.

## Files

- Edit: `py/pytanga/viz/templates/views/stack-view.js`
- Edit: `py/pytanga/viz/templates/views/group-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`

## Steps

- [ ] **2.1 — `StackView` flag + size decoupling**
  - Constructor: accept `scrollable = false`, store `this.scrollable`.
  - Import `stackMainAxis` from `./stack-size.js`.
  - `minSizePx(axis, available)`: when
    `this.scrollable && axis === stackMainAxis(this.direction)`, return only the
    explicit min (`super.minSizePx(axis, available)`); otherwise keep the current
    `Math.max(explicit, stackMinSize(...))`.
  - `preferredPx(axis, available)`: after the existing explicit-preferred
    short-circuit, when
    `this.scrollable && axis === stackMainAxis(this.direction)`, return `null`
    instead of `stackPreferredSize(...)`.

- [ ] **2.2 — `_applyScroll()` + custom scrollbar CSS**
  - Add a module-level `_injectScrollStyles()` guarded by
    `document.getElementById('tanga-scroll-styles')` that injects a `<style>` with
    `.tanga-scroll` WebKit `::-webkit-scrollbar` rules (thin ~8px dark thumb) plus
    `scrollbar-width: thin; scrollbar-color: …` for Firefox.
  - Add `_applyScroll()` on `StackView`: when `scrollable`, call
    `_injectScrollStyles()`, add the `tanga-scroll` class to `this._content`, and
    set `overflow: 'auto'`, `minWidth: '0'`, `minHeight: '0'`,
    `flex: '1 1 auto'` on `this._content`. Call it at the end of the constructor.

- [ ] **2.3 — `GroupView` chrome pinning**
  - Constructor: accept `scrollable = false` and forward to `super()`.
  - In `_setupChrome()`, when `scrollable`: set `el.style.overflow = 'hidden'`
    and `header.style.flexShrink = '0'`.
  - After `_setupChrome()` (the content div has now been retargeted), call
    `this._applyScroll()` so scrolling applies to the content region *below* the
    title bar.

- [ ] **2.4 — `build.js` passthrough**
  - `node.type === 'stack'`: pass `scrollable: node.scrollable`.
  - `node.type === 'group'`: pass `scrollable: node.scrollable`.

## Validation

`node --input-type=module --check py/pytanga/viz/templates/views/stack-view.js py/pytanga/viz/templates/views/group-view.js py/pytanga/viz/templates/views/build.js`

## Notes

- `GroupView` sets `this._content` to a fresh div inside `_setupChrome()` *after*
  `super()`, so `_applyScroll()` must be re-invoked there (the constructor's call
  targets `this.el` for a plain `StackView`).
- Keep non-scrollable behaviour byte-for-byte unchanged.
