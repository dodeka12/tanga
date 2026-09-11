# Phase 6 — Split resolver + `SplitView` + `SpacerView`

## Goal

The split layout math (pure) and the DOM container that uses it, plus the
implicit empty filler.

## Steps

- [x] **6.1 — `templates/views/split-resolver.js` (pure, no DOM)**
  - `resolveSplit(descriptors, available)` (descriptors pre-resolved to px;
    the axis is handled by the caller) returns per-child px sizes, splitter
    positions/`movable` flags, and `spacer`/`overflow` px.
  - Rules: fixed child (`min == max`) pins adjacent splitters; movable splitters
    clamp to both neighbors' `[min, max]`; positive leftover → spacer; negative
    overflow clips.

- [x] **6.2 — Node tests `dev/src/js-tests/split-resolver.test.mjs`**
  - Fixed child → splitter fixed; leftover → spacer; over-constrained → overflow;
    equal/preferred initial sizes; multi-splitter positions.
  - Run: `node --test 'dev/src/js-tests/*.test.mjs'`.

- [x] **6.3 — `templates/views/spacer-view.js`**
  - `SpacerView extends View` (empty, transparent, `pointer-events: none`, no
    min/max).

- [x] **6.4 — `templates/views/split-view.js`**
  - `SplitView extends View`; `orientation`, `children`, `movable`.
  - `addChild` subscribes to child `constraintschange`/`preferredchange` via a
    per-child `AbortController` and re-runs `resolveSplit`; `_sizes` tracks the
    current px sizes as the drag/relayout basis.
  - Splitter bars; `pointerdown/move/up` → recompute neighbor sizes (clamped to
    their min/max) → apply via `el.style` along the axis; implicit `SpacerView`
    fills leftover.

- [x] **6.5 — Browser smoke**
  - `dev/src/js-tests/split-view-smoke.html`: a `SplitView` with two flexible +
    one fixed child; drag the splitter and confirm clamping and spacer fill
    (manual check; serve over HTTP).

- [x] **6.6 — Validate**
  - `node --test 'dev/src/js-tests/*.test.mjs'` (green) + browser smoke.

## Validation

`node --test 'dev/src/js-tests/*.test.mjs'`

## Notes

- `resolveSplit` is the single source of truth for split math; `split-view.js`
  only marshals DOM ↔ resolver. No layout logic duplicated in the container.
