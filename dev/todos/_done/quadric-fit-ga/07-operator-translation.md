# Phase 7 — Operator translation (linear-map expressions)

## Goal

Let `geo(Translator(t))` return a **linear-map `Expression`** for the quadric
spaces (Q2/Q3), where translation has no versor — applied by contraction:
`trans = geo(Translator(t))`, then `conic_trans = trans(conic)` (or
`trans.evaluate(conic)`).  This is the general "algebraic way to specify the
apex": translate the apex-at-origin cone `q3(base)` to a chosen apex.

## Files

- Edit: `py/pytanga/expression/_expression.py`, `py/pytanga/expression/__init__.py`
- Edit: `py/pytanga/quadric/_create.py`, `py/pytanga/geometry/create_q2.py`, `create_q3.py`
- Edit: `py/pytanga/geometry/create.py`, `py/pytanga/geometry/_geometry.py`
- New: `py/tests/expression/test_linear_map.py`, `py/tests/quadric/test_translate.py`

## Steps

- [x] **7.1 — `linear_map` factory**
  - `linear_map(matrix, out_mask, var_name, var_mask) -> Expression` in
    `_expression.py` (the `Expression.inv()` construction, exposed publicly);
    export from `pytanga.expression`.
- [x] **7.2 — positional apply**
  - `Expression.__call__` / `evaluate` accept a single positional value when the
    expression has exactly one variable (`expr(mv)` / `expr.evaluate(mv)`);
    forward `*args` through `ScalarExpression.__call__` / `evaluate`.
- [x] **7.3 — `create_translator`**
  - `create_translator(basis, x, y, z) -> Expression` for Q2 (dim 6, 2D) and Q3
    (dim 10, 3D): build the translation matrix `M_t` (`coeffs(Hᵀ Q H)`, `H = [[I, −t],[0,1]]`),
    wrap with `linear_map` over the grade-1 mask; re-export from `create_q2`/`create_q3`.
- [x] **7.4 — widen return types**
  - `create` / `create_operator` / `Geometry.create` return `MV | Expression`.
- [x] **7.5 — tests**
  - `test_linear_map.py`: factory shape validation, positional apply on a
    one-variable expression, `evaluate(mv)`.
  - `test_translate.py`: `geo(Translator(t))(conic)` translates; round-trip
    `translate(translate(q, t), -t) ≈ q`; a translated cone's apex equals `t`.
- [x] **7.6 — examples**
  - Rewrite `fit_conic_quadric.py` and `cone_from_conic.py`: OPNS-only
    `BasisQ*`, `geo(Point(...))`, `geo(Translator(apex))`, `sp` incidence,
    `which_entity`/`dual` for analysis — no `embed_point`, `_quad_value`, or raw
    coefficient indexing; regenerate example docs.
- [x] **7.7 — docs + changelog**
  - Update `docs/dev/ga/conic-quadric-space.md` (translation as a linear-map
    operator) and the changelog.

## Validation

`uv run pytest py/tests/expression py/tests/quadric -q`

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
