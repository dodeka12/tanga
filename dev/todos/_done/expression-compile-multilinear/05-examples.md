# Phase 5 — Runnable examples

## Goal

Add two runnable `.py` examples under `py/examples/ga/expression/` that
explicitly demonstrate the new features, following `dev/workflows/example-docs.md`
(license header + module docstring with `Run with:` and `Keywords:`), then
regenerate the example docs pages.

## Files

- New: `py/examples/ga/expression/compile_fastpath.py`
- New: `py/examples/ga/expression/quadratic_get_tensor.py`
- (Generated) `docs/py/examples/ga/expression/compile_fastpath.md` and
  `.../quadratic_get_tensor.md` via the generator.

## Steps

- [x] **5.1 — `compile_fastpath.py`**
  - Reproduce the report's minimal repro 1 shape: build `~R * X * R` once with
    `BasisN3` + `Geometry`, and benchmark (a) raw `MV` sandwich `r.rev() * x *
    r`, (b) `expr(R=r, X=x)`, (c) `compiled = expr.compile(); compiled(R=r,
    X=x)`.
  - Assert/print that `compiled(...)` equals `expr(...)` and that the compiled
    loop is substantially faster than the bound-`Expression` loop. Also show
    `AffineExpression.compile()` on a two-term sum.
  - Header docstring: one-line `<name>.py — …` description, `Run with:` line,
    `Keywords: expressions, compile, performance, variable_rotor, N3, einsum`.

- [x] **5.2 — `quadratic_get_tensor.py`**
  - Build a quadratic operator with a twist mask: `x = Variable("X", twist)`,
    `aff = AffineExpression([x * x, x * alg.e12])`.
  - `t = aff.get_tensor()` (print shape), `Q = t.get_array(out_basis=twist.basis_vectors,
    axis_bases={1: twist.basis_vectors, 2: twist.basis_vectors})`, and compare
    `np.einsum("ijk,j,k->i", Q, c, c)` to `aff(X=ω)` for a few concrete `ω`.
  - Header docstring: `Keywords: expressions, get_tensor, get_array,
    multilinear, quadratic, einsum, N3`.

- [x] **5.3 — Regenerate example docs and verify**
  - `uv run python tools/generate-example-docs.py`
  - Confirm the two new pages are listed in
    `docs/py/examples/ga/expression/index.md` and reachable from the nav.

## Validation

`uv run python py/examples/ga/expression/compile_fastpath.py && uv run python py/examples/ga/expression/quadratic_get_tensor.py && uv run python tools/generate-example-docs.py --check`

## Notes

- Both examples must run with no extra dependencies beyond numpy/pytanga.
- Do not import `wafer_grinding` (it is not in this repo); keep the examples
  self-contained with `BasisN3`/`Geometry`, mirroring
  `variable_rotor_entity.py` and `tensor_named_basis.py`.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
