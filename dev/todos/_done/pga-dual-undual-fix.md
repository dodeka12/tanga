# PGA J-map / Hodge dual — fix `undual`, verify `dual` against Dorst/Gunn

**Created:** 2026-08-24 | **Status:** Planned

> Planning-only document. The fix will be applied from a different machine.
> No changes to the `tanga-tutorial` repo are in scope here.

## Goal

Make `BasisPGA3` / `BasisPGA2` duality correct and self-consistent:

1. `undual()` must be the true inverse of `dual()`: `undual(dual(x)) == x`
   and `dual(undual(x)) == x` for **every** subspace blade.
2. `dual()` (the J-map / Hodge star) must be **exactly** the map defined by
   Dorst/Gunn (see Background). If, after re-checking the papers, the
   correct map genuinely yields `x ∧ dual(x) == −I₄` on even grades, that
   behaviour must be **documented in the function** — not "fixed" away.

## Background

### Authoritative definitions (papers are in `_input/`)

- **Gunn** — `_input/Dokument_25.md` (search "define a map **J**"):
  `J(e_S) = e_{S⊥}` (index complement), extended linearly. Defined between
  the Grassmann algebra and its dual algebra.

- **Dorst** — `_input/PGA4CS.md`, §9.1 "Complement Duality and Hodge ⋆":
  the Hodge star `⋆` is the linear, Euclidean-orthogonal refinement of the
  complement dual; **Table 4** gives the signed map on the basis blades of
  3D PGA relative to `I = e0∧e1∧e2∧e3 = e0123`.

Table 4 (3D PGA), transcribed from `_input/PGA4CS.md`:

```
⋆1    = e0123      ⋆e0123 = 1
⋆e0   = e123       ⋆e123  = −e0
⋆e1   = e032       ⋆e032  = −e1      (e032 = −e023)
⋆e2   = e013       ⋆e013  = −e2
⋆e3   = e021       ⋆e021  = −e3      (e021 = −e012)
⋆e01  = e23        ⋆e23   = e01
⋆e02  = e31        ⋆e31   = e02      (e31 = −e13)
⋆e03  = e12        ⋆e12   = e03
```

This table satisfies `x ∧ ⋆x = +I` for **every** basis blade `x`.

### Issue A — `undual` is not the inverse of `dual` (confirmed bug)

`py/pytanga/basis/pga3.py:154-158` and `py/pytanga/basis/pga2.py:123-127`
implement:

```python
def undual(self, a: MV) -> MV:
    return self.dual(a)
```

