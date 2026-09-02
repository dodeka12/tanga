# Phase 4 — SplitView fixed-pane semantics

## Goal

Make a fixed-size pane (`min == max`) keep its size without disabling the
splitter on its far side: a splitter trades space between the **nearest
non-fixed** panes on each side, so `[A, fixed_B, C]` leaves both splitters
movable (A↔B borrows from C; B↔C borrows from A) while `fixed_B` never changes.

## Files

- Edit: `py/pytanga/viz/templates/views/split-resolver.js`
- Edit: `py/pytanga/viz/templates/views/split-view.js`
- Edit: `dev/src/js-tests/split-resolver.test.mjs`
- Edit: `dev/src/js-tests/split-view-smoke.html` (if it asserts movability)

## Steps

- [ ] **4.1 — `split-resolver.js`: nearest-movable-neighbor movability.**
  - Replace the per-splitter `movable: !fixed[i] && !fixed[i + 1]` with a helper
    `_hasMovableSide(fixed, start, step)` that scans outward from a side and
    returns `true` once it finds a non-fixed index (or `false` if it runs off
    the end).
  - For splitter `i`, `movable = _hasMovableSide(fixed, i, -1) && _hasMovableSide(fixed, i + 1, +1)`.
  - Keep `items[i].fixed` and `sizes[i]` unchanged (fixed sizes are still honored).

- [ ] **4.2 — `split-view.js`: redistribute across fixed panes.**
  - In `_onSplitterMove`, replace the immediate `leftIdx = index` /
    `rightIdx = index + 1` with a scan: step `leftIdx` down past fixed children
    and `rightIdx` up past fixed children to the nearest non-fixed panes.
  - Apply the drag delta between those two panes with their own
    `minSizePx`/`maxSizePx` clamps (exactly as today, but on the scanned
    indices). Fixed children's `_sizes` are never touched.

- [ ] **4.3 — Update `split-resolver.test.mjs`.**
  - Rewrite/rename the "a fixed middle pins its two neighbors" test: with
    `[A, fixed_B, C, D]`, assert splitters 0 and 1 are now `movable: true` and
    `fixed_B.size === 50`.
  - Add edge cases:
    - `[fixed_A, B]` → splitter 0 `movable: false` (no movable left side).
    - `[A, fixed_B]` → splitter 0 `movable: false` (no movable right side).
    - `[fixed_A, fixed_B, C]` → both splitters `movable: false`.

- [ ] **4.4 — Smoke page.**
  - Extend `split-view-smoke.html` (or add a focused page) to build
    `[A, fixed_B, C]`, assert both splitters are draggable, and assert
    `fixed_B`'s size is unchanged after simulating a drag on splitter 1.

## Validation

```powershell
node --test dev/src/js-tests/split-resolver.test.mjs
```

Open the updated `split-view-smoke.html` and confirm the fixed pane stays fixed
while its far splitter moves.

## Notes

- This is a deliberate behavior change from the current "either neighbor fixed
  ⇒ locked" rule and resolves
  `_input/pytanga-splitview-fixed-pane-disables-unrelated-splitter.md` without a
  new API flag or nested-`SplitView` workaround.
- `deriveMinSize` and `_distribute` are unchanged; only the splitter-movability
  rule and the drag target selection change.
