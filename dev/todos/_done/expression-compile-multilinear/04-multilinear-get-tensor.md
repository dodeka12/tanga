# Phase 4 — Multilinear `AffineExpression.get_tensor()`

## Goal

Generalize `AffineExpression.get_tensor()` to a single variable appearing
`k >= 1` times per term, returning a rank-`(1 + k)` `MVTensor` suitable for
`get_array()` + `np.einsum("ijk,j,k->i", Q, ω, ω)`. The `k == 1` case stays
byte-for-byte equivalent to today's output.

## Files

- Edit: `py/pytanga/expression/_expression.py` (`AffineExpression.get_tensor`)
- Edit: `py/tests/expression/test_tensor.py`

## Steps

- [x] **4.1 — Rewrite `AffineExpression.get_tensor()`**
  - Keep the single-variable guard (`len(names) != 1` → `ValueError`).
  - Determine `k` from the first term (`len(term.names[var_name])`); require the
    variable present in every term with the **same** `k`, and
    `not term._has_counting_axes()` — otherwise `ValueError` with targeted
    messages.
  - `var_union = self._union_masks()[var_name]`, `out_union = self.out_mask`.
  - Allocate `raw = np.zeros((len(out_union),) + (len(var_union),) * k,
    dtype=np.float64)`.
  - For each term: `t = term.tensor.tensor` (an `MVTensor`, rank `1 + k`);
    `out_pos = [out_union.index(oid) for oid in term.out_mask.ids]`;
    `var_pos = [var_union.index(vid) for vid in term.masks[var_name].ids]`;
    then `raw[np.ix_(out_pos, *([var_pos] * k))] += np.asarray(t.data,
    dtype=np.float64)`.
  - Return `MVTensor(data=raw, masks=(out_union,) + (var_union,) * k)`.

- [x] **4.2 — Preserve the single-occurrence result**
  - The `k == 1` scatter must produce the same array as the current
    `_variable_matrix()`-based implementation. Run the existing
    `test_affine_get_tensor_raw_and_array` first; if it still passes, the
    rewrite is equivalent for `k == 1`.

- [x] **4.3 — Unit tests (multilinear)**
  - Build a quadratic expression with `BasisN3`: `x = Variable("X", twist_mask)`,
    `aff = AffineExpression([x * x, x * alg.e12])` — assert `get_tensor()` shape
    is `(len(out_union), len(twist), len(twist))`.
  - Evaluate `get_tensor().get_array()` (out and both var axes in the twist
    basis) and compare against `aff(X=ω)` for several concrete `ω` via
    `np.einsum("ijk,j,k->i", Q, coeffs, coeffs)`.
  - Inconsistent occurrence counts across terms raises `ValueError` (e.g.
    `AffineExpression([x * x, x])`).
  - Counting-axis term raises `ValueError`.
  - `Expression.get_tensor()` on `x * x` remains rank-3 (regression).

## Validation

`uv run pytest py/tests/expression/test_tensor.py -q`

## Notes

- `Expression.get_tensor()` already returns the raw rank-`(1+k)` tensor with no
  occurrence restriction (`_expression.py:695-703`); this phase only generalizes
  the `AffineExpression` sum.
- `MVTensor.get_array()` already maps each blade axis independently, including
  repeated identical masks, so no change is needed there.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
