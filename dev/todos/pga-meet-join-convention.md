# PGA3 Line Sign Fix + PGA2/3 Meet/Join Convention

**Created:** 2026-08-22 | **Status:** Plan — do not implement yet

## Goal

Two related, but independent, fixes for the Gunn/Dorst plane-based PGA models:

1. **Fix the line sign errors** in PGA3 line creation/analysis. A line created
   from two points via `meet()` (or via `create_entity(Line(...))`) currently
   comes out mirrored across the origin when analyzed, because two plane-offset
   sign errors cancel each other only on the `create → analyze` round-trip.
2. **Invert the user-facing `meet()`/`join()` for PGA2/3** so they match the
   Gunn/Dorst literature convention (`meet` = intersection ∧, `join` = span/union ∨),
   while the internal `_meet`/`_join` keep their current meanings. Document this
   naming, and document how to test *incidence* in PGA2/3.

## Background

### A. The two line sign errors (PGA3 only)

The plane convention used everywhere else in the PGA3 modules is
`plane = n + d·e₀` with `d = -(n·point)` (see `create_pga3._plane_opns` and
`analysis_pga3._plane_from_vector`, which are mutually inverse). Two functions
break this convention:

| # | Function | Bug |
|---|----------|-----|
| 1 | `create_pga3.py:_line_opns` (lines 74-75) | builds the two defining planes with `d = +n·origin` instead of `d = -(n·origin)`. This mirrors the *created* line bivector across the origin. |
| 2 | `analysis_pga3.py:_line_origin_from_planes` (lines 239-240, 272) | reconstructs the plane offsets with `d = -(n·point)` (an extra minus), and then returns the Cramér point with a second negation (the current `-det/det` return). Two mirrors cancel on `create → analyze`, but the standalone `meet → analyze` path is wrong. |

**Evidence (numeric, already verified):**

- `Point(1,0,0).meet(Point(0,1,0))` → analyze gives origin `(0.5, 0.5, 0)` with the
  *current* (negated) analysis code — correct. With the *original* (un-negated)
  code it gave `(-0.5, -0.5, 0)` — the visible mirror the user observed.
- `create_entity(Line(Point(1,2,3), Direction(1,2,0)))` → analyze gives origin
  `(0,0,-3)` with the *current* code (wrong; the true closest point is `(0,0,3)`),
  because `_line_opns` still mirrors the line and the corrected analysis now
  exposes it. This is exactly why `test_entity_line_opns_round_trip` and
  `test_scale2_line_invariant` fail with the user's current local edit.

**The fix (two lines each):**

`create_pga3.py:_line_opns`:
```python
d1 = -(n1[0] * origin.x + n1[1] * origin.y + n1[2] * origin.z)
d2 = -(n2x * origin.x + n2y * origin.y + n2z * origin.z)
```

`analysis_pga3.py:_line_origin_from_planes` (drop the double negation cleanly):
```python
d1 = +(n1x * p1.point.x + n1y * p1.point.y + n1z * p1.point.z)
d2 = +(n2x * p2.point.x + n2y * p2.point.y + n2z * p2.point.z)
...
return Point(detx / det, dety / det, detz / det)
```

Both fixes together make the create path AND the meet path correct (verified:
`(0,0,3)` and `(0.5,0.5,0)` respectively). PGA2 has **no** analogous bug — its
`_line_opns` already uses `d = -(n·origin)` and its `_line_from_vector` is
consistent with it.

### B. Meet/join naming is inverted vs Gunn/Dorst

The codebase follows the Hestenes/DFM07 convention (`join` = progressive/span,
`meet` = regressive/intersection), but Gunn/Dorst's *PGA4CS* uses the opposite
names for the plane-based model:

| Operation | DFM07 / current codebase | Gunn & Dorst (PGA4CS §3.1) |
|-----------|--------------------------|-----------------------------|
| outer/span `∧` | `join` (smallest blade containing both) | **meet** (intersection) |
| regressive `∨` = `dual(join(dual(A), dual(B)))` | `meet` (largest blade contained in both) | **join** (union/span) |

Verified against the current code (PGA3 points are grade-3 OPNS trivectors):

- `p1.meet(p2)` → grade 2 = the connecting **line** = Dorst's *join* `P ∨ Q`.
- `p1.join(p2)` → grade 4 = the pseudoscalar = Dorst's *meet* (two points have
  empty intersection).

So a PGA user writing `a.meet(b)` to get the line through two points is using the
*opposite* of the literature name. Inverting the user-facing names for PGA2/3 only
fixes this and does not affect the other algebras.

## Guiding decisions (agreed)

1. **Outer (`^`/`op`) and inner (`|`/`ip`) products are unchanged.** Only the
   user-facing `meet()`/`join()` switch meaning for PGA2/3.
