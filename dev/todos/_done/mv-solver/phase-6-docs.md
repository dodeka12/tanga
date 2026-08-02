# Phase 6 — Developer Documentation

← [Back to Overview](./overview.md)

> **Always consider the developer docs** under `docs/dev/` when implementing any step in this plan.  
> In particular: the [Python Coding Style Guide](../../../docs/dev/guides/py-coding-style-guide.md).  
> Also review any relevant architecture docs, use-case examples, and best practice documentation found there.

## Goal

Update `docs/py/` to document the new `MVMatrix` and `MVSolver` API for users,
and update `docs/cpp/product-matrices.md` to cross-reference the Python
bindings.

---

## Steps

### 6.1 — Create `docs/py/solver.md` ✓

Create a new user-facing reference page `docs/py/solver.md` covering:

- **Purpose** — what `MVSolver` is and why it is a separate class from `Algebra`.
- **Construction** — `MVSolver(alg)` and the `alg.solver` shorthand.
- **`MVMatrix`** — what it is, its fields (`data`, `row_mask`, `col_mask`), why it bundles masks with data.
- **`BladeMask`** — construction, `from_mv`, `from_str`, `index()`, `union`/`intersection`, why it carries algebra context.
- **Matrix primitives** — `to_matrix`, `from_matrix`, `product_matrix`,
  `product_matrix_array` with a minimal code example.
- **High-level solvers** — `solve`, `solve_lsq`, `solve_mod` with a
  worked example (float and modular-integer).
- **When to use each solver** — table mirroring the one in
  `docs/cpp/product-matrices.md`.

### 6.2 — Update `docs/py/index.md` ✓

Add a row for `solver.md` to the topic table in `docs/py/index.md`.

### 6.3 — Cross-reference in `docs/cpp/product-matrices.md` ✓

Add a short note at the end of `docs/cpp/product-matrices.md` pointing
readers to `docs/py/solver.md` for the Python API:

> **Python API:** See [MVSolver (Python)](../py/solver.md) for the pytanga
> bindings that expose this functionality.
