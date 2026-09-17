# Phase 2 — Repeated-occurrence composition (consistent substitution)

## Goal

Verify and complete the `m_v * k` block expansion so that binding a variable
that appears **more than once** in the host to a sub-expression substitutes it
consistently — the sub-expression's free variables become one shared block, not
independent copies — and cover the case where the sub-expression's own free
variable itself appears multiple times.

## Files

- Edit: `py/pytanga/expression/_expression.py` (only if a bug surfaces)
- Edit: `py/tests/expression/test_bind_expression.py`

## Steps

- [x] **2.1 — Repeated host variable, single-occurrence sub-expression**
  - Host `e = v * v` (two occurrences of `v`); sub-expression `g(w) = w * R`
    (`R` a constant MV).  `e.bind(v=g)` must yield one variable `w` with
    `len(result.names["w"]) == 2`; binding `w` to a single `MV x` gives
    `(x * R) * (x * R)` (same `x` on both sides).

- [x] **2.2 — Single host variable, repeated inner free variable**
  - Sub-expression `g(w) = w * w`; host `e = v`; `e.bind(v=g)` yields one `w`
    with two occurrences; binding `w` to `x` gives `x * x`.

- [x] **2.3 — Both repeated (`m_v * k` = 4, exercises `MAX_DEGREE`)**
  - Host `e = v * v`; sub-expression `g(w) = w * w`; `e.bind(v=g)` yields one
    `w` with four occurrences; binding `w` to `x` gives `(x * x) * (x * x)`.

- [x] **2.4 — Consistency with a `DataArray` binding of the shared free variable**
  - For the 2.1 result, bind the shared `w` to a `DataArray` and confirm the
    batched values match evaluating `g(x_i)` for each `x_i` (no cross-copy
    mixing).

## Validation

`uv run pytest py/tests/expression/test_bind_expression.py -q`

## Notes

- A fresh `allocate_block(m_v * k)` per composition call is expected; the four
  labels in 2.3 are a single registered block (not two independent pairs), which
  is what makes the later single-value binding consistent.
- If the helper from Phase 1 already handles `k > 1` (it was written to), this
  phase is mostly tests plus any correctness fixes it reveals.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
