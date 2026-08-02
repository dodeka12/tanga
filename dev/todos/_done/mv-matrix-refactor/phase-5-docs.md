# Phase 5 — Documentation Updates

← [Back to Overview](./overview.md)

> **Always consider the developer docs** under `docs/dev/` when implementing  
> any step in this plan.

## Goal

Update the user-facing documentation to reflect the renamed parameters, new
classes, and changed return types.

---

## Steps

### Step 5.1 — Update `docs/py/solver.md`

**File:** `docs/py/solver.md`

Make these changes:

1. **Rename parameters throughout:**
   - `col_mask` → `b_mask`
   - `row_mask` → `c_mask`
   - Update all code examples and API signatures.

2. **Document `MVProductMatrix` return type:**
   - Add a short section under "MVMatrix" explaining the new class.
   - Show the 3‑D tensor layout `(|a_mask|, |c_mask|, |b_mask|)`.
   - Explain how to `matmul` with a column vector.

3. **Document new `to_matrix` list-of-MVs capability:**
   - Show example of passing a list of MVs and getting a multi-column `MVMatrix`.

4. **Document new `from_matrix` behavior:**
   - Single column → single `MV` (existing behavior).
   - Multi-column → `list[MV]` (new).

5. **Document `product_matrix_array` with explicit `a_mask`:**
   - Add example showing `a_mask=...` being passed explicitly.
   - Explain that when omitted, `BladeMask.from_array` auto-computes it.

6. **Update all worked examples:**
   - `solve` example — rename masks.
   - Step-by-step example — rename masks.
   - P2 line fitting example — update for `MVProductMatrix` return.

### Step 5.2 — Update `docs/cpp/product-matrices.md`

**File:** `docs/cpp/product-matrices.md`

Make these changes:

1. **Document the new mask-based C++ functions added in Phase 1:**
   - `_EvalProductBladeMask` mask-based overload
   - `EvalProductBladeMask_GP` / `IP` / `OP` mask-based overloads

2. **Update blade mask naming convention throughout:**
   - `xMaskA` / `a_mask` — fixed operand A
   - `xMaskB` / `b_mask` — unknown X subspace
   - `xMaskC` / `c_mask` — result subspace

---

## Files Touched

| File | Action |
|---|---|
| `docs/py/solver.md` | Update parameter names, add `MVProductMatrix` docs, update examples |
| `docs/cpp/product-matrices.md` | Document new C++ functions, update naming convention |