2. **Internal `_meet()`/`_join()` keep their current meanings forever.** They are
   thin wrappers over the C++ `Meet`/`Join` (regressive / progressive). The swap
   lives only in the user-facing `meet()`/`join()`.
3. **The swap is a single `if` in `Algebra.meet()`/`Algebra.join()`** driven by a
   class flag `_swap_meet_join` that `BasisPGA2`/`BasisPGA3` set to `True`. All
   other algebras default to `False` (no behaviour change).
4. **`MV.meet()`/`MV.join()` stay thin delegates** to `self._alg.meet`/
   `self._alg.join`, so they inherit the swap automatically. Only their
   docstrings are updated to explain the PGA exception.
5. **Incidence in PGA2/3 is documented** as the complement-dual outer product
   test `⋆A ∧ ⋆B == 0` (equivalently `A.dual() ^ B.dual() == 0`), per Gunn's
   Poincaré duality (§2.2.4, §2.3 of *Dokument_25*) and Dorst's Hodge-star join
   (§9.2 eq.133: `A ∨ B = ⋆(⋆A ∧ ⋆B)`). The metric-contraction reduction
   `A.dual() | B` is **not** valid in PGA because the pseudoscalar `I₄` is null
   (`I₄² = 0`) — "we cannot undualize so simply" (PGA4CS §3.2).

## Files

- `py/pytanga/geometry/create_pga3.py` — sign fix in `_line_opns`.
- `py/pytanga/geometry/analysis_pga3.py` — sign fix in `_line_origin_from_planes`.
- `py/pytanga/algebra/_algebra.py` — split `join`/`meet` into internal
  `_join`/`_meet` + user-facing `join`/`meet` with the PGA swap `if`.
- `py/pytanga/basis/pga3.py` — add `_swap_meet_join = True`.
- `py/pytanga/basis/pga2.py` — add `_swap_meet_join = True`.
- `py/pytanga/algebra/_mv.py` — update `join`/`meet` docstrings only.
- `py/tests/geometry/test_geometry_pga3_analysis.py` — add the meet/join +
  incidence regression tests.
- `py/tests/geometry/test_geometry_pga2_analysis.py` — add 2D meet/join tests.
- `dev/src/dev_pga_1.ipynb` — change `a.meet(b)` → `a.join(b)` (two points →
  connecting line is the *join* in the Gunn/Dorst convention).
- `docs/py/basis/basis_pga3.md`, `docs/py/basis/basis_pga2.md` — document the
  meet/join convention and the incidence test.
- `docs/py/algebra/algebra.md` — note the PGA2/3 exception on `join`/`meet`.
- `docs/changelog/…` — new branch changelog (see Phase 5).

## Steps

### Phase 1 — Sign fixes

- [x] 1.1 `create_pga3.py:_line_opns`: negate `d1`/`d2`
  (`d = -(n·origin)`), matching `_plane_opns` and PGA2's `_line_opns`.
- [x] 1.2 `analysis_pga3.py:_line_origin_from_planes`: change `d1`/`d2` to
  `+(n·point)` and restore `return Point(detx/det, dety/det, detz/det)`
  (removing the double negation the user added locally).
- [x] 1.3 Run the two currently-failing tests — they must pass:
  `uv run pytest py/tests/geometry/test_geometry_pga3_analysis.py::test_entity_line_opns_round_trip`
  `...::test_scale2_line_invariant`.

### Phase 2 — Meet/join inversion for PGA2/3

- [x] 2.1 `_algebra.py`: add `_swap_meet_join: bool = False` class attribute.
- [x] 2.2 `_algebra.py`: rename the current bodies to `_join` (C++ `join`) and
  `_meet` (C++ `meet`), and add user-facing `join`/`meet`:
  ```python
  def join(self, a, b):
      if self._swap_meet_join:
          return self._meet(a, b)   # Gunn/Dorst join = regressive
      return self._join(a, b)

  def meet(self, a, b):
      if self._swap_meet_join:
          return self._join(a, b)   # Gunn/Dorst meet = progressive/outer
      return self._meet(a, b)
  ```
- [x] 2.3 `basis/pga3.py` and `basis/pga2.py`: set `_swap_meet_join = True`
  (class attribute, documented as the Gunn/Dorst convention).
- [x] 2.4 `_mv.py`: update `MV.join`/`MV.meet` docstrings to state the
  convention: non-PGA = smallest/largest blade; PGA2/3 = Gunn/Dorst
  `join`(union)/`meet`(intersection). No logic change.

### Phase 3 — Tests

- [x] 3.1 Add `test_entity_line_from_two_points_join_round_trip` in
  `test_geometry_pga3_analysis.py`:
  `a = create_entity(b, Point(1,0,0)); c = create_entity(b, Point(0,1,0));
  L = analyze_entity(a.join(c))` → `Line` with origin `(0.5, 0.5, 0)` and
  direction `±(-1,1,0)/√2`.
