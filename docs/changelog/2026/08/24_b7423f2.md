# Changes since version 1.0.0

## New Features
- **`VisualizerApp` shutdown from the browser or a handler** —
  `VisualizerApp` now forwards `enable_server_stop_key` (opt-in Ctrl+Q),
  its `run()` blocks on the global shutdown event (so terminal Ctrl+C and
  browser Ctrl+Q both work), and a new `request_shutdown()` method lets an
  event handler (e.g. a "Quit" button) end the app cleanly.

## Bug Fixes
- **Blade-name parsing now honors index order (sign fix)** — `blade_id()`
  gains a sign-aware companion `blade_id_signed()`; string parsing
  (`Algebra("…")`), bracket access (`mv["e31"]`), and dict/tuple-key
  construction now apply the permutation sign, so reversed names resolve
  correctly (`"e31"` → `-e13`, `"e21"` → `-e12`, `"e321"` → `-e123`).
  Previously `"e31"` silently equaled `+e13`, disagreeing with
  `BasisE3.e31 == -BasisE3.e13`.
- **Canonical bivector attributes on 3D-space bases** — `BasisP3`,
  `BasisN3`, and `BasisPGA3` now expose `e12`/`e13`/`e23` in canonical
  ascending order plus the `e31` alias (`-e13`); `BasisE3` now defines
  `e13` canonically with `e31` as its negation.
- **`BasisPGA3.dual()` now matches Dorst's Table 4** — the even-grade rows of
  the `_DUAL_MAP` (scalar, bivector, and pseudoscalar) were negated relative to
  the Hodge star in `PGA4CS` §9.1, so `x ∧ dual(x)` produced `−I₄` on even
  grades.  The map now satisfies `x ∧ dual(x) = +I₄` for every subspace blade.
- **`BasisPGA3.undual()` is now the true inverse of `dual()`** — it previously
  returned `dual()` under the assumption that the J-map is its own inverse, but
  in 4D PGA the double Hodge dual is the grade involution (odd grades pick up a
  sign).  It now returns `grade_involution(dual(a))`, so `undual(dual(x)) == x`
  and `dual(undual(x)) == x` for every subspace blade.
- **`BasisPGA2.dual()` sign fix** — the grade-1 and grade-2 rows of the 3D PGA
  `_DUAL_MAP` were negated relative to the 2D table, so `x ∧ dual(x)` produced
  `−I₃` on those grades.  The map now satisfies `x ∧ dual(x) = +I₃` for every
  subspace blade.  (`undual()` is unchanged: in 3D PGA the J-map is involutive.)
