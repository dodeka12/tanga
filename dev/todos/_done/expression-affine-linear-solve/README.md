# AffineExpression Counting-Axis Reduction + Linear Solve — Overview

**Created:** 2026-09-11 | **Status:** Done | **Branch:** `fix/jupyter`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Fix three gaps in `AffineExpression` (the pure-Python symbolic layer in
`py/pytanga/expression/_expression.py`) reported in
`_input/pytanga-affine-expression-counting-axis-contraction.md`:

1. A `DataArray`-introduced counting axis can be reduced at the
   `AffineExpression` top level — `affine_expr(pt=weights)` works instead of
   raising `ValueError: unknown variable(s): ['pt']`.
2. A term that never carried the batched variable is broadcast as a constant
   (scaled by `weights.sum()`) instead of raising when the same axis is reduced
   across the sum.
3. `AffineExpression` gains `.lstsq()` / `.svd()` and a working `.inv()` for any
   sum that reduces to a single linear map in one remaining variable, instead of
   only supporting a single `Expression` term.

## Background

`AffineExpression` is a sum of `Expression` terms that could not be merged into
one tensor.  Its `__call__`/`bind` currently validate bindings only against
`self.names` (the union of *variable* names), so counting-axis labels — which
live inside each term's own tensor, not in `names` — are rejected.  A related
gap: a term that does not contain the batched variable (e.g. a constant offset)
never gains the counting axis in the first place, so reducing it raises
`unknown variable(s)` instead of broadcasting it as a constant repeated once per
batched point.  `AffineExpression` also has no `lstsq`/`svd`, and `inv` is a
`NoReturn` stub that always raises.

`Expression` already has all the machinery: `_evaluate` reduces counting axes
(via `_count_binding_tensor`), and `_variable_matrix`/`lstsq`/`svd`/`inv` build
a flat matrix over one variable's blades and delegate to `numpy.linalg`.  This
plan mirrors that machinery onto the sum-of-terms level.

## Architecture (short)

- All changes are in `py/pytanga/expression/_expression.py` (one module).  No
  change to the documented C++/GA architecture (`docs/dev/architecture/*`), and
  no new public top-level exports.
- Gaps 1 & 3: add `Expression._counting_axes()` and
  `AffineExpression._counting_axes_union()`; `AffineExpression.__call__`
  recognizes counting bindings from the union of its terms' axes, forwards them
  to carrying terms, and passes a private `extra_counting` hint so non-carrying
  terms broadcast as constants (scale by `weights.sum()`) through the same
  `Expression._evaluate` path.
- Gap 2: add `AffineExpression._has_counting_axes()` and
  `AffineExpression._variable_matrix()` (the shared matrix builder); `lstsq` /
  `svd` / `inv` are thin wrappers over it that reuse `numpy.linalg`.

## Decisions (confirmed) — fixed contract

- **`Expression._counting_axes() -> dict[str, int]`** — private helper returning
  the term's counting-axis names → lengths (axes past the output axis whose mask
  is `None`), derived from `_axis_names(self._tensor.labels)` and
  `self._tensor.tensor.masks`.
- **`AffineExpression._counting_axes_union() -> dict[str, int]`** — the union of
  each term's counting axes; if two terms carry the same axis name with
  different lengths, raise `ValueError`.  These names are the recognized
  counting-binding keys.
- **`Expression._evaluate(bindings, check_blades, extra_counting=None)`** — gains
  a private `extra_counting: dict[str, int] | None` hint of counting axes known
  to the surrounding reduction but possibly absent from this term's tensor.  A
  binding key in `extra_counting` but not in the term's own `counting` broadcasts
  the term as a constant: for a sum-reduction it scales the result by
  `float(np.sum(value))`; element-wise (`"_"`) broadcast is out of scope and
  raises `ValueError`.
- **`AffineExpression.__call__`** — `unknown = set(bindings) - self.names -
  set(union_counting)`; variable bindings get the scalar→MV conversion and
  `_check_blades` against `_union_masks()`, while counting bindings are passed to
  every term together with `extra_counting=union_counting`.
- **`AffineExpression._has_counting_axes() -> bool`** —
  `any(t._has_counting_axes() for t in self._terms)`.
- **`AffineExpression._variable_matrix() -> tuple[str, BladeMask, np.ndarray]`**
  — returns `(var_name, var_mask, matrix)`.  Requires exactly one variable name
  and that variable to appear **exactly once in every term** (each term linear in
  it; no constant or repeated-variable terms).  Builds `matrix` by evaluating
  `self` at each canonical basis blade of `var_mask` and flattening the results
  over `out_mask` (counting axes, if any, flatten into extra rows).
- **`AffineExpression.lstsq(rhs=None) -> MV`** / **`.svd() -> (values, mvs)`** —
  same semantics as `Expression.lstsq`/`svd` (homogeneous smallest singular
  vector; an explicit `rhs` requires non-stacked).
- **`AffineExpression.inv(var_name) -> Expression`** — requires non-stacked,
  single-variable/single-occurrence-per-term, and square (`len(out_mask) ==
  len(var_mask)`); `np.linalg.inv(matrix)`, then build the inverse `Expression`
  keyed by `var_name` exactly like `Expression.inv`.  Drop `NoReturn` from the
  `typing` import once it is unused.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-counting-axis-reduction.md](./01-counting-axis-reduction.md) | `_counting_axes` helper + union recognition + broadcast in `AffineExpression.__call__` |
| 2 | [02-variable-matrix.md](./02-variable-matrix.md) | `_has_counting_axes` + `_variable_matrix` matrix builder |
| 3 | [03-linear-solve.md](./03-linear-solve.md) | `lstsq` + `svd` + `inv` over the combined matrix |
| 4 | [04-tests.md](./04-tests.md) | Tests for counting-axis reduction, broadcast, and linear solve |
| 5 | [05-examples.md](./05-examples.md) | Example scripts for counting-axis reduction/broadcast and affine linear solve |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Update expression usage docs + branch changelog |

## Testing as you go

- `uv run pytest py/tests/expression/test_affine.py -q` (phases 1–3, regression)
- `uv run pytest py/tests/expression/ -q` (phases 3–4)
- `uv run ruff check py/pytanga/expression/_expression.py py/tests/expression/` (phase 4)
- `uv run python py/examples/ga/expression/affine_counting_reduction.py` (phase 5, smoke)
- `uv run python py/examples/ga/expression/affine_linear_solve.py` (phase 5, smoke)
- `uv run python tools/generate-example-docs.py --check` (phase 5)
- `uv run mkdocs build --strict` (phases 5–6)

## Non-goals

- No change to `Expression`'s existing `lstsq`/`svd`/`inv` behavior.
- No change to the C++ core or `docs/dev/architecture/*`.
- No support for merging an `AffineExpression` into a single `Expression` tensor.
- No support for inverting affine maps with a constant offset (only homogeneous
  linear maps); constant terms are rejected by `_variable_matrix`.
- No element-wise (`"_"` / multiply-and-keep) broadcast of a constant term — only
  sum-reduction broadcast (scale by `weights.sum()`).
