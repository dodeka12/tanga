# MV Matrix Refactor — Overview

← [Back to Todos](../README.md)

> **Always consider the developer docs** under `docs/dev/` when implementing  
> any step in this plan.  In particular:  
> [Python Coding Style Guide](../../docs/dev/guides/py-coding-style-guide.md)  
> [C++ Coding Style Guide](../../docs/dev/guides/cpp-coding-style-guide.md).

## Goal

Refactor the product-matrix pipeline to:

1. Use blade masks (instead of multivectors) as the first argument in
   blade-mask prediction functions — both in C++ and Python.
2. Split the dual-purpose `MVMatrix` into `MVMatrix` (column data) and
   `MVProductMatrix` (3‑D tensor of product matrices).
3. Adopt a consistent naming convention: `a_mask` (fixed operand A),
   `b_mask` (unknown X), `c_mask` (result C).
4. Add `BladeMask.from_array(list[MV])` for unioning blade sets.
5. Make `product_matrix_array()` accept an optional `a_mask` and return
   `MVProductMatrix`.

---

## Summary of Changes

| # | Change | Scope |
|---|--------|-------|
| 1 | Add C++ mask-based blade-mask prediction functions and bind them | C++ / binding |
| 2 | Add `BladeMask.from_array(list[MV])` classmethod | Python |
| 3 | Rename: `col_mask` → `b_mask`, `row_mask` → `c_mask`, MV mask → `a_mask` | Python |
| 4 | Split `MVMatrix` into `MVMatrix` (column data) and `MVProductMatrix` (3‑D tensor) | Python |
| 5 | `product_matrix()` and `product_matrix_array()` return `MVProductMatrix` | Python |
| 6 | `to_matrix()` accepts a list of MVs → creates multi-column `MVMatrix` | Python / binding |
| 7 | `product_matrix_array()` accepts optional `a_mask` | Python |

---

## Phase Overview

| Phase | File | Description | Effort |
|---|---|---|---|
| 1 | [phase-1-cpp-blade-mask.md](./phase-1-cpp-blade-mask.md) | C++ mask-based blade-mask functions + bindings | ~1.5 h |
| 2 | [phase-2-mv-classes.md](./phase-2-mv-classes.md) | `MVMatrix` / `MVProductMatrix` refactor | ~1 h |
| 3 | [phase-3-blademask-array.md](./phase-3-blademask-array.md) | `BladeMask.from_array` classmethod | ~15 min |
| 4 | [phase-4-solver.md](./phase-4-solver.md) | Solver updates (renames, return types, new params) | ~1.5 h |
| 5 | [phase-5-docs.md](./phase-5-docs.md) | Documentation updates | ~45 min |
| 6 | [phase-6-tests.md](./phase-6-tests.md) | Test updates and new tests | ~1 h |
| **Total** | | | **~6 h** |

---

## Dependency Ordering

```
Phase 1 (C++ mask-based functions + bindings)
    │
    ├──► Phase 2 (MVMatrix / MVProductMatrix)
    │        │
    │        ▼
    ├──► Phase 3 (BladeMask.from_array)
    │        │
    │        ▼
    └──► Phase 4 (Solver updates)
             │
             ├──► Phase 5 (Docs)
             └──► Phase 6 (Tests)
```

- **Phase 1** must complete first: the new C++ bindings are required by Phase 4.
- **Phase 2** can proceed in parallel with Phase 1 (pure Python).
- **Phase 3** is independent but needed by Phase 4.
- **Phase 4** depends on Phases 1, 2, and 3.
- **Phases 5 and 6** come after Phase 4.

---

## Verification

After all phases:

1. Run solver tests: `uv run python -m pytest py/tests/test_solver.py -v`
2. Run full test suite: `uv run python -m pytest py/tests/ -v`
3. Run examples:
   - `uv run python py/examples/solver_basics.py`
   - `uv run python py/examples/solver_line_fitting_p2.py`
   - `uv run python py/examples/solver_point_line_p3.py`
   - `uv run python py/examples/solver_rotor_estimation.py`
4. Smoke test the new API surface (see Phase 6 for the full script).

---

## Key Design Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Mask-based C++ functions are **overloads**, not replacements | Backward compatibility with existing MV-based signatures |
| 2 | `MVMatrix` drops `col_mask` | Column order is defined by input list; no mask needed |
| 3 | `MVProductMatrix` is a **3‑D tensor** `(|a_mask|, |c_mask|, |b_mask|)` | Enables batched `matmul` with a single column vector |
| 4 | Naming: `a_mask`, `b_mask`, `c_mask` | Matches equation A ∘ B = C directly |
| 5 | `a_mask` is optional everywhere | Auto-computed from MV(s) when not given |
| 6 | `from_matrix` returns single MV or list | Backwards-compatible: single column → MV, multi-column → list |