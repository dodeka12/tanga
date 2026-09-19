# Expression compile fast-path + multilinear tensor extraction — Overview

**Created:** 2026-09-18 | **Status:** Done | **Branch:** `feat/expression-speed`

## Goal

Eliminate the ~100x per-call dispatch overhead of repeatedly evaluating a bound
`Expression`/`AffineExpression`, and unblock the "precompute the operator tensor
once, contract manually every step" workaround for bilinear/quadratic operators.
This is the fix for `_input/pytanga-expression-call-overhead-vs-einsum.md`.

Concretely, the plan delivers:

1. **Cheap blade validation** — a lightweight `BladeMask.ids_outside(mv)` that
   checks a concrete `MV`'s non-zero blades against a mask with a single C++
   `blade_mask` call, instead of building a full `BladeMask` and attaching the
   display basis (~33 C++ calls per check today).
2. **Memoized structural metadata** on `AffineExpression` (`_union_masks`,
   `out_mask`, `_counting_axes_union`), which are pure functions of the
   immutable term list and are currently recomputed on every `__call__`.
3. **A compiled evaluation fast path**, exposed publicly as
   `Expression.compile()` / `AffineExpression.compile()` and used automatically
   by `__call__`/`evaluate` for the fully-bound `MV`/scalar case. It precomputes
   the einsum layout + contraction path once, and per call does one C++
   `to_matrix` per variable, one `np.einsum`, and one C++ `from_matrix`.
4. **Multilinear `AffineExpression.get_tensor()`** — one variable appearing
   `k >= 1` times per term returns a rank-`(1 + k)` `MVTensor`, so a quadratic
   operator (`Omega` twice) can be extracted as a fixed `Q[i, j, k]` array and
   contracted with `np.einsum("ijk,j,k->i", Q, ω, ω)`.
5. **Runnable examples + docs + changelog** demonstrating the new features.

## Architecture (short)

- Every `Expression` is stored as an `MVLabeledTensor` (axis 0 = output labelled
  `OUT_LABEL`, then one axis per variable occurrence, then optional `None`-mask
  counting axes). `Expression.__call__` → `_evaluate` → `contract_labeled` →
  `np.einsum`. See `docs/py/ga/expression/usage.md` and
  `docs/dev/architecture/system-overview.md`.
- The per-call cost is not the math but the structural rebuild: `_check_blades`
  builds a `BladeMask(value)` with `_attach_display_basis`
  (`py/pytanga/blade_mask/_mask.py:69/312`), `AffineExpression._union_masks`
  calls `BladeMask.union` every call (`_expression.py:820`),
  `MVLabeledTensor.__post_init__` re-parses labels (`_labeled.py:274`), and
  `contract_labeled`/`_build_subscript` rebuild the einsum layout every call
  (`tensor/ops.py:204/121`) and runs a naive (unoptimized) einsum.
- The fix caches/precomputes all structure on the (immutable) `Expression` and
  leaves only the numeric contraction + one C++ `to_matrix`/`from_matrix` per
  variable on the per-call path. `Expression._tensor`/`_names`/`_masks` are
  assigned only in `__init__` (`_expression.py:57-63`); `AffineExpression._terms`
  is assigned only in `__init__` (`_expression.py:797`). Both are therefore safe
  to memoize without invalidation.
- Files to edit: `py/pytanga/blade_mask/_mask.py`,
  `py/pytanga/expression/_expression.py`. Tests:
  `py/tests/blade_mask/test_blade_mask.py`,
  `py/tests/expression/test_expression.py`,
  `py/tests/expression/test_compile.py` (new),
  `py/tests/expression/test_tensor.py`.

## Canonical contract (fixed up front)

### 1. `BladeMask.ids_outside(mv) -> list[int]`

- Returns the non-zero blade ids of `mv` that are **not** members of this mask,
  in ascending blade-id order (identical ordering to the current
  `_check_blades` message).
- Implemented via `self._ids_from_mv(mv, only_nonzero=True)` + membership against
  `self._index`; **no** `_attach_display_basis`, **no** `BladeMask` construction.
- `mv.algebra` must be this mask's algebra (asserted/raised as in the rest of the
  class).

### 2. `Expression.compile() -> Callable[..., MV]`

- Returns a compiled evaluator for the **fully-bound `MV`/scalar** case.
- The callable accepts one keyword per free variable (all `MV`/`int`/`float`),
  returns an `MV`, and satisfies `compiled(**kw) == expr(**kw)` for every such
  binding (scalar→`MV` coercion and the "blades outside the variable mask"
  `ValueError` included).
- A constant `Expression` (`names == {}`) returns a zero-argument callable
  returning the constant `MV`.
