# Phase 3 — Compiled fast path + public `compile()`

## Goal

Add a cached compiled evaluation plan to `Expression`, expose it publicly via
`Expression.compile()` / `AffineExpression.compile()`, and route the
fully-bound `MV`/scalar case of `__call__`/`evaluate` through it automatically.
Per call this does one C++ `to_matrix` per variable, one precomputed-path
`np.einsum`, and one C++ `from_matrix` — skipping `MVLabeledTensor`,
`_build_subscript`, `contract_labeled`, and the naive einsum.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- New: `py/tests/expression/test_compile.py`

## Steps

- [x] **3.1 — Add a private compiled-plan structure**
  - Add a private `@dataclass(frozen=True, slots=True)` (or a plain
    `__slots__` class) `_CompiledPlan` near the top of `_expression.py` holding:
    `base` (`np.ndarray`), `base_axes` (`list[int]`), `var_axes`
    (`dict[str, list[int]]`), `out_axes` (`list[int]`), `masks`
    (`dict[str, BladeMask]`), `out_mask` (`BladeMask`), `order`
    (`tuple[str, ...]`), `path` (the `np.einsum_path` result), and the `algebra`.
  - Assign each distinct axis name of `self._tensor.labels` a small integer
    (reuse the same name→int mapping `_build_subscript` uses); `out_axes` is the
    single output label (axis 0). `var_axes[name]` lists the int labels of that
    variable's occurrence axes in occurrence order.

- [x] **3.2 — Add `Expression._build_plan()` / `_compile()`**
  - `_build_plan()` builds a `_CompiledPlan`: compute `base_axes`, `var_axes`,
    `out_axes` from `_axis_names(self._tensor.labels)`; precompute the greedy
    `np.einsum_path` using placeholder arrays (`np.empty((len(mask),), float64)`
    per occurrence) so the path is fixed once.
  - `_compile()` returns a closure `compiled(**bindings) -> MV` that: validates
    the exact keyword set against `self._names` (raising `TypeError` for
    missing/extra), coerces `int`/`float` to the scalar `MV`, cheaply validates
    blades via `mask.ids_outside(value)` (raise the same `ValueError` as
    `_check_blades`), extracts each variable's coefficients once with
    `alg._mod.to_matrix(mv._impl, mask.ids).ravel()`, assembles the einsum args
    in the plan's fixed `order`, runs `np.einsum(..., optimize=path)`, and
    reconstructs the `MV` with `alg._mod.from_matrix(result.reshape(-1, 1),
    out_mask.ids)` wrapped as `MV(impl, alg)`.
  - Cache the plan lazily: add `"_compiled"` to `Expression.__slots__`, init to
    `None` in both `__init__` branches, and build on first use.

- [x] **3.3 — Add the public `Expression.compile()` method**
  - `def compile(self) -> Callable[..., MV]`: for a constant expression
    (`self._names == {}`) return a zero-arg closure returning the constant `MV`
    (`from_tensor(self._tensor.tensor)`); otherwise return `self._compile()`.
  - Docstring documents the contract from the README §2 (fully-bound MV/scalar
    only; `DataArray`/`Expression` bindings raise `TypeError`).

- [x] **3.4 — Route `_evaluate` through the plan automatically**
  - After computing `var_bindings`/`count_bindings` and coercing scalars, if
    `not count_bindings` and `set(var_bindings) == set(self._names)` and every
    value is an `MV`, call `self._compile()(**var_bindings)` with the current
    `check_blades` flag (the compiled closure does the cheap validation only
    when `check_blades` is true) and return the `MV`.
  - Leave the existing loop (DataArray/Expression/composition/counting) intact
    as the fallback. `broadcast_scale` is always 1.0 on this branch (no counting
    bindings), so no scaling is needed.

- [x] **3.5 — Add `AffineExpression.compile()`**
  - `def compile(self) -> Callable[..., MV]`: validate the full keyword set
    against `self.names`; precompute `union = self._union_masks()` and
    `out_union = self.out_mask`; build each term's `Expression` compiled plan
    once. The returned callable validates each binding against the union mask,
    evaluates each term into a coefficient vector over `out_union`, sums them,
    and reconstructs one `MV`. (Per-term auto-routing from §3.4 already covers
    the `AffineExpression.__call__` path.)

- [x] **3.6 — Unit tests (`test_compile.py`)**
  - `compiled(**kw) == expr(**kw)` for: a single-variable expression; the
    `~R * X * R` sandwich (repeated occurrence); a scalar binding; a constant
    expression (`compiled()` == `expr()`).
  - `compiled` raises `TypeError` for missing/extra/non-MV bindings and
    `ValueError` for an out-of-mask blade (messages match `__call__`).
  - `AffineExpression.compile()(**kw) == aff(**kw)` for a multi-term sum with a
    shared variable.
  - Auto path correctness: assert `__call__` results are unchanged for the
    fast-path shapes (they already are covered by the full suite; add an
    explicit equality test).
  - Performance smoke (not asserted): `compile()` loop vs `__call__` loop vs
    raw `MV` sandwich, printing ms/call.

## Validation

`uv run pytest py/tests/expression/test_compile.py py/tests/expression -q`

## Notes

- `alg._mod.to_matrix` / `from_matrix` are the same bindings
  `pytanga.matrix.convert.to_matrix`/`from_matrix` use (`matrix/convert.py:76/87`);
  call them directly to avoid per-call `MVMatrix`/`MVTensor` wrapper allocation.
- Keep the general `contract_labeled` path unchanged; do not add a global
  `optimize` there.
- The plan is immutable and cached on an immutable `Expression`, so no
  invalidation is needed.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