- [x] 3.2 Add incidence regression tests using the documented predicate:
  for points `(1,0,0)`, `(0,1,0)`, `(0.5,0.5,0)`, `(2,-1,0)` assert
  `P.dual().op(L.dual()).is_zero is True`; for `(0,0,0)`, `(5,5,5)` assert
  `False`. (This is the correct point-on-line test; `P.op(L)` is always zero for
  grade-3 ∧ grade-2 and must not be used.)
- [x] 3.3 Add PGA meet/join convention tests (PGA3 and PGA2):
  - `Point.join(Point)` → grade-2 line (PGA3) / the connecting line.
  - `Point.meet(Point)` → degenerate (empty intersection) on PGA3.
  - `Plane.meet(Plane)` → grade-2 line (intersection) on PGA3.
  - A non-PGA algebra (e.g. `BasisE3`) still has the old semantics
    (`e1.join(e2)` = bivector span; `(e1^e2).meet(e1^e3)` = e1 line).
- [x] 3.4 Run the full geometry + algebra suites:
  `uv run pytest py/tests/geometry py/tests/algebra py/tests/codegen -q`.

### Phase 4 — Docs

- [x] 4.1 `docs/py/basis/basis_pga3.md` (and `basis_pga2.md`): add a
  "Meet / join convention" subsection — `meet` = intersection (∧),
  `join` = union (∨), matching Gunn/Dorst; note the names are inverted relative
  to the other (DFM07-convention) algebras.
- [x] 4.2 Same docs: add an "Incidence" subsection with the complement-dual test
  `A.dual() ^ B.dual() == 0` (= `⋆A ∧ ⋆B = 0`), the point-on-line / point-on-plane
  / line-on-plane examples, and the note that `A.dual() | B` is *not* valid in
  PGA because `I₄² = 0` (PGA4CS §3.2, §9.2).
- [x] 4.3 `docs/py/algebra/algebra.md`: update the `join`/`meet` rows to mention
  the PGA2/3 exception.

### Phase 5 — Changelog + notebook

- [x] 5.1 Add a branch changelog per `dev/workflows/changelog.md`
  (`docs/changelog/YYYY-MM-DD_<branch>.md`). The meet/join inversion is the
  headline **Breaking Changes** bullet:
  - **Breaking: `meet()`/`join()` inverted for PGA2/3 to match Gunn/Dorst** —
    in `BasisPGA2`/`BasisPGA3`, `MV.meet()` is now the intersection (outer
    product) and `MV.join()` the union (regressive product); other algebras are
    unchanged. Code using `a.meet(b)` on PGA to join two points must switch to
    `a.join(b)`.
  - **Bug Fix: PGA3 line offset sign** — `_line_opns` now uses `d = -(n·origin)`
    and `_line_origin_from_planes` drops the compensating double negation, so
    lines round-trip and analyze to the correct side of the origin.
  - **Docs: PGA incidence** — incidence in PGA2/3 is
    `A.dual() ^ B.dual() == 0`; see the basis docs.
- [x] 5.2 `dev/src/dev_pga_1.ipynb`: replace `line = a.meet(b)` with
  `line = a.join(b)` (and update the comment) — the connecting line of two
  points is the Gunn/Dorst **join**.

## Verification (end-to-end)

- [ ] `uv run pytest` full suite green (the two previously-failing tests now pass;
  no regression in `test_blade_ops.py`, which uses E3/N3 and is unaffected).
- [ ] Numeric spot-checks:
  - `Point(1,0,0).join(Point(0,1,0))` → grade-2 line; analyze → origin
    `(0.5,0.5,0)`, direction `(-0.71,0.71,0)`.
  - `create_entity(Line(Point(1,2,3), Direction(1,2,0)))` → analyze → origin
    `(0,0,3)` (not `(0,0,-3)`).
  - `P.dual().op(L.dual()).is_zero` is `True` exactly for on-line points.
- [ ] `uv run ruff check` and `uv run ruff format --check` on the touched files.
- [ ] The `dev/src/dev_pga_1.ipynb` cells run without error (or the equivalent
  scripted check) and the line is on the correct side of the origin.

## Non-goals / optional follow-ups

- **Changing `op`/`ip`/`gp` semantics or symbols** — explicitly out of scope.
- **Re-implementing the C++ `Meet`/`Join`** for PGA — the existing C++ regressive
  `Meet` (via the 5D metric dual) already produces the correct PGA blade up to
  scale (verified: it is proportional to `dual(dual(A) ^ dual(B))` with the
  J-map). We only re-route which one the user-facing names call.
- **PGA2 line sign audit** — checked; PGA2 has no equivalent sign bug (its
  `_line_opns` already uses `d = -(n·origin)`).
- **Changing the DFM07 convention for E2/E3/P2/P3/N2/N3** — out of scope; only
  PGA2/3 follow Gunn/Dorst naming.
