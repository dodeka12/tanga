# Phase 5 — Example scripts

## Goal

Add runnable `.py` examples under `py/examples/ga/expression/` that demonstrate
the new `AffineExpression` capabilities (counting-axis reduction + broadcast,
and `lstsq`/`svd`/`inv`), and regenerate the docs gallery so they appear there.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- New: `py/examples/ga/expression/affine_counting_reduction.py`
- New: `py/examples/ga/expression/affine_linear_solve.py`
- Generated: `docs/py/examples/ga/expression/affine_counting_reduction.md`
- Generated: `docs/py/examples/ga/expression/affine_linear_solve.md`

## Steps

- [x] **5.1 — `affine_counting_reduction.py` (gaps 1 & 3)**
  - Build `f = (v * w) + c` over `BasisE3`: a `v`-linear term plus a constant
    term `c` (an `AffineExpression` with two terms).
  - Bind `v` to a `DataArray` of vectors with counting axis `"n"`, then reduce
    `"n"` at the top level with raw 1-D weights: `result = f(v=data)(n=weights)`.
  - Print/verify `result(w=w_val)` equals `Σ wᵢ·(vᵢ·w_val) + c·Σ wᵢ`,
    demonstrating both top-level counting-axis reduction and constant-term
    broadcast.
  - Follow `dev/workflows/example-docs.md`: license header + module docstring
    with a one-line description, `Run with:` command, and a short `Keywords:`
    line.

- [x] **5.2 — `affine_linear_solve.py` (gap 2)**
  - Build `F = (u * w) + (u * u * w)` (two terms, both linear in `w` but with
    different `u`-degree → `AffineExpression`); bind `u` to a constant MV so
    `F_u` is a single linear map in `w`.
  - Demonstrate `F_u.lstsq(rhs=...)`, `F_u.svd()`, and an `F_u.inv("w")`
    round-trip, printing recovered values and residuals.
  - Same `dev/workflows/example-docs.md` header conventions.

- [x] **5.3 — Regenerate the example docs**
  - `uv run python tools/generate-example-docs.py` to create the `.md` pages and
    nav entries; then `uv run python tools/generate-example-docs.py --check`.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`

## Notes

- Run each script once (`uv run python py/examples/ga/expression/<name>.py`) to
  confirm it is executable and its printed results are plausible.
- Keep keywords short (3–8 terms) and reuse existing ones such as `expressions`,
  `least-squares`, `solve` so MkDocs search clusters the new pages with the
  existing examples.