- Raises `ValueError` for a missing/extra binding and for an out-of-mask blade,
  `TypeError` for a non-`MV`/scalar value — consistent with `__call__` where the
  two APIs overlap.
- The plan is built lazily on first use and cached on the `Expression`.

### 3. `AffineExpression.compile() -> Callable[..., MV]`

- Same contract; delegates to each term's compiled plan and sums the coefficient
  vectors into the union output mask before a single `from_matrix`.
- Per-variable validation is against the **union** mask (exactly as
  `AffineExpression.__call__` does today); each term then contracts with its own
  term mask, silently dropping blades outside that term's mask (again matching
  today's behaviour).

### 4. Multilinear `AffineExpression.get_tensor() -> MVTensor`

- Requires exactly one variable name, appearing the **same** number `k >= 1`
  times in **every** term, and no counting axes on any term. Otherwise raises
  `ValueError` (clear, targeted messages).
- Returns `MVTensor` of shape `(len(out_union), len(var_union), …, len(var_union))`
  with `1 + k` axes, built by scatter-summing each term's raw
  `Expression.get_tensor()` into the union masks via `np.ix_`.
- `k == 1` returns the same tensor as the current implementation (backward
  compatible; existing tests keep passing).
- `Expression.get_tensor()` is unchanged (it already returns the raw rank-`(1+k)`
  tensor with no occurrence restriction).

### 5. Automatic fast path (internal, observable only via performance)

- `Expression._evaluate` routes fully-bound, `MV`/scalar-only bindings (no
  `DataArray`, no `Expression` composition, no counting-axis binding) through the
  compiled plan; `AffineExpression.__call__` inherits this per term.
- Results are numerically identical to the general `contract_labeled` path.

## Decisions (confirmed)

- Compile plans and `AffineExpression` metadata are cached on the immutable
  objects; no invalidation needed.
- The auto fast path is **restricted** to fully-bound `MV`/scalar bindings.
  `DataArray`/`Expression`-composition/counting bindings keep the existing
  general path unchanged.
- `compile()` is a public, explicit "separate one-time setup from per-call
  substitution" API; `__call__` uses the same machinery automatically.
- `np.einsum` in the fast path uses a **precomputed** `np.einsum_path` (greedy);
  the general `contract_labeled` path is left as-is.
- Multilinear `get_tensor()` is single-variable only and rejects counting axes
  for now (they are already folded at construction in the motivating case).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-cheap-blade-validation.md](./01-cheap-blade-validation.md) | `BladeMask.ids_outside` + `_check_blades` rewrite |
| 2 | [02-affine-structural-cache.md](./02-affine-structural-cache.md) | Memoize `_union_masks` / `out_mask` / `_counting_axes_union` |
| 3 | [03-compiled-fastpath.md](./03-compiled-fastpath.md) | `compile()` + automatic fast path for `Expression`/`AffineExpression` |
| 4 | [04-multilinear-get-tensor.md](./04-multilinear-get-tensor.md) | Multilinear `AffineExpression.get_tensor()` |
| 5 | [05-examples.md](./05-examples.md) | New runnable examples demonstrating the features |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | User docs + changelog + full validation |

## Testing as you go

- Python (focused): `uv run pytest py/tests/blade_mask py/tests/expression -q`
- Python (full): `uv run pytest py/tests -q`
- Lint: `uv run ruff check py/pytanga py/tests/expression py/tests/blade_mask`
- Types: `uv run ty check py/pytanga`
- Examples: `uv run python py/examples/ga/expression/compile_fastpath.py`,
  `uv run python py/examples/ga/expression/quadratic_get_tensor.py`
- Example docs: `uv run python tools/generate-example-docs.py --check`
- Docs build: `uv run mkdocs build --strict`

## Non-goals

- No C++ changes; no change to the general `contract_labeled` path or its
  `optimize` default.
- No counting-axis support in the compile fast path or in multilinear
  `get_tensor()` (batched/quadrature bindings stay on the general path).
- No `get_tensor()` support for more than one variable name on
  `AffineExpression`.
- No change to `lstsq`/`svd`/`inv` (they keep their single-occurrence
  requirement via `_variable_matrix`).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.

Relevant docs: `docs/py/ga/expression/usage.md` (authoritative expression API),
`docs/py/ga/expression/index.md`, `docs/py/ga/tensors/mvtensor.md`,
`docs/dev/architecture/system-overview.md`.  This work is additive (one
`BladeMask` method, private caching on immutable objects, one new public
`compile()` method, and a generalization of `AffineExpression.get_tensor()`);
it changes no documented architecture.