under the assumption "the J-map is its own inverse". That assumption is
**false for 4D PGA**. The double Hodge dual carries a grade-dependent sign
(Dorst §9.1: "Undualization is a bit subtle, for when we apply the Hodge
dual twice, a sign may appear"). From Table 4 it is `+1` on even grades and
`−1` on odd grades — i.e. exactly the **grade involution**. Dorst therefore
defines a separate "Hodge undualization `⋆⁻¹`".

Measured over all 16 subspace blades of `BasisPGA3`:

- grades 0, 2, 4 (even): `undual(dual(x)) == x` ✓
- grades 1, 3 (odd):  `undual(dual(x)) == −x` ✗  (8 blades fail)

`BasisPGA2` does not hit this: for 3D PGA the double-dual sign is `+1` for
every grade, so there the J-map *is* involutive.

### Issue B — `dual` (J-map) sign convention vs Dorst Table 4 (needs re-check)

The `_DUAL_MAP` in `py/pytanga/basis/pga3.py:81` matches Table 4 on **odd**
grades but produces **negated** results on **even** grades. Measured on
`BasisPGA3`:

```
x ∧ dual(x) == +I₄   for grades 1 and 3
x ∧ dual(x) == −I₄   for grades 0, 2 and 4   (scalar, bivectors, pseudoscalar)
```

Likely root cause: the `_DUAL_MAP` comments write blades as `ep∧e₁₂₃`
(`ep` first), while the bitmask IDs encode `e₁₂₃∧ep` (`ep` last); these
differ by `(−1)^3 = −1`. So the scalar/bivector/pseudoscalar rows are
negated relative to Table 4. Example: `0: {15: 1.0, 23: 1.0}` produces
`e₁₂₃∧ep + e₁₂₃∧em = −(ep∧e₁₂₃ + em∧e₁₂₃) = −I₄`.

**This is the question to settle against the papers** (Decision 2 below):
is `x ∧ dual(x) == +I₄` for all grades (Dorst Table 4), or is `−I₄` on even
grades actually the intended Gunn/Dorst convention?

## Design decisions

1. **`undual` must be the Hodge undualization, not the J-map.**
   `undual(a) = grade_involution(dual(a))` (equivalently
   `dual(grade_involution(a))`). Verified to round-trip all 16 subspace
   blades. `grade_involution` lives in `py/pytanga/algebra/_algebra.py:367`.
   Confirm the exact `⋆⁻¹` formula in `_input/PGA4CS.md` §9.1 before
   finalising (Dorst: "in odd-D (including 3D!) we have ⋆⁻¹(X) = ⋆X̂").

2. **`dual` must reproduce Dorst's Table 4 / Gunn's J-map exactly.** Re-derive
   every `_DUAL_MAP` entry from the papers. Two acceptable outcomes:
   - **(a)** If the papers define `x ∧ ⋆x = +I` for all grades, fix the
     even-grade rows in `_DUAL_MAP` (negate the scalar/bivector/pseudoscalar
     entries) so the map matches Table 4.
   - **(b)** If it turns out Dorst/Gunn's map genuinely yields
     `x ∧ ⋆x = −I` on even grades (i.e. the current even-grade signs are
     correct), then **document this in the `dual()` docstring** — do not
     change the map.

3. **Keep the docstring honest about signs.** The docstring already claims
   `e_A ∧ J(e_A) = +I₄` (`pga3.py` ~lines 60-79). Whichever Decision 2
   yields, update the docstring and the inline `_DUAL_MAP` comments so the
   stated blade orientation matches the actual bitmask orientation (write
   explicitly `e₀∧e₁₂₃` vs `e₁₂₃∧e₀` — they differ by a sign).

4. **PGA2 gets the same treatment** (check against the 2D table in
   `_input/PGA4CS.md`), even though its `undual` currently round-trips.

## Steps

- [ ] 1. Re-read `_input/PGA4CS.md` §9.1 (Table 4 and the `⋆⁻¹`/double-dual
      formula) and Gunn's J-map in `_input/Dokument_25.md`. Confirm the
      exact even-grade signs and the undualization formula.
- [ ] 2. Settle Issue B (Decision 2) for `BasisPGA3` — fix the even-grade
      `_DUAL_MAP` rows, **or** document the even-grade `−I₄` behaviour.
- [ ] 3. Fix `BasisPGA3.undual` (Decision 1) and update its docstring.
- [ ] 4. Repeat for `BasisPGA2` (`_DUAL_MAP` at `pga2.py:68`, `undual` at
      `pga2.py:123`).
- [ ] 5. Add regression tests (e.g. under `py/tests/basis/`):
      - `undual(dual(x)) == x` and `dual(undual(x)) == x` over all subspace
        blades of PGA3 and PGA2;
      - `dual` matches the (decided) Table-4 mapping for every basis blade;
      - assert/document the `x ∧ dual(x)` sign convention.
- [ ] 6. Run `uv run pytest py/tests` and the PGA notebooks/examples that use
      `dual`/`undual` to confirm no regressions.

## Notes / edge cases

- The 4D PGA pseudoscalar is `I₄ = e0∧e1∧e2∧e3`; the 5D embedding split
  `e0 = ep + em` means a 4D blade containing `e0` maps to **two** 5D blades
  (one per half), each contributing `0.5`/`±0.5`. Keep the split consistent
  when correcting signs.
- `dual()` here is the **PGA complement dual** (J-map/Hodge), NOT the metric
  dual `A·I⁻¹` used by the non-degenerate algebras (`_algebra.py:346`). The
  non-PGA path already round-trips correctly — do not touch it.
- This plan does not change the tutorial repo (`tanga-tutorial`); the
  tutorial-side treatment of `undual` / PGA3 duality should wait until
  pytanga is fixed.

